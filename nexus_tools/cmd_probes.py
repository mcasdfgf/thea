# file: nexus_tools/cmd_probes.py (DEMO VERSION)
# NOTE: This entire file serves as a placeholder for the demo repository.
# In the full version, this module contains complex logic for isolated testing
# of the cognitive services, which requires the live cognitive core and LLM.


async def _show_disabled_message(style):
    """
    A helper function to show a consistent, user-friendly message explaining
    why a command is disabled in the demo.
    """
    message = (
        "This command requires the full cognitive core (services and LLM) "
        "and is disabled in the public demo version."
    )
    # Use .get() for safe access to style elements.
    info_style = style.get("info", "")
    reset_style = style.get("reset", "")

    print(f"\n{info_style}NOTE:{reset_style} {message}")
    print("For more details, please see the project's README.md.")


# --- Placeholder Functions ---
# We create two distinct functions, even though they do the same thing.
# This is to ensure that the command registration logic in nexus.py
# treats them as unique commands and doesn't filter one out as a duplicate.


async def cmd_plan_placeholder(memory, style, **kwargs):
    """Placeholder handler for the 'plan' command."""
    await _show_disabled_message(style)


async def cmd_probe_placeholder(memory, style, **kwargs):
    """Placeholder handler for the 'probe' command."""
    await _show_disabled_message(style)


def register():
    """
    Registers the placeholder commands with the Nexus shell.
    The help text explicitly states that these commands are disabled.
    """
    plan_help = "Tests the Instinct->Enrichment-Plan chain. [DISABLED IN DEMO]"
    probe_help = "Probes memory or the full cognitive cycle. [DISABLED IN DEMO]"

    return {
        "plan": {
            "func": cmd_plan_placeholder,
            "alias": [],
            "help": plan_help,
            "category": "Cognitive Probes",
        },
        "probe": {
            "func": cmd_probe_placeholder,
            "alias": [],
            "help": probe_help,
            "category": "Cognitive Probes",
        },
    }
