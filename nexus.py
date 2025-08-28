# file: nexus.py (DEMO VERSION)

import asyncio
import shlex
import os
import importlib
import inspect
from colorama import init, Fore, Style

# Initialize colorama for cross-platform colored output
init(autoreset=True)


class NexusShell:
    """
    The main class for the Nexus interactive shell.

    This class manages the application state, command loading, the main read-eval-print loop (REPL),
    and the special navigation mode for exploring the memory graph.
    """

    def __init__(self):
        # The 'memory' object will hold the loaded networkx graph.
        self.memory = None
        # The 'llm' is a mock object in the demo, as no live LLM calls are made.
        self.llm = None
        self.commands = {}

        # --- Navigation Mode State ---
        # Holds the ID of the currently focused node.
        self.context_node_id = None
        # A map of {integer_choice: node_id} for the neighbors of the context node.
        self.context_neighbors = {}
        # A history stack to enable the 'back' command.
        self.navigation_history = []
        # ----------------------------

        # A simple dictionary to define the color scheme for the shell.
        self.style = {
            "prompt": Fore.WHITE + Style.BRIGHT,
            "header": Fore.GREEN + Style.BRIGHT,
            "cmd": Fore.CYAN,
            "arg": Fore.YELLOW,
            "error": Fore.RED + Style.BRIGHT,
            "info": Fore.YELLOW,
            "nav_prompt": Fore.MAGENTA + Style.BRIGHT,
            "reset": Style.RESET_ALL,  # Added for convenience
        }
        self._load_commands()

    def _load_commands(self):
        """
        Dynamically loads commands from two sources: built-in methods and external plugins.
        This makes the shell extensible without modifying its core code.
        """
        # --- Register Built-in Commands ---
        self.register_command(
            "help",
            self.cmd_help,
            ["h"],
            "Displays this help message.",
            category="Shell & Memory",
        )
        self.register_command(
            "exit",
            self.cmd_exit,
            ["q", "quit"],
            "Exits the Nexus shell.",
            category="Shell & Memory",
        )
        self.register_command(
            "refresh",
            self.cmd_refresh,
            ["r"],
            "Reloads the memory graph from file.",
            category="Shell & Memory",
        )
        self.register_command(
            "stat",
            lambda m, s, a: asyncio.create_task(self.commands["stat"]["func"](m, s, a)),
            [],
            "Display statistics about the memory graph.",
            category="Shell & Memory",
        )

        # Navigation Mode commands
        self.register_command(
            "back",
            self.cmd_back,
            ["b"],
            "Go back to the previous node.",
            category="Navigation Mode",
        )
        self.register_command(
            "reset",
            self.cmd_reset,
            ["x"],
            "Reset navigation context.",
            category="Navigation Mode",
        )

        # --- Load Commands from Plugins ---
        plugin_dir = "nexus_tools"
        if not os.path.isdir(plugin_dir):
            return

        # A map to assign a category to each plugin file for organized 'help' output.
        plugin_categories = {
            "cmd_nav.py": "Navigation & Inspection",
            "cmd_insights.py": "Knowledge Analysis",
            "cmd_probes.py": "Cognitive Probes",
            "cmd_stat.py": "Shell & Memory",
            "cmd_trace.py": "Navigation & Inspection",
        }

        # Iterate through sorted files in the plugin directory to ensure consistent command order.
        for filename in sorted(os.listdir(plugin_dir)):
            if filename.startswith("cmd_") and filename.endswith(".py"):
                module_name = f"{plugin_dir}.{filename[:-3]}"
                category = plugin_categories.get(filename, "Uncategorized")
                try:
                    module = importlib.import_module(module_name)
                    if hasattr(module, "register"):
                        # Each plugin's 'register' function returns a dictionary of its commands.
                        for cmd_name, cmd_info in module.register().items():
                            self.register_command(
                                cmd_name,
                                cmd_info["func"],
                                cmd_info.get("alias", []),
                                cmd_info.get("help", ""),
                                category=category,
                            )
                except Exception as e:
                    self.print_error(f"Failed to load command from {filename}: {e}")

    async def cmd_refresh(self, args):
        """Built-in command to reload the memory graph from the snapshot file."""
        print(
            f"{self.style['info']}REFRESH:{Style.RESET_ALL} Reloading Memory Core from snapshot..."
        )
        # Reset the current memory instance to trigger re-initialization.
        self.memory = None
        if not await self._initialize_services():
            self.print_error(
                "Failed to refresh memory. Please check file paths and integrity."
            )
        return True  # Return True to keep the shell running.

    def register_command(self, name, func, aliases, help_text, category="default"):
        """
        A helper method to register a command and its aliases in the command dictionary.
        """
        command_info = {
            "func": func,
            "help": help_text,
            "aliases": aliases,
            "category": category,
            # This flag is crucial for managing the navigation context.
            "is_nav_command": name in ["get", "back", "reset"],
        }
        self.commands[name] = command_info
        for alias in aliases:
            self.commands[alias] = command_info

    async def _initialize_services(self):
        """
        Initializes the core services for the shell.
        In the demo version, this simply loads the graph file using networkx.
        """
        if self.memory is None:
            try:
                import networkx as nx
                import os

                GRAPH_FILE_PATH = "memory_core.graphml"

                if not os.path.exists(GRAPH_FILE_PATH):
                    self.print_error(f"Memory file not found: {GRAPH_FILE_PATH}")
                    self.print_error(
                        "Please make sure the graph file is in the root directory."
                    )
                    return False

                # NOTE: In the demo, `self.memory` is a direct networkx graph object,
                # not the custom UniversalMemory class from the full project.
                self.memory = nx.read_graphml(GRAPH_FILE_PATH)

                # A mock LLM is used as a placeholder for commands that expect it.
                class MockLLM:
                    pass

                self.llm = MockLLM()

            except Exception as e:
                self.print_error(f"FAIL: Could not load the memory graph file: {e}")
                import traceback

                traceback.print_exc()
                return False
        return True

    def print_error(self, message):
        """Utility method for printing formatted error messages."""
        print(f"{self.style['error']}Error:{Style.RESET_ALL} {message}")

    async def cmd_help(self, args):
        """Built-in command to display a formatted list of all available commands."""
        print(f"\n{self.style['header']}Nexus Command Shell - Help{Style.RESET_ALL}")

        # Group commands by category for a structured help view.
        categorized_cmds = {}
        unique_funcs = set()
        for cmd_name, cmd_info in self.commands.items():
            # HACK: Filter out aliases by checking the function object's identity
            # to avoid printing the same command multiple times.
            if cmd_info["func"] in unique_funcs:
                continue
            unique_funcs.add(cmd_info["func"])

            category = cmd_info["category"]
            if category not in categorized_cmds:
                categorized_cmds[category] = []

            # Find the primary name of the command (not an alias).
            main_name = next(
                (
                    k
                    for k, v in self.commands.items()
                    if v["func"] == cmd_info["func"] and k not in v["aliases"]
                ),
                cmd_name,
            )

            categorized_cmds[category].append(
                {
                    "name": main_name,
                    "aliases": ", ".join(sorted(cmd_info["aliases"])),
                    "help": cmd_info["help"],
                }
            )

        # Define a fixed order for categories for consistent output.
        category_order = [
            "Navigation & Inspection",
            "Knowledge Analysis",
            "Cognitive Probes",
            "Shell & Memory",
        ]

        # Dynamically add the "Navigation Mode" category if it's active.
        if self.context_node_id:
            category_order.append("Navigation Mode")

        # --- Calculate padding for clean, table-like formatting ---
        max_name_len = 0
        max_alias_len = 0
        for cat in category_order:
            if cat in categorized_cmds:
                for cmd in categorized_cmds[cat]:
                    if len(cmd["name"]) > max_name_len:
                        max_name_len = len(cmd["name"])
                    if len(cmd["aliases"]) > max_alias_len:
                        max_alias_len = len(cmd["aliases"])
        # ---

        # Print the categorized commands.
        for category in category_order:
            if category in categorized_cmds:
                print(f"\n--- {self.style['arg']}{category}{Style.RESET_ALL} ---")
                # Sort commands alphabetically within each category.
                for cmd in sorted(categorized_cmds[category], key=lambda x: x["name"]):
                    name_str = f"{self.style['cmd']}{cmd['name']:<{max_name_len}}{Style.RESET_ALL}"
                    alias_str = f"{self.style['info']}{cmd['aliases']:<{max_alias_len}}{Style.RESET_ALL}"
                    help_str = cmd["help"] or "No description."
                    print(f"  {name_str}  {alias_str}  - {help_str}")

        print("\n" + "=" * 80)
        print(
            f"Tip: For detailed help on a command, type {self.style['cmd']}<command> --help{Style.RESET_ALL} (e.g., 'list --help')."
        )
        return True

    async def cmd_exit(self, args):
        """Built-in command to terminate the shell."""
        return False  # Return False to stop the main REPL loop.

    async def cmd_back(self, args):
        """Built-in command to navigate to the previous node in the history."""
        if len(self.navigation_history) > 1:
            self.navigation_history.pop()  # Remove the current node
            prev_node_id = self.navigation_history[-1]  # Get the previous one

            # NOTE: We directly call the 'get' command's function to simulate user input.
            get_func = self.commands["get"]["func"]
            node_id, neighbors = await get_func(self.memory, self.style, [prev_node_id])
            self._update_nav_context(node_id, neighbors)
        else:
            print(
                f"{self.style['info']}Info:{Style.RESET_ALL} Nowhere to go back to. Navigation reset."
            )
            await self.cmd_reset([])
        return True

    async def cmd_reset(self, args):
        """Built-in command to exit navigation mode and clear the context."""
        self.context_node_id = None
        self.context_neighbors = {}
        self.navigation_history = []
        print(
            f"{self.style['info']}Info:{Style.RESET_ALL} Navigation context has been reset."
        )
        return True

    def _update_nav_context(self, node_id, neighbors):
        """
        Updates the shell's state when entering or moving within navigation mode.
        This method is typically called by the 'get' command.
        """
        if node_id and neighbors:
            self.context_node_id = node_id
            self.context_neighbors = neighbors
            # Add to history only if we are moving to a new node, not going back.
            if not self.navigation_history or self.navigation_history[-1] != node_id:
                self.navigation_history.append(node_id)
        else:
            # If 'get' fails, reset the context to avoid a broken state.
            self.context_node_id = None
            self.context_neighbors = {}

    async def run(self):
        """The main Read-Eval-Print Loop (REPL) for the shell."""
        print(f"\n{self.style['header']}Nexus Command Shell v0.5{Style.RESET_ALL}")
        print(
            f"{self.style['info']}[ BOOT ]: Initializing services...{Style.RESET_ALL}"
        )

        if not await self._initialize_services():
            self.print_error("Initialization failed. Exiting.")
            return

        print(
            f"{self.style['info']}[ BOOT ]: Memory Core loaded successfully.{Style.RESET_ALL}"
        )

        # Automatically run 'stat' on startup to give the user immediate context.
        stat_func = self.commands.get("stat", {}).get("func")
        if stat_func:
            # We need to pass kwargs directly since it's a plugin function.
            await stat_func(self.memory, self.style, [])

        await self.cmd_help([])

        running = True
        while running:
            try:
                # Dynamically change the prompt when in navigation mode.
                if self.context_node_id:
                    prompt = f"\n{self.style['nav_prompt']}[NEXUS:{self.context_node_id[:8]}]> {Style.RESET_ALL}"
                else:
                    prompt = f"\n{self.style['prompt']}[NEXUS]> {Style.RESET_ALL}"

                user_input = input(prompt)
                if not user_input.strip():
                    continue

                # --- Special handling for navigation mode ---
                if self.context_node_id and user_input.isdigit():
                    choice = int(user_input)
                    if choice in self.context_neighbors:
                        target_id = self.context_neighbors[choice]
                        print(
                            f"{self.style['info']}NAVIGATE:{Style.RESET_ALL} Jumping to node {target_id[:8]}..."
                        )
                        get_func = self.commands["get"]["func"]
                        node_id, neighbors = await get_func(
                            self.memory, self.style, [target_id]
                        )
                        self._update_nav_context(node_id, neighbors)
                    else:
                        self.print_error("Invalid choice. Not in neighbor list.")
                    continue
                # ---

                # Split the input into the command and its arguments.
                command_name = user_input.split()[0].lower()
                args_str = user_input.partition(" ")[2]

                # Special handling for nav commands that can be called anytime
                if self.context_node_id and command_name in ["b", "back"]:
                    await self.cmd_back([])
                    continue
                if self.context_node_id and command_name in ["x", "reset"]:
                    await self.cmd_reset([])
                    continue

                # Use shlex for robust parsing of arguments, handling quotes correctly.
                args = shlex.split(args_str)

                command_info = self.commands.get(command_name)
                if not command_info:
                    self.print_error(f"Unknown Command: '{command_name}'. Type 'help'.")
                    continue

                # If a non-nav command is issued while in nav mode, reset the context first.
                if self.context_node_id and not command_info.get("is_nav_command"):
                    await self.cmd_reset([])

                # --- Dynamic Command Execution ---
                command_func = command_info["func"]

                # Inspect the function signature to pass only the arguments it expects.
                # This makes the plugin system robust.
                func_signature = inspect.signature(command_func)
                params = func_signature.parameters
                kwargs = {}
                if "memory" in params:
                    kwargs["memory"] = self.memory
                if "llm" in params:
                    kwargs["llm"] = self.llm
                if "style" in params:
                    kwargs["style"] = self.style
                if "args" in params:
                    kwargs["args"] = args

                result = None
                # Differentiate between built-in methods and external plugin functions for calling.
                # Built-in commands (like help, exit) are instance methods and are called differently
                # from plugin functions, which expect keyword arguments.
                if inspect.ismethod(command_func):
                    result = await command_func(args)
                else:
                    result = await command_func(**kwargs)
                # ---

                # Handle the result to update state or exit.
                if command_name == "get":
                    node_id, neighbors = result if result else (None, None)
                    self._update_nav_context(node_id, neighbors)

                if command_name in ["exit", "q", "quit"]:
                    running = False
                elif isinstance(result, bool):
                    # Some commands can signal to exit by returning False.
                    running = result

            except (KeyboardInterrupt, EOFError):
                running = False
                print(
                    f"\n{self.style['info']}EXIT:{Style.RESET_ALL} Shutting down Nexus."
                )
            except Exception as e:
                self.print_error(f"A fatal error occurred: {e}")
                import traceback

                traceback.print_exc()


async def main():
    """Main entry point for the application."""
    shell = NexusShell()
    await shell.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        # A graceful exit message for Ctrl+C.
        print(f"\n{Fore.YELLOW}Nexus shell terminated by user.{Style.RESET_ALL}")
