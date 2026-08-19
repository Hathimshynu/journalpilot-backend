from datetime import datetime

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    Text,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from app.core.database import Base


class ManuscriptAnalysis(Base):

    __tablename__ = "manuscript_analyses"


    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )


    manuscript_id: Mapped[int] = mapped_column(
        ForeignKey(
            "manuscripts.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        unique=True,
        index=True,
    )


    overall_score: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )


    analysis_json: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )


    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
    )


    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )


    manuscript = relationship(
        "Manuscript",
        back_populates="analysis",
    )