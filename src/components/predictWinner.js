"use client"

import React, { useState } from "react"
import { TrendingUp, Loader2 } from "lucide-react"
import "./predictWinner.css"

const F1_DRIVERS = [
  "Max Verstappen",
  "Lando Norris",
  "Charles Leclerc",
  "Lewis Hamilton",
  "George Russell",
  "Carlos Sainz",
  "Oscar Piastri",
  "Fernando Alonso",
  "Lance Stroll",
  "Esteban Ocon",
  "Pierre Gasly",
  "Alexander Albon",
  "Yuki Tsunoda",
  "Liam Lawson",
  "Nico Hulkenberg",
  "Kevin Magnussen",
  "Gabriel Bortoleto",
  "Issack Hadjar",
  "Kimi Antonelli",
  "Ollie Bearman",
]

const UI_TO_REF = {
    "Max Verstappen": "verstappen",
    "Lando Norris": "norris",
    "Charles Leclerc": "leclerc",
    "Lewis Hamilton": "hamilton",
    "George Russell": "russell",
    "Carlos Sainz": "sainz",
    "Oscar Piastri": "piastri",
    "Fernando Alonso": "alonso",
    "Lance Stroll": "stroll",
    "Esteban Ocon": "ocon",
    "Pierre Gasly": "gasly",
    "Alexander Albon": "albon",
    "Yuki Tsunoda": "tsunoda",
    "Liam Lawson": "lawson",
    "Nico Hulkenberg": "hulkenberg",
    "Ollie Bearman": "bearman",
    "Gabriel Bortoleto": "bortoleto",
    "Issack Hadjar": "hadjar",
    "Kimi Antonelli": "antonelli",
  };

export function PredictWinner({ onSubmit }) {
  const [selectedDriver, setSelectedDriver] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const [isDropdownOpen, setIsDropdownOpen] = useState(false)

  const handleSubmit = async () => {
    if (!selectedDriver) return
    setIsLoading(true)
    try {
      const driverRef = UI_TO_REF[selectedDriver] || selectedDriver.toLowerCase()
      const res = await fetch("http://127.0.0.1:8000/predict/winner", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          driver: driverRef,
          year: 2025,
          round: 16,
          circuitId: 14,
          use_quali: true,
        }),
      })
      const data = await res.json()
      // wait 5 seconds before showing results
      await new Promise((resolve) => setTimeout(resolve, 3000))
      if (data.error) {
        alert(data.error)
      } else {
        // Test logging - remove this later
        console.log("Driver:", selectedDriver)
        console.log("Driver Ref:", driverRef)
        console.log("Predicted Position:", data.predicted_position)
        console.log("Projected Rank:", data.proj_rank)
        console.log("Full API Response:", data)
        
        onSubmit(data) // keep your current UX; optionally pass data
      }
    } catch (e) {
      console.error(e)
      alert("Failed to reach prediction service.")
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
          selectedDriver || "Enter Driver Name",
        ),
        isDropdownOpen &&
          React.createElement(
            "div",
            { className: "select-dropdown" },
            F1_DRIVERS.map((driver) =>
              React.createElement(
                "div",
                {
                  key: driver,
                  className: "select-item",
                  onClick: () => handleDriverSelect(driver),
                },
                driver,
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
