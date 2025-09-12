from sqlalchemy.orm import declarative_base, Mapped, mapped_column
from sqlalchemy import Integer, String, JSON, Float, Boolean, DateTime, func

Base = declarative_base()

class ConveySearch(Base):
    __tablename__ = "convey_searches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    filename: Mapped[str] = mapped_column(String)
    council: Mapped[str] = mapped_column(String)
    extracted_json: Mapped[dict] = mapped_column(JSON)
    risk_json: Mapped[dict] = mapped_column(JSON)
    risk_score: Mapped[float] = mapped_column(Float, nullable=True)
    needs_review: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[str] = mapped_column(DateTime, server_default=func.now())
