# 1. The `Nexus` Interactive Shell

**File:** `nexus.py`

`Nexus` is the central command bridge, providing a unified, interactive interface for all diagnostic tools.

## Purpose

-   **Efficiency:** Loads the memory core once per session, making all subsequent commands instantaneous.
-   **Interactivity:** Allows you to "travel" through the memory graph by navigating from node to node using numeric options in a special *Navigation Mode*.
-   **Extensibility:** Built on a plugin architecture, automatically loading all tools from the `nexus_tools` directory.
-   **Convenience:** Consolidates all tools under short, logical commands with built-in `help` support.

## Launching

```bash
python nexus.py
```

After launching, a welcome message, graph statistics, and the command prompt will appear: `[NEXUS]>`.

## Core Commands

| Command (and alias) | Description |
| :--- | :--- |
| `help` (or `h`) | Displays a list of all available commands, grouped by category. |
| `exit`, `quit` (or `q`) | Exits the Nexus shell. |
| `refresh` (or `r`) | Reloads the memory graph from the `memory_core.graphml` file without restarting the console. |
| `stat` | Displays a brief summary of the number of nodes and edges, as well as their types. |
| `back` (or `b`) | In *Navigation Mode*, returns to the previously viewed node. |
| `reset` (or `x`) | Exits *Navigation Mode* and clears the context. |

> **Tip:** To get detailed help for any command (e.g., `list`), type `<command> --help`. For example: `list --help`.

## Interactive Navigation

This is the key feature of `Nexus`, turning graph analysis into an interactive exploration.

1.  **Entering the Mode:** Start with the `get <node_id>` command to view a node's details.
2.  **Context Change:** Once a node is successfully found, `Nexus` enters *Navigation Mode*. The input prompt will change to show the current node's ID: `[NEXUS:a1b2c3d4]>`. The output will display a numbered list of parent (`<< PARENTS`) and child (`>> CHILDREN`) nodes.
3.  **Traversal:** Simply type the **number** corresponding to the neighbor you wish to inspect and press Enter. `Nexus` will automatically execute the `get` command for that new node, moving you through the graph.
4.  **Return and Exit:** Use the `back` (or `b`) command to go back one step, or `reset` (or `x`) to exit navigation mode.

This mechanism allows for easy and rapid exploration of graph connections by "jumping" from one node to another.

## Plugin Architecture

`Nexus` automatically scans the `nexus_tools/` directory and loads all files starting with `cmd_` as command modules. Each such module "registers" one or more commands, their aliases, help text, and execution logic.

This design makes it easy to add new tools without modifying the `nexus.py` core code. All the logic for commands like `trace`, `list`, `get`, `insights`, `probe`, and `plan` is implemented as these plugins.
