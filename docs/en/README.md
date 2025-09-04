# Nexus: The Diagnostic Console

"Nexus" is a Command-Line Interface (CLI) designed for developers and researchers to directly interact with the `UniversalMemory`—a "consciousness snapshot" from the T.H.E.A. cognitive architecture.

## Key Features

The console is engineered as a "surgical tool" for memory exploration, allowing you to:

-   **Trace Cognitive Processes:** Reconstruct the entire operational chain from a user's query to the final response (`trace`).
-   **Analyze the Knowledge Base:** Examine the system's synthesized "insights" (`KnowledgeCrystalNode`), tracing their origins and connections (`insights`).
-   **Navigate the Graph:** Interactively "walk" through the nodes and their relationships within the memory graph (`list`, `get`).
-   **Perform Isolated Testing:** Emulate individual cognitive cycles, such as planning or memory recall, in a controlled environment (`plan`, `probe`).

## Tools Overview

| Module (`nexus_tools/`)      | Nexus Commands               | Purpose                                                 |
| :--------------------------- | :--------------------------- | :------------------------------------------------------ |
| **`nexus.py`**               | -                            | **[Main Hub]** The interactive shell for all tools.     |
| **`cmd_trace.py`**           | `trace`                      | **[Tracer]** Visualizes the cognitive chain for an impulse. |
| **`cmd_nav.py`**             | `list`, `get`                | **[Navigator]** Lets you browse and traverse the graph.     |
| **`cmd_insights.py`**        | `insights`, `ifind`, `iget`  | **[Inspector]** Analyzes the system's knowledge base.       |
| **`cmd_probes.py`**          | `plan`, `probe`              | **[Probes]** Tests the planning and recall cycles.      |
| **`cmd_stat.py`**            | `stat`                       | **[Statistics]** Displays general statistics of the graph.    |

> ⚠️ **Requirements for Live Commands:** The `plan` and `probe` commands emulate real-time cognitive processes. To use them, you must:
>
> 1.  Have the complete project source code, including all cognitive services.
> 2.  Ensure network access to a running LLM server (e.g., vLLM), with the address configured in the project settings.
>
> All other commands (`trace`, `list`, `get`, `insights`, `stat`) operate on the static `memory_core.graphml` file and do not require a live core.

---

### Detailed Command Documentation

-   [1. The Nexus Interactive Shell](01_nexus_shell.md) (covers `help`, `exit`, `stat`, etc.)
-   [2. The Cognitive Tracer (`trace`)](02_cognitive_tracer.md)
-   [3. The Graph Navigator (`list`, `get`)](03_graph_navigator.md)
-   [4. The Knowledge Inspector (`insights`)](04_insight_inspector.md)
-   [5. The Cognitive Probes (`plan`, `probe`)](05_cognitive_probes.md)

*(Note: Documentation for the `stat` command is included in the guide for the Nexus Interactive Shell.)*
