from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pandas as pd
from f1modelq import (
  artifacts, df, lineup, quali_dict,
  build_snapshot_for_lineup, predict_post_quali, train2Model
)

app = FastAPI()
app.add_middleware(
  CORSMiddleware,
  allow_origins=[
    "http://localhost:3000",
    "http://localhost:3001",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:3001",
  ],
  allow_credentials=True,
  allow_methods=["*"],
  allow_headers=["*"],
)

# Ensure artifacts exist (train once at startup if not loaded from disk)
_artifacts = artifacts if artifacts is not None else train2Model(df)

class WinnerRequest(BaseModel):
  driver: str
  year: int = 2025
  round: int = 16
  circuitId: int = 14
  use_quali: bool = True

class RaceOrderRequest(BaseModel):
  year: int = 2025
  round: int = 16
  circuitId: int = 14
  use_quali: bool = True

@app.get("/health")
def health(): return {"ok": True} 

@app.post("/predict/winner")
def predict_winner(req: WinnerRequest):
  snap = build_snapshot_for_lineup(df, lineup, req.year, req.round, req.circuitId)
  out = predict_post_quali(snap, _artifacts, quali_dict)
  driver_ref = req.driver.lower()
  row = out[out["driverRef"] == driver_ref]
  if row.empty:
    return {"error": f"driver '{req.driver}' not found"}
  return {
    "driverRef": driver_ref,
    "predicted_position": float(row["predicted_position"].values[0]),
    "proj_rank": int(row["proj_rank"].values[0]),
  }

@app.post("/predict/race-order")
def predict_race_order(req: RaceOrderRequest):
  snap = build_snapshot_for_lineup(df, lineup, req.year, req.round, req.circuitId)
  out = predict_post_quali(snap, _artifacts, quali_dict)
  results = out[["driverRef","predicted_position","proj_rank"]].sort_values("proj_rank")
  return {"results": [
    {"driverRef": r.driverRef, "predicted_position": float(r.predicted_position), "proj_rank": int(r.proj_rank)}
    for r in results.itertuples(index=False)
  ]}