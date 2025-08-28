# The "Nexus" Diagnostic Console

Welcome to the documentation for the "Nexus" Diagnostic Console—a suite of tools for analysis, debugging, and direct interaction with the "Assembler of Being" cognitive core.

## Philosophy

These tools are not mere utilities but an integral part of the platform. They are designed as an "MRI scanner" for the neuro-like memory structure, allowing the architect and developer to:

-   **Visualize "thought" processes:** Trace the entire chain from a user's query to the final answer.
-   **Analyze the knowledge base:** Examine the "beliefs" (insights) formed by the system, their sources, and their connections.
-   **Perform isolated testing:** Verify the behavior of individual cognitive cycles (like planning or recall) in a controlled environment.
-   **Directly interact with the memory:** Navigate the memory graph and retrieve detailed information about any of its elements.

All tools are implemented as plugins for the unified interactive console, `Nexus`, which serves as the central hub for all research.

## The Toolkit

| Module (`nexus_tools/`) | `Nexus` Commands | Purpose |
| :--- | :--- | :--- |
| **`nexus.py`** | - | **[The Hub]** The interactive console for accessing all tools. |
| **`cmd_trace.py`** | `trace` | **[The Tracer]** Visualizes the cognitive chain for a single impulse. |
| **`cmd_nav.py`** | `list`, `get` | **[The Navigator]** Allows browsing graph nodes and "traveling" through it. |
| **`cmd_insights.py`**| `insights`, `ifind`, `iget` | **[The Inspector]** Analyzes the system's knowledge base of "insights". |
| **`cmd_probes.py`** | `plan`, `probe` | **[The Probes]** Test the cognitive cycles of planning and recall in isolation. |
| **`cmd_stat.py`** | `stat` | **[The Statistician]** Displays general statistics about the memory graph. |

> ⚠️ **Note for the Demo Version:** The `plan` and `probe` commands emulate the system's "live" thought processes and require access to the full cognitive core (including services and the LLM interface). In this demo repository, which is designed for analyzing a pre-existing "memory snapshot," these commands are disabled.

---

### Detailed Documentation

-   [1. The `Nexus` Interactive Shell](01_nexus_shell.md)
-   [2. The Cognitive Tracer (`trace`)](02_cognitive_tracer.md)
-   [3. The Graph Navigator (`list`, `get`)](03_graph_navigator.md)
-   [4. The Insight Inspector (`insights`, `ifind`, `iget`)](04_insight_inspector.md)
-   [5. The Cognitive Probes (`plan`, `probe`)](05_cognitive_probes.md)

*(Note: Documentation for the simple `stat` command is included in the description of the main `Nexus` interface.)*
