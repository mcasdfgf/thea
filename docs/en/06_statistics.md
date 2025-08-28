# 6. Graph Statistics

**Module:** `nexus_tools/cmd_stat.py`
**`Nexus` Command:** `stat`

## Purpose

The `stat` command provides a quick overview of the current state of the memory graph. It is useful for getting a general sense of the size and composition of the "consciousness snapshot" you are working with.

## Usage

The command takes no arguments.
```
[NEXUS]> stat
```

## Interpreting the Output

The output is a brief summary of the graph's key metrics:

```
--- Memory Core Statistics ---
  Total Nodes: 2451
  Total Edges: 3120

Node Types Breakdown:
    - ReportNode                : 890
    - TaskNode                  : 852
    - ConceptNode               : 450
    - UserImpulse               : 85
    - FinalResponseNode         : 85
    - KnowledgeCrystalNode      : 45
    - ... (other node types)
------------------------------
```

*   **Total Nodes:** The total number of nodes (vertices) in the graph.
*   **Total Edges:** The total number of connections (edges) between nodes.
*   **Node Types Breakdown:** A list of all node types found in the graph, sorted in descending order by their count. This allows you to immediately see which entities are most prevalent in the current memory.

This command is automatically executed once when `Nexus` starts to give you immediate context about the loaded memory.
