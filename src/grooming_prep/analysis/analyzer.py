from datetime import datetime, timezone, timedelta

STALE_DAYS = 60
MIN_DESCRIPTION_LENGTH = 100

BLOCKER_LINK_TYPES = {"is blocked by", "blocked by", "blocks"}


def _parse_date(date_str: str) -> datetime | None:
    if not date_str:
        return None
    try:
        # JIRA format: 2024-01-15T10:30:00.000+0000
        return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
    except ValueError:
        return None


def analyze_ticket(ticket: dict) -> dict:
    risks = []
    now = datetime.now(timezone.utc)

    # Missing acceptance criteria
    ac = ticket.get("acceptance_criteria", "").strip()
    if not ac:
        risks.append({"type": "missing_ac", "label": "Missing AC", "severity": "high"})

    # Unclear description
    desc = ticket.get("description", "").strip()
    if not desc or len(desc) < MIN_DESCRIPTION_LENGTH:
        risks.append({"type": "unclear_desc", "label": "Unclear Description", "severity": "high"})

    # Stale ticket
    updated = _parse_date(ticket.get("updated", ""))
    if updated and (now - updated) > timedelta(days=STALE_DAYS):
        days_stale = (now - updated).days
        risks.append({
            "type": "stale",
            "label": f"Stale ({days_stale}d)",
            "severity": "medium",
        })

    # Blocker dependency
    for link in ticket.get("links", []):
        link_type = link.get("type", "").lower()
        if any(b in link_type for b in BLOCKER_LINK_TYPES):
            risks.append({
                "type": "blocked",
                "label": f"Blocked by {link['key']}",
                "severity": "high",
            })
            break

    ticket["risks"] = risks
    return ticket


def analyze_tickets(tickets: list[dict]) -> list[dict]:
    return [analyze_ticket(t) for t in tickets]


def sort_tickets(tickets: list[dict]) -> list[dict]:
    return sorted(tickets, key=lambda t: (t.get("priority_order", 3), t["key"]))


def build_discussion_order(tickets: list[dict]) -> list[dict]:
    """Return tickets in suggested discussion order: priority then blocked last within group."""
    def sort_key(t):
        has_blocker = any(r["type"] == "blocked" for r in t.get("risks", []))
        return (t.get("priority_order", 3), int(has_blocker), t["key"])

    return sorted(tickets, key=sort_key)
