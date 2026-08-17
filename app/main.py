from __future__ import annotations

import os
from collections.abc import AsyncIterator, Generator
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Literal

from fastapi import Depends, FastAPI, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from app.domain.booking import InvalidBookingInterval, occupied_interval
from app.infra.database import build_engine, build_session_factory, session_scope
from app.infra.models import Base, Booking, Resource

BookingStatus = Literal["pending_payment", "confirmed", "cancelled", "completed"]


class ResourceCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)


class ResourceRead(BaseModel):
    id: int
    name: str


class BookingCreate(BaseModel):
    resource_id: int = Field(gt=0)
    starts_at: datetime
    ends_at: datetime
    buffer_before_min: int = Field(default=0, ge=0, le=240)
    buffer_after_min: int = Field(default=0, ge=0, le=240)
    status: BookingStatus = "pending_payment"


class BookingRead(BaseModel):
    id: int
    resource_id: int
    starts_at: datetime
    ends_at: datetime
    occupied_start: datetime
    occupied_end: datetime
    status: BookingStatus


def create_app(database_url: str | None = None) -> FastAPI:
    default_url = "postgresql+psycopg://booking:booking@localhost:5432/booking"
    resolved_url = database_url or os.getenv("DATABASE_URL") or default_url
    engine = build_engine(resolved_url)
    factory = build_session_factory(engine)

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        if engine.dialect.name == "sqlite":
            Base.metadata.create_all(engine)
        yield

    app = FastAPI(title="Booking Rules Demo", version="0.1.0", lifespan=lifespan)
    app.state.engine = engine
    app.state.session_factory = factory

    def get_session(request: Request) -> Generator[Session, None, None]:
        request_factory: sessionmaker[Session] = request.app.state.session_factory
        yield from session_scope(request_factory)

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/resources", response_model=ResourceRead, status_code=status.HTTP_201_CREATED)
    def create_resource(
        payload: ResourceCreate,
        session: Session = Depends(get_session),
    ) -> Resource:
        resource = Resource(name=payload.name)
        session.add(resource)
        try:
            session.commit()
        except IntegrityError as error:
            session.rollback()
            raise HTTPException(status_code=409, detail="Resource name already exists") from error
        session.refresh(resource)
        return resource

    @app.post("/bookings", response_model=BookingRead, status_code=status.HTTP_201_CREATED)
    def create_booking(payload: BookingCreate, session: Session = Depends(get_session)) -> Booking:
        resource = session.scalar(select(Resource).where(Resource.id == payload.resource_id))
        if resource is None:
            raise HTTPException(status_code=404, detail="Resource not found")

        try:
            interval = occupied_interval(
                payload.starts_at,
                payload.ends_at,
                payload.buffer_before_min,
                payload.buffer_after_min,
            )
        except InvalidBookingInterval as error:
            raise HTTPException(status_code=422, detail=str(error)) from error

        booking = Booking(
            resource_id=payload.resource_id,
            starts_at=payload.starts_at,
            ends_at=payload.ends_at,
            occupied_start=interval.start,
            occupied_end=interval.end,
            status=payload.status,
        )
        session.add(booking)
        try:
            session.commit()
        except IntegrityError as error:
            session.rollback()
            raise HTTPException(
                status_code=409,
                detail="This active booking overlaps an existing occupied interval",
            ) from error
        session.refresh(booking)
        return booking

    return app


app = create_app()
