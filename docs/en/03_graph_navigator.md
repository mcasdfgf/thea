# 3. The Graph Navigator

**Module:** `nexus_tools/cmd_nav.py`
**Nexus Commands:** `list` (alias: `ls`), `get`

## Purpose

The Navigator provides the primary tools for "walking" through the memory graph. It allows you to browse lists of nodes by type and to inspect any individual node and its immediate surroundings in detail.

## Commands

### `list` — List Nodes

Displays a paginated list of nodes of a specified type, sorted by timestamp (newest first).

#### Usage

```
[NEXUS]> list <NodeType | Index> [--page N] [--limit N]
```

-   `<NodeType | Index>` (Required): Specify the node type by its full name, a partial name, or its index number from `list --help`.
-   `--page <N>` (Optional): The page number to display (default is 1).
-   `--limit <N>` (Optional): The number of nodes per page (default is 10).

> **Tip:** In `Nexus`, the command `list --help` will show you an **up-to-date, numbered list of all node types** that currently exist in your graph.

#### Examples

```
# Show the second page of 'ConceptNode' nodes
[NEXUS]> list ConceptNode --page 2

# Show the 5 most recent nodes using index 10 from 'list --help'
[NEXUS]> ls 10 --limit 5
```

### `get` — Get Node

Displays all attributes of a specific node, as well as its direct parents and children in the graph. **This command activates *Navigation Mode***.

#### Usage

```
[NEXUS]> get <node_ID>
```

-   `<node_ID>`: The full or partial ID of the node to inspect.

#### Understanding the Output

1.  A complete list of the node's attributes (ID, type, timestamp, content, etc.).
2.  **`<< INCOMING EDGES (Predecessors)`**: A numbered list of nodes that point **to** the current node.
3.  **`>> OUTGOING EDGES (Successors)`**: A numbered list of nodes that the current node points **to**.

This numbered list serves as an interactive menu. Simply type a number to "jump" to the corresponding node. For a detailed explanation of this mechanic, see the [1. The Nexus Interactive Shell](01_nexus_shell.md) document.
