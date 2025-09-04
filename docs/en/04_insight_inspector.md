# 4. The Knowledge Inspector

**Module:** `nexus_tools/cmd_insights.py`
**Nexus Commands:** `insights` (alias: `i`), `ifind`, `iget`

## Purpose

The Knowledge Inspector is a specialized toolset for working with the system's knowledge base. It focuses exclusively on `KnowledgeCrystalNode`s ("insights"), which are atomic units of knowledge the system has synthesized from its experiences during reflection.

## Commands

### `insights` — List Insights

Displays a list of insights with filtering by status. The list is always sorted by three criteria: **status** (active first), then **strength** (stronger first), and finally **timestamp** (newest first).

#### Usage

```
[NEXUS]> insights [--state <StatusCode>] [--page N]
```

-   `--state 1`: **ACTIVE** — Current, in-use knowledge. This includes both "strong" insights (results of merging) and new, "weak" hypotheses that have not yet been merged.
-   `--state 0`: **ARCHIVED** — Outdated knowledge. These are insights that have been superseded by newer, stronger ones during the reflection process.
-   `--page <N>` (Optional): The page number to display.

> **Tip:** For complete help on this command, including filter descriptions, use `insights --help`.

#### Examples

```
# Show the first page of all insights
[NEXUS]> i

# Show the second page of only ACTIVE insights
[NEXUS]> i --state 1 --page 2
```

### `ifind` — Find Insight by Concept

Finds all insights that are semantically linked to a specified concept.

#### Usage

```
[NEXUS]> ifind "<Concept>"
```

-   `<Concept>`: The exact name of the concept (e.g., "coffee" or "french press").

### `iget` — Get Insight

Displays complete and detailed information for a specific insight by its ID.

#### Usage

```
[NEXUS]> iget <insight_ID>
```

-   `<insight_ID>`: The full or partial ID of the `KnowledgeCrystalNode`.

#### Understanding the Output

The output includes all key attributes of the insight: its full text (`content`), status (`active_status`), accumulated strength (`strength`), creation timestamp, as well as the **source concepts** and the **source impulse ID** from which it was originally generated. This allows you to trace the complete "ancestry" of any piece of knowledge.
