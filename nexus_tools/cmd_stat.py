# cmd_stat.py: Implements the 'stat' command for the Nexus shell.
# This command provides a quick, high-level overview of the contents
# of the loaded UniversalMemory graph, including total node and edge counts,
# and a breakdown of nodes by their type.

from collections import Counter
from colorama import Fore, Style


def register():
    """Registers the 'stat' command with the Nexus shell."""
    return {
        "stat": {
            "func": cmd_stat,
            "alias": [],
            "help": "Displays statistics about the loaded memory graph.",
        }
    }


async def cmd_stat(memory, style, args):
    """Handler for the 'stat' command."""
    if not memory or not memory.graph:
        print(f"{style['error']}Error:{Style.RESET_ALL} Memory graph is not loaded.")
        return

    nodes = list(memory.graph.nodes(data=True))
    edges = memory.graph.edges()

    num_nodes = len(nodes)
    num_edges = len(edges)

    node_types = [data.get("type", "Untyped") for _, data in nodes]
    type_counts = Counter(node_types)

    print(f"\n{style['section_header']}--- Memory Core Statistics ---{Style.RESET_ALL}")
    print(f"  {style['arg_name']}Total Nodes:{Style.RESET_ALL} {num_nodes}")
    print(f"  {style['arg_name']}Total Edges:{Style.RESET_ALL} {num_edges}")

    if type_counts:
        print(f"\n{style['arg_name']}Node Types Breakdown:{Style.RESET_ALL}")

        sorted_types = sorted(
            type_counts.items(), key=lambda item: item[1], reverse=True
        )
        for node_type, count in sorted_types:
            print(
                f"    - {style['cmd_name']}{node_type:<25}{Style.RESET_ALL} : {count}"
            )
    print(f"{style['section_header']}------------------------------{Style.RESET_ALL}")
