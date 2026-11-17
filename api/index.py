import sys
import threading
import time
from pathlib import Path
from typing import Optional

import pandas as pd
from fastapi import APIRouter, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# f1data.py and f1modelq.py live in the project root, one level above this file
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from f1data import CURRENT_SEASON_TTL, build_dataset  # noqa: E402
from f1modelq import load_or_train, predict_next_race  # noqa: E402

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Data and models are built on the first request and rebuilt when stale.
# build_dataset() only downloads again when Jolpica has new rows, and
# load_or_train() only retrains when a new race result has come in.
_state = {"data": None, "artifacts": None, "built_at": 0.0}
_lock = threading.Lock()


def get_state(force=False):
    with _lock:
        stale = time.time() - _state["built_at"] > CURRENT_SEASON_TTL
        if force or stale or _state["data"] is None:
            try:
                data = build_dataset(force=force)
                artifacts = load_or_train(data["df"])
            except Exception as e:
                if _state["data"] is None:
                    raise HTTPException(status_code=503, detail=f"Could not load race data: {e}")
                # keep serving the previous data if a refresh fails
                _state["data"]["warnings"] = [f"Refresh failed: {e}"]
                _state["built_at"] = time.time()
                return _state
            _state.update(data=data, artifacts=artifacts, built_at=time.time())
        return _state


class RaceOrderRequest(BaseModel):
    # None = use qualifying data when it is available
    use_quali: Optional[bool] = None


class WinnerRequest(RaceOrderRequest):
    driver: str


def _context(state):
    data, artifacts = state["data"], state["artifacts"]
    year, rnd = artifacts["trained_through"]
    return {
        "next_race": data["next_race"],
        "last_race": data["last_race"],
        "quali_available": data["quali_available"],
        "lineup_source": data["lineup_source"],
        "trained_through": {"year": year, "round": rnd},
        "warnings": data["warnings"],
    }


def _predict(req):
    state = get_state()
    data = state["data"]
    if data["next_race"] is None:
        raise HTTPException(status_code=404, detail="There is no upcoming race on the calendar.")
    # Qualifying can only be used once it has happened
    use_quali = data["quali_available"] and req.use_quali is not False
    try:
        out = predict_next_race(data["df"], state["artifacts"], use_quali)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {e}")

    names = {d["driverRef"]: d for d in data["lineup"]}
    results = []
    for r in out.to_dict("records"):
        info = names.get(r["driverRef"], {})
        grid = r.get("grid")
        results.append({
            "driverRef": r["driverRef"],
            "name": info.get("name") or r["driverRef"],
            "code": info.get("code"),
            "constructorRef": r["constructorRef"],
            "team": info.get("team") or r["constructorRef"],
            "grid": None if grid is None or pd.isna(grid) else int(grid),
            "predicted_position": float(r["predicted_position"]),
            "proj_rank": int(r["proj_rank"]),
        })
    return {**_context(state), "use_quali": use_quali, "results": results}


router = APIRouter()


@router.get("/")
def root():
    return {"ok": True, "message": "F1 Prediction API is running"}


@router.get("/health")
def health():
    return {"ok": True, "data_loaded": _state["data"] is not None}


@router.get("/race/next")
def next_race():
    """The next race, the drivers expected in it, and how current the data is."""
    state = get_state()
    return {**_context(state), "lineup": state["data"]["lineup"]}


@router.post("/refresh")
def refresh():
    """Check Jolpica for new results now instead of waiting for the cache to expire."""
    state = get_state(force=True)
    return {**_context(state), "lineup": state["data"]["lineup"]}


@router.post("/predict/race-order")
def predict_race_order(req: RaceOrderRequest):
    return _predict(req)


@router.post("/predict/winner")
def predict_winner(req: WinnerRequest):
    out = _predict(req)
    driver_ref = req.driver.strip().lower()
    row = next((r for r in out["results"] if r["driverRef"] == driver_ref), None)
    if row is None:
        raise HTTPException(status_code=404, detail=f"Driver '{req.driver}' is not in the lineup")
    del out["results"]
    return {**out, **row}


# The frontend calls /api/... (Vercel rewrite in production, CRA proxy locally).
# The same routes are also served without the prefix for direct use.
app.include_router(router, prefix="/api")
app.include_router(router)
