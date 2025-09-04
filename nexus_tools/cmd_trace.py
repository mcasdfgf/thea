# cmd_trace.py: Implements the 'trace' command for the Nexus shell.
# This command reconstructs and displays the "cognitive chain" for a given node.
# It traverses the memory graph along specific "process" edges (like IS_TASK_FOR,
# IS_RESULT_OF) to create a visual tree of the operations that led to or
# followed from a particular event, making it an essential debugging tool.

from collections import deque
from colorama import Fore, Style


def register():
    """Registers the 'trace' command with the shell."""
    return {
        "trace": {
            "func": cmd_trace,
            "alias": ["tr"],
            "help": "Trace the cognitive chain for a node. Usage: trace <id>",
        }
    }


def print_trace_help(style):
    cmd, arg_name, sec, header, reset = (
        style["cmd_name"],
        style["arg_name"],
        style["secondary_text"],
        style["header"],
        style["reset"],
    )

    print(f"\n{header}Usage: {cmd}trace (tr) {arg_name}<ID>{reset}")
    print(
        f"{sec}Traces the full cognitive process chain related to a given node ID.{reset}\n"
    )

    print(f"{header}Arguments:{reset}")
    print(
        f"  {arg_name}<ID>{reset}    (Required) The full or partial ID of the node to start the trace from.\n"
    )
    print(f"{header}Description:{reset}")
    print(
        f"{sec}This command reconstructs the sequence of tasks and reports that led to the creation of a node, "
        f"or that were initiated by it. It traverses the graph using only 'process-related' edges "
        f"to show the logical flow of operations, ignoring purely conceptual links.{reset}"
    )


async def cmd_trace(memory, style, args):
    """Handler for the 'trace' command."""
    if not args or "--help" in args:
        print_trace_help(style)
        return

    partial_start_id = args[0]

    print(
        f"{style['section_header']}TRACE:{style['reset']} Tracing cognitive chain for ID starting with '{partial_start_id}'..."
    )
    print("-" * 80)

    try:
        _trace_chain_wrapper(memory, style, partial_start_id)
    except Exception as e:
        print(f"{style['error']}Error during trace: {e}")

    print("-" * 80)
    print(f"{style['section_header']}END TRACE{style['reset']}")


def _trace_chain_wrapper(memory, style, partial_start_id: str):
    # Defines the edge labels that represent the flow of a cognitive process.
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

    # Step 1: Find the full node ID from a partial prefix.
    full_start_id = None
    if memory.graph.has_node(partial_start_id):
        full_start_id = partial_start_id
    else:
        for node_id in memory.graph.nodes:
            if node_id.startswith(partial_start_id):
                full_start_id = node_id
                break

    if not full_start_id:
        print(
            f"{style['error']}Error:{Style.RESET_ALL} Node with ID prefix '{partial_start_id}' not found."
        )
        return

    # Step 2: Perform a Breadth-First Search (BFS) starting from the target node,
    # traversing only along "process" edges to find all nodes in the same chain.
    nodes_in_chain = set()
    queue = deque([full_start_id])
    visited_for_bfs = {full_start_id}
    while queue:
        current_id = queue.popleft()
        nodes_in_chain.add(current_id)
        for neighbor_id in list(memory.graph.predecessors(current_id)) + list(
            memory.graph.successors(current_id)
        ):
            edge_fwd = memory.graph.get_edge_data(current_id, neighbor_id)
            edge_bwd = memory.graph.get_edge_data(neighbor_id, current_id)
            is_process_edge = (edge_fwd and edge_fwd.get("label") in PROCESS_EDGES) or (
                edge_bwd and edge_bwd.get("label") in PROCESS_EDGES
            )
            if is_process_edge and neighbor_id not in visited_for_bfs:
                visited_for_bfs.add(neighbor_id)
                queue.append(neighbor_id)

    # Step 3: Build a parent-to-child relationship map for tree traversal
    # and identify the root nodes of the chain (nodes with no parents within the chain).
    children_map = {node_id: [] for node_id in nodes_in_chain}
    roots = set(nodes_in_chain)
    for node_id in nodes_in_chain:
        for predecessor_id in memory.graph.predecessors(node_id):
            if predecessor_id in nodes_in_chain:
                edge_data = memory.graph.get_edge_data(predecessor_id, node_id)
                if edge_data and edge_data.get("label") in PROCESS_EDGES:
                    children_map[node_id].append(predecessor_id)
                    # A node that is a child cannot be a root.
                    if predecessor_id in roots:
                        roots.remove(predecessor_id)

    # Step 4: Determine the final starting points for printing the tree.
    # Prioritize 'UserImpulse' as the most logical start of a chain.
    final_roots = [
        r for r in roots if memory.graph.nodes[r].get("type") == "UserImpulse"
    ]
    if not final_roots:
        for node_id in nodes_in_chain:
            if memory.graph.nodes[node_id].get("type") == "UserImpulse":
                final_roots.append(node_id)
                break
    if not final_roots:
        final_roots = sorted(list(roots))

    # Step 5: Recursively print the tree structure starting from the root(s).
    visited_for_print = set()

    def print_tree(node_id, prefix="", is_last=True):
        node_data = memory.graph.nodes.get(node_id, {})
        node_type = node_data.get("type", "Unknown")

        print(prefix, end="")

        if node_id in visited_for_print:
            print(f"{Fore.YELLOW}↪ (link to already shown {node_type} [{node_id[:8]}])")
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

        children = sorted(list(set(children_map.get(node_id, []))))
        for i, child_id in enumerate(children):
            is_child_last = i == len(children) - 1

            if prefix.endswith("├─> "):
                base_prefix = prefix[:-4] + "│   "
            elif prefix.endswith("└─> "):
                base_prefix = prefix[:-4] + "    "
            else:
                base_prefix = prefix

            connector = "└─> " if is_child_last else "├─> "
            print_tree(child_id, base_prefix + connector)

    # Final call to print the tree for each identified root.
    for root_id in final_roots:
        print_tree(root_id, prefix="", is_last=True)
