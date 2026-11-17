"use client"

import React, { useState } from "react"
import { TrendingUp, Loader2 } from "lucide-react"
import { predictDriver } from "../api"
import "./predictWinner.css"

// lineup: drivers expected in the next race, from the API
export function PredictWinner({ lineup = [], onSubmit }) {
  const [selectedDriver, setSelectedDriver] = useState(null)
  const [isLoading, setIsLoading] = useState(false)
  const [isDropdownOpen, setIsDropdownOpen] = useState(false)

  const handleSubmit = async () => {
    if (!selectedDriver) return
    setIsLoading(true)
    try {
      const data = await predictDriver(selectedDriver.driverRef)
      // short pause before showing results
      await new Promise((resolve) => setTimeout(resolve, 3000))
      onSubmit(data)
    } catch (e) {
      alert(e.message)
    } finally {
      setIsLoading(false)
    }
  }
  
  const handleDriverSelect = (driver) => {
    setSelectedDriver(driver)
    setIsDropdownOpen(false)
  }

  return React.createElement(
    "div",
    { className: "predict-winner-container" },
    React.createElement("h1", { className: "main-title" }, "Predict the Results of the Driver"),
    React.createElement("p", { className: "subtitle" }, "What position will they take the checkered flag at the next Grand Prix?"),
    React.createElement(
      "div",
      { className: "form-section" },
      React.createElement(
        "div",
        { className: "select-container" },
        React.createElement(
          "button",
          {
            className: "select-trigger",
            onClick: () => setIsDropdownOpen(!isDropdownOpen),
          },
          selectedDriver ? selectedDriver.name : (lineup.length ? "Enter Driver Name" : "Loading drivers..."),
        ),
        isDropdownOpen &&
          React.createElement(
            "div",
            { className: "select-dropdown" },
            lineup.map((driver) =>
              React.createElement(
                "div",
                {
                  key: driver.driverRef,
                  className: "select-item",
                  onClick: () => handleDriverSelect(driver),
                },
                `${driver.name} · ${driver.team}`,
              ),
            ),
          ),
      ),
      React.createElement(
        "button",
        {
          className: `submit-button ${!selectedDriver || isLoading ? "disabled" : ""}`,
          onClick: handleSubmit,
          disabled: !selectedDriver || isLoading,
        },
        isLoading
          ? React.createElement(
              React.Fragment,
              null,
              React.createElement(Loader2, { className: "loading-icon" }),
              "Analyzing...",
            )
          : React.createElement(
              React.Fragment,
              null,
              "Submit Prediction",
              React.createElement(TrendingUp, { className: "submit-icon" }),
            ),
      ),
    ),
  )
}
