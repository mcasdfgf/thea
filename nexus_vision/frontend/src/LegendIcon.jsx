/**
 * @file LegendIcon.jsx
 * @description
 * A simple, presentational component that renders a small visual icon
 * representing a node type in the Control Panel's filter list.
 * It dynamically applies CSS styles to create different shapes (circle, star, box, etc.)
 * and colors based on the props it receives, matching the appearance of the nodes on the graph.
 */

import React from "react";

function LegendIcon({ color, shape }) {
  const style = {
    width: "16px",
    height: "16px",
    backgroundColor: color,
    border: `1px solid ${color}80`,
    marginRight: "8px",
    flexShrink: 0,
    boxSizing: "border-box",
  };

  if (shape === "circle" || shape === "dot") {
    style.borderRadius = "50%";
  } else if (shape === "database") {
    style.borderRadius = "4px";
  } else if (shape === "star") {
    style.clipPath =
      "polygon(50% 0%, 61% 35%, 98% 35%, 68% 57%, 79% 91%, 50% 70%, 21% 91%, 32% 57%, 2% 35%, 39% 35%)";
  } else if (shape === "triangle") {
    style.clipPath = "polygon(50% 0%, 0% 100%, 100% 100%)";
  } else if (shape === "box") {
    style.borderRadius = "2px";
  }

  return <div style={style}></div>;
}

export default React.memo(LegendIcon);
