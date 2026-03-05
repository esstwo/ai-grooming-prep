from pydantic import BaseModel


class ReportRequest(BaseModel):
    project: str
    status: str = "Backlog"
    skip_ai: bool = False


class RiskItem(BaseModel):
    type: str
    label: str
    severity: str


class TicketLink(BaseModel):
    type: str
    key: str
    summary: str
    direction: str


class Ticket(BaseModel):
    key: str
    url: str
    summary: str
    description: str
    priority: str
    priority_order: int
    status: str
    issue_type: str
    labels: list[str]
    links: list[TicketLink]
    created: str
    updated: str
    comment_count: int
    assignee: str
    acceptance_criteria: str
    ai_summary: str
    risks: list[RiskItem]


class ReportSummary(BaseModel):
    total: int
    high_priority_count: int
    flagged_count: int
    stale_count: int
    blocked_count: int


class ReportResponse(BaseModel):
    project: str
    status: str
    run_date: str
    summary: ReportSummary
    tickets: list[Ticket]
    discussion_order: list[Ticket]
