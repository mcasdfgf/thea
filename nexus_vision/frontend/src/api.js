/**
 * @file api.js
 * @description
 * This module centralizes all communication with the Nexus Vision backend API.
 * It uses Axios to create a pre-configured client that handles the base URL
 * and headers, abstracting the raw HTTP requests away from the UI components.
 * Each exported function corresponds to a specific API endpoint.
 */

import axios from "axios";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8008";

const apiClient = axios.create({
  baseURL: API_URL,
  headers: { "Content-Type": "application/json" },
});

export const getGraphView = (filters) => {
  return apiClient.post("/api/graph_view", { filters });
};

export const getAppMetadata = (timeFilters) => {
  return apiClient.post("/api/metadata", timeFilters || {});
};

export const getVisualMetadata = () => {
  return apiClient.get("/api/visual_metadata");
};

export const traceChainById = (nodeId) => {
  return apiClient.get(`/api/trace_chain/${nodeId}`);
};
