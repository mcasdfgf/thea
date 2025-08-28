/**
 * @file InspectorContentRenderer.jsx
 * @description
 * A specialized component for displaying the contents of the Inspector panel.
 *
 * It intelligently formats the data of a selected graph node, displaying key
 * attributes like ID, type, and timestamp. For complex nodes like 'ReportNode',
 * it attempts to parse the content and show a concise summary instead of the raw data.
 * It also provides the "Show Raw Data" button to open the full details in a modal
 * and a clickable ID to trigger the application's trace mode.
 */

import React from "react";

function parseForSummary(contentStr) {
  if (typeof contentStr !== "string") return null;
  try {
    const jsonStr = contentStr
      .replace(/'/g, '"')
      .replace(/True/g, "true")
      .replace(/False/g, "false")
      .replace(/None/g, "null");
    return JSON.parse(jsonStr);
  } catch (e) {
    return null;
  }
}

function InspectorContentRenderer({
  element,
  onShowRawData,
  traceStartNodeId,
}) {
  if (!element) return null;

  const { id, data } = element.data;
  const { type, full_data } = data;

  const renderSummary = () => {
    const content = full_data.content || "";

    if (type === "ReportNode") {
      const parsed = parseForSummary(content);
      if (parsed && parsed.result_text) {
        return (
          <div className="inspector-summary-report">
            <span className="inspector-label">Result:</span>
            <pre className="inspector-summary-text">
              {parsed.result_text.substring(0, 300)}...
            </pre>
          </div>
        );
      }
    }

    return (
      <pre className="inspector-summary-text">
        {typeof content === "string"
          ? content.substring(0, 300)
          : JSON.stringify(content)}
        ...
      </pre>
    );
  };

  return (
    <div className="inspector-content">
      <div className="inspector-item">
        <span className="inspector-label">ID:</span>
        <button
          className="inspector-id-button"
          onClick={() => onShowRawData(id, "trace")}
        >
          <span className="inspector-value-id">{id}</span>
        </button>
        {!traceStartNodeId && (
          <p className="trace-hint">(click ID to trace the chain)</p>
        )}
      </div>
      <div className="inspector-item">
        <span className="inspector-label">Type:</span>
        <span className="inspector-value">{type}</span>
      </div>
      <div className="inspector-item">
        <span className="inspector-label">Timestamp:</span>
        <span className="inspector-value">
          {new Date(full_data.timestamp).toLocaleString()}
        </span>
      </div>
      <hr />
      <div className="inspector-item">
        <span className="inspector-label">Summary:</span>
        {renderSummary()}
      </div>
      <button
        className="show-raw-button"
        onClick={() => onShowRawData(full_data, "view")}
      >
        Show Raw Data
      </button>
    </div>
  );
}

export default InspectorContentRenderer;
