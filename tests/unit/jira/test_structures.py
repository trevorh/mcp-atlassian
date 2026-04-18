from unittest.mock import Mock

import pytest
from requests.exceptions import HTTPError

from mcp_atlassian.exceptions import MCPAtlassianAuthenticationError
from mcp_atlassian.jira.structures import StructuresMixin


class TestStructuresMixin:
    @pytest.fixture
    def mixin(self, mock_config, mock_atlassian_jira):
        m = StructuresMixin(config=mock_config)
        m.jira = mock_atlassian_jira
        return m

    # ---- get_structure ----

    def test_get_structure_success(self, mixin):
        mixin.jira.get.return_value = {
            "id": 585,
            "name": "My Structure",
            "description": "A board",
            "editable": True,
            "isArchived": False,
        }

        result = mixin.get_structure("585")

        assert result["id"] == 585
        assert result["name"] == "My Structure"
        assert result["editable"] is True

    def test_get_structure_invalid_response(self, mixin):
        mixin.jira.get.return_value = "bad"

        result = mixin.get_structure("585")

        assert result["error"] == "Invalid response"

    def test_get_structure_auth_error(self, mixin):
        mixin.jira.get.side_effect = HTTPError(response=Mock(status_code=401))
        with pytest.raises(MCPAtlassianAuthenticationError):
            mixin.get_structure("585")

    # ---- get_structure_forest ----

    def test_get_structure_forest_success(self, mixin):
        mixin.jira.post.return_value = {
            "formula": "1:0:100:0,2:1:200:0,3:1:300:0",
            "version": 42,
        }

        result = mixin.get_structure_forest("585")

        assert result["total_rows"] == 3
        assert result["rows"][0]["depth"] == 0
        assert result["rows"][0]["item_id"] == "100"
        assert result["rows"][1]["depth"] == 1
        assert result["version"] == 42

    def test_get_structure_forest_invalid_response(self, mixin):
        mixin.jira.post.return_value = {"no_formula": True}

        result = mixin.get_structure_forest("585")

        assert result["error"] == "Invalid response"

    def test_get_structure_forest_auth_error(self, mixin):
        mixin.jira.post.side_effect = HTTPError(response=Mock(status_code=401))
        with pytest.raises(MCPAtlassianAuthenticationError):
            mixin.get_structure_forest("585")

    # ---- _parse_formula ----

    def test_parse_formula_issue_rows(self):
        rows = StructuresMixin._parse_formula("1:0:100:0,2:1:200:0")
        assert len(rows) == 2
        assert rows[0] == {
            "row_id": "1",
            "depth": 0,
            "item_id": "100",
            "item_type": "0",
            "row_type": "issue",
        }

    def test_parse_formula_generator_rows(self):
        rows = StructuresMixin._parse_formula("10:2:gen/abc")
        assert len(rows) == 1
        assert rows[0]["row_type"] == "generator"
        assert rows[0]["item_ref"] == "gen/abc"

    def test_parse_formula_empty(self):
        assert StructuresMixin._parse_formula("") == []

    def test_parse_formula_mixed(self):
        rows = StructuresMixin._parse_formula("1:0:100:0,2:1:gen/x,3:0:200:0")
        assert len(rows) == 3
        assert rows[0]["row_type"] == "issue"
        assert rows[1]["row_type"] == "generator"
        assert rows[2]["row_type"] == "issue"

    # ---- get_structure_issues ----

    def test_get_structure_issues_success(self, mixin):
        mixin.jira.get.return_value = {
            "id": 585,
            "name": "Board",
            "description": "",
            "editable": True,
            "isArchived": False,
        }
        mixin.jira.post.return_value = {
            "formula": "1:0:100:0,2:1:200:0",
            "version": 1,
        }
        mixin.jira.jql.return_value = {
            "issues": [
                {
                    "id": "100",
                    "key": "PROJ-1",
                    "fields": {
                        "summary": "Top level",
                        "issuetype": {"name": "Epic"},
                        "status": {
                            "name": "Open",
                            "statusCategory": {"name": "To Do"},
                        },
                        "project": {"key": "PROJ"},
                    },
                },
                {
                    "id": "200",
                    "key": "PROJ-2",
                    "fields": {
                        "summary": "Child",
                        "issuetype": {"name": "Story"},
                        "status": {
                            "name": "Done",
                            "statusCategory": {"name": "Done"},
                        },
                        "project": {"key": "PROJ"},
                    },
                },
            ],
        }

        result = mixin.get_structure_issues("585")

        assert result["total_items"] == 2
        assert result["resolved_count"] == 2
        assert result["items"][0]["key"] == "PROJ-1"
        assert result["items"][0]["depth"] == 0
        assert result["items"][1]["key"] == "PROJ-2"
        assert result["items"][1]["depth"] == 1

    def test_get_structure_issues_with_max_depth(self, mixin):
        mixin.jira.get.return_value = {
            "id": 1,
            "name": "B",
            "description": "",
        }
        mixin.jira.post.return_value = {
            "formula": "1:0:100:0,2:1:200:0,3:2:300:0",
            "version": 1,
        }
        mixin.jira.jql.return_value = {
            "issues": [
                {
                    "id": "100",
                    "key": "P-1",
                    "fields": {
                        "summary": "A",
                        "issuetype": {"name": "Task"},
                        "status": {"name": "Open", "statusCategory": {"name": "To Do"}},
                        "project": {"key": "P"},
                    },
                },
                {
                    "id": "200",
                    "key": "P-2",
                    "fields": {
                        "summary": "B",
                        "issuetype": {"name": "Task"},
                        "status": {"name": "Open", "statusCategory": {"name": "To Do"}},
                        "project": {"key": "P"},
                    },
                },
            ],
        }

        result = mixin.get_structure_issues("1", max_depth=1)

        assert result["total_items"] == 2
        depths = [i["depth"] for i in result["items"]]
        assert all(d <= 1 for d in depths)

    def test_get_structure_issues_auth_error(self, mixin):
        mixin.jira.get.side_effect = HTTPError(response=Mock(status_code=401))
        with pytest.raises(MCPAtlassianAuthenticationError):
            mixin.get_structure_issues("585")
