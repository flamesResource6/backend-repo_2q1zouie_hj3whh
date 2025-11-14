import os
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from database import db, create_document, get_documents
from schemas import Transaction, Alert

app = FastAPI(title="Fraud Detection API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Fraud Detection API is running"}

@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"

    return response

# Helper to compute risk score

def compute_risk_score(tx: Transaction) -> float:
    score = 0.0
    # Amount-based risk
    if tx.amount >= 5000:
        score += 50
    elif tx.amount >= 1000:
        score += 25
    elif tx.amount >= 200:
        score += 10

    # Country risk
    risky_countries = {"RU", "NG", "UA", "BR", "CN"}
    if tx.country and tx.country.upper() in risky_countries:
        score += 15

    # Channel risk
    if tx.channel and tx.channel.lower() in {"web", "card-not-present"}:
        score += 10

    # Merchant category hints
    high_risk_mcc = {"gambling", "crypto", "adult"}
    if tx.merchant_category and tx.merchant_category.lower() in high_risk_mcc:
        score += 10

    # IP/device missing
    if not tx.ip_address or not tx.device_id:
        score += 5

    return min(score, 100.0)


def score_to_level(score: float) -> str:
    if score >= 70:
        return "high"
    if score >= 40:
        return "medium"
    return "low"


class CreateTransactionRequest(Transaction):
    pass

class CreateTransactionResponse(BaseModel):
    id: str
    risk_score: float
    risk_level: str

class ListTransactionsResponse(BaseModel):
    items: List[dict]

class ListAlertsResponse(BaseModel):
    items: List[dict]


@app.post("/api/transactions", response_model=CreateTransactionResponse)
async def create_transaction(payload: CreateTransactionRequest):
    data = payload.model_dump()
    if not data.get("timestamp"):
        data["timestamp"] = datetime.now(timezone.utc)

    # Compute risk
    score = compute_risk_score(payload)
    level = score_to_level(score)
    data["risk_score"] = score
    data["risk_level"] = level

    # Store transaction
    inserted_id = create_document("transaction", data)

    # If high risk, create an alert
    if level == "high":
        alert = Alert(
            transaction_ref=inserted_id,
            user_id=payload.user_id,
            reason=f"High-risk transaction: ${payload.amount} {payload.currency} at {payload.merchant or 'unknown merchant'}",
            risk_score=score,
            risk_level=level,
            tags=[t for t in [payload.merchant_category, payload.channel, payload.country] if t]
        )
        create_document("alert", alert)

    return {"id": inserted_id, "risk_score": score, "risk_level": level}


@app.get("/api/transactions", response_model=ListTransactionsResponse)
async def list_transactions(limit: Optional[int] = 50):
    limit = min(max(1, limit or 50), 200)
    items = get_documents("transaction", {}, limit)
    # Convert ObjectId to str
    for it in items:
        if "_id" in it:
            it["_id"] = str(it["_id"])
        if isinstance(it.get("timestamp"), datetime):
            it["timestamp"] = it["timestamp"].isoformat()
    return {"items": items}


@app.get("/api/alerts", response_model=ListAlertsResponse)
async def list_alerts(limit: Optional[int] = 50):
    limit = min(max(1, limit or 50), 200)
    items = get_documents("alert", {}, limit)
    for it in items:
        if "_id" in it:
            it["_id"] = str(it["_id"])
        if isinstance(it.get("created_at"), datetime):
            it["created_at"] = it["created_at"].isoformat()
    return {"items": items}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
