from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .config import load_config
from .jira_client import JiraClient
from .ai_summarizer import summarize_tickets
from .analyzer import analyze_tickets, sort_tickets, build_discussion_order
from .models import ReportRequest, ReportResponse, ReportSummary

app = FastAPI(title="Grooming Prep API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/report", response_model=ReportResponse)
async def generate_report(req: ReportRequest):
    try:
        config = load_config()
    except SystemExit as e:
        raise HTTPException(status_code=400, detail=str(e))

    client = JiraClient(config)
    try:
        tickets = client.fetch_tickets(req.project, req.status)
    except SystemExit as e:
        raise HTTPException(status_code=502, detail=str(e))

    if not tickets:
        raise HTTPException(
            status_code=404,
            detail=f"No tickets found for project '{req.project}' with status '{req.status}'.",
        )

    if not req.skip_ai:
        tickets = summarize_tickets(tickets, config["groq_api_key"], config["groq_model"])

    tickets = analyze_tickets(tickets)
    tickets = sort_tickets(tickets)
    discussion_order = build_discussion_order(tickets)

    summary = ReportSummary(
        total=len(tickets),
        high_priority_count=sum(1 for t in tickets if t.get("priority_order", 3) <= 2),
        flagged_count=sum(1 for t in tickets if t.get("risks")),
        stale_count=sum(1 for t in tickets if any(r["type"] == "stale" for r in t.get("risks", []))),
        blocked_count=sum(1 for t in tickets if any(r["type"] == "blocked" for r in t.get("risks", []))),
    )

    return ReportResponse(
        project=req.project,
        status=req.status,
        run_date=datetime.now(timezone.utc).isoformat(),
        summary=summary,
        tickets=tickets,
        discussion_order=discussion_order,
    )
