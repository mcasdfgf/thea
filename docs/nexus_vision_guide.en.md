# `nexus-vision` Guide

`nexus-vision` is an interactive web-based visualizer designed for exploring the "memory snapshot" (`memory_core.graphml`) of the T.H.E.A. cognitive architecture. It allows you to visually analyze the connections between the system's thoughts, tasks, and knowledge.

### Interface Overview

The interface is divided into three main areas:
1.  **Control Panel (Left):** The primary hub for graph interaction. Here you will find:
    *   **Control Buttons:** To refresh the graph, toggle the physics simulation, release all pinned nodes, and show/hide edge labels.
    *   **Filters:** Allow you to display nodes by a time range and by their type. This is the main tool for reducing noise and focusing on the data of interest.

2.  **Graph Canvas (Center):** The space where nodes and edges are rendered.
    *   **Navigation:** Zoom with the mouse wheel, pan by dragging the canvas.
    *   **Interaction:** Nodes can be dragged and dropped.

3.  **Inspector (Right):** When you click on a node or an edge, this panel displays its detailed information.

### Key Features & Pro-Tips

#### 1. Tracing the "Thought Chain"
This is the most powerful debugging feature. It allows you to reconstruct the complete sequence of actions that led to the creation of a specific node.

*   **How to use:**
    1.  Click on a node of interest (e.g., a `FinalResponseNode`).
    2.  In the **Inspector** on the right, click the node's **ID** (it is styled as a button).
    3.  The graph will automatically switch to **Trace Mode**, displaying only the nodes that participated in that specific "thought process."
    4.  To exit this mode, click the red **"Reset Trace"** button in the Control Panel.

#### 2. Pinning Nodes
The physics simulation constantly rearranges nodes for optimal layout. To fix an important node in place and manage its position manually:

*   **Click and drag a node:** As soon as you start dragging a node, it gets automatically "pinned" to the canvas. After you release the mouse button, it will remain in its new position, unaffected by the simulation.
*   **Unpinning a node:** To release a node back into the "live" simulation, **double-click** on it. It will become "unpinned" and will be repositioned by the simulation forces.
*   **Unpinning all nodes:** The Control Panel has a **"Release All Nodes"** button. It unpins every node you have manually fixed, giving the simulation a powerful impulse to beautifully rearrange the entire graph.

#### 3. Highlighting Context
To quickly see a node's direct connections without running a full trace:

*   **Single-click** on a node. The node, its immediate neighbors, and the edges between them will remain bright. The rest of the graph will fade, allowing you to focus on the local context.

#### 4. Inferred Edges
Sometimes, you might filter nodes in such a way that the start and end nodes of a chain are visible, but the intermediate ones are not. In this case, `nexus-vision` will draw a **dashed line** between them. This indicates that the two nodes are not directly connected in the current view but are linked via a path in the full graph.

#### 5. The Smart Inspector
The Inspector is designed for deep-diving into node content.

*   **Quick Summary:** When you select a node, the Inspector displays its key attributes and attempts to show the most relevant part of its content as a brief summary.
*   **Viewing Raw Data:** For a complete and detailed analysis, click the **"Show Raw Data"** button. A modal window will open, displaying the full, formatted content of the node, which can be easily viewed and copied.
