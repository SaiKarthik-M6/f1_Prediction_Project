"use client"

import React, { useState } from "react"
import { Trophy, Loader2 } from "lucide-react"
import "./raceOrder.css"

export function RaceOrder({ onSubmit }) {
  const [isLoading, setIsLoading] = useState(false)

  const handleSubmit = async () => {
    setIsLoading(true)
    try {
      const res = await fetch("http://127.0.0.1:8000/predict/race-order", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ year: 2025, round: 16, circuitId: 14, use_quali: true }),
      })
      const data = await res.json()
      // wait 5 seconds before showing results
      await new Promise((resolve) => setTimeout(resolve, 3000))
      onSubmit(data.results)   // <-- send full list up
    } finally {
      setIsLoading(false)
    }
  }

  return React.createElement(
    "div",
    { className: "race-order-container" },
    React.createElement("h1", { className: "main-title" }, "Predict Full Race Order"),
    React.createElement(
      "p",
      { className: "subtitle" },
      "Get complete race predictions with driver standings",
    ),
    React.createElement(
      "button",
      {
        className: `predict-button ${isLoading ? "disabled" : ""}`,
        onClick: handleSubmit,
        disabled: isLoading,
      },
      isLoading
        ? React.createElement(
            React.Fragment,
            null,
            React.createElement(Loader2, { className: "loading-icon" }),
            "Generating Predictions...",
          )
        : React.createElement(
            React.Fragment,
            null,
            "Predict Race Order",
            React.createElement(Trophy, { className: "trophy-icon" }),
          ),
    ),
  )
}
