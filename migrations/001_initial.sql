-- PostgreSQL-only schema for the conflict-safe runtime.
-- The API keeps the occupied interval explicit so the constraint remains easy to inspect.

CREATE EXTENSION IF NOT EXISTS btree_gist;

CREATE TABLE IF NOT EXISTS resources (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(120) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS bookings (
    id BIGSERIAL PRIMARY KEY,
    resource_id BIGINT NOT NULL REFERENCES resources(id),
    starts_at TIMESTAMPTZ NOT NULL,
    ends_at TIMESTAMPTZ NOT NULL,
    occupied_start TIMESTAMPTZ NOT NULL,
    occupied_end TIMESTAMPTZ NOT NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'pending_payment',
    CHECK (ends_at > starts_at),
    CHECK (occupied_end > occupied_start),
    CHECK (status IN ('pending_payment', 'confirmed', 'cancelled', 'completed')),
    CONSTRAINT bookings_no_overlap_resource
        EXCLUDE USING gist (
            resource_id WITH =,
            tstzrange(occupied_start, occupied_end, '[)') WITH &&
        )
        WHERE (status IN ('pending_payment', 'confirmed'))
);
