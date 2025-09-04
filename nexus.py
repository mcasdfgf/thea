# nexus.py: The Nexus Command Shell.
# This module provides a developer-facing CLI for inspecting and interacting
# with the UniversalMemory of the T.H.E.A. cognitive architecture. It implements
# a REPL (Read-Eval-Print Loop) that dynamically loads command plugins from the
# `nexus_tools` directory, allowing for direct inspection of the memory graph,
# analysis of knowledge structures, and probing of cognitive services.

import asyncio
import shlex
import sys
import os
import importlib
import inspect
from typing import List
from colorama import init, Fore, Style
from collections import Counter

init(autoreset=True)


class NexusShell:
    """Manages the state and command execution for the Nexus REPL."""

    def __init__(self):
        self.memory = None
        self.llm = None
        self.commands = {}
        self.context_node_id = None
        self.context_neighbors = {}
        self.navigation_history = []
        self.style = {
            # --- UI Elements ---
            "prompt": Fore.WHITE + Style.BRIGHT,
            "nav_prompt": Fore.MAGENTA + Style.BRIGHT,
            "header": Fore.CYAN + Style.BRIGHT,
            "section_header": Fore.GREEN,
            "error": Fore.RED + Style.BRIGHT,
            "meta_info": Fore.YELLOW,
            # --- Semantic Content ---
            "cmd_name": Fore.CYAN + Style.BRIGHT,
            "arg_name": Fore.CYAN,
            "arg_value": Fore.YELLOW,
            "highlight": Fore.GREEN,
            "lowlight": Fore.WHITE,
            "secondary_text": Fore.WHITE,
            "reset": Style.RESET_ALL,
        }
        self._load_commands()

    def _load_commands(self):
        """Dynamically loads all available shell commands from the `nexus_tools` directory."""

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

        # Dynamically load commands from the nexus_tools directory
        plugin_dir = "nexus_tools"
        if not os.path.isdir(plugin_dir):
            return

        # Defines the display order and grouping for commands in the help message.
        plugin_categories = {
            "cmd_nav.py": "Navigation & Inspection",
            "cmd_insights.py": "Knowledge Analysis",
            "cmd_probes.py": "Cognitive Probes",
            "cmd_stat.py": "Shell & Memory",
            "cmd_trace.py": "Navigation & Inspection",
        }

        for filename in sorted(os.listdir(plugin_dir)):
            if filename.startswith("cmd_") and filename.endswith(".py"):
                module_name = f"{plugin_dir}.{filename[:-3]}"
                category = plugin_categories.get(filename, "Uncategorized")
                try:
                    module = importlib.import_module(module_name)
                    if hasattr(module, "register"):
                        for cmd_name, cmd_info in module.register().items():
                            self.register_command(
                                cmd_name,
                                cmd_info["func"],
                                cmd_info.get("alias", []),
                                cmd_info.get("help", ""),
                                category=category,
                            )
                except Exception as e:
                    self.print_error(f"Failed to load commands from {filename}: {e}")

    async def cmd_refresh(self, args):
        """Handler for the 'refresh' command."""
        print(
            f"{self.style['meta_info']}REFRESH:{Style.RESET_ALL} Reloading Memory Core from snapshot..."
        )
        # Invalidate the current memory instance to force a reload.
        self.memory = None
        if await self._initialize_services():
            pass
        else:
            self.print_error(
                "Failed to refresh memory. Please check file path and integrity."
            )
        return True  # Keep the shell running

    def register_command(self, name, func, aliases, help_text, category="default"):
        command_info = {
            "func": func,
            "help": help_text,
            "aliases": aliases,
            "category": category,
            "is_nav_command": name in ["get", "back", "reset"],
        }
        self.commands[name] = command_info
        for alias in aliases:
            self.commands[alias] = command_info

    async def _initialize_services(self):
        if self.memory is None:
            try:
                from memory.memory_core import UniversalMemory
                from config import MEMORY_GRAPH_FILE_PATH
                from llm_interface import LLMInterface

                if self.llm is None:
                    self.llm = LLMInterface()

                self.memory = UniversalMemory(
                    schema_path="memory/schema.yaml",
                    snapshot_path=MEMORY_GRAPH_FILE_PATH,
                )
            except Exception as e:
                self.print_error(f"FAIL: Could not load Memory Core: {e}")
                return False
        return True

    def print_error(self, message):
        print(f"{self.style['error']}Error:{Style.RESET_ALL} {message}")

    async def cmd_help(self, args: List[str]):
        print(
            f"\n{self.style['header']}Nexus Command Shell - Help{self.style['reset']}"
        )

        categorized_cmds = {}
        unique_funcs = set()
        for cmd_name, cmd_info in self.commands.items():
            if cmd_info["func"] in unique_funcs:
                continue
            unique_funcs.add(cmd_info["func"])

            category = cmd_info["category"]
            if category not in categorized_cmds:
                categorized_cmds[category] = []

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

        category_order = [
            "Navigation & Inspection",
            "Knowledge Analysis",
            "Cognitive Probes",
            "Shell & Memory",
        ]

        if self.context_node_id:
            category_order.insert(0, "Navigation Mode")

        max_name_len = 0
        max_alias_len = 0
        all_cmds_flat = [
            cmd for cat_cmds in categorized_cmds.values() for cmd in cat_cmds
        ]
        if all_cmds_flat:
            max_name_len = max(len(cmd["name"]) for cmd in all_cmds_flat)
            max_alias_len = max(len(cmd["aliases"]) for cmd in all_cmds_flat)

        for category in category_order:
            if category in categorized_cmds:
                print(
                    f"\n--- {self.style['section_header']}{category}{self.style['reset']} ---"
                )
                for cmd in sorted(categorized_cmds[category], key=lambda x: x["name"]):
                    name_str = f"  {self.style['cmd_name']}{cmd['name']:<{max_name_len}}{self.style['reset']}"
                    aliases = f"({cmd['aliases']})" if cmd["aliases"] else ""
                    alias_str = f"{self.style['arg_value']}{aliases:<{max_alias_len+2}}{self.style['reset']}"
                    help_str = f"- {self.style['secondary_text']}{cmd['help'] or 'No description.'}{self.style['reset']}"
                    print(f"{name_str}  {alias_str}  {help_str}")

        print("\n" + "=" * 80)
        print(
            f"{self.style['meta_info']}Tip:{self.style['reset']} For detailed help on a specific command, type {self.style['cmd_name']}<command> --help{self.style['reset']} (e.g., '{self.style['cmd_name']}list --help{self.style['reset']}')."
        )
        return True

    async def cmd_exit(self, args):
        return False

    async def cmd_back(self, args):
        if len(self.navigation_history) > 1:
            self.navigation_history.pop()
            prev_node_id = self.navigation_history[-1]
            get_func = self.commands["get"]["func"]
            node_id, neighbors = await get_func(self.memory, self.style, [prev_node_id])
            self._update_nav_context(node_id, neighbors)
        else:
            print(
                f"{self.style['meta_info']}Info:{self.style['reset']} No previous node in history. Resetting navigation context."
            )

            await self.cmd_reset([])
        return True

    async def cmd_reset(self, args):
        self.context_node_id = None
        self.context_neighbors = {}
        self.navigation_history = []
        print(
            f"{self.style['meta_info']}Info:{self.style['reset']} Navigation context has been reset."
        )
        return True

    def _update_nav_context(self, node_id, neighbors):
        if node_id and neighbors:
            self.context_node_id = node_id
            self.context_neighbors = neighbors

            if not self.navigation_history or self.navigation_history[-1] != node_id:
                self.navigation_history.append(node_id)
        else:
            self.context_node_id = None
            self.context_neighbors = {}

    async def run(self):
        """The main REPL loop for the shell."""
        print(
            f"\n{self.style['section_header']}Nexus Command Shell v0.1{Style.RESET_ALL}"
        )
        print(
            f"{self.style['meta_info']}[ BOOT ]: Initializing services...{self.style['reset']}"
        )

        if not await self._initialize_services():
            self.print_error("Initialization failed. Exiting.")
            return

        print(
            f"{self.style['meta_info']}[ BOOT ]: Memory Core loaded successfully.{self.style['reset']}"
        )

        stat_func = self.commands.get("stat", {}).get("func")
        if stat_func:
            await stat_func(self.memory, self.style, [])

        await self.cmd_help([])

        running = True
        while running:
            try:
                if self.context_node_id:
                    prompt = f"\n{self.style['nav_prompt']}[NEXUS:{self.context_node_id[:8]}]> {Style.RESET_ALL}"
                else:
                    prompt = f"\n{self.style['prompt']}[NEXUS]> {Style.RESET_ALL}"

                user_input = input(prompt)
                if not user_input.strip():
                    continue

                if self.context_node_id and user_input.isdigit():
                    # Handle numeric shortcuts for navigating to neighbors
                    choice = int(user_input)
                    if choice in self.context_neighbors:
                        target_id = self.context_neighbors[choice]
                        print(
                            f"{self.style['meta_info']}NAVIGATE:{self.style['reset']} Jumping to node {target_id[:8]}..."
                        )
                        get_func = self.commands["get"]["func"]
                        node_id, neighbors = await get_func(
                            self.memory, self.style, [target_id]
                        )
                        self._update_nav_context(node_id, neighbors)
                    else:
                        self.print_error(
                            f"Invalid choice. Not in the numbered neighbor list."
                        )
                    continue

                # Standard command parsing
                command_name = user_input.split()[0].lower()
                args_str = user_input.partition(" ")[2]

                # Handle navigation commands as special cases to keep context
                if self.context_node_id and command_name in ["b", "back"]:
                    await self.cmd_back([])
                    continue
                if self.context_node_id and command_name in ["x", "reset"]:
                    await self.cmd_reset([])
                    continue

                args = shlex.split(args_str)

                command_info = self.commands.get(command_name)

                if not command_info:
                    self.print_error(
                        f"Unknown Command: '{command_name}'. Type 'help' for a list of commands."
                    )
                    continue

                # Exit navigation mode if a non-navigation command is used.
                if self.context_node_id and not command_info.get("is_nav_command"):
                    await self.cmd_reset([])

                # --- Dynamic command execution using reflection ---
                # This block inspects the function signature of the command
                # and provides the required arguments (memory, llm, style, args)
                # if the function is designed to accept them.
                command_func = command_info["func"]
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
                if inspect.ismethod(command_func):
                    # Built-in commands are methods of the class, called with `args`
                    result = await command_func(args)
                else:
                    # Plugin commands are functions, called with dynamic kwargs (memory, style, etc.)
                    result = await command_func(**kwargs)

                # --- Post-execution handling ---
                # The 'get' command returns data used to update the navigation context.
                if command_name == "get":
                    node_id, neighbors = result if result else (None, None)
                    self._update_nav_context(node_id, neighbors)

                if command_name in ["exit", "q", "quit"]:
                    running = False
                elif isinstance(result, bool):
                    running = result

            except (KeyboardInterrupt, EOFError):
                running = False
                print(
                    f"\n{self.style['meta_info']}EXIT:{self.style['reset']} Shutting down Nexus."
                )

            except Exception as e:
                self.print_error(f"A fatal error occurred: {e}")
                import traceback

                traceback.print_exc()


async def main():
    """Initializes and runs the NexusShell."""
    shell = NexusShell()
    await shell.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Nexus shell terminated by user.{Style.RESET_ALL}")
