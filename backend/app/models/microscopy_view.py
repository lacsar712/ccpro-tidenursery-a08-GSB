from datetime import datetime

from sqlalchemy import String, Integer, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class MicroscopyView(Base):
    __tablename__ = "microscopy_views"
    __table_args__ = (
        UniqueConstraint("batch_id", "view_no", name="uq_batch_view_no"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    batch_id: Mapped[int] = mapped_column(
        ForeignKey("microscopy_batches.id"), nullable=False, index=True
    )
    view_no: Mapped[int] = mapped_column(Integer, nullable=False)
    floc_density: Mapped[str] = mapped_column(String(8), nullable=False)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    batch: Mapped["MicroscopyBatch"] = relationship("MicroscopyBatch", back_populates="views")
