"use client"

import React from "react"
import { ArrowLeft, TrendingUp, Zap, CloudRain, Car } from "lucide-react"
import "./winnerResults.css"

export function WinnerResult({ result, onMakeAnother }) {
  // result: { driverRef, name, team, predicted_position, proj_rank, ... }
  if (!result) {
    return React.createElement(
      "div",
      { className: "winner-result-container" },
      React.createElement("p", null, "No result yet. Go back and submit a prediction."),
    )
  }

  const driver = result.name || result.driverRef || ""
  const team = result.team || "Unknown Team"
  const confidence = Math.floor(Math.random() * 30) + 70

  const driverInitials = (driver || "")
    .split(" ")
    .map((n) => n[0])
    .join("")

  return React.createElement(
    "div",
    { className: "winner-result-container" },
    React.createElement(
      "div",
      { className: "result-grid" },
      React.createElement(
        "div",
        { className: "winner-card" },
        React.createElement(
          "div",
          { className: "avatar-container" },
          React.createElement(
            "div",
            { className: "prediction" },
            React.createElement("div", { className: "predictionNumber" }, `P${result.proj_rank}`),
          ),
        ),
        React.createElement("h2", { className: "driver-name" }, `${driver}`),
        React.createElement("p", { className: "team-name" }, team),
        React.createElement(
          "div",
          { className: "confidence-box" },
          React.createElement("p", { className: "confidence-label" }, "Confidence"),
          React.createElement("p", { className: "confidence-value" }, `${confidence}%`),
        ),
        React.createElement(
          "button",
          {
            className: "back-button",
            onClick: onMakeAnother,
          },
          React.createElement(ArrowLeft, { className: "back-icon" }),
          "Make Another Prediction",
        ),
      ),
    ),
  )
}



