import React from "react"
import { Trophy, User } from "lucide-react"
import "./header.css"

export function Header({ onHome, onResults, active = "home" }) {
  return React.createElement(
    "header",
    { className: "header" },
    React.createElement(
      "div",
      { className: "header-container" },
      React.createElement(
        "div",
        { className: "header-content" },
        React.createElement(
          "div",
          { className: "logo-section" },
          React.createElement(
            "div",
            { className: "logo-icon" },
            React.createElement(Trophy, { className: "trophy-icon" }),
          ),
          React.createElement("h1", { className: "logo-text" }, "F1 Predictions"),
        ),
        React.createElement(
          "nav",
          { className: "navigation" },
          React.createElement(
            "a",
            { href: "#", className: `nav-link ${active === "home" ? "active" : ""}`, onClick: (e) => { e.preventDefault(); onHome && onHome(); } },
            "Home",
          ),
          React.createElement(
            "a",
            { href: "#", className: `nav-link ${active === "results" ? "active" : ""}`, onClick: (e) => { e.preventDefault(); onResults && onResults(); } },
            "Results",
          ),
        ),
        null,
      ),
    ),
  )
}
