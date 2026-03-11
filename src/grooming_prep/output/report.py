import os
import webbrowser
from datetime import datetime
from pathlib import Path

from jinja2 import Environment, FileSystemLoader


TEMPLATES_DIR = Path(__file__).parent / "templates"


def generate_report(tickets: list[dict], project: str, status: str, discussion_order: list[dict]) -> str:
    env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)), autoescape=True)
    template = env.get_template("report.html")

    now = datetime.now()
    run_date = now.strftime("%Y-%m-%d %H:%M")
    timestamp = now.strftime("%Y%m%d_%H%M%S")

    flagged_tickets = [t for t in tickets if t.get("risks")]
    high_priority_count = sum(1 for t in tickets if t.get("priority_order", 3) <= 2)
    stale_count = sum(1 for t in tickets if any(r["type"] == "stale" for r in t.get("risks", [])))
    blocked_count = sum(1 for t in tickets if any(r["type"] == "blocked" for r in t.get("risks", [])))

    html = template.render(
        project=project,
        status=status,
        run_date=run_date,
        total_tickets=len(tickets),
        high_priority_count=high_priority_count,
        flagged_count=len(flagged_tickets),
        stale_count=stale_count,
        blocked_count=blocked_count,
        flagged_tickets=flagged_tickets,
        tickets=tickets,
        discussion_order=discussion_order,
    )

    output_path = f"/tmp/grooming-report-{timestamp}.html"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    return output_path
