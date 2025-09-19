"use client"

import React from "react"
import { ArrowLeft } from "lucide-react"
import "./raceOrderResults.css"


// Top of file (below imports)
const refToName = (ref) =>
  ref ? ref.split("_").map(w => w[0].toUpperCase() + w.slice(1)).join(" ") : ""

export function RaceOrderResult({ results = [], onMakeAnother }) {
  if (!results.length) {
    return React.createElement("div", { className: "race-order-result-container" },
      React.createElement("p", null, "No results yet."))
  }

  return React.createElement(
    "div",
    { className: "race-order-result-container" },
    React.createElement(
      "div",
      { className: "standings-header" },
      React.createElement("h1", { className: "standings-title" }, "Predicted Race Order"),
      React.createElement(
        "button",
        { className: "back-button", onClick: onMakeAnother },
        React.createElement(ArrowLeft, { className: "back-icon" }),
        "Make Another Prediction"
      )
    ),
    React.createElement(
      "div",
      { className: "standings-table" },
      React.createElement(
        "div",
        { className: "table-header" },
        React.createElement("div", { className: "header-cell pos" }, "POS."),
        React.createElement("div", { className: "header-cell driver" }, "DRIVER"),
        React.createElement("div", { className: "header-cell position" }, "PREDICTED POS."),
        React.createElement("div", { className: "header-cell team" }, "TEAM"),
        React.createElement("div", { className: "header-cell score" }, "SCORE"),
      ),
      results.map((r, index) => {
        const name = refToName(r.driverRef)
        const initials = name.split(" ").map(n => n[0]).join("")
        return React.createElement(
          "div",
          { key: `${r.driverRef}-${r.proj_rank}`, className: "table-row" },
          React.createElement("div", { className: "cell pos" }, r.proj_rank),
          React.createElement(
            "div",
            { className: "cell driver" },
            React.createElement("div", { className: "driver-avatar" },
              React.createElement("div", { className: "driver-avatar-fallback" }, initials)),
            React.createElement("span", { className: "driver-name" }, name)
          ),
          React.createElement("div", { className: "cell position" }, `P${r.proj_rank}`),
          React.createElement("div", { className: "cell team" }, "F1 Team"), // You can map this to actual teams
          React.createElement("div", { className: "cell score" }, (r.predicted_position.toFixed?.(3) ?? r.predicted_position).toString())
        )
      })
    )
  )
}