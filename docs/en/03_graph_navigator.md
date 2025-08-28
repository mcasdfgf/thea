# 3. The Graph Navigator

**Module:** `nexus_tools/cmd_nav.py`
**`Nexus` Commands:** `list` (alias: `ls`), `get`

## Purpose

The Navigator is your primary tool for "walking" through the memory graph. It allows you to view lists of nodes by type and to examine any single node and its immediate surroundings in detail.

## Commands

### `list` — List Nodes

Displays a paginated list of nodes of a specified type, sorted by time (newest to oldest).

#### Usage
```
[NEXUS]> list <NodeType | Index> [--page N] [--limit N]
```
-   `<NodeType | Index>` (required): Specify the node type by its full name, a partial name, or its index number from `list --help`.
-   `--page <N>` (optional): The page number to display (default is 1).
-   `--limit <N>` (optional): The number of nodes per page (default is 10).

> **Tip:** In `Nexus`, the command `list --help` will show you a **dynamic, numbered list of all node types** that currently exist in your graph. This is the easiest way to see what data is available to view.

**Examples:**
```
# Show page 2 of nodes of type 'ConceptNode'
[NEXUS]> list ConceptNode --page 2

# Show the last 5 'UserImpulse' nodes (assuming its index in 'list --help' is 10)
[NEXUS]> ls 10 --limit 5
```

### `get` — Get Node

Displays all attributes of a single node, as well as its direct parent and child nodes in the graph. **This command activates *Navigation Mode***.

#### Usage
```
[NEXUS]> get <node_id>
```
-   `<node_id>`: The full or partial ID of the node to inspect.

#### Interpreting the Output
1.  **`// NODE DATA //`**: A complete list of all the node's attributes (ID, type, state, timestamp, content, etc.).
2.  **`<< PARENTS (Predecessors)`**: A numbered list of nodes that **point to** the current node.
3.  **`>> CHILDREN (Successors)`**: A numbered list of nodes that the current node **points to**.

This numbered list serves as an interactive menu. Simply type a number to "jump" to the corresponding node. See [The `Nexus` Interactive Shell](01_nexus_shell.md) for more details.
