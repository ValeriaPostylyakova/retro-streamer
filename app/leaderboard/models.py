from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import ForeignKey, Index, Integer, String, func
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
    scope: Mapped[int] = mapped_column(Integer, nullable=False)
    render_id: Mapped[UUID] = mapped_column(
        ForeignKey("game_renders.id", ondelete="SET NULL")
    )

    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    user: Mapped["User"] = relationship("User")
    render: Mapped["GameRender"] = relationship("GameRender")

    __table_args__ = (
        Index(
            "idx_leaderboard_game_name_scope_created",
            "game_name",
            scope.desc(),
            created_at.desc(),
        ),
        Index("idx_leaderboard_render_id", "render_id"),
    )
