from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import ForeignKey, Index, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, relationship
from sqlalchemy.testing.schema import mapped_column

from app.core.database import Base

if TYPE_CHECKING:
    from app.auth.models import User
    from app.game_renders.models import GameRender


class Leaderboard(Base):
    __tablename__ = "leaderboard"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    game_name: Mapped[str] = mapped_column(String(50), nullable=False)
    score: Mapped[int] = mapped_column(Integer, nullable=False)
    steps_count: Mapped[int] = mapped_column(Integer, nullable=True)
    render_id: Mapped[UUID] = mapped_column(
        ForeignKey("game_renders.id", ondelete="SET NULL")
    )
    seed: Mapped[int] = mapped_column(Integer, nullable=False)
    season_id: Mapped[int] = mapped_column(Integer, nullable=False)

    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    user: Mapped["User"] = relationship("User")
    render: Mapped["GameRender"] = relationship("GameRender")

    __table_args__ = (
        UniqueConstraint("user_id", "render_id", name="uq_user_render"),
        Index(
            "idx_leaderboard_game_name_score_created",
            "game_name",
            "seed",
            "season_id",
            score.desc(),
            steps_count.desc(),
            created_at.desc(),
        ),
        Index("idx_leaderboard_render_id", "render_id"),
    )
