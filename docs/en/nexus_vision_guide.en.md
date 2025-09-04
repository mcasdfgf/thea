# `nexus-vision` User Guide

`nexus-vision` is an interactive web-based visualizer designed for exploring a static "memory snapshot" (`memory_core.graphml`) from the T.H.E.A. cognitive architecture. It renders the `UniversalMemory` graph and provides tools for visually analyzing its structure.

### Interface Overview

The interface is divided into three main areas:
1.  **Control Panel (Left):** Your primary workspace for interacting with the graph. Here you will find:
    -   **Control Buttons:** Refresh the graph, toggle the physics simulation, and release all pinned nodes.
    -   **View Settings:** Toggle the visibility of text labels on the graph edges.
    -   **Filters:** Display nodes by a specific time range (`Time Filter`) and by type (`Node Types`). This is the main tool for reducing noise and focusing on the data you're interested in.

2.  **Graph Canvas (Center):** The space where nodes and edges are rendered.
    -   **Navigation:** Zoom with the mouse wheel, pan the canvas by clicking and dragging.
    -   **Interaction:** Nodes can be dragged and repositioned.

3.  **Inspector (Right):** When you click on a node or edge, detailed information appears here.

### Key Features & Hidden Gems

#### 1. Tracing the "Thought Process"
This is the most powerful debugging feature. It allows you to reconstruct the full sequence of actions that led to the creation of a specific node.

-   **How to use:**
    1.  Click on a node of interest (e.g., a `FinalResponseNode`).
    2.  In the **Inspector** panel on the right, click on the **Node ID** (it is styled like a button). A hint "(click ID to trace the chain)" will appear below it.
    3.  The graph will automatically switch to **Trace Mode**, leaving only the nodes that participated in that specific "thought process" on the screen.
    4.  To exit this mode, click the red **"Reset Trace"** button in the Control Panel.

#### 2. Pinning Nodes
The physics simulation constantly moves nodes to find an optimal layout. To pin an important node in place and control its position manually:

-   **Click and drag a node:** As soon as you start dragging a node, it gets "pinned" to the canvas. After you release the mouse button, it will remain in its new position, unaffected by the simulation.
-   **Unpin a node:** To release a node back into the live simulation, **double-click** it. It will become "unpinned" and reposition itself according to the simulation's forces.
-   **Unpin all nodes:** The Control Panel has a **"Release All Nodes"** button. This unpins every node you have manually positioned and gives the simulation a powerful impulse to beautifully rearrange the entire graph.

#### 3. Context Highlighting
To quickly see a node's direct connections without running a full trace:

-   **Single-click** on a node. The node, its immediate neighbors, and the edges connecting them will remain bright. The rest of the graph will fade, allowing you to focus on the local context.

#### 4. Inferred Edges
Sometimes, you might filter the nodes in such a way that the start and end nodes of a chain are visible, but the intermediate nodes are hidden. In this case, `nexus-vision` will draw a **dashed line** between them. This "inferred" edge means: "These two nodes are not directly connected, but there is a path between them through one or more nodes that you have hidden with the filters."

#### 5. The Smart Inspector
The Inspector is designed for deep-diving into a node's content.

-   **Summary View:** When a node is selected, the Inspector displays its key attributes and attempts to show the most relevant part of its content as a concise summary.
-   **Viewing Raw Data:** for a complete and detailed analysis, click the **"Show Raw Data"** button. A modal window will open with the full, formatted content of the node, which you can easily review and copy.
