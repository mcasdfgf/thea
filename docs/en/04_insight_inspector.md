# 4. The Insight Inspector

**Module:** `nexus_tools/cmd_insights.py`
**`Nexus` Commands:** `insights` (alias: `i`), `ifind`, `iget`

## Purpose

The Insight Inspector is a specialized set of tools for working with the system's knowledge base. It focuses exclusively on `KnowledgeCrystalNode` entities ("insights"), which represent the "beliefs" or conclusions the system has formed through reflection.

## Commands

### `insights` — List Insights

Displays a list of insights with options for filtering by status and pagination. Insights are always sorted by strength (`VERIFIED` > `UNVERIFIED` > `ARCHIVED`) and recency.

#### Usage
```
[NEXUS]> insights [<StatusCode>] [--page N]
```
-   `<StatusCode>` (optional): Filters insights by their status.
    -   `1`: `VERIFIED` (Strong, confirmed knowledge)
    -   `2`: `UNVERIFIED` (Weak hypotheses based on single experiences)
    -   `3`: `ARCHIVED` (Outdated knowledge, superseded by new insights)
-   `--page <N>` (optional): The page number to view.

> **Tip:** For complete help on the command, including the list of status codes, use `insights --help`.

**Examples:**
```
# Show the first page of all insights
[NEXUS]> i

# Show the second page of only VERIFIED insights
[NEXUS]> i 1 --page 2
```

### `ifind` — Find Insight by Concept

Searches for all insights that are semantically linked to the specified concept.

#### Usage
```
[NEXUS]> ifind "<Concept>"
```
-   `<Concept>`: The exact name of the concept (e.g., "coffee" or "french press").

### `iget` — Get Insight

Displays the full, detailed information for a specific insight by its ID.

#### Usage
```
[NEXUS]> iget <insight_id>
```
-   `<insight_id>`: The full or partial ID of the `KnowledgeCrystalNode`.

#### Interpreting the Output
The output includes all key attributes of an insight: its status, timestamp, full text, as well as the **source concepts** and the **source impulse ID** that generated it. This allows for a complete audit trail of any piece of knowledge.
