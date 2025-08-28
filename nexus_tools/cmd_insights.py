# file: nexus_tools/cmd_insights.py

import textwrap
from colorama import Fore


def register():
    """Registers the insight-specific commands with the Nexus shell."""
    return {
        "insights": {
            "func": cmd_list_insights,
            "alias": ["i"],
            "help": 'List insights with filters and pagination. Use "i --help" for details.',
            "category": "Knowledge Analysis",
        },
        "ifind": {
            "func": cmd_find_insight,
            "alias": [],
            "help": "Find insights by concept. Usage: ifind <concept>",
            "category": "Knowledge Analysis",
        },
        "iget": {
            "func": cmd_get_insight,
            "alias": [],
            "help": "Get insight details by ID. Usage: iget <id>",
            "category": "Knowledge Analysis",
        },
    }


# --- Constants for state mapping and sorting ---
# Maps user-friendly numeric codes to the internal state names.
STATE_MAP = {"1": "VERIFIED", "2": "UNVERIFIED", "3": "ARCHIVED"}
# Defines a custom sort order. VERIFIED insights are considered most important.
STATE_ORDER = {"VERIFIED": 0, "UNVERIFIED": 1, "ARCHIVED": 2}

# --- Command Logic ---


async def cmd_list_insights(memory, style, args, **kwargs):
    """Handler for the 'insights' command to list and filter KnowledgeCrystals."""
    if "--help" in args:
        print_insights_help(style)
        return

    # --- Simple argument parsing for flags and values ---
    # NOTE: A full argparse is avoided here for simplicity, as the arguments are basic.
    state_code = None
    page = 1
    page_size = 20  # Default items per page

    # Look for a state code (a single digit) as a positional argument.
    for arg in args:
        if arg in STATE_MAP:
            state_code = arg
            break
    # Also support the --state flag for clarity.
    if "--state" in args:
        try:
            state_code = args[args.index("--state") + 1]
        except IndexError:
            print(
                f"{style['error']}Error:{style['reset']} --state flag requires an argument."
            )
            return

    # Look for the --page flag.
    if "--page" in args:
        try:
            page = int(args[args.index("--page") + 1])
        except (IndexError, ValueError):
            print(
                f"{style['error']}Error:{style['reset']} --page flag requires a number."
            )
            return

    if state_code and state_code not in STATE_MAP:
        print(
            f"{style['error']}Error:{style['reset']} Invalid state code '{state_code}'. Use 1, 2, or 3."
        )
        return

    print(f"{style['info']}SCAN:{style['reset']} Scanning & sorting insights...")
    all_insights = _get_all_insights(memory)
    if not all_insights:
        print("Info: No KnowledgeCrystal nodes found in memory.")
        return

    # --- Filtering Logic ---
    filtered = all_insights
    state_filter_str = "all states"
    if state_code:
        target_state = STATE_MAP[state_code]
        state_filter_str = f"state '{target_state}'"
        # Filter the list based on the 'state' attribute.
        filtered = [
            i for i in all_insights if i.get("state", "").upper() == target_state
        ]

    if not filtered:
        print(f"Info: No insights found with {state_filter_str}.")
        return

    sorted_insights = _sort_insights(filtered)

    # --- Pagination Logic ---
    start_index = (page - 1) * page_size
    end_index = start_index + page_size
    paginated_results = sorted_insights[start_index:end_index]
    total_pages = (len(sorted_insights) + page_size - 1) // page_size

    if not paginated_results:
        print(f"Info: No insights on page {page}. Total pages: {total_pages}.")
        return

    # --- Formatted Output ---
    print("-" * 120)
    header = f"🔬 Knowledge Inspector: Found {len(sorted_insights)} insights (filter: {state_filter_str})"
    pagination_info = f"Displaying page {page}/{total_pages}"
    print(f"{style['header']}{header:<80} {pagination_info:>38}{style['reset']}")
    print("-" * 120)

    for insight in paginated_results:
        _print_insight_row(style, insight)

    print("-" * 120)
    if page < total_pages:
        print(
            f"Hint: To see the next page, use 'i --page {page + 1}' (with your filters)."
        )


async def cmd_find_insight(memory, style, args, **kwargs):
    """Handler for the 'ifind' command to find insights by a concept."""
    if not args:
        print(f"{style['error']}Error:{style['reset']} Usage: ifind <concept>")
        return

    concept = " ".join(args)
    concept_to_find = concept.strip().lower()
    print(
        f"{style['info']}QUERY:{style['reset']} Searching for insights linked to concept: '{concept_to_find}'..."
    )

    all_insights = _get_all_insights(memory)

    # Filter insights where the concept is present in the 'source_concepts' attribute.
    # The 'source_concepts' is expected to be a comma-separated string.
    found = [
        i
        for i in all_insights
        if concept_to_find
        in [c.strip().lower() for c in i.get("source_concepts", "").split(",")]
    ]

    if not found:
        print(f"Info: No insights linked to concept '{concept}'.")
        return

    sorted_found = _sort_insights(found)

    print("-" * 120)
    print(
        f"🔬 {style['header']}Knowledge Inspector:{style['reset']} Found {len(sorted_found)} insights for concept '{concept}'."
    )
    print("-" * 120)
    for insight in sorted_found:
        _print_insight_row(style, insight)
    print("-" * 120)


async def cmd_get_insight(memory, style, args, **kwargs):
    """Handler for the 'iget' command to display details of a single insight."""
    if not args:
        print(f"{style['error']}Error:{style['reset']} Usage: iget <id>")
        return

    partial_id = args[0].strip().lower()
    print(
        f"{style['info']}FETCH:{style['reset']} Retrieving insight with ID starting with: '{partial_id}'..."
    )

    all_insights = _get_all_insights(memory)

    # Find the first insight whose ID starts with the provided partial ID.
    found_insight = next(
        (i for i in all_insights if i.get("id", "").lower().startswith(partial_id)),
        None,
    )

    if not found_insight:
        print(f"Info: Insight with ID prefix '{partial_id}' not found.")
        return

    # --- Formatted Detailed Output ---
    print(
        f"\n// {style['header']}INSIGHT DATA :: {found_insight.get('id')[:8]}{style['reset']} //"
    )
    print("-" * 60)
    state = found_insight.get("state", "N/A")
    state_color = (
        Fore.GREEN
        if state == "VERIFIED"
        else Fore.YELLOW
        if state == "UNVERIFIED"
        else Fore.RED
    )
    print(f"{style['arg']}{'ID':<15}:{style['reset']} {found_insight.get('id')}")
    print(
        f"{style['arg']}{'State':<15}:{style['reset']} {state_color}{state}{style['reset']}"
    )
    print(
        f"{style['arg']}{'Timestamp':<15}:{style['reset']} {found_insight.get('timestamp')}"
    )
    print(
        f"{style['arg']}{'Source Impulse':<15}:{style['reset']} {found_insight.get('source_impulse', 'N/A')}"
    )
    print(
        f"{style['arg']}{'Source Concepts':<15}:{style['reset']} {style['cmd']}{found_insight.get('source_concepts', 'N/A')}{style['reset']}"
    )
    print(f"{style['arg']}{'Content':<15}:{style['reset']}")
    # Use textwrap to neatly format the content for readability.
    print(
        textwrap.fill(
            found_insight.get("content", ""),
            width=80,
            initial_indent="  ",
            subsequent_indent="  ",
        )
    )
    print("-" * 60)


# --- Helper Functions ---


def print_insights_help(style):
    """Prints a detailed, static help message for the 'insights' command."""
    print(
        f"\n{style['header']}Usage: insights [<StateCode>] [--state <StateCode>] [--page <Number>]{style['reset']}"
    )
    print("Lists insights (KnowledgeCrystals) with filters and pagination.\n")
    print(f"{style['arg']}Arguments:{style['reset']}")
    print(
        f"  {style['cmd']}<StateCode>{style['reset']}         (Optional) Filter by state using a shorthand number."
    )
    print(
        f"  {style['cmd']}--state <StateCode>{style['reset']} (Optional) Filter by state using the full flag."
    )
    print(
        f"  {style['cmd']}--page <Number>{style['reset']}      (Optional) Specify the page number to display. Default is 1.\n"
    )
    print(f"{style['header']}Available State Codes:{style['reset']}")
    print(
        f"  {style['cmd']}1{style['reset']} - VERIFIED   (Strong, confirmed knowledge)"
    )
    print(f"  {style['cmd']}2{style['reset']} - UNVERIFIED (Weak hypotheses)")
    print(f"  {style['cmd']}3{style['reset']} - ARCHIVED   (Outdated knowledge)")
    print(f"\n{style['header']}Examples:{style['reset']}")
    print("  i              # Show page 1 of all insights")
    print("  i 1            # Show page 1 of VERIFIED insights")
    print("  i 2 --page 3   # Show page 3 of UNVERIFIED insights")


def _get_all_insights(memory):
    """Helper function to extract all nodes of type 'KnowledgeCrystalNode' from the graph."""
    insights = []
    for node_id, data in memory.nodes(data=True):
        if data.get("type") == "KnowledgeCrystalNode":
            node_copy = data.copy()
            # IMPORTANT: Add the node's ID to its data dictionary for easy access later.
            node_copy["id"] = node_id
            insights.append(node_copy)
    return insights


def _sort_insights(insights: list):
    """
    Sorts a list of insights based on two criteria:
    1. By state, according to the predefined STATE_ORDER (VERIFIED first).
    2. By timestamp, newest first.
    """
    # Sort by timestamp first (secondary sort key).
    insights.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    # Then sort by state (primary sort key).
    insights.sort(key=lambda x: STATE_ORDER.get(x.get("state", "UNVERIFIED"), 99))
    return insights


def _print_insight_row(style, insight: dict):
    """Helper function to print a single, formatted row in the 'insights' list."""
    node_id, state = insight.get("id", "")[:8], insight.get("state", "N/A")
    content = insight.get("content", "").replace("\n", " ").replace("\r", "")
    concepts = insight.get("source_concepts", "N/A")

    state_color = (
        Fore.GREEN
        if state == "VERIFIED"
        else Fore.YELLOW
        if state == "UNVERIFIED"
        else Fore.RED
    )
    state_str = f"{state_color}{state:<12}{style['reset']}"

    content_short = textwrap.shorten(content, width=70, placeholder="...")

    print(
        f"{state_str} | ID: {node_id} | Concepts: {style['cmd']}{concepts:<35.35}{style['reset']}| Insight: '{content_short}'"
    )
