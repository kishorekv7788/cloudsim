-- PostgreSQL schema (Stage 1). Run: psql -d cloudsim -f schema.sql
CREATE TABLE users (
    id          BIGSERIAL PRIMARY KEY,
    name        TEXT NOT NULL,
    role        TEXT NOT NULL CHECK (role IN ('student', 'trainer', 'admin')),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE modules (
    id                  BIGSERIAL PRIMARY KEY,
    certification_code  TEXT NOT NULL UNIQUE,      -- e.g. 'AZ-900'
    title               TEXT NOT NULL,
    level               TEXT NOT NULL,             -- fundamentals | associate | expert | specialty | extras
    phase               INT  NOT NULL              -- roadmap phase 1..5
);

CREATE TABLE lessons (
    id          BIGSERIAL PRIMARY KEY,
    module_id   BIGINT NOT NULL REFERENCES modules(id),
    position    INT NOT NULL,
    title       TEXT NOT NULL,
    content     TEXT NOT NULL
);

CREATE TABLE quizzes (
    id          BIGSERIAL PRIMARY KEY,
    module_id   BIGINT NOT NULL REFERENCES modules(id),
    questions   JSONB NOT NULL                     -- same shape as app/quiz.py
);

CREATE TABLE quiz_results (
    id          BIGSERIAL PRIMARY KEY,
    user_id     BIGINT NOT NULL REFERENCES users(id),
    quiz_id     BIGINT NOT NULL REFERENCES quizzes(id),
    score       INT NOT NULL,
    taken_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE labs (
    id          TEXT PRIMARY KEY,                  -- e.g. 'az900-lab02'
    module_id   BIGINT REFERENCES modules(id),
    provider    TEXT NOT NULL,
    title       TEXT NOT NULL,
    difficulty  TEXT NOT NULL,
    definition  JSONB NOT NULL                     -- the lab JSON file
);

CREATE TABLE lab_configs (
    id          BIGSERIAL PRIMARY KEY,
    lab_id      TEXT NOT NULL REFERENCES labs(id),
    user_id     BIGINT NOT NULL REFERENCES users(id),
    topology    JSONB NOT NULL,
    version     INT NOT NULL DEFAULT 1,
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE lab_progress (
    id            BIGSERIAL PRIMARY KEY,
    user_id       BIGINT NOT NULL REFERENCES users(id),
    lab_id        TEXT NOT NULL REFERENCES labs(id),
    status        TEXT NOT NULL DEFAULT 'not_started'
                  CHECK (status IN ('not_started', 'in_progress', 'completed')),
    attempts      INT NOT NULL DEFAULT 0,
    completed_at  TIMESTAMPTZ,
    UNIQUE (user_id, lab_id)
);

CREATE TABLE validation_logs (
    id             BIGSERIAL PRIMARY KEY,
    lab_config_id  BIGINT REFERENCES lab_configs(id),
    rule           TEXT NOT NULL,
    result         TEXT NOT NULL,
    message        TEXT,
    latency_ms     INT
);
