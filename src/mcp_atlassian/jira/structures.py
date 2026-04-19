"""Module for Jira Structure (Almworks) board operations."""

import logging
from typing import Any

from requests.exceptions import HTTPError

from ..utils.decorators import handle_auth_errors
from .client import SERVER_DC_PAGE_SIZE, JiraClient

logger = logging.getLogger("mcp-jira")


class StructuresMixin(JiraClient):
    """Mixin for Jira Structure plugin operations.

    Requires the Structure by Almworks plugin on the Jira instance.
    Uses the Structure REST API (rest/structure/2.0/).
    """

    @handle_auth_errors("Jira API")
    def get_structure(self, structure_id: int | str) -> dict[str, Any]:
        """Get metadata for a Structure board.

        Args:
            structure_id: The ID of the structure.

        Returns:
            Dictionary with structure name, description, etc.
        """
        result = self.jira.get(f"rest/structure/2.0/structure/{structure_id}")

        if not isinstance(result, dict):
            return {"structure_id": str(structure_id), "error": "Invalid response"}

        return {
            "id": result.get("id"),
            "name": result.get("name"),
            "description": result.get("description", ""),
            "editable": result.get("editable", False),
            "is_archived": result.get("isArchived", False),
        }

    @handle_auth_errors("Jira API")
    def get_structure_forest(self, structure_id: int | str) -> dict[str, Any]:
        """Get the raw forest (hierarchy formula) for a Structure board.

        Returns the parsed row list with item IDs and depths, but
        without resolved issue details. Use get_structure_issues()
        for the fully resolved hierarchy.

        Args:
            structure_id: The ID of the structure.

        Returns:
            Dictionary with rows (row_id, depth, item_id, item_type)
            and metadata.
        """
        result = self.jira.post(
            "rest/structure/2.0/forest/latest",
            json={"structureId": int(structure_id)},
        )

        if not isinstance(result, dict) or "formula" not in result:
            return {"structure_id": str(structure_id), "error": "Invalid response"}

        rows = self._parse_formula(result["formula"])

        return {
            "structure_id": int(structure_id),
            "total_rows": len(rows),
            "rows": rows,
            "version": result.get("version"),
        }

    @handle_auth_errors("Jira API")
    def get_structure_issues(
        self,
        structure_id: int | str,
        max_depth: int | None = None,
    ) -> dict[str, Any]:
        """Get the full resolved hierarchy for a Structure board.

        Fetches the forest, resolves all item IDs to Jira issue
        details (key, summary, status, type, project), and returns
        a flat list with depth for hierarchy reconstruction.

        Args:
            structure_id: The ID of the structure.
            max_depth: Optional maximum depth to include (0 = top level only).

        Returns:
            Dictionary with resolved issue hierarchy and structure metadata.
        """
        # Step 1: Get structure metadata
        meta = self.get_structure(structure_id)

        # Step 2: Get the forest
        forest_result = self.jira.post(
            "rest/structure/2.0/forest/latest",
            json={"structureId": int(structure_id)},
        )

        if not isinstance(forest_result, dict) or "formula" not in forest_result:
            return {
                "structure_id": int(structure_id),
                "name": meta.get("name"),
                "error": "Could not fetch forest",
            }

        rows = self._parse_formula(forest_result["formula"])

        # Apply depth filter
        if max_depth is not None:
            rows = [r for r in rows if r["depth"] <= max_depth]

        # Step 3: Collect issue IDs to resolve (validate numeric)
        item_ids = [
            r["item_id"] for r in rows if r.get("item_id") and r["item_id"].isdigit()
        ]
        unique_ids = list(dict.fromkeys(item_ids))

        # Step 4: Batch resolve via JQL (50 at a time)
        resolved: dict[str, dict] = {}
        for i in range(0, len(unique_ids), SERVER_DC_PAGE_SIZE):
            batch = unique_ids[i : i + SERVER_DC_PAGE_SIZE]
            jql = f"id in ({','.join(batch)})"
            try:
                search_result = self.jira.jql(
                    jql,
                    fields="summary,issuetype,status,project",
                    limit=SERVER_DC_PAGE_SIZE,
                )
                if not isinstance(search_result, dict):
                    continue
                for issue in search_result.get("issues", []):
                    fields = issue.get("fields", {})
                    resolved[issue["id"]] = {
                        "key": issue["key"],
                        "summary": fields.get("summary", ""),
                        "issue_type": (fields.get("issuetype", {}).get("name", "")),
                        "status": (fields.get("status", {}).get("name", "")),
                        "status_category": (
                            fields.get("status", {})
                            .get("statusCategory", {})
                            .get("name", "")
                        ),
                        "project": (fields.get("project", {}).get("key", "")),
                    }
            except HTTPError:
                raise
            except Exception:
                logger.warning("Failed to resolve batch starting at index %d", i)

        # Step 5: Build resolved hierarchy
        items = []
        for row in rows:
            item_id = row.get("item_id")
            if item_id and item_id in resolved:
                entry = {
                    "depth": row["depth"],
                    **resolved[item_id],
                }
                items.append(entry)
            elif row.get("row_type") == "generator":
                items.append(
                    {
                        "depth": row["depth"],
                        "key": None,
                        "summary": f"[generator: {row.get('item_ref', '?')}]",
                        "issue_type": "generator",
                        "status": "",
                        "status_category": "",
                        "project": "",
                    }
                )

        return {
            "structure_id": int(structure_id),
            "name": meta.get("name", ""),
            "description": meta.get("description", ""),
            "total_items": len(items),
            "resolved_count": sum(1 for i in items if i.get("key")),
            "items": items,
        }

    @staticmethod
    def _parse_formula(formula: str) -> list[dict[str, Any]]:
        """Parse a Structure forest formula string into row dicts.

        The formula format is comma-separated entries of:
          rowId:depth:itemId:itemType  (issue rows)
          rowId:depth:typeId/generatorId  (generator rows)

        Args:
            formula: The raw formula string from the API.

        Returns:
            List of row dicts with depth, item_id, etc.  Malformed
            entries are skipped with a warning log.
        """
        rows: list[dict[str, Any]] = []
        skipped = 0
        for entry in formula.split(","):
            entry = entry.strip()
            if not entry:
                continue
            parts = entry.split(":")
            try:
                if len(parts) == 4:
                    row_id, depth, item_id, item_type = parts
                    rows.append(
                        {
                            "row_id": row_id,
                            "depth": int(depth),
                            "item_id": item_id,
                            "item_type": item_type,
                            "row_type": "issue",
                        }
                    )
                elif len(parts) == 3:
                    row_id, depth, item_ref = parts
                    rows.append(
                        {
                            "row_id": row_id,
                            "depth": int(depth),
                            "item_ref": item_ref,
                            "row_type": "generator",
                        }
                    )
                else:
                    skipped += 1
                    logger.debug("Skipping malformed formula entry: %s", entry)
            except (ValueError, TypeError):
                skipped += 1
                logger.debug("Skipping malformed formula entry: %s", entry)
        if skipped:
            logger.warning(
                "Skipped %d malformed formula entries during parsing", skipped
            )
        return rows
