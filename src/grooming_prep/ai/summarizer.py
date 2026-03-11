import asyncio
import re
from groq import AsyncGroq

PROMPT_TEMPLATE = """You are a technical analyst helping an engineering manager prepare for a grooming session.

Analyze this JIRA ticket and provide a concise summary with the following sections:

**Ticket:** {key} - {summary}

**Description:**
{description}

Provide your analysis in this exact format:

**Purpose & Impact:** (1-2 sentences: what problem does this solve and for whom?)

**Technical Scope:** (2-3 bullet points: key technical work involved)

**Ambiguities / Open Questions:** (bullet points of unclear requirements, missing info, or decisions needed — write "None identified" if clear)

Keep each section brief and actionable for a grooming discussion. Total response should be under 200 words."""


async def summarize_ticket_async(client: AsyncGroq, ticket: dict, model: str) -> str:
    description = ticket.get("description", "").strip()
    if not description:
        return "Summary unavailable: ticket missing description."

    prompt = PROMPT_TEMPLATE.format(
        key=ticket["key"],
        summary=ticket["summary"],
        description=description[:2000],  # cap to avoid token overflow
    )

    try:
        response = await client.chat.completions.create(
            model=model,
            max_tokens=400,
            messages=[{"role": "user", "content": prompt}],
        )
        content = response.choices[0].message.content
        # Strip <think>...</think> blocks from reasoning models (e.g. qwen3)
        content = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL)
        return content.strip()
    except Exception as e:
        return f"Summary generation failed: {e}"


async def summarize_all_async(tickets: list[dict], api_key: str, model: str) -> list[dict]:
    client = AsyncGroq(api_key=api_key)
    tasks = [summarize_ticket_async(client, t, model) for t in tickets]
    summaries = await asyncio.gather(*tasks)
    for ticket, summary in zip(tickets, summaries):
        ticket["ai_summary"] = summary
    return tickets


def summarize_tickets(tickets: list[dict], api_key: str, model: str) -> list[dict]:
    return asyncio.run(summarize_all_async(tickets, api_key, model))
