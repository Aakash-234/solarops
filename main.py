from fastapi import FastAPI, File, UploadFile, HTTPException, Request, Form
from fastapi.responses import JSONResponse, HTMLResponse, Response
from fastapi.templating import Jinja2Templates
from ocr import extract_text_textract
from extractor import extract_fields
from validator import validate_fields, generate_ai_suggestion
from llm import extract_fields_llm
import os
import shutil
import boto3

from config import (
    AWS_ACCESS_KEY_ID,
    AWS_SECRET_ACCESS_KEY,
    AWS_S3_BUCKET_NAME,
    AWS_REGION
)

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from model import Base, ValidationResult

from datetime import datetime

# ✅ Email sender helper
from emailr import send_email

app = FastAPI()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

s3_client = boto3.client(
    "s3",
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_REGION
)

SQLALCHEMY_DATABASE_URL = "sqlite:///./solarops.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)
print("✅ Tables ensured!")

templates = Jinja2Templates(directory="templates")


@app.get("/")
def root():
    return {"message": "SolarOps Validator Running ✅"}


@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    try:
        local_path = f"{UPLOAD_DIR}/{file.filename}"
        with open(local_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        print(f"✅ File saved: {local_path}")

        s3_client.upload_file(local_path, AWS_S3_BUCKET_NAME, file.filename)
        print(f"✅ Uploaded to S3: s3://{AWS_S3_BUCKET_NAME}/{file.filename}")

        extracted_text = extract_text_textract(file.filename)
        print(f"✅ Textract output: {extracted_text[:80]}...")

        fields = extract_fields(extracted_text)
        print(f"✅ Regex fields: {fields}")

        use_llm = False
        critical = ["customer_name", "system_capacity_kw", "panel_serial_numbers"]
        if use_llm and any(not fields.get(key) for key in critical):
            llm_fields = extract_fields_llm(extracted_text)
            fields = {**llm_fields, **fields}
            print(f"✅ LLM fallback merged: {fields}")

        validation = validate_fields(fields)
        confidence = validation["confidence"]
        print(f"✅ Validation: {validation}")

        ai_suggestion = "No suggestion."
        if not validation["valid"]:
            ai_suggestion = generate_ai_suggestion(fields, validation["issues"])
        print(f"✅ AI Suggestion: {ai_suggestion}")

        db = SessionLocal()
        result = ValidationResult(
            filename=file.filename,
            fields=fields,
            valid=validation["valid"],
            issues=validation["issues"],
            confidence=confidence,
            ai_suggestion=ai_suggestion,
            status="pending",
            reviewed_by=None,
            reviewed_at=None,
            reviewer_comment=None,
            audit_trail=[]
        )
        db.add(result)
        db.commit()
        db.refresh(result)
        db.close()
        print(f"✅ Saved to DB: {file.filename}")

        return {
            "message": f"File '{file.filename}' processed ✅",
            "s3_path": f"s3://{AWS_S3_BUCKET_NAME}/{file.filename}",
            "fields": fields,
            "validation": validation,
            "confidence": confidence,
            "ai_suggestion": ai_suggestion
        }

    except Exception as e:
        print("❌ INTERNAL ERROR:", str(e))
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@app.get("/results")
def list_results():
    db = SessionLocal()
    results = db.query(ValidationResult).all()
    output = []
    for r in results:
        output.append({
            "filename": r.filename,
            "timestamp": r.timestamp.isoformat(),
            "valid": r.valid,
            "issues": r.issues,
            "confidence": r.confidence,
            "ai_suggestion": r.ai_suggestion,
            "status": r.status
        })
    db.close()
    print(f"✅ Returned {len(output)} results")
    return JSONResponse(content={"results": output})


@app.get("/dashboard")
def dashboard(request: Request):
    db = SessionLocal()
    results = db.query(ValidationResult).all()
    db.close()
    print(f"✅ Rendering dashboard with {len(results)} results")
    return templates.TemplateResponse(
        "dashboard.html",
        {"request": request, "results": results}
    )


@app.get("/report/{filename}", response_class=Response)
def feedback_report(filename: str):
    db = SessionLocal()
    record = db.query(ValidationResult).filter(ValidationResult.filename == filename).first()
    db.close()

    if not record:
        return HTMLResponse(content=f"<h2>❌ Report: File '{filename}' not found.</h2>")

    html_content = f"""
    <html>
        <head>
            <title>Feedback Report - {filename}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 2rem; }}
                .valid {{ color: green; }}
                .invalid {{ color: red; }}
                pre {{ background: #f8f8f8; padding: 1rem; border-radius: 4px; }}
            </style>
        </head>
        <body>
            <h1>🔍 Feedback Report</h1>
            <h2>File: {record.filename}</h2>
            <p><strong>Timestamp:</strong> {record.timestamp}</p>
            <p><strong>Validation:</strong> <span class="{ 'valid' if record.valid else 'invalid' }">{record.valid}</span></p>
            <p><strong>Confidence:</strong> {record.confidence}%</p>
            <p><strong>Status:</strong> {record.status}</p>
            <p><strong>AI Suggestion:</strong> {record.ai_suggestion}</p>
            <h3>Extracted Fields:</h3>
            <pre>{record.fields}</pre>
            <h3>Issues:</h3>
            <pre>{record.issues}</pre>
        </body>
    </html>
    """

    return Response(
        content=html_content,
        media_type="text/html",
        headers={"Content-Disposition": f"attachment; filename={filename}_report.html"}
    )


@app.post("/override")
async def override_status(
    filename: str = Form(...),
    new_status: str = Form(...),
    reviewer: str = Form(...),
    comment: str = Form(...)
):
    db = SessionLocal()
    record = db.query(ValidationResult).filter(ValidationResult.filename == filename).first()
    if not record:
        db.close()
        raise HTTPException(status_code=404, detail="File not found")

    old_status = record.status
    record.status = new_status
    record.reviewed_by = reviewer
    record.reviewed_at = datetime.utcnow()
    record.reviewer_comment = comment

    if not record.audit_trail:
        record.audit_trail = []
    record.audit_trail.append({
        "timestamp": datetime.utcnow().isoformat(),
        "old_status": old_status,
        "new_status": new_status,
        "reviewer": reviewer,
        "comment": comment
    })

    db.commit()
    db.refresh(record)
    db.close()

    print(f"✅ Status for '{filename}' changed from {old_status} to {new_status} by {reviewer}")

    # ✅ Send notification
    recipient = "client@example.com"  # Replace with actual
    subject = f"[SolarOps] File '{filename}' status updated"
    body = f"""
Hi,

The file **{filename}** status has changed.

• Old Status: {old_status}
• New Status: {new_status}
• Reviewer: {reviewer}
• Comment: {comment}

View audit: http://127.0.0.1:8000/audit/{filename}

Thank you,
SolarOps
"""
    send_email(recipient, subject, body)

    return JSONResponse(content={"message": f"Status updated to {new_status}"})


@app.get("/audit/{filename}", response_class=HTMLResponse)
def audit_trail(filename: str):
    db = SessionLocal()
    record = db.query(ValidationResult).filter(ValidationResult.filename == filename).first()
    db.close()

    if not record:
        return HTMLResponse(content=f"<h2>❌ No audit trail for '{filename}'</h2>")

    trail = record.audit_trail or []

    html = f"""
    <html>
      <head>
        <title>Audit Trail - {filename}</title>
        <style>
          body {{ font-family: Arial, sans-serif; margin: 2rem; }}
          table {{ border-collapse: collapse; width: 100%; }}
          th, td {{ border: 1px solid #ccc; padding: 8px; }}
          th {{ background: #eee; }}
        </style>
      </head>
      <body>
        <h1>🔍 Audit Trail - {filename}</h1>
        <table>
          <tr>
            <th>Time</th>
            <th>From</th>
            <th>To</th>
            <th>Reviewer</th>
            <th>Comment</th>
          </tr>
    """
    for entry in trail:
        html += f"""
          <tr>
            <td>{entry.get('timestamp')}</td>
            <td>{entry.get('old_status')}</td>
            <td>{entry.get('new_status')}</td>
            <td>{entry.get('reviewer')}</td>
            <td>{entry.get('comment')}</td>
          </tr>
        """
    html += "</table></body></html>"

    return HTMLResponse(content=html)
