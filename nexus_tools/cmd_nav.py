# file: nexus_tools/cmd_nav.py

import json
import argparse


# HACK: We use a custom ArgumentParser class to prevent the default `sys.exit()`
# behavior on --help or on parsing errors. Instead of terminating the whole
# Nexus shell, it raises a SystemExit exception which we can catch gracefully.
class NexusArgParser(argparse.ArgumentParser):
    """Custom parser that raises exceptions instead of exiting the program."""

    def exit(self, status=0, message=None):
        # We raise the message to be caught by the command handler.
        raise SystemExit(message)

    def error(self, message):
        self.print_usage()
        # Prepending the error for clarity.
        error_message = f"Error: {message}\n"
        print(error_message)
        raise SystemExit(error_message)


def register():
    """Registers the navigation commands with the Nexus shell."""
    return {
        "list": {
            "func": cmd_list,
            "alias": ["ls"],
            "help": 'List nodes with filters and pagination. Use "list --help" for details.',
            "category": "Navigation & Inspection",
        },
        "get": {
            "func": cmd_get,
            "alias": [],
            "help": "Get node details and enter Navigation Mode.",
            "category": "Navigation & Inspection",
        },
    }


# --- Command Logic ---


async def cmd_list(memory, style, args, **kwargs):
    """
    Handler for the 'list' command. Parses arguments and displays a paginated
    list of nodes of a specific type.
    """
    # NOTE: A custom parser is used here to handle --help gracefully within the REPL.
    # `add_help=False` is crucial because we trigger our own help function.
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
        # This catches errors from our custom parser, preventing a crash.
        return

    # If --help is passed or no type is specified, show the detailed help screen.
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

    # --- Node Type Resolution Logic ---
    # First, check if the input is a number, corresponding to the index from `list --help`.
    if node_type_input.isdigit():
        try:
            index = int(node_type_input)
            if 1 <= index <= len(node_types):
                node_type = node_types[index - 1]
            else:
                print(
                    f"{style['error']}Error:{style['reset']} Invalid index '{index}'. Use 'list --help' to see options."
                )
                return
        except (ValueError, TypeError):
            pass  # It's not a valid number, so we'll treat it as a string.

    # If it's not a valid index, treat it as a name (full or partial).
    if node_type is None:
        # Find all types that contain the input string (case-insensitive).
        found_types = [t for t in node_types if node_type_input.lower() in t.lower()]
        if len(found_types) == 1:
            node_type = found_types[0]
        elif len(found_types) > 1:
            print(
                f"{style['error']}Error:{style['reset']} Ambiguous type '{node_type_input}'. Matches: {', '.join(found_types)}"
            )
            return
        else:
            print(
                f"{style['error']}Error:{style['reset']} Node type '{node_type_input}' not found. Use 'list --help'."
            )
            return
    # --- End Resolution Logic ---

    print(
        f"{style['info']}QUERY:{style['reset']} Finding nodes of type '{node_type}'..."
    )

    # Filter nodes from the graph based on the resolved type.
    nodes_of_type = [
        (node_id, data)
        for node_id, data in memory.nodes(data=True)
        if data.get("type") == node_type
    ]
    if not nodes_of_type:
        print(f"Info: Nodes of type '{node_type}' not found.")
        return

    # Sort nodes by timestamp, newest first.
    nodes_of_type.sort(key=lambda item: item[1].get("timestamp", ""), reverse=True)

    # --- Pagination Logic ---
    start_index = (page - 1) * limit
    end_index = start_index + limit
    paginated_results = nodes_of_type[start_index:end_index]
    total_pages = (len(nodes_of_type) + limit - 1) // limit

    if not paginated_results:
        print(f"Info: No nodes on page {page}. Total pages: {total_pages}.")
        return

    # --- Formatted Output ---
    print("-" * 100)
    header = f"Displaying {len(paginated_results)} of {len(nodes_of_type)} nodes: {style['header']}{node_type}{style['reset']}"
    pagination_info = f"Page {page}/{total_pages}"
    print(f"{header:<80} {pagination_info:>18}")
    print("-" * 100)

    for node_id, node_data in paginated_results:
        timestamp = node_data.get("timestamp", "N/A")[:19]
        content = str(node_data.get("content", ""))
        # Create a single-line preview of the content.
        preview = (
            (content[:70] + "...").replace("\n", " ")
            if len(content) > 70
            else content.replace("\n", " ")
        )
        print(
            f"[{style['cmd']}{node_id[:8]}{style['reset']}] ({timestamp}) │ {preview}"
        )

    print("-" * 100)
    # Provide a helpful hint for navigating to the next page.
    if page < total_pages:
        base_cmd = (
            f"ls {node_type_input}"
            if not parsed_args.type_from_flag
            else f"ls --type {node_type}"
        )
        print(
            f"Hint: Next page -> {style['cmd']}{base_cmd} --page {page + 1} --limit {limit}{style['reset']}"
        )


async def cmd_get(memory, style, args, **kwargs):
    """
    Handler for the 'get' command. Finds a single node by its ID,
    displays its details and neighbors, and returns data to Nexus to
    enter Navigation Mode.

    Returns:
        A tuple (node_id, neighbors_map) on success, or (None, {}) on failure.
    """
    if "--help" in args:
        print_get_help(style)
        return None, {}
    if not args:
        print(f"{style['error']}Error:{style['reset']} Usage: get <id>")
        return None, {}

    partial_id = args[0]
    node_id_found = None

    # --- Node ID Resolution ---
    # First, check for an exact match, which is fastest.
    if memory.has_node(partial_id):
        node_id_found = partial_id
    else:
        # If no exact match, iterate to find a node that starts with the partial ID.
        for nid in memory.nodes:
            if nid.startswith(partial_id):
                node_id_found = nid
                break
    # ---

    if not node_id_found:
        print(
            f"{style['error']}Error:{style['reset']} Node with ID prefix '{partial_id}' not found."
        )
        return None, {}

    node_data = memory.nodes[node_id_found]
    print(f"\n// {style['header']}NODE DATA :: {node_id_found}{style['reset']} //")
    print("-" * 60)
    for key, value in sorted(node_data.items()):
        val_str = str(value)
        # HACK: Pretty-print stringified JSON content for readability.
        if val_str.strip().startswith(("{", "[")):
            try:
                parsed = json.loads(val_str)
                val_str = json.dumps(parsed, ensure_ascii=False, indent=2)
            except (json.JSONDecodeError, TypeError):
                pass  # If it's not valid JSON, just print the raw string.
        print(f"{style['arg']}{key:<15}:{style['reset']} {val_str}")

    # This map will be returned to Nexus to enable numeric navigation.
    neighbors_map = {}
    i = 1

    # --- Display Neighbors ---
    print(f"\n{style['cmd']}<< PARENTS (Predecessors){style['reset']}")
    predecessors = list(memory.predecessors(node_id_found))
    if not predecessors:
        print("   (None)")
    for pred_id in predecessors:
        pred_data = memory.nodes[pred_id]
        label = memory.get_edge_data(pred_id, node_id_found).get("label", "related")
        print(
            f"   [{style['arg']}{i}{style['reset']}] {pred_id[:8]} ({pred_data.get('type')}) --[{label}]-->"
        )
        neighbors_map[i] = pred_id
        i += 1

    print(f"\n{style['cmd']}>> CHILDREN (Successors){style['reset']}")
    successors = list(memory.successors(node_id_found))
    if not successors:
        print("   (None)")
    for succ_id in successors:
        succ_data = memory.nodes[succ_id]
        label = memory.get_edge_data(node_id_found, succ_id).get("label", "leads")
        print(
            f"   [{style['arg']}{i}{style['reset']}] --[{label}]--> {succ_id[:8]} ({succ_data.get('type')})"
        )
        neighbors_map[i] = succ_id
        i += 1
    print("-" * 60)

    return node_id_found, neighbors_map


# --- Help and Utility Functions ---


def _get_available_node_types(memory):
    """Dynamically collects all unique node 'type' attributes from the graph."""
    try:
        # Using a set comprehension for efficiency in finding unique types.
        return sorted(
            list({d.get("type") for _, d in memory.nodes(data=True) if d.get("type")})
        )
    except Exception:
        return []


def print_list_help(memory, style):
    """Prints a detailed, dynamic help message for the 'list' command."""
    print(
        f"\n{style['header']}Usage: list <NodeType | Index> [--page <Num>] [--limit <Num>]{style['reset']}"
    )
    print("Lists nodes with filters and pagination. The node type is required.\n")
    print(f"{style['arg']}Arguments & Options:{style['reset']}")
    print(
        f"  {style['cmd']}<NodeType | Index>{style['reset']} (Required) Specify type by name, partial name, or index."
    )
    print(
        f"  {style['cmd']}--type <NodeType>{style['reset']}   (Alternative) Specify type using a flag."
    )
    print(
        f"  {style['cmd']}--page <Number>{style['reset']}      (Optional) Page to display. Default is 1."
    )
    print(
        f"  {style['cmd']}--limit <Number>{style['reset']}     (Optional) Items per page. Default is 10.\n"
    )

    # NOTE: The help message dynamically generates a list of available types,
    # making it extremely useful for exploring a new memory graph.
    node_types = _get_available_node_types(memory)
    if node_types:
        print(f"{style['header']}Available Node Types:{style['reset']}")
        for i, node_type in enumerate(node_types, 1):
            print(
                f"  {style['arg']}{i:>2}.{style['reset']} {style['cmd']}{node_type}{style['reset']}"
            )
    else:
        print(
            f"{style['info']}Info:{style['reset']} No nodes with a 'type' attribute found in the current graph."
        )

    print(f"\n{style['header']}Examples:{style['reset']}")
    print(
        "  ls 10 --limit 5          # List first 5 nodes of type 'UserImpulse' (if it's #10)"
    )
    print(
        "  ls Concept --page 2      # List page 2 of nodes with type containing 'Concept'"
    )
    print("  ls --type TaskNode       # List nodes by full name with a flag")


def print_get_help(style):
    """Prints a static help message for the 'get' command."""
    print(f"\n{style['header']}Usage: get <ID>{style['reset']}")
    print("Fetches details for a single node and enters Navigation Mode.\n")
    print(f"{style['arg']}Arguments:{style['reset']}")
    print(
        f"  {style['cmd']}<ID>{style['reset']}    (Required) The full or partial ID of the node to inspect.\n"
    )
    print(f"{style['header']}Navigation Mode Commands:{style['reset']}")
    print("Once you 'get' a node, you can use these commands:")
    print(
        f"  {style['cmd']}<Number>{style['reset']}  Jump to a numbered neighbor node."
    )
    print(
        f"  {style['cmd']}b, back{style['reset']}   Go back to the previous node in your navigation history."
    )
    print(
        f"  {style['cmd']}x, reset{style['reset']}  Exit Navigation Mode and clear history."
    )
