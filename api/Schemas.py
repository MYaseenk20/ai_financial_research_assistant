from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr


class UserRegister(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None

class UserLogin(BaseModel):
    email:    EmailStr
    password: str

class UserOut(BaseModel):
    id : int
    email: EmailStr
    full_name: Optional[str] = None
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}

class Token(BaseModel):
    access_token: str
    token_type:   str = "bearer"

class AnalyzeRequest(BaseModel):
    company: str


class ReportResultOut(BaseModel):
    research_result: Optional[str] = ""
    rag_result: Optional[str] = ""
    risk_result: Optional[str] = ""
    final_result:    Optional[str]

    model_config = {"from_attributes": True}


class TokenData(BaseModel):
    user_id: Optional[int] = None