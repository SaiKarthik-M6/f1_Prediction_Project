"""Live data layer for the F1 prediction model.

Combines the historical dataset (cleanedData2.csv, 2010 -> 2025 round 15) with
results, qualifying and schedule data fetched from the Jolpica API, then
rebuilds the engineered features over the combined data.

Every feature for a race is computed only from races before it, so the rows
for an upcoming race are built by exactly the same code as the training rows.
"""

import json
import os
import tempfile
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
CSV_PATH = BASE_DIR / "cleanedData2.csv"

API = "https://api.jolpi.ca/ergast/f1"
USER_AGENT = "f1-prediction-dashboard"
CURRENT_SEASON_TTL = 15 * 60   # seconds before the current season is re-checked
MIN_REQUEST_GAP = 0.3          # Jolpica allows 4 requests per second

# Value the historical dataset uses when a driver set no qualifying time
QUALI_FILL = 1012.64

# Numeric circuitId in cleanedData2.csv -> Jolpica circuitId.
# Verified by joining the CSV's (year, round) with the Jolpica schedules.
CIRCUIT_REF = {
    1: "albert_park", 2: "sepang", 3: "bahrain", 4: "catalunya", 5: "istanbul",
    6: "monaco", 7: "villeneuve", 9: "silverstone", 10: "hockenheimring",
    11: "hungaroring", 12: "valencia", 13: "spa", 14: "monza", 15: "marina_bay",
    17: "shanghai", 18: "interlagos", 20: "nurburgring", 21: "imola",
    22: "suzuka", 24: "yas_marina", 32: "rodriguez", 34: "ricard",
    35: "yeongam", 39: "zandvoort", 68: "buddh", 69: "americas",
    70: "red_bull_ring", 71: "sochi", 73: "baku", 75: "portimao",
    76: "mugello", 77: "jeddah", 78: "losail", 79: "miami", 80: "vegas",
}


# ---------------------------------------------------------------- Jolpica

_last_request = 0.0


def _get_json(url):
    global _last_request
    for attempt in range(5):
        wait = MIN_REQUEST_GAP - (time.monotonic() - _last_request)
        if wait > 0:
            time.sleep(wait)
        _last_request = time.monotonic()
        req = urllib.request.Request(
            url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"}
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.load(resp)
        except urllib.error.HTTPError as e:
            if (e.code == 429 or e.code >= 500) and attempt < 4:
                retry_after = e.headers.get("Retry-After")
                time.sleep(float(retry_after) if retry_after else 2 ** attempt)
                continue
            raise
    raise RuntimeError(f"Jolpica request failed: {url}")


def _total(path):
    """Number of rows Jolpica has for an endpoint (one small request)."""
    return int(_get_json(f"{API}/{path}.json?limit=1")["MRData"]["total"])


def _fetch_races(path):
    """Fetch every page of an endpoint and merge the pages by round."""
    races, offset, total = {}, 0, 0
    while True:
        data = _get_json(f"{API}/{path}.json?limit=100&offset={offset}")["MRData"]
        total = int(data["total"])
        for race in data["RaceTable"]["Races"]:
            rnd = int(race["round"])
            if rnd not in races:
                races[rnd] = race
                continue
            for key in ("Results", "QualifyingResults"):
                if key in race:
                    races[rnd].setdefault(key, []).extend(race[key])
        offset += int(data["limit"])
        if offset >= total:
            break
    return [races[r] for r in sorted(races)], total


def _lap_seconds(text):
    """'1:18.518' -> 78.518"""
    if not text:
        return None
    try:
        parts = text.split(":")
        return round(sum(float(p) * 60 ** i for i, p in enumerate(reversed(parts))), 3)
    except ValueError:
        return None


def _entrant(row):
    d, c = row["Driver"], row["Constructor"]
    return {
        "driverRef": d["driverId"],
        "code": d.get("code"),
        "name": f"{d.get('givenName', '')} {d.get('familyName', '')}".strip(),
        "constructorRef": c["constructorId"],
        "team": c.get("name"),
    }


def _schedule_rows(season):
    races, total = _fetch_races(str(season))
    rows = []
    for r in races:
        c, loc = r["Circuit"], r["Circuit"].get("Location", {})
        q = r.get("Qualifying", {})
        rows.append({
            "round": int(r["round"]),
            "raceName": r["raceName"],
            "date": r.get("date"),
            "time": r.get("time"),
            "circuitId": c["circuitId"],
            "circuitName": c.get("circuitName"),
            "locality": loc.get("locality"),
            "country": loc.get("country"),
            "lat": loc.get("lat"),
            "long": loc.get("long"),
            "quali_date": q.get("date"),
            "quali_time": q.get("time"),
            "sprint": "Sprint" in r,
        })
    return rows, total


def _result_rows(season):
    races, total = _fetch_races(f"{season}/results")
    rows = []
    for r in races:
        for x in r.get("Results", []):
            rows.append({
                "round": int(r["round"]),
                **_entrant(x),
                "grid": int(x["grid"]),
                "positionText": x["positionText"],
                "positionOrder": int(x["position"]),
                "status": x.get("status"),
            })
    return rows, total


def _quali_rows(season):
    races, total = _fetch_races(f"{season}/qualifying")
    rows = []
    for r in races:
        for x in r.get("QualifyingResults", []):
            times = [t for t in (_lap_seconds(x.get(k)) for k in ("Q1", "Q2", "Q3")) if t]
            rows.append({
                "round": int(r["round"]),
                **_entrant(x),
                "position": int(x["position"]),
                "best_s": min(times) if times else None,
            })
    return rows, total


_KINDS = {
    "schedule": (_schedule_rows, lambda s: str(s)),
    "results": (_result_rows, lambda s: f"{s}/results"),
    "qualifying": (_quali_rows, lambda s: f"{s}/qualifying"),
}


# ------------------------------------------------------------------ cache

def cache_dir():
    path = Path(os.environ.get("F1_CACHE_DIR") or BASE_DIR / "data_cache")
    try:
        path.mkdir(parents=True, exist_ok=True)
        probe = path / ".write_test"
        probe.write_text("")
        probe.unlink()
        return path
    except OSError:  # read-only filesystem (serverless)
        path = Path(tempfile.gettempdir()) / "f1_data_cache"
        path.mkdir(parents=True, exist_ok=True)
        return path


def today():
    return datetime.now(timezone.utc).date()


def season_rows(season, kind, force=False, warnings=None):
    """Rows for one season of one kind, from the cache when it is still good.

    A finished season is fetched once and kept. The current season is
    re-checked after CURRENT_SEASON_TTL (or when force=True), and only
    downloaded again if Jolpica reports a different number of rows.
    If Jolpica cannot be reached, the cached copy is used.
    """
    fetch, path_for = _KINDS[kind]
    file = cache_dir() / f"{season}_{kind}.json"
    cached = None
    if file.exists():
        try:
            cached = json.loads(file.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            cached = None

    if cached is not None:
        if season < today().year and cached.get("final"):
            return cached["rows"]
        if not force and time.time() - cached["checked_at"] < CURRENT_SEASON_TTL:
            return cached["rows"]

    try:
        if cached is not None and _total(path_for(season)) == cached.get("total"):
            cached["checked_at"] = time.time()
        else:
            rows, total = fetch(season)
            cached = {"rows": rows, "total": total, "checked_at": time.time()}
        cached["final"] = season < today().year
        file.write_text(json.dumps(cached), encoding="utf-8")
    except (urllib.error.URLError, OSError, RuntimeError, ValueError) as e:
        if cached is None:
            raise RuntimeError(f"Could not fetch {season} {kind} from Jolpica: {e}")
        if warnings is not None:
            warnings.append(f"Using cached {season} {kind}; Jolpica unavailable ({e})")
    return cached["rows"]


# ---------------------------------------------------------------- dataset

RAW_COLUMNS = [
    "year", "round", "circuitId", "driverRef", "constructorRef", "grid",
    "positionText", "positionOrder", "status", "quali_best_s", "accident_flag",
]


def load_history():
    """The historical CSV, reduced to raw columns, plus its driverScore values."""
    csv = pd.read_csv(CSV_PATH)
    raw = pd.DataFrame({
        "year": csv["year"],
        "round": csv["round"],
        "circuitId": csv["circuitId"].map(CIRCUIT_REF),
        "driverRef": csv["driverRef"],
        "constructorRef": csv["constructorRef"],
        "grid": csv["grid"].astype(float),
        "positionText": csv["positionText"].astype(str),
        "positionOrder": csv["positionOrder"].astype(float),
        "status": csv["status"],
        "quali_best_s": csv["quali_best_s"],
        "accident_flag": csv["accident_flag"].astype(float),
    })
    if raw["circuitId"].isna().any():
        raise ValueError("cleanedData2.csv has a circuitId missing from CIRCUIT_REF")
    scores = csv.groupby("driverRef")["driverScore"].first()
    return raw, scores


def _season_frame(season, force, warnings):
    """Completed races of one season from Jolpica, in the raw column layout."""
    results = pd.DataFrame(season_rows(season, "results", force, warnings))
    if results.empty:
        return pd.DataFrame(columns=RAW_COLUMNS), results
    schedule = pd.DataFrame(season_rows(season, "schedule", force, warnings))
    quali = pd.DataFrame(season_rows(season, "qualifying", force, warnings))

    frame = results.merge(schedule[["round", "circuitId"]], on="round", how="left")
    if quali.empty:
        frame["quali_best_s"] = np.nan
    else:
        best = quali.groupby(["round", "driverRef"])["best_s"].min().rename("quali_best_s")
        frame = frame.merge(best, on=["round", "driverRef"], how="left")
    frame["year"] = season
    frame["grid"] = frame["grid"].astype(float)
    frame["positionOrder"] = frame["positionOrder"].astype(float)
    # Jolpica only reports "Retired" for recent seasons, not the reason, so
    # whether a retirement was an accident is unknown for these rows.
    frame["accident_flag"] = np.nan
    return frame[RAW_COLUMNS], results


def _prior_mean(df, keys, value="positionOrder"):
    """Mean of `value` over all rows of the same `keys` in earlier races."""
    per_race = (
        df.groupby(keys + ["race_idx"])[value].agg(["sum", "count"]).reset_index()
        .sort_values("race_idx")
    )
    g = per_race.groupby(keys)
    prior_sum = g["sum"].cumsum() - per_race["sum"]
    prior_count = g["count"].cumsum() - per_race["count"]
    per_race["_val"] = (prior_sum / prior_count).where(prior_count > 0)
    merged = df[keys + ["race_idx"]].merge(
        per_race[keys + ["race_idx", "_val"]], on=keys + ["race_idx"], how="left"
    )
    return merged["_val"].values


def _estimate_scores(df, scores):
    """driverScore for drivers who are not in the historical CSV.

    The original driverScore formula is not recoverable from the CSV, so new
    drivers get a value from a linear fit of the known scores on three career
    stats (average classified finish, top-10 rate, accident rate).
    """
    done = df[df["positionOrder"].notna()].assign(top10=lambda d: (d["positionOrder"] <= 10))
    stats = done.groupby("driverRef").agg(
        avg=("pos_clean", "mean"), top10=("top10", "mean"), err=("accident_flag", "mean"),
        races=("positionOrder", "size"),
    )
    stats["avg"] = stats["avg"].fillna(stats["avg"].max())
    stats["err"] = stats["err"].fillna(0.0)

    known = stats.join(scores.rename("score"), how="inner")
    X = np.c_[known[["avg", "top10", "err"]].values, np.ones(len(known))]
    coef, *_ = np.linalg.lstsq(X, known["score"].values, rcond=None)

    new = stats[~stats.index.isin(scores.index)]
    est = pd.Series(
        np.c_[new[["avg", "top10", "err"]].values, np.ones(len(new))] @ coef, index=new.index
    )
    # With only a few races the fit is unreliable, so pull it towards the median
    weight = new["races"] / (new["races"] + 20)
    est = (scores.median() + (est - scores.median()) * weight).clip(scores.min(), scores.max())
    return pd.concat([scores, est])


def add_features(df, scores):
    """Rebuild the engineered features, using only races before each row's race."""
    df = df.sort_values(["year", "round", "positionOrder"], na_position="last").reset_index(drop=True)
    df["race_idx"] = df["year"] * 100 + df["round"]
    classified = df["positionText"].astype(str).str.isdigit()
    df["pos_clean"] = df["positionOrder"].where(classified)
    df["no_quali_time"] = df["quali_best_s"].isna().astype(int)
    df["quali_best_s_filled"] = df["quali_best_s"].fillna(QUALI_FILL)
    df["constructorId_x"] = df["constructorRef"]

    # Driver form: minus the mean of the last k classified finishes
    by_driver = df.groupby("driverRef", sort=False)
    for k in (3, 5, 10):
        df[f"momentum_{k}"] = -by_driver["pos_clean"].transform(
            lambda s: s.shift().rolling(k, min_periods=1).mean()
        )

    # Share of earlier races that ended in an accident (where the cause is known)
    df["driverErrorRate"] = by_driver["accident_flag"].transform(
        lambda s: s.shift().expanding().mean()
    )

    all_scores = _estimate_scores(df, scores)
    df["driverScore"] = df["driverRef"].map(all_scores).fillna(scores.median())

    # Constructor's average finish this season so far; in the first race of a
    # season, its average over the previous season.
    df["constructor_avg_pos"] = _prior_mean(df, ["constructorRef", "year"])
    season_avg = df.groupby(["constructorRef", "year"])["positionOrder"].mean().reset_index()
    season_avg["year"] += 1
    prev = df[["constructorRef", "year"]].merge(
        season_avg, on=["constructorRef", "year"], how="left"
    )["positionOrder"].values
    df["constructor_avg_pos"] = df["constructor_avg_pos"].fillna(pd.Series(prev, index=df.index))

    # Constructor form: minus the mean of its last 5 results before this race
    done = df[df["positionOrder"].notna()]
    roll = done.groupby("constructorRef")["positionOrder"].transform(
        lambda s: s.rolling(5, min_periods=1).mean()
    )
    per_race = (
        done.assign(_roll=roll).groupby(["constructorRef", "race_idx"])["_roll"].last()
        .reset_index().sort_values("race_idx")
    )
    # merge_asof picks, for each row, the constructor's latest earlier race
    left = df[["constructorRef", "race_idx"]].reset_index().sort_values("race_idx")
    asof = pd.merge_asof(
        left, per_race, on="race_idx", by="constructorRef", allow_exact_matches=False
    ).set_index("index")["_roll"]
    df["constructor_momentum"] = -asof.reindex(df.index)

    df["driver_circuit_avg"] = _prior_mean(df, ["driverRef", "circuitId"])
    df["constructor_circuit_avg"] = _prior_mean(df, ["constructorRef", "circuitId"])
    return df


def _race_info(year, row):
    info = {k: (None if pd.isna(v) else v) for k, v in row.items()}
    info["year"] = int(year)
    info["round"] = int(info["round"])
    info["sprint"] = bool(info.get("sprint"))
    return info


def build_dataset(force=False):
    """Fetch what is needed and return the full feature table and race context.

    Returns a dict with:
      df           every completed race since 2010 plus one row per driver for
                   the next race (is_upcoming == True), with features
      next_race    schedule info for the next race, or None after the finale
      last_race    schedule info for the latest completed race
      lineup       drivers expected in the next race
      lineup_source "qualifying" or "last_race"
      quali_available  whether the next race has qualifying results
      warnings     problems that did not stop the build
    """
    warnings = []
    raw, scores = load_history()
    last_csv = (int(raw["year"].max()), int(raw[raw["year"] == raw["year"].max()]["round"].max()))
    season = today().year

    frames, entrants_by_season = [raw], {}
    for yr in range(last_csv[0], season + 1):
        frame, results = _season_frame(yr, force, warnings)
        entrants_by_season[yr] = results
        if yr == last_csv[0]:
            frame = frame[frame["round"] > last_csv[1]]
        if not frame.empty:
            frames.append(frame)
    completed = pd.concat(frames, ignore_index=True)
    completed["is_upcoming"] = False

    latest_year = int(completed["year"].max())
    latest_round = int(completed[completed["year"] == latest_year]["round"].max())
    latest_schedule = pd.DataFrame(season_rows(latest_year, "schedule", False, warnings))
    last_race = _race_info(
        latest_year, latest_schedule[latest_schedule["round"] == latest_round].iloc[0]
    )

    # The next race is the first one on the calendar after the latest result
    next_race = None
    schedule = pd.DataFrame(season_rows(season, "schedule", force, warnings))
    if not schedule.empty:
        done_round = latest_round if latest_year == season else 0
        ahead = schedule[schedule["round"] > done_round].sort_values("round")
        if not ahead.empty:
            next_race = _race_info(season, ahead.iloc[0])

    lineup, lineup_source, quali_available = [], None, False
    df = completed
    if next_race is not None:
        quali = pd.DataFrame(season_rows(season, "qualifying", force, warnings))
        if not quali.empty:
            quali = quali[quali["round"] == next_race["round"]]
        quali_available = not quali.empty

        if quali_available:
            entrants, lineup_source = quali, "qualifying"
        else:
            last_results = entrants_by_season[latest_year]
            entrants = last_results[last_results["round"] == latest_round]
            lineup_source = "last_race"
        lineup = (
            entrants[["driverRef", "code", "name", "constructorRef", "team"]]
            .drop_duplicates("driverRef").to_dict("records")
        )

        upcoming = pd.DataFrame(lineup)[["driverRef", "constructorRef"]]
        upcoming["year"] = season
        upcoming["round"] = next_race["round"]
        upcoming["circuitId"] = next_race["circuitId"]
        upcoming["positionText"] = ""
        for col in ("grid", "positionOrder", "quali_best_s", "accident_flag"):
            upcoming[col] = np.nan
        upcoming["status"] = None
        if quali_available:
            q = quali.set_index("driverRef")
            upcoming["grid"] = upcoming["driverRef"].map(q["position"]).astype(float)
            upcoming["quali_best_s"] = upcoming["driverRef"].map(q["best_s"]).astype(float)
        upcoming["is_upcoming"] = True
        df = pd.concat([completed, upcoming[RAW_COLUMNS + ["is_upcoming"]]], ignore_index=True)

    df = add_features(df, scores)
    return {
        "df": df,
        "next_race": next_race,
        "last_race": last_race,
        "lineup": lineup,
        "lineup_source": lineup_source,
        "quali_available": quali_available,
        "warnings": warnings,
    }


if __name__ == "__main__":
    data = build_dataset()
    d = data["df"]
    print(f"{len(d)} rows, {d['year'].min()}-{d['year'].max()}")
    print("Latest completed race:", data["last_race"]["year"], data["last_race"]["raceName"])
    nr = data["next_race"]
    if nr:
        print("Next race:", nr["year"], "round", nr["round"], nr["raceName"], nr["date"])
        print("Qualifying available:", data["quali_available"], "| lineup from:", data["lineup_source"])
        cols = ["driverRef", "constructorRef", "grid", "momentum_3", "momentum_10", "driverScore",
                "constructor_avg_pos", "constructor_momentum", "driver_circuit_avg"]
        print(d[d["is_upcoming"]][cols].round(2).to_string(index=False))
    for w in data["warnings"]:
        print("WARNING:", w)
