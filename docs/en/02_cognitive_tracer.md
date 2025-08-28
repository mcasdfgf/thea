# 2. The Cognitive Tracer

**Module:** `nexus_tools/cmd_trace.py`
**`Nexus` Command:** `trace` (alias: `tr`)

## Purpose

The Tracer answers the most critical debugging question: **"How did the system arrive at this conclusion?"** It visualizes the entire "thought chain"—the sequence of steps (nodes in memory) that were executed to process a single user query.

## Usage

```
[NEXUS]> trace <node_id>
```
-   `<node_id>`: The full or partial ID of the starting node, typically a `UserImpulse` or `FinalResponseNode`.

## Interpreting the Output

The result is a colorized ASCII tree that shows the hierarchy and sequence of cognitive acts.

**Example for the new cognitive cycle:**
```
TRACE: Tracing cognitive chain for ID starting with '73930751'...
--------------------------------------------------------------------------------
[ 73930751 ] UserImpulse                          : расскажи про фотосинтез
├─> [ 204f00eb ] TaskNode                             : {"original_impulse": "расскажи про фотосинтез", "instinctive...
│   └─> [ c80b960a ] ReportNode                           : {"text": "Фотосинтез - это природный процесс, который позвол...
│       └─> [ 211ca6b4 ] FinalResponseNode                : Фотосинтез - это природный процесс, который позволяет растен...
├─> (link to FinalResponseNode [211ca6b4])
├─> [ 857c8c2c ] InstinctiveResponseNode              : Фотосинтез - это процесс, который позволяет растениям, а так...
├─> [ a6df850d ] TaskNode                             : {"original_impulse": "расскажи про фотосинтез"}
│   └─> [ df97d109 ] ReportNode                           : {"queries": [{"semantic_query": "расскажи про фотосинтез", "...
│       └─> [ e3eb08d4 ] SearchPlanNode                       : {"queries": [{"semantic_query": "расскажи про фотосинтез", "...
│           └─> [ 53f072e5 ] TaskNode                             : {"request_payload": {"semantic_query": "расскажи про фотосин...
│               └─> [ 9ecc6d10 ] ReportNode                           : {"found_nodes": [{"type": "KnowledgeCrystalNode", "content":...
└─> [ c027ec38 ] TaskNode                             : {"impulse_text": "расскажи про фотосинтез", "history": [{"ro...
    └─> [ 77ae53bb ] ReportNode                           : {"text": "Фотосинтез - это процесс, который позволяет растен...
--------------------------------------------------------------------------------
END TRACE
```

### How to Read the Tree:
-   **`[ Node ID ]`**: The unique identifier of the step (a node in memory).
-   **`NodeType`**: The role of this step in the process. The color of the node type corresponds to its semantic role (e.g., green for user interaction, cyan for tasks, yellow for reports).
-   **`:` (colon)**: A brief preview of the node's content.
-   **`└─>` & `├─>`**: Indicate child processes. For example, a `TaskNode` gives rise to a `ReportNode`.

The Tracer follows only **"process" edges** (like `IS_RESULT_OF`, `IS_TASK_FOR`, `WAS_SYNTHESIZED_FROM`, etc.), ignoring semantic edges (like `CONTAINS_CONCEPT`). This is intentional, to show the **operational logic** of the system rather than all related data.
