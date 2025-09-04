# cmd_probes.py: Implements commands for emulating parts of the cognitive cycle.
# This module provides high-level commands (`plan`, `probe`) that allow developers
# to simulate the core cognitive loop in an isolated environment. This is essential
# for debugging and testing individual cognitive services without running the full
# application server.

import json
import asyncio
import shlex
import argparse
from unittest.mock import MagicMock
from dataclasses import asdict
from colorama import Fore, Style

from services.simple_executor_service import SimpleExecutorService
from services.enrichment_planner_service import EnrichmentPlannerService
from services.memory_recall_service import MemoryRecallService
from services.synthesis_service import SynthesisService
from events import Task
from nexus_tools.cmd_nav import NexusArgParser


def register():
    return {
        "plan": {
            "func": cmd_probe_planner,
            "alias": [],
            "help": 'Probe the Instinct -> Enrichment Plan chain. Usage: plan "<impulse text>"',
        },
        "probe": {
            "func": cmd_probe,
            "alias": [],
            "help": 'Probe the full cognitive cycle with fine-grained control. Use "probe --help" for details.',
        },
    }


def print_plan_help(style):
    cmd, arg_name, sec, header, reset, arg_val = (
        style["cmd_name"],
        style["arg_name"],
        style["secondary_text"],
        style["header"],
        style["reset"],
        style["arg_value"],
    )
    print(f'\n{header}Usage: {cmd}plan {arg_name}"<impulse text>"{reset}')
    print(f"{sec}Probes the Instinct -> Enrichment Plan generation chain.{reset}\n")
    print(
        f"{sec}This command is a shortcut to test how the system deconstructs a user request "
        f"into a structured JSON plan before it queries the long-term memory.{reset}\n"
    )
    print(f"{header}Example:{reset}")
    print(
        f'  {cmd}plan {arg_val}"remind me about coffee and what is the capital of Brazil"{reset}'
    )


def print_probe_help(style):
    cmd, arg_name, sec, header, reset, arg_val = (
        style["cmd_name"],
        style["arg_name"],
        style["secondary_text"],
        style["header"],
        style["reset"],
        style["arg_value"],
    )

    print(
        f"\n{header}Usage: {cmd}probe {arg_name}[<impulse text> | --plan-json <JSON>]{reset} [{arg_name}--no-synth{reset}]"
    )
    print(f"{sec}Probes the full cognitive cycle with fine-grained control.{reset}\n")

    print(f"{header}Modes of Operation:{reset}")
    print(
        f'  1. {cmd}probe {arg_name}"<text>"{reset}:{sec} Runs the full cycle (Instinct -> Plan -> Recall -> Synthesis).{reset}'
    )
    print(
        f'  2. {cmd}probe {arg_name}"<text>" --no-synth{reset}:{sec} Runs up to the memory recall stage, showing what the system found.{reset}'
    )
    print(
        f"  3. {cmd}probe {arg_name}--plan-json '<json>'{reset}:{sec} Skips planning and uses your custom JSON plan for memory recall.{reset}\n"
    )

    print(f"{header}Options:{reset}")
    print(
        f"  {arg_name}--no-synth{reset}            Stop after memory recall, before the final synthesis step."
    )
    print(
        f"  {arg_name}--plan-json <JSON>{reset}    Provide a JSON string of a pre-made enrichment plan to use directly."
    )
    print(f"  {arg_name}--help{reset}                Show this help message.\n")

    print(f"{header}Example Workflow (Debugging Memory Recall):{reset}")
    print(f'  1. Generate a plan: {cmd}plan {arg_val}"remind me about coffee"{reset}')
    print(f"  2. Copy the JSON output from the plan command.")
    print(
        f"  3. Test memory recall with that specific plan: {cmd}probe {arg_name}--plan-json {arg_val}'<paste JSON here>'{reset}"
    )


def _print_header(style, title):
    print(f"\n{style['header']}--- {title.upper()} ---{Style.RESET_ALL}")


def _print_json(style, data, title="JSON Output"):
    print(f"{style['meta_info']}{title}:{Style.RESET_ALL}")
    print(json.dumps(data, ensure_ascii=False, indent=2))


async def cmd_probe_planner(memory, llm, style, args):
    if not args or "--help" in args:
        print_plan_help(style)
        return

    impulse = " ".join(args)
    mock_orchestrator = MagicMock()

    _print_header(style, "STEP 1: Instinct Generation (SimpleExecutorService)")
    executor = SimpleExecutorService(mock_orchestrator, memory)
    instinct_task = Task(
        type="generate_instinctive_response",
        payload={"impulse_text": impulse, "history": []},
    )
    instinct_report = await executor.handle_task(instinct_task)
    instinctive_response = instinct_report.data.get("text", "")
    print(
        f"{style['meta_info']}Generated Instinct:{Style.RESET_ALL}\n{instinctive_response}"
    )

    _print_header(style, "STEP 2: Enrichment Planning (EnrichmentPlannerService)")
    enrichment_planner = EnrichmentPlannerService(mock_orchestrator, memory)
    plan_task = Task(
        type="create_enrichment_plan",
        payload={
            "original_impulse": impulse,
            "instinctive_response": instinctive_response,
        },
    )
    plan_report = await enrichment_planner.handle_task(plan_task)
    _print_json(style, plan_report.data, "Generated Enrichment Plan")

    _print_header(style, "NEXT STEP: Probe Memory")
    plan_json_str = json.dumps(plan_report.data, ensure_ascii=False)
    probe_command = f"probe --plan-json {shlex.quote(plan_json_str)}"
    print(
        "To test memory recall with this specific plan, copy and run the command below:"
    )
    print(f"{style['cmd_name']}{probe_command}{Style.RESET_ALL}")


async def cmd_probe(memory, llm, style, args):
    if not args or (len(args) == 1 and args[0] == "--help"):
        print_probe_help(style)
        return

    parser = NexusArgParser(
        prog="probe",
        description="Probe the full cognitive cycle with fine-grained control.",
        add_help=False,
    )
    parser.add_argument(
        "impulse_parts",
        nargs="*",
        help="The user's text impulse (ignored if --plan-json is used).",
    )
    parser.add_argument(
        "--no-synth",
        action="store_true",
        help="Stop after memory recall, before final synthesis.",
    )
    parser.add_argument(
        "--plan-json",
        type=str,
        help="A JSON string representing a pre-made enrichment plan to use directly.",
    )
    parser.add_argument("--help", action="store_true", help="Show this help message.")

    try:
        parsed_args = parser.parse_args(args)
    except SystemExit:
        return

    if parsed_args.help:
        parser.print_help()
        return

    impulse = " ".join(parsed_args.impulse_parts)

    if not impulse and not parsed_args.plan_json:
        print(
            f"{style['error']}Error:{style['reset']} You must provide either an impulse text or a plan with --plan-json."
        )
        parser.print_help()
        return

    await _run_probe_worker(
        memory,
        llm,
        style,
        impulse=impulse,
        no_synth=parsed_args.no_synth,
        plan_json_str=parsed_args.plan_json,
    )


async def _run_probe_worker(memory, llm, style, impulse, no_synth, plan_json_str):
    """The main worker that executes the cognitive cycle emulation."""

    # Use a MagicMock to simulate the Orchestrator. This is a pragmatic choice
    # to reuse service code without instantiating the full orchestrator, which
    # has its own async loops and state. This makes the probe self-contained.
    mock_orchestrator = MagicMock()
    plan_report = None
    instinctive_response = "N/A (skipped due to provided plan)"

    if plan_json_str:
        _print_header(style, "STEP 1 & 2: Skipped (Using Provided Plan)")
        try:
            plan_data = json.loads(plan_json_str)
            plan_report = MagicMock()
            plan_report.data = plan_data
            impulse = "N/A (provided by plan)"
            _print_json(style, plan_data, "Using Provided Enrichment Plan")
        except json.JSONDecodeError as e:
            print(
                f"{style['error']}Error:{style['reset']} Invalid JSON provided to --plan-json: {e}"
            )
            return
    else:
        _print_header(style, f"STEP 1: Instinct Generation for '{impulse}'")
        executor = SimpleExecutorService(mock_orchestrator, memory)
        instinct_task = Task(
            type="generate_instinctive_response",
            payload={"impulse_text": impulse, "history": []},
        )
        instinct_report = await executor.handle_task(instinct_task)
        instinctive_response = instinct_report.data.get("text", "")
        print(instinctive_response)

        _print_header(style, "STEP 2: Enrichment Plan Generation")
        enrichment_planner = EnrichmentPlannerService(mock_orchestrator, memory)
        plan_task = Task(
            type="create_enrichment_plan",
            payload={
                "original_impulse": impulse,
                "instinctive_response": instinctive_response,
            },
        )
        plan_report = await enrichment_planner.handle_task(plan_task)
        _print_json(style, plan_report.data)

    _print_header(style, "STEP 3: Memory Recall")
    recall_service = MemoryRecallService(mock_orchestrator, memory)
    enrichment_reports = []

    search_queries = plan_report.data.get("queries", [])
    if search_queries:
        for i, query_data in enumerate(search_queries):
            query_text = query_data.get("semantic_query")
            print(
                f"\n{style['meta_info']}> Executing query {i+1}/{len(search_queries)}:{style['reset']} '{query_text}'"
            )
            recall_task = Task(
                type="recall_request", payload={"request_payload": query_data}
            )
            report = await recall_service.handle_task(recall_task)
            enrichment_reports.append(report)

            found_nodes = report.data.get("found_nodes", [])
            if not found_nodes:
                print("  -> No relevant nodes found.")
            else:
                print(f"  -> Found {len(found_nodes)} relevant nodes:")
                for node in found_nodes:
                    preview = (str(node.get("content", ""))[:60] + "...").replace(
                        "\n", " "
                    )
                    score = node.get("relevance_score", 0)
                    print(
                        f"    - [{node.get('id','')[:8]}] (Score: {score:.2f}, Type: {node.get('type')}) '{preview}'"
                    )
    else:
        print("Info: No search queries were found in the plan.")

    if no_synth:
        _print_header(style, "--- Execution stopped before Synthesis (--no-synth) ---")
        return

    _print_header(style, "STEP 4: Final Synthesis")
    synthesis_service = SynthesisService(mock_orchestrator, memory)
    final_task = Task(
        type="synthesize_final_response",
        payload={
            "original_impulse": impulse,
            "instinctive_response": instinctive_response,
            "memory_package": [asdict(r) for r in enrichment_reports if r],
        },
    )
    final_report = await synthesis_service.handle_task(final_task)
    final_text = final_report.data.get(
        "text", "Synthesis failed or produced no output."
    )

    _print_header(style, "--- Final Synthesized Response ---")
    print(final_text)
