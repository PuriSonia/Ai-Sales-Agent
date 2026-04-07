from fastapi import APIRouter
from openai import OpenAI
from pydantic import BaseModel
import os
import smtplib
import ssl
from email.message import EmailMessage
from learning import (
    save_learning,
    best,
    save_lead,
    list_leads,
    update_lead_opened,
    update_lead_replied,
    update_lead_status,
)

router = APIRouter()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = int(os.getenv("SMTP_PORT", 465))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
SMTP_FROM = os.getenv("SMTP_FROM")
SEND_EMAILS = os.getenv("SEND_EMAILS", "false").lower() == "true"

SALES_CONTEXT = """
You sell MRV data infrastructure for carbon and climate companies in India and Africa.

Core value:
- audit-grade data analytics
- faster verification and credit issuance
- higher buyer trust
- reduced consultant and audit costs
- ability to scale projects without scaling MRV teams

Key insight:
Strong carbon projects often fail verification or get undervalued because their data cannot survive scrutiny.

What you do:
- automated, reproducible baseline calculations
- conservative stress-testing of assumptions
- early detection of data gaps and audit risks
- audit-ready evidence packaging
- transparent calculation trails aligned with global standards

Ideal customers:
India:
- private carbon project developers
- renewable energy, industrial efficiency, waste, methane projects
- selling to EU, Japan, or global buyers

Africa:
- NGOs running cookstove, nature, or community renewable projects
- project aggregators managing multiple sites
- climate funds supporting distributed portfolios

Outreach style:
- short
- curious
- human
- not pushy
- lead with a data-risk question
- do not sound like generic software sales

Good hooks:
- verification readiness
- data confidence
- buyer trust
- reduced consultant dependence
- audit defensibility
- funder-ready transparency

Pilot angle:
Offer a short MRV data readiness pilot or integrity pilot rather than a hard sell.
"""

class LeadIn(BaseModel):
    email: str
    website: str
    message: str

class LeadStatusIn(BaseModel):
    id: int
    status: str | None = None

def generate_outreach(lead_text: str):
    examples = best()
    prompt = f"""
You are a carbon data sales expert.

Use this business context:
{SALES_CONTEXT}

Past best examples:
{examples}

Task:
Write a short cold outreach email for this lead:
{lead_text}

Rules:
- under 120 words
- ask exactly 1 simple question
- no buzzwords
- no exaggerated claims
- sound human
- focus on MRV, verification, data confidence, buyer trust, or audit readiness
- output only the email body
"""

    res = client.responses.create(
        model="gpt-4o-mini",
        input=prompt
    )
    return res.output_text.strip()

def send_email(to: str, subject: str, body: str):
    if not all([SMTP_HOST, SMTP_USER, SMTP_PASSWORD, SMTP_FROM]):
        raise RuntimeError("SMTP env vars are missing")

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = SMTP_FROM
    msg["To"] = to
    msg.set_content(body)

    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, context=context) as server:
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.send_message(msg)

@router.post("/chat")
def chat(data: dict):
    msg = data.get("message", "")
    try:
        reply = generate_outreach(msg)
        save_learning({"input": msg, "reply": reply, "score": 1})
        return {"reply": reply}
    except Exception as e:
        return {"reply": f"Error: {str(e)}"}

@router.post("/qualify")
def qualify(data: dict):
    text = data.get("text", "")
    prompt = f"""
Decide if this is a real target customer.

Criteria:
- climate or carbon company, project developer, NGO, aggregator, fund, or related buyer
- likely to care about MRV, verification, carbon credit readiness, monitoring, data integrity, or buyer trust
- not a blog, directory, news site, generic agency, or social profile

Answer ONLY: YES or NO

Text:
{text[:1500]}
"""

    try:
        res = client.responses.create(
            model="gpt-4o-mini",
            input=prompt
        )
        return {"decision": res.output_text.strip()}
    except Exception as e:
        return {"decision": f"ERROR: {str(e)}"}

@router.post("/save-lead")
def save_lead_route(data: LeadIn):
    lead_id = save_lead(data.email, data.website, data.message, "generated")
    return {"status": "saved", "id": lead_id}

@router.get("/leads")
def get_leads():
    rows = list_leads()
    leads = [
        {
            "id": r[0],
            "email": r[1],
            "website": r[2],
            "message": r[3],
            "status": r[4],
            "opened": r[5],
            "replied": r[6],
            "created_at": str(r[7]),
        }
        for r in rows
    ]
    return {"leads": leads}

@router.post("/mark-open")
def mark_open(data: LeadStatusIn):
    update_lead_opened(data.id)
    update_lead_status(data.id, "opened")
    return {"status": "ok"}

@router.post("/mark-replied")
def mark_replied(data: LeadStatusIn):
    update_lead_replied(data.id)
    return {"status": "ok"}

@router.post("/send-lead-email")
def send_lead_email(data: LeadIn):
    subject = "Quick question"
    try:
        if SEND_EMAILS:
            send_email(data.email, subject, data.message)
            lead_id = save_lead(data.email, data.website, data.message, "sent")
            return {"status": "sent", "id": lead_id}
        else:
            lead_id = save_lead(data.email, data.website, data.message, "ready_to_send")
            return {"status": "ready_to_send", "id": lead_id}
    except Exception as e:
        return {"status": "error", "error": str(e)}
