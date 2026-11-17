  "use client"

  import React, { useEffect, useState } from "react"
  import { Header } from "./components/header.js"
  import { PredictWinner } from "./components/predictWinner.js"
  import { RaceOrder } from "./components/raceOrder.js"
  import { WinnerResult } from "./components/winnerResults.js"
  import { RaceOrderResult } from "./components/raceOrderResults.js"
  import { getNextRace, refreshData } from "./api"
  import "./App.css"

  const formatDate = (iso) =>
    iso
      ? new Date(`${iso}T00:00:00Z`).toLocaleDateString(undefined, {
          day: "numeric", month: "short", year: "numeric", timeZone: "UTC",
        })
      : ""

  // Shows which race is being predicted and how current the data is
  function RaceBanner({ race, error, isRefreshing, onRefresh }) {
    if (error) {
      return React.createElement(
        "div",
        { className: "race-banner race-banner-error" },
        `${error} `,
        React.createElement(
          "button",
          { className: "race-banner-refresh", onClick: onRefresh, disabled: isRefreshing },
          isRefreshing ? "Retrying..." : "Retry",
        ),
      )
    }
    if (!race) {
      return React.createElement("div", { className: "race-banner" }, "Loading the latest race data...")
    }
    const next = race.next_race
    const last = race.last_race
    return React.createElement(
      "div",
      { className: "race-banner" },
      next
        ? React.createElement(
            React.Fragment,
            null,
            React.createElement("div", { className: "race-banner-title" }, `${next.year} ${next.raceName}`),
            React.createElement(
              "div",
              { className: "race-banner-detail" },
              `Round ${next.round} · ${next.circuitName} · ${formatDate(next.date)}`,
            ),
          )
        : React.createElement("div", { className: "race-banner-title" }, "No upcoming race on the calendar"),
      React.createElement(
        "div",
        { className: "race-banner-detail" },
        `Results through the ${last.year} ${last.raceName} · `,
        race.quali_available ? "Using qualifying results" : "Qualifying not held yet",
        " · ",
        React.createElement(
          "button",
          { className: "race-banner-refresh", onClick: onRefresh, disabled: isRefreshing },
          isRefreshing ? "Checking..." : "Check for new results",
        ),
      ),
      (race.warnings || []).map((w) =>
        React.createElement("div", { key: w, className: "race-banner-warning" }, w),
      ),
    )
  }

  export default function HomePage() {
    const [mode, setMode] = useState("winner")
    const [appState, setAppState] = useState("prediction")
    const [winnerResult, setWinnerResult] = useState(null)
    const [raceOrderResult, setRaceOrderResult] = useState([])
    const [race, setRace] = useState(null)
    const [raceError, setRaceError] = useState("")
    const [isRefreshing, setIsRefreshing] = useState(false)

    useEffect(() => {
      let cancelled = false
      getNextRace()
        .then((data) => { if (!cancelled) setRace(data) })
        .catch((e) => { if (!cancelled) setRaceError(e.message) })
      return () => { cancelled = true }
    }, [])

    const handleRefresh = async () => {
      setIsRefreshing(true)
      try {
        setRace(await refreshData())
        setRaceError("")
      } catch (e) {
        setRaceError(e.message)
      } finally {
        setIsRefreshing(false)
      }
    }

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
        React.createElement(RaceBanner, {
          race,
          error: raceError,
          isRefreshing,
          onRefresh: handleRefresh,
        }),
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
              ? React.createElement(PredictWinner, {
                  lineup: race ? race.lineup : [],
                  onSubmit: handleWinnerPrediction,
                })
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
