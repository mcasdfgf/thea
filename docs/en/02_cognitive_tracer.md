# 2. The Cognitive Tracer

**Module:** `nexus_tools/cmd_trace.py`
**Nexus Command:** `trace` (alias: `tr`)

## Purpose

The Cognitive Tracer is a debugging tool that answers the critical question: **"How did the system arrive at this conclusion?"** It reconstructs and visualizes the entire "thought process"—a tree of operations (tasks and reports)—related to a single user impulse.

## Usage

```
[NEXUS]> trace <node_ID>
```

-   `<node_ID>`: The full or partial ID of the starting node, typically a `UserImpulse` or `FinalResponseNode`.

## Understanding the Output

The command's output is a color-coded ASCII tree that displays the hierarchy and sequence of cognitive acts.

**Example of a Cognitive Cycle Trace:**

```
TRACE: Reconstructing cognitive chain for ID starting with '67b6575e'...
--------------------------------------------------------------------------------
[ 67b6575e ] UserImpulse                          : приветик!
├─> [ 819ed939 ] TaskNode                             : {"original_impulse": "приветик!", "instinctive_response": "З...
│   └─> [ 1cd57c52 ] ReportNode                           : {"queries": [{"semantic_query": "какой любимый цвет пользова...
│       └─> [ 4376a050 ] SearchPlanNode                       : {"queries": [{"semantic_query": "какой любимый цвет пользова...
│           ├─> [ 375feb83 ] TaskNode                             : {"request_payload": {"semantic_query": "объяснение процесса ...
│           │   └─> [ 08a6df7f ] ReportNode                           : {"found_nodes": [{"type": "UserImpulse", "content": "привети...
│           └─> [ ba2bb654 ] TaskNode                             : {"request_payload": {"semantic_query": "какой любимый цвет п...
│               └─> [ 2dff91c9 ] ReportNode                           : {"found_nodes": [{"type": "UserImpulse", "content": "привети...
├─> [ 84bdda29 ] InstinctiveResponseNode              : Здравствуйте! Чем я могу вам помочь сегодня?
├─> [ 95dbc510 ] TaskNode                             : {"impulse_text": "приветик!", "history": []}
│   └─> [ 0ec0e8ab ] ReportNode                           : {"text": "Здравствуйте! Чем я могу вам помочь сегодня?"}
├─> [ a8ac5491 ] FinalResponseNode                : Здравствуйте! Я всегда рада вам помочь. Как я могу быть вам ...
└─> [ e9f140bd ] TaskNode                             : {"original_impulse": "приветик!", "instinctive_response": "З...
    └─> [ a8545ab8 ] ReportNode                           : {"text": "Здравствуйте! Я всегда рада вам помочь. Как я могу...
        └─> ↪ (link to already shown FinalResponseNode [a8ac5491])
--------------------------------------------------------------------------------
END TRACE
```

### How to Read the Tree:

-   **`[ node_ID ]`**: The abbreviated ID of the node in `UniversalMemory`.
-   **`NodeType`**: The role of this step in the process. The **color** of the node type reflects its semantic category (e.g., user interaction, task, report).
-   **`:` (colon)**: A preview of the node's `content`.
-   **`└─>` & `├─>`**: Indicate a cause-and-effect relationship. For example, a `TaskNode` leads to a `ReportNode`.
-   **`↪ (link to ...)`**: Denotes a link to a node that has already been displayed higher up in the tree, avoiding redundancy.

The tracer intentionally follows only **"process" edges** (like `IS_RESULT_OF`, `IS_TASK_FOR`), ignoring purely semantic links (like `CONTAINS_CONCEPT`). This filters out noise and reveals the system's **operational logic**—how it "thinks," rather than everything it knows about a topic.
