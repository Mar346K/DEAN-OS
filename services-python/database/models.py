import datetime
import uuid
from typing import List, Optional
from sqlalchemy import String, Text, Float, DateTime, ForeignKey, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase):
    """The root class for all database tables."""
    pass

class SwarmRun(Base):
    """Tracks a top-level user request from start to finish."""
    __tablename__ = "swarm_runs"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    prompt: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(50), default="INITIATING") # INITIATING, RUNNING, COMPLETED, FAILED

    # Timing
    created_at: Mapped[datetime.datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime.datetime] = mapped_column(onupdate=func.now(), nullable=True)

    # Relationships
    traces: Mapped[List["TaskTrace"]] = relationship(back_populates="run", cascade="all, delete-orphan")
    ledger_entries: Mapped[List["ValkyrieLedger"]] = relationship(back_populates="run")

class TaskTrace(Base):
    """Tracks a specific 'hop' or action taken by an AI Agent."""
    __tablename__ = "task_traces"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    run_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("swarm_runs.id"))

    # Metadata from the TelemetryEngine
    trace_id: Mapped[str] = mapped_column(String(8)) # The 8-char trace ID
    agent_name: Mapped[str] = mapped_column(String(100))
    action: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(50)) # running, success, error
    logs: Mapped[Optional[str]] = mapped_column(Text, nullable=True) # Full stack traces or raw AI thoughts

    timestamp: Mapped[datetime.datetime] = mapped_column(server_default=func.now())

    # Relationships
    run: Mapped["SwarmRun"] = relationship(back_populates="traces")

class ValkyrieLedger(Base):
    """The FinOps record of token usage and financial cost."""
    __tablename__ = "valkyrie_ledger"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    run_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("swarm_runs.id"))
    trace_id: Mapped[str] = mapped_column(String(8))

    tokens_used: Mapped[int] = mapped_column(default=0)
    cost_usd: Mapped[float] = mapped_column(Float, default=0.0)

    timestamp: Mapped[datetime.datetime] = mapped_column(server_default=func.now())

    # Relationships
    run: Mapped["SwarmRun"] = relationship(back_populates="ledger_entries")
