from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import sqlite3
import json
from datetime import datetime
from fpdf import FPDF
import os

app = FastAPI(title="AdAudit SaaS API V4 - Admin Data Entry")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database Setup
def init_db():
    conn = sqlite3.connect("audits.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS audit_reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_name TEXT,
            timestamp TEXT,
            data TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

@app.get("/api/accounts")
def get_accounts():
    conn = sqlite3.connect("audits.db")
    cursor = conn.cursor()
    cursor.execute("SELECT client_name FROM audit_reports GROUP BY client_name")
    rows = cursor.fetchall()
    conn.close()
    
    accounts = [{"id": r[0], "name": r[0]} for r in rows]
    return {"status": "success", "accounts": accounts}

@app.get("/api/audit_report/{client_name}")
def get_audit_report(client_name: str):
    conn = sqlite3.connect("audits.db")
    cursor = conn.cursor()
    cursor.execute("SELECT data FROM audit_reports WHERE client_name = ? ORDER BY id DESC LIMIT 1", (client_name,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return {"status": "success", "data": json.loads(row[0])}
    return {"status": "error", "message": "Not found"}

class PlatformMetrics(BaseModel):
    spend: float
    roas: float
    leads: int
    impression_share: Optional[float] = None
    frequency: Optional[float] = None
    hook_rate: Optional[float] = None

class OmnichannelRequest(BaseModel):
    client_name: str
    meta: PlatformMetrics
    google: PlatformMetrics

@app.post("/api/omnichannel-audit")
def generate_omnichannel_audit(req: OmnichannelRequest):
    meta = req.meta
    google = req.google
    
    red = []
    yellow = []
    green = []
    
    # 1. Summary Metrics
    total_spend = meta.spend + google.spend
    total_leads = meta.leads + google.leads
    total_revenue = (meta.spend * meta.roas) + (google.spend * google.roas)
    avg_roas = total_revenue / total_spend if total_spend > 0 else 0
    
    # 2. Omnichannel Logic
    if meta.roas > 2.5 and google.impression_share is not None and google.impression_share < 40:
        yellow.append({
            "title": "Losing Meta-Generated Demand on Google",
            "description": f"Meta ROAS is high ({meta.roas}x) driving brand awareness, but Google Impression Share is critically low at {google.impression_share}%.",
            "tip": "Competitors are likely capturing your Meta-generated branded search traffic. Immediately increase exact match bids on your branded terms."
        })
        
    if total_spend > 0 and (meta.spend / total_spend) > 0.8:
        yellow.append({
            "title": "Platform Over-Reliance (Meta)",
            "description": "Over 80% of your total spend is concentrated on Meta.",
            "tip": "Start scaling YouTube and PMax campaigns with video assets to diversify customer acquisition and protect against Meta CPM spikes."
        })
        
    # Standard logic applied to specific inputs
    if meta.roas < 1.5:
        red.append({
            "title": "Meta Campaigns Bleeding Money",
            "description": f"Overall Meta ROAS is only {meta.roas}x.",
            "tip": "Pause bottom-performing creatives immediately. Your offer or creative angle is fundamentally missing the mark with this audience."
        })
    elif meta.roas > 3.0:
        green.append({
            "title": "Meta Campaigns Ready to Scale",
            "description": f"Meta ROAS is strong at {meta.roas}x.",
            "tip": "Increase budget by 20% on winning ad sets. Don't restrict the algorithm—let it find more converters."
        })

    # New Frequency & Hook Rate Logic
    if meta.frequency is not None and meta.frequency > 4.0:
        red.append({
            "title": "Severe Ad Fatigue (Meta)",
            "description": f"Frequency has climbed to {meta.frequency}. Your audience is seeing the exact same creatives too often.",
            "tip": "Launch a fresh batch of creatives immediately. Fatigue is artificially inflating your CPMs and CPA."
        })

    if meta.hook_rate is not None and meta.hook_rate < 25:
        yellow.append({
            "title": "Low Hook Rate (Meta)",
            "description": f"Hook rate is only {meta.hook_rate}%. Users are scrolling past your videos in the first 3 seconds.",
            "tip": "Test extreme contrast, dynamic text, or controversial statements in the first 3 seconds to stop the scroll."
        })
        
    if google.roas < 1.5:
        red.append({
            "title": "Google Campaigns Underperforming",
            "description": f"Overall Google ROAS is {google.roas}x.",
            "tip": "Audit your Search Terms report immediately. You are likely bidding on broad match terms with low buyer intent. Add negative keywords."
        })
    elif google.roas > 3.0:
        green.append({
            "title": "Google Campaigns Highly Profitable",
            "description": f"Google ROAS is {google.roas}x.",
            "tip": "Your search intent mapping is excellent. Consider testing PMax to capture additional inventory at this ROAS."
        })
        
    if not red and not yellow and not green:
        green.append({
            "title": "Stable Baseline Performance",
            "description": "Accounts are performing within average industry benchmarks.",
            "tip": "Begin introducing 2-3 new creative angles per week to break through to the next level of scaling."
        })
        
    audit_data = {
        "summary": {
            "total_spend": round(total_spend, 2),
            "avg_roas": round(avg_roas, 2),
            "total_leads": total_leads
        },
        "red": red,
        "yellow": yellow,
        "green": green
    }
    
    # Save to SQLite
    conn = sqlite3.connect("audits.db")
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO audit_reports (client_name, timestamp, data) VALUES (?, ?, ?)",
        (req.client_name, datetime.now().isoformat(), json.dumps(audit_data))
    )
    conn.commit()
    conn.close()
    
    return {"status": "success", "data": audit_data}

class AuditPDFRequest(BaseModel):
    client_name: str
    data: Dict[str, Any]

@app.post("/api/generate-pdf")
def generate_pdf(request: AuditPDFRequest):
    pdf = FPDF()
    pdf.add_page()
    
    logo_path = os.path.join(os.path.dirname(__file__), "..", "frontend", "logo.webp")
    if os.path.exists(logo_path):
        pdf.image(logo_path, x=10, y=8, h=12)
        pdf.ln(10)
    
    pdf.set_font("Helvetica", 'B', 22)
    pdf.set_text_color(10, 30, 80)
    pdf.cell(0, 20, txt=f"Pinnacle Media | Full-Funnel Audit: {request.client_name}", ln=True, align="C")
    pdf.ln(5)
    
    summary = request.data.get('summary', {})
    if summary:
        pdf.set_font("Helvetica", 'B', 14)
        pdf.set_text_color(80, 80, 80)
        pdf.cell(0, 10, txt=f"Total Combined Spend: ${summary.get('total_spend', 0)}", ln=True)
        pdf.cell(0, 10, txt=f"Average Blended ROAS: {summary.get('avg_roas', 0)}x", ln=True)
        pdf.cell(0, 10, txt=f"Total Conversions: {summary.get('total_leads', 0)}", ln=True)
        pdf.ln(10)
    
    def add_section(title, color, items):
        if not items: return
        pdf.set_font("Helvetica", 'B', 16)
        pdf.set_text_color(*color)
        pdf.cell(0, 10, txt=title, ln=True)
        pdf.ln(2)
        
        for item in items:
            pdf.set_font("Helvetica", 'B', 12)
            pdf.set_text_color(40, 40, 40)
            pdf.multi_cell(0, 8, txt=item['title'])
            
            pdf.set_font("Helvetica", '', 11)
            pdf.set_text_color(80, 80, 80)
            pdf.multi_cell(0, 6, txt=item['description'])
            
            pdf.set_font("Helvetica", 'I', 11)
            pdf.set_text_color(0, 100, 200)
            pdf.multi_cell(0, 6, txt=f"Senior Buyer's Tip: {item['tip']}")
            pdf.ln(6)
        pdf.ln(5)

    add_section("Stop Leakage (Critical)", (220, 53, 69), request.data.get('red', []))
    add_section("Optimize (Warning)", (210, 150, 0), request.data.get('yellow', []))
    add_section("Scale (Winners)", (40, 167, 69), request.data.get('green', []))
    
    pdf_bytes = bytes(pdf.output())
    filename = f"FullFunnel_Audit_{request.client_name.replace(' ', '_')}.pdf"
    return Response(
        content=pdf_bytes, 
        media_type="application/pdf", 
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
