from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional, List
from datetime import datetime

# ─── Auth Schemas ────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=30)
    email: EmailStr
    password: str = Field(..., min_length=8)
    privacy_policy_consent: bool

    @field_validator("privacy_policy_consent")
    @classmethod
    def kvkk_must_be_true(cls, v: bool) -> bool:
        if not v:
            raise ValueError("KVKK onayı zorunludur (madde 5/6 - Açık Rıza).")
        return v


class VerifyEmailRequest(BaseModel):
    email: EmailStr
    code: int = Field(..., ge=100000, le=999999)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    user: dict
    code: Optional[int] = None


# ─── Interview Schemas ───────────────────────────────────────────

class InterviewOut(BaseModel):
    id: int
    title: str
    category: str
    level: str
    description: str
    starter_code: str
    hints: List[str]


class InterviewListResponse(BaseModel):
    items: List[InterviewOut]
    total: int
    filters: dict


# ─── Attempt Schemas ─────────────────────────────────────────────

class AttemptSubmit(BaseModel):
    question_id: int
    user_code: str
    passed_tests: int
    total_tests: int
    success: bool
    execution_time_ms: Optional[int] = 0
    hints_used: int = 0


class AttemptOut(BaseModel):
    id: str
    question_id: int
    question_title: Optional[str] = None
    user_code: str
    passed_tests: int
    total_tests: int
    success: bool
    execution_time_ms: int
    hints_used: int
    created_at: datetime


# ─── Runner Schemas ──────────────────────────────────────────────

class RunRequest(BaseModel):
    question_id: int
    user_code: str


class RunResponse(BaseModel):
    question_id: int
    title: str
    total_tests: int
    passed_tests: int
    success_rate: str
    results: list