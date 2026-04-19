from unittest.mock import MagicMock, Mock

import pytest
from requests.exceptions import HTTPError

from mcp_atlassian.exceptions import MCPAtlassianAuthenticationError
from mcp_atlassian.models.jira.common import (
    JiraIssueType,
    JiraStatus,
    JiraStatusCategory,
    JiraUser,
)
from mcp_atlassian.models.jira.issue import JiraIssue
from mcp_atlassian.models.jira.search import JiraSearchResult


def _make_issue(
    key: str = "PROJ-1",
    summary: str = "Test",
    status_name: str = "Open",
    status_category_key: str = "new",
    assignee_name: str | None = "Alice",
    issue_type_name: str = "Task",
) -> JiraIssue:
    """Build a minimal JiraIssue."""
    status_cat = JiraStatusCategory(
        key=status_category_key, name=status_category_key.title()
    )
    status = JiraStatus(name=status_name, category=status_cat)
    assignee = JiraUser(display_name=assignee_name) if assignee_name else None
    return JiraIssue(
        key=key,
        summary=summary,
        status=status,
        issue_type=JiraIssueType(name=issue_type_name),
        assignee=assignee,
    )


def _epic_issue(key: str = "PROJ-100", summary: str = "My Epic") -> JiraIssue:
    return _make_issue(
        key=key,
        summary=summary,
        issue_type_name="Epic",
        status_name="In Progress",
        status_category_key="indeterminate",
    )


def _search_result(issues: list[JiraIssue]) -> JiraSearchResult:
    return JiraSearchResult(
        total=len(issues), start_at=0, max_results=50, issues=issues
    )


class TestEpicAnalysisMixin:
    @pytest.fixture
    def mixin(self, jira_fetcher):
        return jira_fetcher

    def test_get_epic_summary_basic(self, mixin):
        """Happy path with a few children."""
        children = [
            _make_issue("C-1", status_name="Done", status_category_key="done"),
            _make_issue("C-2", status_name="Open", status_category_key="new"),
            _make_issue(
                "C-3",
                status_name="Done",
                status_category_key="done",
                assignee_name="Bob",
            ),
        ]

        mixin.get_issue = MagicMock(return_value=_epic_issue())
        mixin.search_issues = MagicMock(return_value=_search_result(children))

        result = mixin.get_epic_summary("PROJ-100")

        assert result["epic"]["key"] == "PROJ-100"
        assert result["summary"]["total_children"] == 3
        assert result["summary"]["by_status"]["Done"] == 2
        assert result["summary"]["by_status"]["Open"] == 1
        assert result["summary"]["by_assignee"]["Alice"] == 2
        assert result["summary"]["by_assignee"]["Bob"] == 1
        assert result["summary"]["completion_percentage"] == pytest.approx(66.7)
        assert len(result["children"]) == 3

    def test_get_epic_summary_not_an_epic(self, mixin):
        """Raises ValueError when the issue isn't an epic."""
        mixin.get_issue = MagicMock(return_value=_make_issue(issue_type_name="Story"))

        with pytest.raises(ValueError, match="not an Epic"):
            mixin.get_epic_summary("PROJ-1")

    def test_get_epic_summary_no_children(self, mixin):
        """Empty child set returns zero counts."""
        mixin.get_issue = MagicMock(return_value=_epic_issue())
        mixin.search_issues = MagicMock(return_value=_search_result([]))

        result = mixin.get_epic_summary("PROJ-100")

        assert result["summary"]["total_children"] == 0
        assert result["summary"]["completion_percentage"] == 0.0
        assert result["children"] == []

    def test_get_epic_summary_exclude_children(self, mixin):
        """include_children=False omits the children list."""
        children = [_make_issue("C-1")]
        mixin.get_issue = MagicMock(return_value=_epic_issue())
        mixin.search_issues = MagicMock(return_value=_search_result(children))

        result = mixin.get_epic_summary("PROJ-100", include_children=False)

        assert result["summary"]["total_children"] == 1
        assert result["children"] == []

    def test_get_epic_summary_unassigned(self, mixin):
        """Children without an assignee are grouped as Unassigned."""
        children = [_make_issue("C-1", assignee_name=None)]
        mixin.get_issue = MagicMock(return_value=_epic_issue())
        mixin.search_issues = MagicMock(return_value=_search_result(children))

        result = mixin.get_epic_summary("PROJ-100")

        assert result["summary"]["by_assignee"]["Unassigned"] == 1

    def test_get_epic_summary_100_percent_done(self, mixin):
        """All children done gives 100% completion."""
        children = [
            _make_issue("C-1", status_name="Done", status_category_key="done"),
            _make_issue("C-2", status_name="Closed", status_category_key="done"),
        ]
        mixin.get_issue = MagicMock(return_value=_epic_issue())
        mixin.search_issues = MagicMock(return_value=_search_result(children))

        result = mixin.get_epic_summary("PROJ-100")

        assert result["summary"]["completion_percentage"] == 100.0

    def test_get_epic_summary_auth_error(self, mixin):
        """401 raises MCPAtlassianAuthenticationError."""
        mixin.get_issue = MagicMock(
            side_effect=HTTPError(response=Mock(status_code=401))
        )

        with pytest.raises(MCPAtlassianAuthenticationError):
            mixin.get_epic_summary("PROJ-100")

    def test_fetch_epic_children_fallback_jql(self, mixin):
        """When the first JQL pattern fails, the second is tried."""
        children = [_make_issue("C-1")]

        call_count = 0

        def fake_search(jql, fields=None, start=0, limit=50, **kw):
            nonlocal call_count
            call_count += 1
            if "parent" in jql:
                raise Exception("parent not supported")
            return _search_result(children)

        mixin.get_issue = MagicMock(return_value=_epic_issue())
        mixin.search_issues = MagicMock(side_effect=fake_search)

        result = mixin.get_epic_summary("PROJ-100")

        assert result["summary"]["total_children"] == 1
        assert call_count == 2

    def test_localized_epic_type_korean(self, mixin):
        """Korean localized epic name should be accepted."""
        epic = _make_issue(
            key="PROJ-100",
            summary="에픽 이슈",
            issue_type_name="에픽",
        )
        mixin.get_issue = MagicMock(return_value=epic)
        mixin.search_issues = MagicMock(return_value=_search_result([]))

        result = mixin.get_epic_summary("PROJ-100")
        assert result["epic"]["key"] == "PROJ-100"

    def test_localized_epic_type_japanese(self, mixin):
        """Japanese localized epic name should be accepted."""
        epic = _make_issue(
            key="PROJ-100",
            summary="エピック課題",
            issue_type_name="エピック",
        )
        mixin.get_issue = MagicMock(return_value=epic)
        mixin.search_issues = MagicMock(return_value=_search_result([]))

        result = mixin.get_epic_summary("PROJ-100")
        assert result["epic"]["key"] == "PROJ-100"

    def test_cloud_no_repaging_children(self, mixin):
        """On Cloud, _fetch_epic_children must not manually re-page."""
        mixin.config = MagicMock(is_cloud=True)
        children = [_make_issue(f"C-{i}") for i in range(80)]

        mixin.get_issue = MagicMock(return_value=_epic_issue())
        mixin.search_issues = MagicMock(return_value=_search_result(children))

        result = mixin.get_epic_summary("PROJ-100")

        assert result["summary"]["total_children"] == 80
        assert mixin.search_issues.call_count == 1
