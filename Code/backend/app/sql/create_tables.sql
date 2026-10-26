
CREATE TABLE IF NOT EXISTS researches (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    user_id BIGINT NOT NULL
        REFERENCES users(id)
        ON DELETE CASCADE,

    question TEXT NOT NULL,

    status VARCHAR(30) NOT NULL DEFAULT 'pending'
        CHECK (
            status IN (
                'pending',
                'in_progress',
                'completed',
                'failed'
            )
        ),

    result JSONB,

    error_message TEXT,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    completed_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_researches_user_id
    ON researches(user_id);

CREATE INDEX IF NOT EXISTS idx_researches_status
    ON researches(status);

CREATE INDEX IF NOT EXISTS idx_researches_created_at
    ON researches(created_at DESC);

CREATE TABLE IF NOT EXISTS users(
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
    );   

CREATE TABLE IF NOT EXISTS research_sources (
    id BIGSERIAL PRIMARY KEY,
    research_id BIGINT NOT NULL REFERENCES researches(id) ON DELETE CASCADE,
    title TEXT,
    url TEXT NOT NULL,
    content TEXT,
    score DOUBLE PRECISION,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );
CREATE INDEX IF NOT EXISTS idx_research_sources_research_id
ON research_sources(research_id);