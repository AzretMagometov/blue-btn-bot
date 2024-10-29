from datetime import datetime
from typing import Set

from sqlalchemy import BigInteger, String, Boolean, ForeignKey, DateTime, func, Index
from sqlalchemy.orm import DeclarativeBase, mapped_column, relationship, Mapped


class Base(DeclarativeBase):
    created: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=func.now(),
        server_default=func.now()
    )
    updated: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=func.now(),
        server_default=func.now(),
        onupdate=func.now()
    )


class User(Base):
    __tablename__ = "user"

    id: Mapped[int] = mapped_column(
        autoincrement=True,
        primary_key=True,
        nullable=False
    )
    tg_id: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        unique=True,
        index=True
    )
    tg_name: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        default=''
    )
    is_blocked: Mapped[bool] = mapped_column(
        Boolean,
        default=False
    )

    chats: Mapped[Set["Chat"]] = relationship(
        "Chat",
        back_populates="user",
        lazy="selectin"
    )


class Chat(Base):
    __tablename__ = "chat"

    id: Mapped[int] = mapped_column(
        autoincrement=True,
        primary_key=True,
        nullable=False
    )
    tg_id: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        index=True
    )
    tg_name: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        default=''
    )
    fk_user_id: Mapped[int] = mapped_column(
        ForeignKey("user.id"),
        nullable=False,
        index=True
    )

    user: Mapped['User'] = relationship(
        "User",
        back_populates="chats"
    )
    __table_args__ = (
        Index('ix_chat_tg_id', 'tg_id'),
        Index('ix_chat_fk_user_id', 'fk_user_id'),
    )
