"""Walk-forward backtest of the prediction models.

For each completed race of the latest season, train on the races before it and
predict it, exactly as the app would have done on the day. Compares training
windows (how many previous seasons to include).

    python backtest.py            # compare windows 0, 1, 2 and all seasons
    python backtest.py 1          # one window only
"""

import sys

import numpy as np
import pandas as pd

from f1data import build_dataset
from f1modelq import WITH_QUALI, WITHOUT_QUALI, _encode, _fit

FIRST_ROUND = 3  # earlier rounds have too little current-season data to train on


def backtest(df, previous_seasons):
    done = df[df["positionOrder"].notna()]
    season = done["year"].max()
    first_year = done["year"].min() if previous_seasons is None else season - previous_seasons
    rows = []
    for rnd in sorted(done[done["year"] == season]["round"].unique()):
        if rnd < FIRST_ROUND:
            continue
        race = done[(done["year"] == season) & (done["round"] == rnd)]
        train = done[(done["race_idx"] < season * 100 + rnd) & (done["year"] >= first_year)]
        for name, features in (("with_quali", WITH_QUALI), ("without_quali", WITHOUT_QUALI)):
            art = _fit(train, features)
            pred = art["model"].predict(_encode(race, features, art["columns"]))
            rank = pd.Series(pred).rank(method="first").values
            actual = race["positionOrder"].values
            rows.append({
                "model": name,
                "round": rnd,
                "mae": np.abs(rank - actual).mean(),
                "spearman": pd.Series(rank).corr(pd.Series(actual), method="spearman"),
                "winner": int(actual[rank.argmin()] == 1),
                "podium": len(set(np.argsort(rank)[:3]) & set(np.argsort(actual)[:3])) / 3,
            })
        # Baseline: finish in grid order (pit-lane starts, grid 0, go last)
        grid = race["grid"].replace(0, 99).rank(method="first").values
        rows.append({
            "model": "grid_order",
            "round": rnd,
            "mae": np.abs(grid - actual).mean(),
            "spearman": pd.Series(grid).corr(pd.Series(actual), method="spearman"),
            "winner": int(actual[grid.argmin()] == 1),
            "podium": len(set(np.argsort(grid)[:3]) & set(np.argsort(actual)[:3])) / 3,
        })
    return pd.DataFrame(rows).groupby("model")[["mae", "spearman", "winner", "podium"]].mean()


if __name__ == "__main__":
    df = build_dataset()["df"]
    windows = [int(a) for a in sys.argv[1:]] or [0, 1, 2, None]
    for w in windows:
        label = "all seasons since 2010" if w is None else f"current season + {w} previous"
        print(f"\nTraining window: {label}")
        print(backtest(df, w).round(3).to_string())
    print("\nmae = average places off; spearman = rank agreement (1 is perfect);")
    print("winner = share of races where the predicted winner won; podium = share of podium drivers picked.")
