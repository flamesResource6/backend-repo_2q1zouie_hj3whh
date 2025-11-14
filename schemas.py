"""
Database Schemas

Define your MongoDB collection schemas here using Pydantic models.
These schemas are used for data validation in your application.

Each Pydantic model represents a collection in your database.
Model name is converted to lowercase for the collection name:
- User -> "user" collection
- Product -> "product" collection
- BlogPost -> "blogs" collection
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

# Example schemas (retain for reference)

class User(BaseModel):
    """
    Users collection schema
    Collection name: "user" (lowercase of class name)
    """
    name: str = Field(..., description="Full name")
    email: str = Field(..., description="Email address")
    address: str = Field(..., description="Address")
    age: Optional[int] = Field(None, ge=0, le=120, description="Age in years")
    is_active: bool = Field(True, description="Whether user is active")

class Product(BaseModel):
    """
    Products collection schema
    Collection name: "product" (lowercase of class name)
    """
    title: str = Field(..., description="Product title")
    description: Optional[str] = Field(None, description="Product description")
    price: float = Field(..., ge=0, description="Price in dollars")
    category: str = Field(..., description="Product category")
    in_stock: bool = Field(True, description="Whether product is in stock")

# Fraud detection app schemas

class Transaction(BaseModel):
    """
    Transactions collection schema
    Collection name: "transaction"
    """
    transaction_id: Optional[str] = Field(None, description="External transaction ID")
    user_id: str = Field(..., description="User identifier")
    amount: float = Field(..., ge=0, description="Transaction amount")
    currency: str = Field("USD", description="Currency code")
    merchant: Optional[str] = Field(None, description="Merchant name")
    merchant_category: Optional[str] = Field(None, description="MCC or category")
    country: Optional[str] = Field("US", description="Country code")
    channel: Optional[str] = Field("card", description="Channel, e.g., card, web, mobile")
    timestamp: Optional[datetime] = Field(None, description="Event time; defaults to now if missing")
    device_id: Optional[str] = Field(None, description="Device identifier")
    ip_address: Optional[str] = Field(None, description="IP address")
    # Labels/derived fields (may be set by backend)
    risk_score: Optional[float] = Field(None, ge=0, le=100)
    risk_level: Optional[str] = Field(None, description="low|medium|high")
    is_fraud: Optional[bool] = Field(False, description="Confirmed fraud label")

class Alert(BaseModel):
    """
    Alerts collection schema
    Collection name: "alert"
    """
    transaction_ref: str = Field(..., description="Reference to transaction _id as string")
    user_id: str = Field(..., description="User identifier")
    reason: str = Field(..., description="Why this alert was created")
    risk_score: float = Field(..., ge=0, le=100)
    risk_level: str = Field(..., description="low|medium|high")
    tags: Optional[List[str]] = Field(default_factory=list)
