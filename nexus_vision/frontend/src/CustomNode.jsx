/**
 * @file CustomNode.jsx
 * @description
 * A custom node renderer for React Flow.
 *
 * This component is responsible for the visual representation of a single node.
 * It dynamically determines the node's appearance (shape, color, size, shadows)
 * based on the 'data' prop passed from the main App component.
 * It also provides invisible handles on all four sides to ensure edges can connect correctly.
 */

import React, { memo } from "react";
import { Handle, Position } from "reactflow";

const handleStyle = { background: "transparent", border: "none" };

const CustomNode = memo(({ data, selected }) => {
  const nodeStyle = {
    width: "100%",
    height: "100%",
    background: `radial-gradient(circle, ${data.color}BF, ${data.color} 80%)`,
    border: `2px solid ${data.color}`,
    boxSizing: "border-box",
    transform: selected ? "scale(1.1)" : "scale(1)",
    filter: selected ? `drop-shadow(0 0 10px ${data.color})` : "none",
  };

  if (data.shape === "circle" || data.shape === "dot")
    nodeStyle.borderRadius = "50%";
  else if (data.shape === "database") nodeStyle.borderRadius = "15px";
  else if (data.shape === "star")
    nodeStyle.clipPath =
      "polygon(50% 0%, 61% 35%, 98% 35%, 68% 57%, 79% 91%, 50% 70%, 21% 91%, 32% 57%, 2% 35%, 39% 35%)";
  else if (data.shape === "triangle")
    nodeStyle.clipPath = "polygon(50% 0%, 0% 100%, 100% 100%)";
  else if (data.shape === "box") nodeStyle.borderRadius = "5px";

  return (
    <div style={nodeStyle}>
      <Handle
        type="source"
        position={Position.Top}
        id="top"
        style={handleStyle}
      />
      <Handle
        type="source"
        position={Position.Right}
        id="right"
        style={handleStyle}
      />
      <Handle
        type="source"
        position={Position.Bottom}
        id="bottom"
        style={handleStyle}
      />
      <Handle
        type="source"
        position={Position.Left}
        id="left"
        style={handleStyle}
      />
      <Handle
        type="target"
        position={Position.Top}
        id="top"
        style={handleStyle}
      />
      <Handle
        type="target"
        position={Position.Right}
        id="right"
        style={handleStyle}
      />
      <Handle
        type="target"
        position={Position.Bottom}
        id="bottom"
        style={handleStyle}
      />
      <Handle
        type="target"
        position={Position.Left}
        id="left"
        style={handleStyle}
      />
    </div>
  );
});

export default CustomNode;
