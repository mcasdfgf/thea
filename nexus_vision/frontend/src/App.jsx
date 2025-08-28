/**
 * @file App.jsx
 * @description
 * This is the main component of the Nexus Vision application. It serves as the root
 * of the UI, assembling all major components and managing the global application state.
 *
 * Core Responsibilities:
 * - Fetches all metadata and graph data from the backend API.
 * - Manages the state of filters (node types, time range) from the Control Panel.
 * - Renders the main layout: Control Panel, Graph Canvas, and Inspector Panel.
 * - Passes data down to the React Flow instance for rendering.
 * - Handles global state such as loading indicators, selected elements, and trace mode.
 * - Integrates the `useForceLayout` custom hook to power the D3.js physics simulation.
 */

import { useState, useEffect, useCallback, useMemo, useRef } from "react";
import ReactFlow, {
  Background,
  Controls,
  MiniMap,
  MarkerType,
  ReactFlowProvider,
} from "reactflow";
import "reactflow/dist/style.css";
import { useReactFlow } from "reactflow";
import {
  getAppMetadata,
  getGraphView,
  getVisualMetadata,
  traceChainById,
} from "./api";
import "./App.css";
import "./themes.css";
import Modal from "./Modal";
import DataFormatter, { unpackAllNestedStrings } from "./DataFormatter";
import InspectorContentRenderer from "./InspectorContentRenderer";
import CustomEdge from "./CustomEdge";
import CustomNode from "./CustomNode";
import LegendIcon from "./LegendIcon";
import { useForceLayout } from "./useForceLayout";

const nodeTypes = { customNode: CustomNode };
const edgeTypes = { customEdge: CustomEdge };
const initialFilters = { node_types: ["UserImpulse", "FinalResponseNode"] };

function App() {
  const [isPhysicsEnabled, setIsPhysicsEnabled] = useState(true);
  const {
    nodes,
    edges,
    onNodesChange,
    onEdgesChange,
    updateGraph,
    onNodeDragStart,
    onNodeDrag,
    onNodeDragStop,
    onNodeDoubleClick,
    releaseAllNodes,
  } = useForceLayout({ isPhysicsEnabled });

  const [filters, setFilters] = useState(initialFilters);
  const [masterMetadata, setMasterMetadata] = useState(null);
  const [displayMetadata, setDisplayMetadata] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selectedElement, setSelectedElement] = useState(null);
  const [legendData, setLegendData] = useState(null);
  const [tooltip, setTooltip] = useState({
    visible: false,
    data: null,
    x: 0,
    y: 0,
  });
  const graphContainerRef = useRef(null);
  const [showLabels, setShowLabels] = useState(false);
  const [timeRange, setTimeRange] = useState("2h");
  const [refreshTrigger, setRefreshTrigger] = useState(0);
  const [traceStartNodeId, setTraceStartNodeId] = useState(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [modalContent, setModalContent] = useState({ title: "", data: {} });
  const [theme, setTheme] = useState("theme-default");

  const handleShowRawData = (data, type) => {
    if (type === "trace") {
      setTraceStartNodeId(data);
      return;
    }
    setModalContent({
      title: `Full Node Data: ${selectedElement?.data?.id.substring(0, 8)}...`,
      data: data,
    });
    setIsModalOpen(true);
  };

  const togglePhysics = useCallback(() => {
    setIsPhysicsEnabled((prev) => !prev);
  }, []);

  useEffect(() => {
    if (!traceStartNodeId) return;

    setLoading(true);
    traceChainById(traceStartNodeId)
      .then((res) => {
        const { nodes: backendNodes, edges: backendEdges } = res.data;
        const reactFlowNodes = backendNodes.map((node) => ({
          ...node,
          position: { x: 0, y: 0 },
          style: { width: node.data.size, height: node.data.size },
        }));
        const reactFlowEdges = backendEdges.map((e) => ({
          ...e,
          id: e.id || `e-${e.source}-${e.target}`,
        }));
        updateGraph(reactFlowNodes, reactFlowEdges);
      })
      .catch((err) => console.error("Trace failed", err))
      .finally(() => setLoading(false));
  }, [traceStartNodeId, updateGraph]);

  useEffect(() => {
    if (traceStartNodeId) return;
    getAppMetadata().then((res) => setMasterMetadata(res.data));
    getVisualMetadata().then((res) => setLegendData(res.data));
  }, [refreshTrigger, traceStartNodeId]);

  useEffect(() => {
    if (traceStartNodeId || !masterMetadata) return;

    setLoading(true);

    let timeFilters = { start_time: null, end_time: null };
    if (masterMetadata.max_timestamp && timeRange !== "all") {
      const endTime = new Date(masterMetadata.max_timestamp);
      const hours = parseInt(timeRange.replace("h", ""));
      const startTime = new Date(endTime.getTime() - hours * 60 * 60 * 1000);
      timeFilters = {
        start_time: startTime.toISOString(),
        end_time: endTime.toISOString(),
      };
    }

    const graphFilters = { ...filters, ...timeFilters };
    if (!graphFilters.node_types || graphFilters.node_types.length === 0) {
      updateGraph([], []);
      setLoading(false);
      return;
    }

    Promise.all([getAppMetadata(timeFilters), getGraphView(graphFilters)])
      .then(([metaRes, graphRes]) => {
        setDisplayMetadata(metaRes.data);
        const { nodes: backendNodes, edges: backendEdges } = graphRes.data;
        const reactFlowNodes = backendNodes.map((node) => ({
          ...node,
          position: { x: 0, y: 0 },
          style: { width: node.data.size, height: node.data.size },
        }));
        const reactFlowEdges = backendEdges.map((e) => ({
          ...e,
          id: e.id || `e-${e.source}-${e.target}`,
        }));
        updateGraph(reactFlowNodes, reactFlowEdges);
      })
      .catch((err) => console.error("Data loading failed", err))
      .finally(() => setLoading(false));
  }, [filters, timeRange, masterMetadata, updateGraph, traceStartNodeId]);

  const displayedNodeCounts = useMemo(() => {
    const counts = {};
    if (displayMetadata?.all_node_types) {
      displayMetadata.all_node_types.forEach((type) => {
        counts[type] = 0;
      });
    }
    for (const node of nodes) {
      const type = node.data.type;
      if (counts[type] !== undefined) {
        counts[type]++;
      }
    }
    return counts;
  }, [nodes, displayMetadata]);

  const handleNodeTypeChange = (e) => {
    const { name, checked } = e.target;
    setFilters((prev) => {
      const current = prev.node_types || [];
      const newTypes = checked
        ? [...current, name]
        : current.filter((t) => t !== name);
      setSelectedElement(null);
      return { ...prev, node_types: newTypes };
    });
  };

  const handleSelectAllChange = (e) => {
    const isChecked = e.target.checked;
    const availableTypes = displayMetadata?.all_node_types || [];
    setFilters((prev) => ({
      ...prev,
      node_types: isChecked ? [...availableTypes] : [],
    }));
    setSelectedElement(null);
  };

  const onSelectionChange = useCallback(({ nodes, edges }) => {
    if (nodes.length === 1)
      setSelectedElement({ type: "node", data: nodes[0] });
    else if (edges.length === 1)
      setSelectedElement({ type: "edge", data: edges[0] });
    else setSelectedElement(null);
  }, []);

  const nodeColorMap = useMemo(
    () => new Map(nodes.map((n) => [n.id, n.data.color])),
    [nodes],
  );

  const getEdgeParams = (source, target) => {
    const sourcePos = source.position;
    const targetPos = target.position;
    const sourceWidth = source.style.width;
    const sourceHeight = source.style.height;
    const targetWidth = target.style.width;
    const targetHeight = target.style.height;

    const dx = sourcePos.x + sourceWidth / 2 - (targetPos.x + targetWidth / 2);
    const dy =
      sourcePos.y + sourceHeight / 2 - (targetPos.y + targetHeight / 2);

    if (Math.abs(dx) > Math.abs(dy)) {
      return dx > 0
        ? { sourceHandle: "left", targetHandle: "right" }
        : { sourceHandle: "right", targetHandle: "left" };
    }
    return dy > 0
      ? { sourceHandle: "top", targetHandle: "bottom" }
      : { sourceHandle: "bottom", targetHandle: "top" };
  };

  const { processedNodes, processedEdges } = useMemo(() => {
    const selectedNode =
      selectedElement?.type === "node" ? selectedElement.data : null;
    const nodesMap = new Map(nodes.map((node) => [node.id, node]));

    const newEdges = edges
      .map((edge) => {
        const source = nodesMap.get(edge.source);
        const target = nodesMap.get(edge.target);
        if (
          !source?.position ||
          !target?.position ||
          !source.style?.width ||
          !target.style?.width
        ) {
          return null;
        }
        const { sourceHandle, targetHandle } = getEdgeParams(source, target);
        const className = edge.type === "dashed" ? "edge-phantom" : "";
        return {
          ...edge,
          sourceHandle,
          targetHandle,
          className,
          type: "customEdge",
          style: { stroke: nodeColorMap.get(edge.target) },
          markerEnd: {
            type: MarkerType.ArrowClosed,
            color: nodeColorMap.get(edge.target),
          },
          data: { ...edge.data, showLabel: showLabels },
        };
      })
      .filter(Boolean);

    const newNodes = nodes.map((n) => ({ ...n }));
    if (selectedNode) {
      const connectedEdgeIds = new Set();
      const connectedNodeIds = new Set([selectedNode.id]);
      newEdges.forEach((edge) => {
        if (
          edge.source === selectedNode.id ||
          edge.target === selectedNode.id
        ) {
          connectedEdgeIds.add(edge.id);
          connectedNodeIds.add(edge.source);
          connectedNodeIds.add(edge.target);
        }
      });
      newNodes.forEach((n) => {
        n.className = connectedNodeIds.has(n.id)
          ? "node-focused"
          : "node-unfocused";
      });
      newEdges.forEach((e) => {
        e.className = (e.className || "")
          .replace(/edge-connected|edge-unfocused/g, "")
          .trim();
        e.className =
          `${e.className} ${connectedEdgeIds.has(e.id) ? "edge-connected" : "edge-unfocused"}`.trim();
      });
    }
    return { processedNodes: newNodes, processedEdges: newEdges };
  }, [nodes, edges, selectedElement, showLabels, nodeColorMap]);

  const onNodeMouseEnter = useCallback((event, node) => {
    if (!graphContainerRef.current) return;
    const graphBounds = graphContainerRef.current.getBoundingClientRect();
    setTooltip({
      visible: true,
      data: node,
      x: event.clientX - graphBounds.left,
      y: event.clientY - graphBounds.top,
    });
  }, []);

  const onNodeMouseMove = useCallback((event) => {
    if (!graphContainerRef.current) return;
    const graphBounds = graphContainerRef.current.getBoundingClientRect();
    setTooltip((prev) => ({
      ...prev,
      x: event.clientX - graphBounds.left,
      y: event.clientY - graphBounds.top,
    }));
  }, []);

  const onNodeMouseLeave = useCallback(() => {
    setTooltip({ visible: false, data: null, x: 0, y: 0 });
  }, []);

  const onEdgeMouseEnter = useCallback((event, edge) => {
    if (!graphContainerRef.current) return;
    const graphBounds = graphContainerRef.current.getBoundingClientRect();
    setTooltip({
      visible: true,
      data: {
        isEdge: true,
        label: edge.label || edge.data?.label_text || "Untyped Edge",
      },
      x: event.clientX - graphBounds.left,
      y: event.clientY - graphBounds.top,
    });
  }, []);

  const onEdgeMouseMove = useCallback((event) => {
    if (!graphContainerRef.current) return;
    const graphBounds = graphContainerRef.current.getBoundingClientRect();
    setTooltip((prev) => ({
      ...prev,
      x: event.clientX - graphBounds.left,
      y: event.clientY - graphBounds.top,
    }));
  }, []);

  const onEdgeMouseLeave = useCallback(() => {
    onNodeMouseLeave();
  }, [onNodeMouseLeave]);

  const handleReleaseAll = useCallback(() => {
    releaseAllNodes();
    if (!isPhysicsEnabled) {
      setIsPhysicsEnabled(true);
    }
  }, [releaseAllNodes, isPhysicsEnabled]);

  return (
    <div className={`app-container ${theme}`}>
      <div className="panel control-panel">
        <h2>Nexus Vision</h2>
        <p className="subtitle">
          Decompiling consciousness, one node at a time.
        </p>
        <hr />
        <div className="icon-button-group">
          <button
            className="icon-button"
            data-tooltip="Refresh Graph"
            onClick={() => {
              setIsPhysicsEnabled(true);
              setRefreshTrigger((c) => c + 1);
            }}
            disabled={loading}
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              width="20"
              height="20"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <polyline points="23 4 23 10 17 10"></polyline>
              <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"></path>
            </svg>
          </button>
          <button
            className="icon-button"
            data-tooltip="Release All Nodes"
            onClick={handleReleaseAll}
            disabled={loading || !isPhysicsEnabled}
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              width="20"
              height="20"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <path d="M14.5 4.5l7 7M14.5 11.5l7-7M4.5 14.5l7 7M11.5 14.5l-7 7M4.5 4.5l7 7M4.5 11.5l7-7"></path>
            </svg>
          </button>
          <button
            className="icon-button"
            data-tooltip={
              isPhysicsEnabled ? "Freeze Physics" : "Unfreeze Physics"
            }
            onClick={togglePhysics}
          >
            {isPhysicsEnabled ? (
              <svg
                xmlns="http://www.w3.org/2000/svg"
                width="20"
                height="20"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <line x1="2" y1="12" x2="22" y2="12"></line>
                <line x1="12" y1="2" x2="12" y2="22"></line>
                <path d="m20 7-8 8-8-8"></path>
                <path d="m4 17 8-8 8 8"></path>
              </svg>
            ) : (
              <svg
                xmlns="http://www.w3.org/2000/svg"
                width="20"
                height="20"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <path d="M14.5 4.5c.3-.3.8-.3 1 0l6 6c.3.3.3.8 0 1l-2.5 2.5c-.3.3-.8.3-1 0l-6-6c-.3-.3-.3-.8 0-1z"></path>
                <path d="m10.5 8.5-5 5c-2 2-5 2-7 0v0c-2-2-2-5 0-7l5-5"></path>
                <path d="M14.5 17.5c-3 0-4.5-1.5-4.5-4.5s1.5-4.5 4.5-4.5"></path>
              </svg>
            )}
          </button>
        </div>
        <div
          className={
            traceStartNodeId || !isPhysicsEnabled ? "filters-disabled" : ""
          }
        >
          <h4>Time Filter</h4>
          <select
            className="time-filter-select"
            value={timeRange}
            onChange={(e) => setTimeRange(e.target.value)}
            disabled={!!traceStartNodeId || !masterMetadata}
          >
            <option value="1h">Last hour of activity</option>
            <option value="2h">Last 2 hours of activity</option>
            <option value="3h">Last 3 hours of activity</option>
            <option value="5h">Last 5 hours of activity</option>
            <option value="24h">Last 24 hours of activity</option>
            <option value="all">All time</option>
          </select>
          <hr />
          <p style={{ fontSize: "0.8em", opacity: 0.7, marginTop: "15px" }}>
            Double-click a node to unpin it.
          </p>
          <hr />
          <h4>Node Types (Filter)</h4>
          <p className="filter-warning">
            Warning: Selecting node types with many instances (&gt;1000) may
            slow down rendering.
          </p>
          <label className="filter-item select-all">
            <input
              type="checkbox"
              onChange={handleSelectAllChange}
              checked={
                displayMetadata?.all_node_types?.length > 0 &&
                displayMetadata.all_node_types.length ===
                  filters.node_types?.length
              }
            />
            <strong>Select All / Deselect All</strong>
          </label>
          {displayMetadata?.all_node_types ? (
            displayMetadata.all_node_types.map((type) => {
              const visuals = legendData?.[type] || {};
              return (
                <label key={type} className="filter-item">
                  <div className="filter-item-left">
                    <input
                      type="checkbox"
                      name={type}
                      checked={(filters.node_types || []).includes(type)}
                      onChange={handleNodeTypeChange}
                    />
                    <LegendIcon
                      color={visuals.color || "#ccc"}
                      shape={visuals.shape || "dot"}
                    />
                    <span style={{ color: visuals.color || "#f0f0f0" }}>
                      {type}
                    </span>
                  </div>
                  <span className="node-type-count">
                    [
                    <span className="count-displayed">
                      {displayedNodeCounts[type] || 0}
                    </span>
                    /
                    <span className="count-total">
                      {displayMetadata?.node_type_counts?.[type] || 0}
                    </span>
                    ]
                  </span>
                </label>
              );
            })
          ) : (
            <p>Loading...</p>
          )}
        </div>
        <hr />
        <h4>Theme</h4>
        <select
          className="time-filter-select"
          value={theme}
          onChange={(e) => setTheme(e.target.value)}
        >
          <option value="theme-default">Nexus Vision (Default)</option>
          <option value="theme-hacker">Hacker Terminal</option>
          <option value="theme-pink">Synthwave Pink</option>
        </select>
        <hr />
        <h4>View Settings</h4>
        <label>
          <input
            type="checkbox"
            checked={showLabels}
            onChange={(e) => setShowLabels(e.target.checked)}
          />{" "}
          Show edge labels
        </label>
      </div>
      <div
        ref={graphContainerRef}
        className={`graph-container ${showLabels ? "labels-visible" : ""}`}
      >
        {loading && <div className="loader">Loading...</div>}
        {tooltip.visible &&
          tooltip.data &&
          (() => {
            const tooltipStyle = {
              top: `${tooltip.y + 15}px`,
              left: `${tooltip.x + 15}px`,
              transform: "translateX(0)",
            };
            if (graphContainerRef.current) {
              if (tooltip.x + 380 > graphContainerRef.current.offsetWidth) {
                tooltipStyle.left = `${tooltip.x - 15}px`;
                tooltipStyle.transform = "translateX(-100%)";
              }
            }
            const isEdge = tooltip.data.isEdge;
            return (
              <div className="tooltip" style={tooltipStyle}>
                {isEdge ? (
                  <>
                    <div className="tooltip-title">Edge</div>
                    {tooltip.data.label}
                  </>
                ) : (
                  <>
                    <div className="tooltip-title">
                      {tooltip.data.data.type}
                    </div>
                    ID: {tooltip.data?.id?.substring(0, 8) || "N/A"}
                    <br />
                    Timestamp:{" "}
                    {tooltip.data?.data?.full_data?.timestamp
                      ? new Date(
                          tooltip.data.data.full_data.timestamp,
                        ).toLocaleString()
                      : "N/A"}
                  </>
                )}
              </div>
            );
          })()}
        <ReactFlow
          nodes={processedNodes}
          edges={processedEdges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onSelectionChange={onSelectionChange}
          onNodeDragStart={onNodeDragStart}
          onNodeDrag={onNodeDrag}
          onNodeDragStop={onNodeDragStop}
          onNodeDoubleClick={onNodeDoubleClick}
          onNodeMouseEnter={onNodeMouseEnter}
          onNodeMouseMove={onNodeMouseMove}
          onNodeMouseLeave={onNodeMouseLeave}
          onEdgeMouseEnter={onEdgeMouseEnter}
          onEdgeMouseMove={onEdgeMouseMove}
          onEdgeMouseLeave={onEdgeMouseLeave}
          nodeTypes={nodeTypes}
          edgeTypes={edgeTypes}
          onPaneClick={() => setSelectedElement(null)}
          nodesConnectable={false}
          fitView
          proOptions={{ hideAttribution: true }}
          minZoom={0.1}
        >
          <Background variant="dots" />
          <Controls />
          <MiniMap
            nodeColor={(n) => n.data.color}
            pannable={true}
            zoomable={true}
            style={{
              backgroundColor: "var(--color-background)",
              border: "1px solid var(--color-border)",
            }}
            maskColor="rgba(42, 45, 48, 0.6)"
            maskStrokeColor="var(--color-accent)"
            maskStrokeWidth={2}
          />
        </ReactFlow>
      </div>
      <div className="panel inspector-panel">
        <h4>Inspector</h4>
        <p className="subtitle">
          Finding the signal in the noise. And also the noise.
        </p>
        <hr />
        {traceStartNodeId && (
          <div className="trace-controls-container">
            <p className="trace-mode-indicator">TRACE MODE</p>
            <button
              className="trace-reset-button"
              onClick={() => setTraceStartNodeId(null)}
            >
              Reset Trace
            </button>
          </div>
        )}

        {!selectedElement && (
          <p className="inspector-placeholder">
            Click on a node or edge to inspect...
          </p>
        )}
        {selectedElement?.type === "node" && (
          <InspectorContentRenderer
            element={selectedElement}
            onShowRawData={handleShowRawData}
            traceStartNodeId={traceStartNodeId}
          />
        )}
        {selectedElement?.type === "edge" && (
          <div className="inspector-content">
            <div className="inspector-item">
              <span className="inspector-label">Edge ID:</span>
              <span className="inspector-value-id">
                {selectedElement.data.id}
              </span>
            </div>
            <button
              className="show-raw-button"
              onClick={() => handleShowRawData(selectedElement.data, "view")}
            >
              Show Raw Data
            </button>
          </div>
        )}
        <Modal
          isOpen={isModalOpen}
          onClose={() => setIsModalOpen(false)}
          title={modalContent.title}
          dataToCopy={unpackAllNestedStrings(modalContent.data)}
        >
          <DataFormatter data={modalContent.data} />
        </Modal>
      </div>
    </div>
  );
}

export default function AppWrapper() {
  return (
    <ReactFlowProvider>
      <App />
    </ReactFlowProvider>
  );
}
