"use client"

import React, { useState } from "react"
import { Trophy, Loader2 } from "lucide-react"
import { predictRaceOrder } from "../api"
import "./raceOrder.css"

export function RaceOrder({ onSubmit }) {
  const [isLoading, setIsLoading] = useState(false)

  const handleSubmit = async () => {
    setIsLoading(true)
    try {
      const data = await predictRaceOrder()
      // short pause before showing results
      await new Promise((resolve) => setTimeout(resolve, 3000))
      onSubmit(data.results || [])   // <-- send full list up
    } catch (e) {
      alert(e.message)
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
