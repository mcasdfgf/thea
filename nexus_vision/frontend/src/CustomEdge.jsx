/**
 * @file CustomEdge.jsx
 * @description
 * A custom edge renderer for React Flow.
 *
 * This component renders the connections (edges) between nodes.
 * It uses a Bezier path for a smooth, curved appearance and includes
 * logic to display an optional text label at the center of the edge path.
 * The edge color and arrowhead are styled dynamically based on the target node's color.
 */

import React from "react";
import { BaseEdge, EdgeLabelRenderer, getBezierPath } from "reactflow";

export default function CustomEdge({
  id,
  sourceX,
  sourceY,
  targetX,
  targetY,
  sourcePosition,
  targetPosition,
  data,
  style,
  markerEnd,
}) {
  const [edgePath, labelX, labelY] = getBezierPath({
    sourceX,
    sourceY,
    sourcePosition,
    targetX,
    targetY,
    targetPosition,
  });

  const shouldRenderLabel =
    data?.showLabel && data?.label_text && data.label_text.length > 0;

  return (
    <>
      <BaseEdge id={id} path={edgePath} style={style} markerEnd={markerEnd} />
      {shouldRenderLabel && (
        <EdgeLabelRenderer>
          <div
            style={{
              position: "absolute",
              transform: `translate(-50%, -50%) translate(${labelX}px,${labelY}px)`,
              pointerEvents: "all",
            }}
            className="edge-label"
          >
            {data.label_text}
          </div>
        </EdgeLabelRenderer>
      )}
    </>
  );
}
