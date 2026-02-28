-- ============================================================
-- FIKSI Database Schema Reference
-- Generated: 2026-02-28
-- ============================================================
-- This file documents the full database schema.
-- Tables are created by SQLAlchemy (app/db/init_db.py).
-- ============================================================

-- ┌─────────────────────────────────────────────────────────┐
-- │  EXISTING TABLES                                         │
-- └─────────────────────────────────────────────────────────┘

CREATE TABLE IF NOT EXISTS users (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    real_name       VARCHAR(255),
    username        VARCHAR(50) UNIQUE NOT NULL,
    email           VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    is_active       BOOLEAN NOT NULL DEFAULT FALSE,
    subscription    VARCHAR(50) NOT NULL DEFAULT 'Free',
    bio             TEXT NOT NULL DEFAULT '',
    avatar_url      VARCHAR(500),
    created_at      TIMESTAMP NOT NULL DEFAULT now(),
    updated_at      TIMESTAMP NOT NULL DEFAULT now(),
    -- Gamification (global rollups)
    xp_total        INTEGER NOT NULL DEFAULT 0,
    xp_current      INTEGER NOT NULL DEFAULT 0,
    level           INTEGER NOT NULL DEFAULT 1,
    reputation      INTEGER NOT NULL DEFAULT 0,
    cp_total        INTEGER NOT NULL DEFAULT 0  -- Challenge Points (global)
);

CREATE TABLE IF NOT EXISTS categories (
    -- Used for POST topics (not academic subjects)
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name        VARCHAR(100) UNIQUE NOT NULL,
    slug        VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    icon        VARCHAR(50),
    created_at  TIMESTAMP NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS posts (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    author_id    UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    category_id  UUID REFERENCES categories(id) ON DELETE SET NULL,
    title        VARCHAR(500) NOT NULL,
    content      TEXT NOT NULL,
    image_url    VARCHAR(500),
    is_published BOOLEAN NOT NULL DEFAULT FALSE,
    excerpt      TEXT,
    created_at   TIMESTAMP NOT NULL DEFAULT now(),
    updated_at   TIMESTAMP NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS comments (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    post_id     UUID NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
    author_id   UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    content     TEXT NOT NULL,
    is_accepted BOOLEAN NOT NULL DEFAULT FALSE,
    created_at  TIMESTAMP NOT NULL DEFAULT now(),
    updated_at  TIMESTAMP NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS upvotes (
    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id    UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    post_id    UUID REFERENCES posts(id) ON DELETE CASCADE,
    comment_id UUID REFERENCES comments(id) ON DELETE CASCADE,
    created_at TIMESTAMP NOT NULL DEFAULT now(),
    CONSTRAINT unique_post_upvote UNIQUE (user_id, post_id),
    CONSTRAINT uq_upvote_user_comment UNIQUE (user_id, comment_id),
    CONSTRAINT ck_upvotes_exactly_one_target CHECK (
        (post_id IS NOT NULL AND comment_id IS NULL) OR
        (post_id IS NULL AND comment_id IS NOT NULL)
    )
);

CREATE TABLE IF NOT EXISTS quizzes (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    author_id           UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title               VARCHAR(500) NOT NULL,
    description         TEXT,
    is_public           BOOLEAN NOT NULL DEFAULT FALSE,
    started_at          TIMESTAMP NOT NULL DEFAULT now(),
    finished_at         TIMESTAMP,
    time_used_seconds   INTEGER,
    passing_score       INTEGER NOT NULL DEFAULT 70,
    attempts_allowed    INTEGER NOT NULL DEFAULT -1,
    show_answers        BOOLEAN NOT NULL DEFAULT TRUE,
    randomize_questions BOOLEAN NOT NULL DEFAULT FALSE,
    created_at          TIMESTAMP NOT NULL DEFAULT now(),
    updated_at          TIMESTAMP NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS admins (
    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id    UUID UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role       VARCHAR(50) NOT NULL DEFAULT 'moderator',
    created_at TIMESTAMP NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS friendships (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    requester_id  UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    addressee_id  UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    status        VARCHAR(20) NOT NULL DEFAULT 'pending',
    created_at    TIMESTAMP NOT NULL DEFAULT now(),
    updated_at    TIMESTAMP NOT NULL DEFAULT now(),
    CONSTRAINT unique_friendship UNIQUE (requester_id, addressee_id)
);

CREATE TABLE IF NOT EXISTS assets (
    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    post_id    UUID NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
    file_url   VARCHAR NOT NULL,
    media_type VARCHAR NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT now()
);


-- ┌─────────────────────────────────────────────────────────┐
-- │  NEW TABLES — Multi-Subject Rank System                  │
-- └─────────────────────────────────────────────────────────┘

-- Academic categories group subjects (Science, Social, etc.)
CREATE TABLE IF NOT EXISTS academic_categories (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name        VARCHAR(100) UNIQUE NOT NULL,
    slug        VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    icon        VARCHAR(50),
    created_at  TIMESTAMP NOT NULL DEFAULT now()
);

-- Individual school subjects (Matematika, Fisika, etc.)
CREATE TABLE IF NOT EXISTS subjects (
    id                   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    academic_category_id UUID NOT NULL REFERENCES academic_categories(id) ON DELETE CASCADE,
    name                 VARCHAR(100) UNIQUE NOT NULL,
    slug                 VARCHAR(100) UNIQUE NOT NULL,
    icon                 VARCHAR(50),
    created_at           TIMESTAMP NOT NULL DEFAULT now()
);

-- Rank ladder per subject (Bronze → Diamond)
-- Allows future custom themes per subject
CREATE TABLE IF NOT EXISTS subject_ranks (
    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    subject_id UUID NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,
    tier       INTEGER NOT NULL,
    name       VARCHAR(50) NOT NULL,
    icon       VARCHAR(50) NOT NULL,
    min_rp     INTEGER NOT NULL DEFAULT 0,
    CONSTRAINT uq_subject_rank_tier UNIQUE (subject_id, tier)
);

-- Per-user, per-subject XP / level / rank progress
-- CP stays global on users table; RP drives per-subject rank
CREATE TABLE IF NOT EXISTS user_subject_progress (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    subject_id  UUID NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,
    xp_total    INTEGER NOT NULL DEFAULT 0,
    xp_current  INTEGER NOT NULL DEFAULT 0,
    level       INTEGER NOT NULL DEFAULT 1,
    rank_points INTEGER NOT NULL DEFAULT 0,
    updated_at  TIMESTAMP NOT NULL DEFAULT now(),
    CONSTRAINT uq_user_subject UNIQUE (user_id, subject_id)
);
