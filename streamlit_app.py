import requests
import streamlit as st

st.set_page_config(page_title="Grooming Prep", layout="wide")
st.title("Grooming Prep")

# Sidebar inputs
with st.sidebar:
    st.header("Settings")
    api_url = st.text_input("API URL", value="http://localhost:8000")
    project = st.text_input("Project Key", placeholder="e.g. RN")
    status = st.selectbox("Status", ["Backlog", "To Do", "In Progress", "Selected for Development"])
    skip_ai = st.checkbox("Skip AI summarization")
    generate = st.button("Generate Report", type="primary", disabled=not project)

if not generate:
    st.info("Enter a project key and click Generate Report.")
    st.stop()

# Fetch report
with st.spinner("Fetching and analyzing tickets..."):
    try:
        resp = requests.post(
            f"{api_url}/report",
            json={"project": project, "status": status, "skip_ai": skip_ai},
            timeout=300,
        )
    except requests.ConnectionError:
        st.error(f"Could not connect to API at {api_url}. Is the server running?")
        st.stop()

if not resp.ok:
    try:
        detail = resp.json().get("detail", resp.text)
    except Exception:
        detail = resp.text
    st.error(f"API error {resp.status_code}: {detail}")
    st.stop()

data = resp.json()
summary = data["summary"]
tickets = data["tickets"]
discussion_order = data["discussion_order"]

# Summary metrics
col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Total", summary["total"])
col2.metric("High Priority", summary["high_priority_count"])
col3.metric("Flagged", summary["flagged_count"])
col4.metric("Stale", summary["stale_count"])
col5.metric("Blocked", summary["blocked_count"])

st.divider()

# Flagged risks section
flagged = [t for t in tickets if t["risks"]]
if flagged:
    st.subheader("Flagged Tickets")
    for ticket in flagged:
        has_high = any(r["severity"] == "high" for r in ticket["risks"])
        msg = f"**[{ticket['key']}]({ticket['url']})** — {ticket['summary']}  \n"
        msg += ", ".join(f"`{r['label']}`" for r in ticket["risks"])
        if has_high:
            st.error(msg)
        else:
            st.warning(msg)
    st.divider()

# Ticket breakdown
st.subheader("All Tickets")
priority_colors = {"Highest": "🔴", "High": "🟠", "Medium": "🟡", "Low": "🟢", "Lowest": "⚪"}
for ticket in tickets:
    icon = priority_colors.get(ticket["priority"], "⚪")
    label = f"{icon} [{ticket['key']}]({ticket['url']}) — {ticket['summary']}"
    with st.expander(label):
        cols = st.columns([1, 1, 1])
        cols[0].write(f"**Priority:** {ticket['priority']}")
        cols[1].write(f"**Assignee:** {ticket['assignee']}")
        cols[2].write(f"**Comments:** {ticket['comment_count']}")

        if ticket["ai_summary"]:
            st.markdown("**AI Summary**")
            st.markdown(ticket["ai_summary"])

        if ticket["risks"]:
            st.markdown("**Risks:** " + " ".join(f"`{r['label']}`" for r in ticket["risks"]))

        if ticket["links"]:
            st.markdown("**Dependencies**")
            for link in ticket["links"]:
                jira_base = ticket["url"].rsplit("/browse/", 1)[0]
                st.markdown(f"- {link['type']}: [{link['key']}]({jira_base}/browse/{link['key']}) — {link['summary']}")

st.divider()

# Suggested discussion order
st.subheader("Suggested Discussion Order")
for i, ticket in enumerate(discussion_order, 1):
    icon = priority_colors.get(ticket["priority"], "⚪")
    risk_labels = " ".join(f"`{r['label']}`" for r in ticket["risks"]) if ticket["risks"] else ""
    st.markdown(f"{i}. {icon} **[{ticket['key']}]({ticket['url']})** — {ticket['summary']} {risk_labels}")
