"""Seed demo members into local DB and/or Supabase."""
from __future__ import annotations

import argparse
import hashlib
from datetime import datetime
import uuid

from sqlalchemy import create_engine, text

from app.core.config import DATABASE_URL


DEMO_MEMBERS = [
    {
        "real_name": "Alice Johnson",
        "username": "alice_demo",
        "email": "alice.demo@fiksi.local",
        "is_active": True,
        "subscription": "Pro",
        "bio": "Demo member for local and Supabase testing.",
        "avatar_url": None,
    },
    {
        "real_name": "Brian Smith",
        "username": "brian_demo",
        "email": "brian.demo@fiksi.local",
        "is_active": True,
        "subscription": "Free",
        "bio": "Second demo member account.",
        "avatar_url": None,
    },
    {
        "real_name": "Cynthia Lee",
        "username": "cynthia_demo",
        "email": "cynthia.demo@fiksi.local",
        "is_active": False,
        "subscription": "Free",
        "bio": "Inactive demo member for auth edge-case testing.",
        "avatar_url": None,
    },
]


def fake_hash_password(raw_password: str) -> str:
    return hashlib.sha256(raw_password.encode("utf-8")).hexdigest()


def build_local_engine():
    return create_engine(DATABASE_URL)


def seed_local() -> None:
    engine = build_local_engine()
    if engine.dialect.name == "sqlite":
        with engine.begin() as conn:
            conn.execute(
                text(
                    """
                    CREATE TABLE IF NOT EXISTS users (
                        id TEXT PRIMARY KEY,
                        real_name TEXT,
                        username TEXT UNIQUE NOT NULL,
                        email TEXT UNIQUE NOT NULL,
                        hashed_password TEXT NOT NULL,
                        is_active INTEGER NOT NULL DEFAULT 0,
                        subscription TEXT NOT NULL DEFAULT 'Free',
                        bio TEXT NOT NULL DEFAULT '',
                        avatar_url TEXT,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL
                    )
                    """
                )
            )
    elif engine.dialect.name == "postgresql":
        with engine.begin() as conn:
            conn.execute(
                text(
                    """
                    CREATE TABLE IF NOT EXISTS users (
                        id UUID PRIMARY KEY,
                        real_name VARCHAR(255),
                        username VARCHAR(50) UNIQUE NOT NULL,
                        email VARCHAR(255) UNIQUE NOT NULL,
                        hashed_password VARCHAR(255) NOT NULL,
                        is_active BOOLEAN NOT NULL DEFAULT FALSE,
                        subscription VARCHAR(50) NOT NULL DEFAULT 'Free',
                        bio TEXT NOT NULL DEFAULT '',
                        avatar_url VARCHAR(500),
                        created_at TIMESTAMP NOT NULL,
                        updated_at TIMESTAMP NOT NULL
                    )
                    """
                )
            )

    inserted = 0
    skipped = 0
    with engine.begin() as conn:
        for member in DEMO_MEMBERS:
            exists = conn.execute(
                text("SELECT 1 FROM users WHERE email = :email LIMIT 1"),
                {"email": member["email"]},
            ).first()

            if exists:
                skipped += 1
                continue

            conn.execute(
                text(
                    """
                    INSERT INTO users (
                        id, real_name, username, email, hashed_password, is_active,
                        subscription, bio, avatar_url, created_at, updated_at
                    ) VALUES (
                        :id, :real_name, :username, :email, :hashed_password, :is_active,
                        :subscription, :bio, :avatar_url, :created_at, :updated_at
                    )
                    """
                ),
                {
                    "id": str(uuid.uuid4()),
                    "real_name": member["real_name"],
                    "username": member["username"],
                    "email": member["email"],
                    "hashed_password": fake_hash_password("demo12345"),
                    "is_active": 1 if member["is_active"] else 0,
                    "subscription": member["subscription"],
                    "bio": member["bio"],
                    "avatar_url": member["avatar_url"],
                    "created_at": datetime.utcnow().isoformat(),
                    "updated_at": datetime.utcnow().isoformat(),
                },
            )
            inserted += 1

    print(f"[local] inserted={inserted}, skipped={skipped}")


def seed_supabase() -> None:
    from app.db.session import supabase

    # Read current users to avoid duplicate insert attempts.
    query = supabase.table("users").select("email").in_(
        "email", [member["email"] for member in DEMO_MEMBERS]
    )
    existing_resp = query.execute()
    existing_emails = {row["email"] for row in (existing_resp.data or [])}

    rows_to_insert = []
    for member in DEMO_MEMBERS:
        if member["email"] in existing_emails:
            continue
        rows_to_insert.append(
            {
                **member,
                "hashed_password": fake_hash_password("demo12345"),
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
            }
        )

    if not rows_to_insert:
        print(f"[supabase] inserted=0, skipped={len(DEMO_MEMBERS)}")
        return

    supabase.table("users").insert(rows_to_insert).execute()
    print(f"[supabase] inserted={len(rows_to_insert)}, skipped={len(DEMO_MEMBERS) - len(rows_to_insert)}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Seed demo members into local DB and/or Supabase."
    )
    parser.add_argument(
        "--target",
        choices=["local", "supabase", "both"],
        default="both",
        help="Where to seed demo members.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if args.target in {"local", "both"}:
        seed_local()

    if args.target in {"supabase", "both"}:
        seed_supabase()


if __name__ == "__main__":
    main()
