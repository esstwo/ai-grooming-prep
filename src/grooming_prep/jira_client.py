import requests
from requests.auth import HTTPBasicAuth
from typing import Any

# Common JIRA custom field names for acceptance criteria
AC_FIELD_NAMES = [
    "customfield_10016",  # story points (skip)
    "customfield_10014",
    "customfield_10015",
    "customfield_10020",
    "customfield_10030",
    "customfield_10031",
]

PRIORITY_ORDER = {
    "Highest": 1,
    "High": 2,
    "Medium": 3,
    "Low": 4,
    "Lowest": 5,
}


class JiraClient:
    def __init__(self, config: dict):
        self.base_url = config["jira_url"]
        self.auth = HTTPBasicAuth(config["jira_email"], config["jira_api_token"])
        self.headers = {"Accept": "application/json"}
        self._ac_field: str | None = None

    def _get(self, path: str, params: dict | None = None) -> Any:
        url = f"{self.base_url}/rest/api/3/{path}"
        resp = requests.get(url, auth=self.auth, headers=self.headers, params=params)
        if not resp.ok:
            raise SystemExit(
                f"JIRA API error {resp.status_code}: {resp.text}\n"
                f"Check your JIRA_URL, JIRA_EMAIL, and JIRA_API_TOKEN in .env"
            )
        return resp.json()

    def _detect_ac_field(self, fields: dict) -> str | None:
        """Detect acceptance criteria custom field from a ticket's fields."""
        for key, val in fields.items():
            if not key.startswith("customfield_"):
                continue
            if val is None:
                continue
            # Look for text content fields that might be AC
            if isinstance(val, dict) and val.get("type") == "doc":
                # Likely Atlassian Document Format field
                if key != "customfield_10016":  # skip story points
                    return key
            if isinstance(val, str) and len(val) > 10:
                if key != "customfield_10016":
                    return key
        return None

    def _extract_text(self, field_value: Any) -> str:
        """Extract plain text from JIRA field (handles ADF and plain strings)."""
        if field_value is None:
            return ""
        if isinstance(field_value, str):
            return field_value
        if isinstance(field_value, dict):
            # Atlassian Document Format
            if field_value.get("type") == "doc":
                return self._adf_to_text(field_value)
        return str(field_value)

    def _adf_to_text(self, node: dict) -> str:
        """Recursively extract text from ADF nodes."""
        if node.get("type") == "text":
            return node.get("text", "")
        parts = []
        for child in node.get("content", []):
            parts.append(self._adf_to_text(child))
        return " ".join(p for p in parts if p)

    def fetch_tickets(self, project: str, status: str) -> list[dict]:
        jql = f'project = "{project}" AND status = "{status}" ORDER BY priority ASC'
        tickets = []
        start = 0
        page_size = 100

        fields = (
            "summary,description,priority,status,issuetype,labels,"
            "issuelinks,created,updated,comment,assignee,reporter"
        )

        while True:
            data = self._get(
                "search",
                params={
                    "jql": jql,
                    "startAt": start,
                    "maxResults": page_size,
                    "fields": fields,
                },
            )
            issues = data.get("issues", [])
            if not issues:
                break

            for issue in issues:
                tickets.append(self._parse_ticket(issue))

            start += len(issues)
            if start >= data.get("total", 0):
                break

        return tickets

    def _parse_ticket(self, issue: dict) -> dict:
        f = issue["fields"]
        key = issue["key"]

        description = self._extract_text(f.get("description"))
        priority_name = (f.get("priority") or {}).get("name", "Medium")

        # Parse issue links
        links = []
        for link in f.get("issuelinks", []):
            link_type = link.get("type", {}).get("name", "")
            if "outwardIssue" in link:
                linked = link["outwardIssue"]
                links.append({
                    "type": link.get("type", {}).get("outward", link_type),
                    "key": linked["key"],
                    "summary": linked["fields"].get("summary", ""),
                    "direction": "outward",
                })
            if "inwardIssue" in link:
                linked = link["inwardIssue"]
                links.append({
                    "type": link.get("type", {}).get("inward", link_type),
                    "key": linked["key"],
                    "summary": linked["fields"].get("summary", ""),
                    "direction": "inward",
                })

        comment_count = (f.get("comment") or {}).get("total", 0)

        return {
            "key": key,
            "url": f"{self.base_url}/browse/{key}",
            "summary": f.get("summary", ""),
            "description": description,
            "priority": priority_name,
            "priority_order": PRIORITY_ORDER.get(priority_name, 3),
            "status": (f.get("status") or {}).get("name", ""),
            "issue_type": (f.get("issuetype") or {}).get("name", ""),
            "labels": f.get("labels", []),
            "links": links,
            "created": f.get("created", ""),
            "updated": f.get("updated", ""),
            "comment_count": comment_count,
            "assignee": ((f.get("assignee") or {}).get("displayName", "Unassigned")),
            "acceptance_criteria": "",  # filled below if detected
            "ai_summary": "",
            "risks": [],
        }
