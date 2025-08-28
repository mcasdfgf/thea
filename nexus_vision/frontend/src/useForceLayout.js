/**
 * @file useForceLayout.js
 * @description
 * This is a custom React hook that integrates the D3 Force Simulation library with React Flow.
 * It provides a physics-based, force-directed layout for the graph nodes and edges.
 *
 * Key Features:
 * - Manages a D3 simulation instance in a React-friendly way using `useRef`.
 * - Decouples the physics simulation ticks from React's render cycle by using `requestAnimationFrame`
 *   for smooth, performant animations.
 * - Provides callback functions (`onNodeDrag`, `onNodeDoubleClick`, etc.) that allow user
 *   interactions to influence the physics simulation (e.g., pinning nodes).
 * - Exposes a state management interface (`nodes`, `edges`, `onNodesChange`, etc.) that is
 *   compatible with the main `ReactFlow` component.
 */

import { useCallback, useEffect, useRef } from "react";
import { useNodesState, useEdgesState } from "reactflow";
import {
  forceSimulation,
  forceLink,
  forceManyBody,
  forceCenter,
  forceCollide,
  forceX,
  forceY,
} from "d3-force";

export function useForceLayout({ isPhysicsEnabled }) {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);

  const simulationRef = useRef();
  const animationFrameRef = useRef();

  const updateGraph = useCallback(
    (newNodes, newEdges) => {
      const simulation = simulationRef.current;
      if (!simulation) return;
      setNodes(newNodes);
      setEdges(newEdges);
      const oldNodesMap = new Map(
        simulation.nodes().map((node) => [node.id, node]),
      );
      const updatedSimNodes = newNodes.map((node) => {
        const oldNode = oldNodesMap.get(node.id);
        return oldNode
          ? {
              ...node,
              x: oldNode.x,
              y: oldNode.y,
              fx: oldNode.fx,
              fy: oldNode.fy,
            }
          : node;
      });
      simulation.nodes(updatedSimNodes);
      simulation.force("link").links(newEdges.map((e) => ({ ...e })));
      simulation.alpha(1).restart();
    },
    [setNodes, setEdges],
  );

  useEffect(() => {
    const simulation = forceSimulation()
      .force(
        "link",
        forceLink()
          .id((d) => d.id)
          .distance(150)
          .strength(0.7),
      )
      .force("charge", forceManyBody().strength(-450).distanceMax(250))
      .force(
        "collide",
        forceCollide()
          .radius((d) => d.data.size / 2 + 15)
          .strength(0.8),
      )
      .force("x", forceX().strength(0.005))
      .force("y", forceY().strength(0.005));
    simulationRef.current = simulation;
  }, []);

  useEffect(() => {
    const simulation = simulationRef.current;
    if (!simulation) return;

    const animationLoop = () => {
      setNodes((currentNodes) => {
        const simNodesMap = new Map(simulation.nodes().map((n) => [n.id, n]));
        return currentNodes.map((rn) => {
          const simNode = simNodesMap.get(rn.id);
          return simNode
            ? { ...rn, position: { x: simNode.x, y: simNode.y } }
            : rn;
        });
      });
      animationFrameRef.current = requestAnimationFrame(animationLoop);
    };

    if (isPhysicsEnabled) {
      simulation.alpha(0.3).restart();
      animationFrameRef.current = requestAnimationFrame(animationLoop);
    } else {
      simulation.stop();
      cancelAnimationFrame(animationFrameRef.current);
    }

    return () => {
      cancelAnimationFrame(animationFrameRef.current);
    };
  }, [isPhysicsEnabled, setNodes]);

  const onNodeDragStart = useCallback((_, node) => {}, []);

  const onNodeDrag = useCallback(
    (_, draggedNode) => {
      if (!isPhysicsEnabled) {
        setNodes((nds) =>
          nds.map((n) =>
            n.id === draggedNode.id
              ? { ...n, position: draggedNode.position }
              : n,
          ),
        );
      }

      const simulation = simulationRef.current;
      if (simulation) {
        const simNode = simulation.nodes().find((n) => n.id === draggedNode.id);
        if (simNode) {
          simNode.fx = draggedNode.position.x;
          simNode.fy = draggedNode.position.y;
        }
      }

      if (isPhysicsEnabled) {
        simulation?.alphaTarget(0.1).restart();
      }
    },
    [isPhysicsEnabled, setNodes],
  );

  const onNodeDragStop = useCallback(
    (_, node) => {
      const simulation = simulationRef.current;
      if (!simulation) return;

      if (isPhysicsEnabled) {
        simulation.alphaTarget(0);
      }

      const simNode = simulation.nodes().find((n) => n.id === node.id);
      if (simNode) {
        simNode.fx = node.position.x;
        simNode.fy = node.position.y;
      }
    },
    [isPhysicsEnabled],
  );

  const onNodeDoubleClick = useCallback((_, node) => {
    const simulation = simulationRef.current;
    if (!simulation) return;

    const simNode = simulation.nodes().find((n) => n.id === node.id);
    if (simNode) {
      if (simNode.fx !== null) {
        simNode.fx = null;
        simNode.fy = null;

        simulation.alpha(0.5).restart();
      } else {
        simNode.fx = node.position.x;
        simNode.fy = node.position.y;
      }
    }
  }, []);

  const releaseAllNodes = useCallback(() => {
    const simulation = simulationRef.current;
    if (!simulation) return;

    simulation.nodes().forEach((node) => {
      node.fx = null;
      node.fy = null;
    });

    simulation.alpha(1).restart();
  }, []);

  const stopPhysics = useCallback(() => {
    simulationRef.current?.stop();
  }, []);

  const resumePhysics = useCallback(() => {
    simulationRef.current?.alpha(0.5).restart();
  }, []);

  return {
    nodes,
    edges,
    onNodesChange,
    onEdgesChange,
    updateGraph,
    onNodeDragStart,
    onNodeDrag,
    onNodeDragStop,
    onNodeDoubleClick,
    releaseAllNodes,
    stopPhysics,
    resumePhysics,
  };
}
