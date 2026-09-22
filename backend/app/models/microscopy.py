from datetime import date, datetime
from typing import List, Optional

from sqlalchemy import String, Integer, ForeignKey, Date, DateTime, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class MicroscopyBatch(Base):
    """生物絮团镜检批次：挂塘口，开检日按东八区，同塘开检日唯一。"""

    __tablename__ = "microscopy_batches"
    __table_args__ = (
        UniqueConstraint("pond_id", "opened_on", name="uq_microscopy_pond_opened_on"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    pond_id: Mapped[int] = mapped_column(ForeignKey("ponds.id"), nullable=False, index=True)
    opened_on: Mapped[date] = mapped_column(Date, nullable=False)
    closed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    chief_inspector: Mapped[str] = mapped_column(String(64), nullable=False)

    pond: Mapped["Pond"] = relationship("Pond", back_populates="microscopy_batches")
    fields: Mapped[List["MicroscopyField"]] = relationship(
        "MicroscopyField",
        back_populates="batch",
        cascade="all, delete-orphan",
        order_by="MicroscopyField.view_seq",
    )


class MicroscopyField(Base):
    """镜检视野条目：未封批次内视野序号唯一（封检后禁止追加，故批次内全局唯一即可）。"""

    __tablename__ = "microscopy_fields"
    __table_args__ = (
        UniqueConstraint("batch_id", "view_seq", name="uq_microscopy_batch_view_seq"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    batch_id: Mapped[int] = mapped_column(
        ForeignKey("microscopy_batches.id"), nullable=False, index=True
    )
    view_seq: Mapped[int] = mapped_column(Integer, nullable=False)
    density: Mapped[str] = mapped_column(String(8), nullable=False)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    batch: Mapped["MicroscopyBatch"] = relationship("MicroscopyBatch", back_populates="fields")
