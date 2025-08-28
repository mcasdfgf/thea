# file: nexus_tools/cmd_stat.py

from collections import Counter
from colorama import Style


def register():
    """Registers the 'stat' command with the Nexus shell."""
    return {
        "stat": {
            "func": cmd_stat,
            "alias": [],
            "help": "Display statistics about the memory graph.",
            # NOTE: We add the category here for organized 'help' output in nexus.py
            "category": "Shell & Memory",
        }
    }


async def cmd_stat(memory, style, args):
    """
    Handler for the 'stat' command.
    Calculates and prints a summary of the loaded memory graph.

    Args:
        memory (nx.DiGraph): The networkx graph object.
        style (dict): A dictionary of colorama styles for output.
        args (list): A list of command-line arguments (not used by this command).
    """
    # NOTE: In the demo version, 'memory' is the networkx graph object itself.
    # We check if it has nodes, as an empty graph is a valid state.
    if not memory or not memory.graph:
        print(f"{style['error']}Error:{Style.RESET_ALL} Memory graph is not loaded.")
        return

    nodes = list(memory.nodes(data=True))
    edges = memory.edges()

    num_nodes = len(nodes)
    num_edges = len(edges)

    # Extract the 'type' attribute from each node's data dictionary.
    # Use 'Untyped' as a default for nodes that might lack this attribute.
    node_types = [data.get("type", "Untyped") for _, data in nodes]
    # Use Counter to efficiently count occurrences of each node type.
    type_counts = Counter(node_types)

    # --- Print the formatted output ---
    header = style.get("header", "")
    arg = style.get("arg", "")
    cmd = style.get("cmd", "")
    reset = style.get("reset", "")

    print(f"\n{header}--- Memory Core Statistics ---{reset}")
    print(f"  {arg}Total Nodes:{reset} {num_nodes}")
    print(f"  {arg}Total Edges:{reset} {num_edges}")

    if type_counts:
        print(f"\n{style['arg']}Node Types Breakdown:{Style.RESET_ALL}")
        # Sort types by count in descending order for a more readable summary.
        sorted_types = sorted(
            type_counts.items(), key=lambda item: item[1], reverse=True
        )
        for node_type, count in sorted_types:
            # Use f-string formatting for clean, aligned columns.
            print(f"    - {cmd}{node_type:<25}{reset} : {count}")
    print(f"{header}------------------------------{reset}")
