# 1. The `Nexus` Interactive Shell

**File:** `nexus.py`

`Nexus` is the central command bridge, providing a unified, interactive interface for all diagnostic tools.

## Purpose

-   **Efficiency:** The `UniversalMemory` graph is loaded into memory only once per session, making all subsequent commands instantaneous.
-   **Interactive Navigation:** Allows you to "walk" the graph by moving from node to node using numeric commands in a special *Navigation Mode*.
-   **Extensibility:** The console automatically discovers and loads all tools from the `nexus_tools` directory, simplifying the addition of new commands.
-   **Usability:** All tools are accessible via short, intuitive commands with built-in help (`--help`).

## Launching the Shell

```bash
python nexus.py
```

After launching, a welcome message and graph statistics will be displayed, followed by the command prompt: `[NEXUS]>`.

## Core Commands

| Command (and alias)       | Description                                                                                       |
| :------------------------ | :------------------------------------------------------------------------------------------------ |
| `help` (or `h`)           | Displays a list of all available commands, grouped by category.                                   |
| `exit`, `quit` (or `q`)   | Exits the `Nexus` session.                                                                        |
| `refresh` (or `r`)        | Reloads the memory graph from the `memory_core.graphml` file without restarting the shell.          |
| `stat`                    | Displays statistics for the loaded graph: total node/edge counts and a breakdown by type.         |
| `back` (or `b`)           | In *Navigation Mode*, returns to the previously viewed node in your navigation history.           |
| `reset` (or `x`)          | Resets the navigation context and exits *Navigation Mode*.                                        |

> **Tip:** To get detailed help for any command (e.g., `list`), type `<command> --help`. For example: `list --help`.

## Interactive Navigation

This is a key feature of `Nexus` that transforms graph analysis into an interactive exploration.

1.  **Enter the Mode:** Start with the `get <node_id>` command to inspect a node's details.
2.  **Context Change:** Once a node is successfully found, `Nexus` enters *Navigation Mode*. The prompt will change to show the current node's ID: `[NEXUS:a1b2c3d4]>`. The output will display a numbered list of `<< INCOMING EDGES (Predecessors)` (nodes pointing to the current one) and `>> OUTGOING EDGES (Successors)` (nodes the current one points to).
3.  **Traversal:** Simply type the **number** corresponding to the neighbor you want to inspect and press Enter. `Nexus` will automatically execute the `get` command for that new node, moving you through the graph.
4.  **Return and Exit:** Use the `back` (or `b`) command to go back one step, or `reset` (or `x`) to exit Navigation Mode.

This mechanism allows for quick and easy exploration of graph relationships by "jumping" from one node to another.

## Plugin Architecture

`Nexus` automatically scans the `nexus_tools/` directory and loads all files starting with `cmd_` as command modules. Each module "registers" one or more commands, their aliases, help text, and execution logic.

This design makes it easy to add new tools without modifying the `nexus.py` core. All the logic for commands like `trace`, `list`, `get`, `insights`, `probe`, and `plan` is implemented as such plugins.
