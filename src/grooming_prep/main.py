import webbrowser
import click

from .config import load_config
from .jira.client import JiraClient
from .ai.summarizer import summarize_tickets
from .analysis.analyzer import analyze_tickets, sort_tickets, build_discussion_order
from .output.report import generate_report


@click.command()
@click.option("--project", "-p", default=None, help="JIRA project key (e.g. RN)")
@click.option("--status", "-s", default="Backlog", show_default=True, help="JIRA status to filter by")
@click.option("--no-browser", is_flag=True, default=False, help="Skip opening report in browser")
@click.option("--no-ai", is_flag=True, default=False, help="Skip AI summarization (faster, for testing)")
def cli(project, status, no_browser, no_ai):
    """Generate a grooming prep report from JIRA tickets."""
    config = load_config()

    project = project or config.get("jira_project")
    if not project:
        raise click.UsageError("No project specified. Use --project or set JIRA_PROJECT in .env")

    click.echo(f"Fetching tickets from JIRA project '{project}' (status: {status})...")
    client = JiraClient(config)

    try:
        tickets = client.fetch_tickets(project, status)
    except SystemExit as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)

    if not tickets:
        click.echo(f"No tickets found for project '{project}' with status '{status}'.")
        raise SystemExit(0)

    click.echo(f"Found {len(tickets)} tickets.")

    if not no_ai:
        click.echo("Generating AI summaries (concurrent)...")
        tickets = summarize_tickets(tickets, config["groq_api_key"], config["groq_model"])
        click.echo("AI summaries complete.")

    click.echo("Analyzing dependencies and risks...")
    tickets = analyze_tickets(tickets)
    tickets = sort_tickets(tickets)
    discussion_order = build_discussion_order(tickets)

    flagged = sum(1 for t in tickets if t.get("risks"))
    click.echo(f"Analysis complete. {flagged} tickets flagged with risks.")

    click.echo("Generating HTML report...")
    report_path = generate_report(tickets, project, status, discussion_order)
    click.echo(f"Report saved to: {report_path}")

    if not no_browser:
        webbrowser.open(f"file://{report_path}")
        click.echo("Report opened in browser.")
