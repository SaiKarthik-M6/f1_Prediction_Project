  "use client"

  import React, { useState } from "react"
  import { Header } from "./components/header.js"
  import { PredictWinner } from "./components/predictWinner.js"
  import { RaceOrder } from "./components/raceOrder.js"
  import { WinnerResult } from "./components/winnerResults.js"
  import { RaceOrderResult } from "./components/raceOrderResults.js"
  import "./App.css"

  export default function HomePage() {
    const [mode, setMode] = useState("winner")
    const [appState, setAppState] = useState("prediction")
    const [selectedDriver, setSelectedDriver] = useState("")
    const [winnerResult, setWinnerResult] = useState(null)
    const [raceOrderResult, setRaceOrderResult] = useState([])

    const handleWinnerPrediction = (dataFromChild) => {
      setWinnerResult(dataFromChild)
      setAppState("winnerResult")
    }

    const handleRaceOrderPrediction = (listFromChild) => {
      setRaceOrderResult(listFromChild)  // <-- save list
      setAppState("raceOrderResult")
    }

    const handleMakeAnotherPrediction = () => {
      setAppState("prediction")
      setSelectedDriver("")
    }

    return React.createElement(
      "div",
      { className: "page-container" },
      React.createElement(Header, {
        active: appState === "prediction" ? "home" : (appState.includes("Result") ? "results" : "home"),
        onHome: () => setAppState("prediction"),
        onResults: () => setAppState(raceOrderResult.length ? "raceOrderResult" : (winnerResult ? "winnerResult" : "prediction")),
      }),
      React.createElement(
        "main",
        { className: "main-content" },
        appState === "prediction" &&
          React.createElement(
            React.Fragment,
            null,
            React.createElement(
              "div",
              { className: "mode-toggle-container" },
              React.createElement(
                "div",
                { className: "mode-toggle" },
                React.createElement(
                  "button",
                  {
                    onClick: () => setMode("winner"),
                    className: `mode-button ${mode === "winner" ? "active" : ""}`,
                  },
                  "Predict Winner",
                ),
                React.createElement(
                  "button",
                  {
                    onClick: () => setMode("race-order"),
                    className: `mode-button ${mode === "race-order" ? "active" : ""}`,
                  },
                  "Race Order",
                ),
              ),
            ),
            mode === "winner"
              ? React.createElement(PredictWinner, { onSubmit: handleWinnerPrediction })
              : React.createElement(RaceOrder, { onSubmit: handleRaceOrderPrediction }),
          ),
        appState === "winnerResult" &&
          React.createElement(WinnerResult, {
            result: winnerResult,
            onMakeAnother: handleMakeAnotherPrediction,
          }),
        appState === "raceOrderResult" &&
          React.createElement(RaceOrderResult, {
            results: raceOrderResult,
            onMakeAnother: handleMakeAnotherPrediction,
          }),
      ),
    )
  }
