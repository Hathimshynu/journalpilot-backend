from datetime import datetime

from pydantic import BaseModel, Field


# ==================================================
# SECTION ANALYSIS
# ==================================================

class AnalysisSection(BaseModel):

    score: int = Field(
        ge=0,
        le=100,
    )

    feedback: str

    recommendations: list[str]


# ==================================================
# COMPLETE MANUSCRIPT ANALYSIS
# ==================================================

class ManuscriptAnalysisResult(BaseModel):

    overall_score: int = Field(
        ge=0,
        le=100,
    )

    summary: str

    article_type: str

    research_area: str

    keywords: list[str]

    structure: AnalysisSection

    abstract: AnalysisSection

    methodology: AnalysisSection

    results: AnalysisSection

    discussion: AnalysisSection

    language: AnalysisSection

    submission_readiness: list[str]

    critical_issues: list[str]

    improvement_priorities: list[str]


# ==================================================
# API RESPONSE
# ==================================================

class AnalysisResponse(BaseModel):

    id: int

    manuscript_id: int

    overall_score: int

    analysis: ManuscriptAnalysisResult

    created_at: datetime