from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

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