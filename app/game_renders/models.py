import uuid
from datetime import datetime
from uuid import UUID

from sqlalchemy import Index, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class GameRender(Base):
    __tablename__ = "game_renders"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid.uuid4)

    game_name: Mapped[str] = mapped_column(String(50), nullable=False)
    seed: Mapped[int] = mapped_column(Integer, nullable=False)
    season_id: Mapped[int] = mapped_column(Integer, nullable=False)
    commands_hash: Mapped[str] = mapped_column(String(32), nullable=False)
    s3_key: Mapped[str] = mapped_column(String(512), nullable=False)
    score: Mapped[int] = mapped_column(Integer, nullable=False)
    steps_count: Mapped[int] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    __table_args__ = (Index("idx_game_renders_seed_season", "seed", "season_id"),)
