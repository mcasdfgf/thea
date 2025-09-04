# cmd_nav.py: Implements core navigation commands for the Nexus shell.
# This module provides the essential 'list' and 'get' commands, forming the
# foundation for manual graph traversal and inspection.

import json
import argparse
from colorama import Fore, Style


class NexusArgParser(argparse.ArgumentParser):
    """
    An ArgumentParser that raises SystemExit instead of calling sys.exit().
    This allows command functions to gracefully handle parsing errors or --help
    requests without terminating the entire Nexus shell.
    """

    def exit(self, status=0, message=None):
        raise SystemExit(message)

    def error(self, message):
        self.print_usage()
        print(f"Error: {message}\n")
        raise SystemExit(message)


def register():
    return {
        "list": {
            "func": cmd_list,
            "alias": ["ls"],
            "help": 'List nodes with filters, pagination. Use "list --help" for details.',
        },
        "get": {
            "func": cmd_get,
            "alias": [],
            "help": 'Get node details and enter Navigation Mode. Use "get --help" for details.',
        },
    }


# --- Command Logic ---
async def cmd_list(memory, style, args):
    """Handler for the 'list' command with interactive type, pagination and limit."""
    parser = NexusArgParser(prog="list", add_help=False)
    parser.add_argument(
        "type_or_index", nargs="?", help="Node type name or index from 'list --help'."
    )
    parser.add_argument(
        "--type", dest="type_from_flag", help="Specify node type with a flag."
    )
    parser.add_argument("--page", type=int, default=1, help="Page number to display.")
    parser.add_argument(
        "--limit", type=int, default=10, help="Number of items per page."
    )
    parser.add_argument("--help", action="store_true", help="Show help message.")

    try:
        parsed_args = parser.parse_args(args)
    except SystemExit:
        return

    if parsed_args.help or not (
        parsed_args.type_or_index or parsed_args.type_from_flag
    ):
        print_list_help(memory, style)
        return

    node_type_input = parsed_args.type_from_flag or parsed_args.type_or_index
    page = parsed_args.page
    limit = parsed_args.limit

    node_types = _get_available_node_types(memory)
    node_type = None

    if node_type_input.isdigit():
        try:
            index = int(node_type_input)
            if 1 <= index <= len(node_types):
                node_type = node_types[index - 1]
            else:
                print(
                    f"{style['error']}Error:{Style.RESET_ALL} Invalid index '{index}'. Use 'list --help' to see available options."
                )
                return
        except (ValueError, TypeError):
            pass

    if node_type is None:
        found_types = [t for t in node_types if node_type_input.lower() in t.lower()]
        if len(found_types) == 1:
            node_type = found_types[0]
        elif len(found_types) > 1:
            print(
                f"{style['error']}Error:{Style.RESET_ALL} Ambiguous type '{node_type_input}'. It matches: {', '.join(found_types)}"
            )
            return
        else:
            print(
                f"{style['error']}Error:{Style.RESET_ALL} Node type '{node_type_input}' not found. Use 'list --help' to see available types."
            )
            return

    print(
        f"{style['meta_info']}QUERY:{style['reset']} Finding nodes of type '{style['arg_name']}{node_type}{style['reset']}'..."
    )

    nodes_of_type = [
        (node_id, data)
        for node_id, data in memory.graph.nodes(data=True)
        if data.get("type") == node_type
    ]
    if not nodes_of_type:
        print(f"Info: No nodes found for type '{node_type}'.")
        return

    nodes_of_type.sort(key=lambda item: item[1].get("timestamp", ""), reverse=True)

    start_index = (page - 1) * limit
    end_index = start_index + limit
    paginated_results = nodes_of_type[start_index:end_index]
    total_pages = (len(nodes_of_type) + limit - 1) // limit

    if not paginated_results:
        print(f"Info: No nodes on page {page}. Total pages available: {total_pages}.")
        return

    print("-" * 100)
    header = f"Displaying {len(paginated_results)} of {len(nodes_of_type)} nodes: {style['header']}{node_type}{style['reset']}"
    pagination_info = f"Page {page}/{total_pages}"
    print(f"{header:<80} {pagination_info:>18}")
    print("-" * 100)

    for node_id, node_data in paginated_results:
        timestamp = node_data.get("timestamp", "N/A")[:19]
        content = str(node_data.get("content", ""))
        preview = (
            (content[:70] + "...").replace("\n", " ")
            if len(content) > 70
            else content.replace("\n", " ")
        )

        print(
            f"[{style['cmd_name']}{node_id[:8]}{style['reset']}] ({style['secondary_text']}{timestamp}{style['reset']}) │ {preview}"
        )

    print("-" * 100)
    if page < total_pages:
        base_cmd = (
            f"ls {node_type_input}"
            if not parsed_args.type_from_flag
            else f"ls --type {node_type}"
        )
        print(
            f"Hint: Hint: To see the next page, use: {style['cmd_name']}{base_cmd} --page {style['arg_name']}{page + 1}{style['reset']} --limit {style['arg_name']}{limit}{style['reset']}"
        )


async def cmd_get(memory, style, args):
    if not args or "--help" in args:
        print_get_help(style)
        return None, {}
    if not args:
        print(
            f"{style['error']}Error:{Style.RESET_ALL} Usage: get <partial_or_full_id>"
        )
        return None, {}
    partial_id = args[0]
    node_id_found = None
    if memory.graph.has_node(partial_id):
        node_id_found = partial_id
    else:
        for nid in memory.graph.nodes:
            if nid.startswith(partial_id):
                node_id_found = nid
                break
    if not node_id_found:
        print(
            f"{style['error']}Error:{Style.RESET_ALL} Node with ID prefix '{partial_id}' not found."
        )
        return None, {}
    node_data = memory.graph.nodes[node_id_found]
    print(f"\n// {style['section_header']}NODE :: {node_id_found}{style['reset']} //")
    print("-" * 60)

    for key, value in sorted(node_data.items()):
        val_str = str(value)
        if val_str.strip().startswith(("{", "[")):
            try:
                parsed = json.loads(val_str)
                val_str = json.dumps(parsed, ensure_ascii=False, indent=2)
            except (json.JSONDecodeError, TypeError):
                pass
        print(f"{style['cmd_name']}{key:<15}:{style['reset']} {val_str}")
    neighbors_map = {}
    i = 1
    print(f"\n{style['header']}<< INCOMING EDGES (Predecessors){style['reset']}")
    predecessors = list(memory.graph.predecessors(node_id_found))
    if not predecessors:
        print(f"   {style['secondary_text']}(None){style['reset']}")
    for pred_id in predecessors:
        pred_data = memory.graph.nodes[pred_id]
        label = memory.graph.get_edge_data(pred_id, node_id_found).get(
            "label", "related"
        )
        print(
            f"   [{style['arg_name']}{i}{style['reset']}] {pred_id[:8]} ({pred_data.get('type')}) --[{style['meta_info']}{label}{style['reset']}]-->"
        )
        neighbors_map[i] = pred_id
        i += 1

    print(f"\n{style['header']}>> OUTGOING EDGES (Successors){style['reset']}")
    successors = list(memory.graph.successors(node_id_found))
    if not successors:
        print(f"   {style['secondary_text']}(None){style['reset']}")
    for succ_id in successors:
        succ_data = memory.graph.nodes[succ_id]
        label = memory.graph.get_edge_data(node_id_found, succ_id).get("label", "leads")
        print(
            f"   [{style['arg_name']}{i}{style['reset']}] --[{style['meta_info']}{label}{style['reset']}]--> {succ_id[:8]} ({succ_data.get('type')})"
        )
        neighbors_map[i] = succ_id
        i += 1
    print("-" * 60)
    return node_id_found, neighbors_map


# --- Help and Utility Functions ---


def _get_available_node_types(memory):
    try:
        return sorted(
            list(
                set(
                    d.get("type")
                    for _, d in memory.graph.nodes(data=True)
                    if d.get("type")
                )
            )
        )
    except Exception:
        return []


def print_list_help(memory, style):
    cmd, arg_name, arg_val, sec, header, reset = (
        style["cmd_name"],
        style["arg_name"],
        style["arg_value"],
        style["secondary_text"],
        style["header"],
        style["reset"],
    )

    print(
        f"\n{header}Usage: {cmd}list (ls) {arg_name}<NodeType | Index>{reset} [{arg_name}--page{reset} {arg_val}<Num>{reset}] [{arg_name}--limit{reset} {arg_val}<Num>{reset}]"
    )
    print(
        f"{sec}Lists nodes, sorted by timestamp, with filtering and pagination.{reset}\n"
    )

    print(f"{header}Arguments & Options:{reset}")
    print(
        f"  {arg_name}<NodeType | Index>{reset} (Required) Specify type by its full name, a partial name, or its index number."
    )
    print(
        f"  {arg_name}--type <NodeType>{reset}   (Alternative) Specify type using a flag."
    )
    print(
        f"  {arg_name}--page <Number>{reset}      (Optional) The page number to display. Default is 1."
    )
    print(
        f"  {arg_name}--limit <Number>{reset}     (Optional) The number of items per page. Default is 10.\n"
    )

    node_types = _get_available_node_types(memory)
    if node_types:
        print(f"{header}Available Node Types:{reset}")
        for i, node_type in enumerate(node_types, 1):
            print(f"  {arg_val}{i:>2}.{reset} {cmd}{node_type}{reset}")
    else:
        print(
            f"{style['meta_info']}Info:{reset} No nodes with a 'type' attribute were found in the graph."
        )

    print(f"\n{header}Examples:{reset}")
    print(
        f"  {cmd}ls {arg_val}10 {arg_name}--limit {arg_val}5{reset}          {sec}# List the first 5 nodes of type #10.{reset}"
    )
    print(
        f"  {cmd}ls {arg_val}Concept {arg_name}--page {arg_val}2{reset}      {sec}# List page 2 of nodes with a type containing 'Concept'.{reset}"
    )
    print(
        f"  {cmd}ls {arg_name}--type {arg_val}TaskNode{reset}       {sec}# List nodes by full name using the flag.{reset}"
    )


def print_get_help(style):
    cmd, arg_name, sec, header, reset = (
        style["cmd_name"],
        style["arg_name"],
        style["secondary_text"],
        style["header"],
        style["reset"],
    )

    print(f"\n{header}Usage: {cmd}get {arg_name}<ID>{reset}")
    print(
        f"{sec}Fetches details for a single node and enters Navigation Mode.{reset}\n"
    )

    print(f"{header}Arguments:{reset}")
    print(
        f"  {arg_name}<ID>{reset}    (Required) The full or partial ID of the node to inspect.\n"
    )

    print(f"{header}Navigation Mode:{reset}")
    print(f"{sec}After using 'get', you can use these shortcuts to navigate:{reset}")
    print(f"  {arg_name}<Number>{reset}  Jumps to the numbered neighbor node.")
    print(
        f"  {cmd}b, back{reset}   Goes back to the previous node in your navigation history."
    )
    print(f"  {cmd}x, reset{reset}  Exits Navigation Mode and clears the history.")
