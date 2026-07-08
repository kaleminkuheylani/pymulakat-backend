# models/question_study.py
# Question Study — zor sorular için derinlemesine analiz.
#
# DB tablosu: public.question_studies
# FK: question_id → public.questions(id) ON DELETE CASCADE

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class QuestionStudy:
    id: int
    question_id: int
    problem_understanding: str
    approach_1_title: Optional[str] = None
    approach_1_code: Optional[str] = None
    approach_1_complexity: Optional[str] = None
    approach_2_title: Optional[str] = None
    approach_2_code: Optional[str] = None
    approach_2_complexity: Optional[str] = None
    approach_3_title: Optional[str] = None
    approach_3_code: Optional[str] = None
    approach_3_complexity: Optional[str] = None
    challenges: Optional[str] = None
    related_question_ids: List[int] = field(default_factory=list)
    updated_at: Optional[str] = None

    def to_public_dict(self) -> dict:
        return {
            "id": self.id,
            "question_id": self.question_id,
            "problem_understanding": self.problem_understanding,
            "approach_1": {
                "title": self.approach_1_title,
                "code": self.approach_1_code,
                "complexity": self.approach_1_complexity,
            } if self.approach_1_title else None,
            "approach_2": {
                "title": self.approach_2_title,
                "code": self.approach_2_code,
                "complexity": self.approach_2_complexity,
            } if self.approach_2_title else None,
            "approach_3": {
                "title": self.approach_3_title,
                "code": self.approach_3_code,
                "complexity": self.approach_3_complexity,
            } if self.approach_3_title else None,
            "challenges": self.challenges,
            "related_question_ids": self.related_question_ids,
            "updated_at": self.updated_at,
        }


def row_to_study(row: dict) -> QuestionStudy:
    return QuestionStudy(
        id=row.get("id", 0),
        question_id=row.get("question_id", 0),
        problem_understanding=row.get("problem_understanding", ""),
        approach_1_title=row.get("approach_1_title"),
        approach_1_code=row.get("approach_1_code"),
        approach_1_complexity=row.get("approach_1_complexity"),
        approach_2_title=row.get("approach_2_title"),
        approach_2_code=row.get("approach_2_code"),
        approach_2_complexity=row.get("approach_2_complexity"),
        approach_3_title=row.get("approach_3_title"),
        approach_3_code=row.get("approach_3_code"),
        approach_3_complexity=row.get("approach_3_complexity"),
        challenges=row.get("challenges"),
        related_question_ids=list(row.get("related_question_ids") or []),
        updated_at=row.get("updated_at"),
    )