# file: nexus_tools/cmd_trace.py

from collections import deque
from colorama import Fore, Style


def register():
    """Registers the 'trace' command with the Nexus shell."""
    return {
        "trace": {
            "func": cmd_trace,
            "alias": ["tr"],
            "help": "Trace the cognitive chain. Usage: trace <id>",
        }
    }


async def cmd_trace(memory, style, args):
    """
    Handler for the 'trace' command. Finds a start node and initiates the tracing logic.

    Args:
        memory (nx.DiGraph): The networkx graph object.
        style (dict): A dictionary of colorama styles for output.
        args (list): A list of command-line arguments, expects one: the node ID.
    """
    if not args:
        print(f"{style['error']}Error:{Style.RESET_ALL} Usage: trace <id>")
        return

    partial_start_id = args[0]
    H_GREEN = style["header"]

    print(
        f"{H_GREEN}TRACE:{Style.RESET_ALL} Tracing cognitive chain for ID starting with '{partial_start_id}'..."
    )
    print("-" * 80)

    try:
        # NOTE: The core logic is wrapped to keep the handler clean.
        # This function operates directly on the networkx graph object.
        _trace_chain_wrapper(memory, style, partial_start_id)
    except Exception as e:
        print(f"{style['error']}Error during trace: {e}")

    print("-" * 80)
    print(f"{H_GREEN}END TRACE{Style.RESET_ALL}")


def _trace_chain_wrapper(memory, style, partial_start_id: str):
    """
    Finds the full cognitive chain related to a start node and prints it as a tree.
    This is a complex operation that reconstructs a directed acyclic graph (DAG)
    from what might be a cyclic subgraph and then finds its roots to print hierarchically.
    """
    # Define the edge labels that represent a direct "process" flow.
    # This helps distinguish operational links from semantic ones (e.g., CONTAINS_CONCEPT).
    PROCESS_EDGES = [
        "IS_TASK_FOR",
        "IS_RESULT_OF",
        "CONTAINS_PLAN",
        "WAS_SYNTHESIZED_FROM",
        "IS_RESPONSE_TO",
        "IS_INSTINCT_FOR",
        "HAS_RESEARCH",
        "USED_QUERY",
        "FOUND_SOURCE",
        "CONTAINS_FACT",
        "SOURCED_FROM",
        "SUPERSEDES",
    ]

    # --- Step 1: Find the full node ID if a partial one was given. ---
    full_start_id = None
    if memory.has_node(partial_start_id):
        full_start_id = partial_start_id
    else:
        for node_id in memory.nodes:
            if node_id.startswith(partial_start_id):
                full_start_id = node_id
                break

    if not full_start_id:
        print(
            f"{style['error']}Error:{Style.RESET_ALL} Node with ID prefix '{partial_start_id}' not found."
        )
        return

    # --- Step 2: Traverse the graph to find all nodes in the process chain. ---
    # We use Breadth-First Search (BFS) starting from the initial node,
    # following PROCESS_EDGES in both directions to capture the entire "island" of activity.
    nodes_in_chain = set()
    queue = deque([full_start_id])
    visited_for_bfs = {full_start_id}
    while queue:
        current_id = queue.popleft()
        nodes_in_chain.add(current_id)
        # Check both predecessors and successors to walk the graph regardless of edge direction.
        for neighbor_id in list(memory.predecessors(current_id)) + list(
            memory.successors(current_id)
        ):
            edge_fwd = memory.get_edge_data(current_id, neighbor_id)
            edge_bwd = memory.get_edge_data(neighbor_id, current_id)
            is_process_edge = (edge_fwd and edge_fwd.get("label") in PROCESS_EDGES) or (
                edge_bwd and edge_bwd.get("label") in PROCESS_EDGES
            )
            if is_process_edge and neighbor_id not in visited_for_bfs:
                visited_for_bfs.add(neighbor_id)
                queue.append(neighbor_id)

    # --- Step 3: Reconstruct the parent-child hierarchy and find the roots. ---
    # The graph can have cycles or multiple parents. To print it as a tree, we need
    # to establish a clear parent->child flow and identify the root nodes (those without parents *within the chain*).
    children_map = {node_id: [] for node_id in nodes_in_chain}
    # Assume all nodes are roots initially, then disqualify them if they are found to be children.
    roots = set(nodes_in_chain)
    for node_id in nodes_in_chain:
        for predecessor_id in memory.predecessors(node_id):
            if predecessor_id in nodes_in_chain:
                edge_data = memory.get_edge_data(predecessor_id, node_id)
                if edge_data and edge_data.get("label") in PROCESS_EDGES:
                    # NOTE: We are building a map from child to parent (predecessor).
                    children_map[node_id].append(predecessor_id)
                    # If a node is a child of another node in the chain, it cannot be a root.
                    if predecessor_id in roots:
                        roots.remove(predecessor_id)

    # --- Step 4: Refine the root selection. ---
    # Ideally, a trace should start from a UserImpulse. We prioritize this.
    final_roots = [r for r in roots if memory.nodes[r].get("type") == "UserImpulse"]
    if not final_roots:
        # If no UserImpulse is in the initial root set (e.g., trace started mid-chain),
        # search the entire chain for one to provide better context.
        for node_id in nodes_in_chain:
            if memory.nodes[node_id].get("type") == "UserImpulse":
                final_roots.append(node_id)
                break
    if not final_roots:
        # If there's no UserImpulse at all, fall back to the calculated roots.
        final_roots = sorted(list(roots))

    # --- Step 5: Recursively print the tree starting from the identified roots. ---
    visited_for_print = set()

    def print_tree(node_id, prefix="", is_last=True):
        """A recursive function to print the reconstructed tree structure."""
        node_data = memory.nodes.get(node_id, {})
        node_type = node_data.get("type", "Unknown")

        print(prefix, end="")

        # HACK: Handle potential cycles in the reconstructed graph by printing a link
        # instead of re-printing an entire subtree.
        if node_id in visited_for_print:
            print(f"{Fore.YELLOW}(link to {node_type} [{node_id[:8]}])")
            return

        visited_for_print.add(node_id)

        content = str(node_data.get("content", ""))
        preview = (
            (content.replace("\n", " ")[:60] + "...")
            if len(content) > 60
            else content.replace("\n", " ")
        )

        type_color_map = {
            "UserImpulse": Fore.GREEN,
            "FinalResponseNode": Fore.GREEN + Style.BRIGHT,
            "InstinctiveResponseNode": Fore.CYAN,
            "TaskNode": Fore.CYAN,
            "ReportNode": Fore.YELLOW,
            "SearchPlanNode": Fore.MAGENTA,
        }
        type_str = (
            f"{type_color_map.get(node_type, Fore.WHITE)}{node_type}{Style.RESET_ALL}"
        )

        print(
            f"[ {Fore.MAGENTA}{node_id[:8]}{Style.RESET_ALL} ] {type_str:<45} : {preview}"
        )

        # Note: The map is built from child to parent, so we look up `node_id` to find its parents.
        # For printing, we conceptually treat the parents as "children" in the tree display.
        children = sorted(list(set(children_map.get(node_id, []))))
        for i, child_id in enumerate(children):
            is_child_last = i == len(children) - 1

            # This logic correctly builds the tree structure prefixes (│, └, ├).
            if prefix.endswith("├─> "):
                base_prefix = prefix[:-4] + "│   "
            elif prefix.endswith("└─> "):
                base_prefix = prefix[:-4] + "    "
            else:
                base_prefix = prefix  # Root level

            connector = "└─> " if is_child_last else "├─> "
            print_tree(child_id, base_prefix + connector)

    # --- Final invocation for each root found ---
    for root_id in final_roots:
        print_tree(root_id, prefix="", is_last=True)
