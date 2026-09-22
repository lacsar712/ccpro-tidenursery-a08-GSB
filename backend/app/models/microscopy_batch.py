from datetime import date, datetime
from typing import List, Optional

from sqlalchemy import String, Integer, ForeignKey, Date, DateTime, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class MicroscopyBatch(Base):
    __tablename__ = "microscopy_batches"
    __table_args__ = (
        UniqueConstraint("pond_id", "inspected_on", name="uq_pond_inspected_on"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    pond_id: Mapped[int] = mapped_column(ForeignKey("ponds.id"), nullable=False, index=True)
    inspected_on: Mapped[date] = mapped_column(Date, nullable=False)
    sealed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    chief_inspector: Mapped[str] = mapped_column(String(64), nullable=False)

    pond: Mapped["Pond"] = relationship("Pond", back_populates="microscopy_batches")
    views: Mapped[List["MicroscopyView"]] = relationship(
        "MicroscopyView",
        back_populates="batch",
        cascade="all, delete-orphan",
        order_by="MicroscopyView.view_no",
    )
