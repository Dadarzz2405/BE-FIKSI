"""
Complete database setup script with FULL RESET.
This script performs a clean database initialization:
1. DROP all existing tables (clean slate)
2. CREATE all tables fresh
3. Seed users/posts + academic categories/subjects/ranks
"""

import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from sqlalchemy.orm import Session

# Add the parent directory to the path so imports work
sys.path.insert(0, str(Path(__file__).parent))

from app.core.config import SERVICE_ROLE_KEY, SUPABASE_URL
from app.db.base import Base
from app.db.session import SessionLocal, engine
from app.models.academic_category import AcademicCategory
from app.models.admin import Admin
from app.models.assets import Asset
from app.models.friendship import Friendship
from app.models.post import Post
from app.models.quiz import Quiz
from app.models.subject import Subject
from app.models.subject_rank import SubjectRank
from app.models.user import User
from app.models.user_subject_progress import UserSubjectProgress
from supabase import create_client

# ── Subject/Rank seed data ───────────────────────────────────────────────────

CATEGORIES = [
    {"name": "Science", "slug": "science", "icon": "🔬", "description": "Ilmu Pengetahuan Alam (IPA)"},
    {"name": "Social", "slug": "social", "icon": "🌍", "description": "Ilmu Pengetahuan Sosial (IPS)"},
    {"name": "Language", "slug": "language", "icon": "📖", "description": "Bahasa dan Sastra"},
    {"name": "Technology", "slug": "technology", "icon": "💻", "description": "Teknologi Informasi"},
    {"name": "Civic & Character", "slug": "civic-character", "icon": "🇮🇩", "description": "Pendidikan Kewarganegaraan dan Karakter"},
]

SUBJECTS = {
    "science": [
        ("Matematika", "matematika", "📐"),
        ("Fisika", "fisika", "⚛️"),
        ("Kimia", "kimia", "🧪"),
        ("Biologi", "biologi", "🧬"),
    ],
    "social": [
        ("Ekonomi", "ekonomi", "📊"),
        ("Geografi", "geografi", "🗺️"),
        ("Sosiologi", "sosiologi", "👥"),
        ("Sejarah", "sejarah", "📜"),
    ],
    "language": [
        ("Bahasa Indonesia", "bahasa-indonesia", "🇮🇩"),
        ("Bahasa Inggris", "bahasa-inggris", "🇬🇧"),
    ],
    "technology": [
        ("Informatika", "informatika", "🖥️"),
    ],
    "civic-character": [
        ("PPKn", "ppkn", "⚖️"),
    ],
}

DEFAULT_RANKS = [
    (1, "Bronze", "🥉", 0),
    (2, "Silver", "🥈", 100),
    (3, "Gold", "🥇", 500),
    (4, "Platinum", "⚡", 1500),
    (5, "Diamond", "💎", 5000),
]


# ── Core setup helpers ───────────────────────────────────────────────────────

def reset_database() -> None:
    """Drop all existing tables for a clean database reset."""
    print("\n" + "=" * 70)
    print("🗑️  RESETTING DATABASE (Dropping all tables)")
    print("=" * 70 + "\n")

    try:
        Base.metadata.drop_all(bind=engine)
        print("✓ All existing tables dropped successfully")
        engine.dispose()
        print("✓ Database connections cleared\n")
    except Exception as e:
        print(f"⚠️  Note: {e}")
        print("(This is OK if tables didn't exist yet)\n")


def create_tables() -> None:
    """Create all database tables from model definitions."""
    print("=" * 70)
    print("📊 CREATING DATABASE TABLES")
    print("=" * 70 + "\n")

    try:
        Base.metadata.create_all(bind=engine)
        print("✓ All tables created successfully:")
        for table in Base.metadata.sorted_tables:
            print(f"  • {table.name}")
        print()
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        raise


# ── Supabase + user/post seed helpers ────────────────────────────────────────

def _bucket_name(bucket) -> str:
    """Support supabase-py returning bucket dicts or typed objects."""
    if isinstance(bucket, dict):
        return str(bucket.get("name", ""))
    return str(getattr(bucket, "name", ""))


def _provision_supabase_auth_user(
    supabase_client,
    email: str,
    password: str,
) -> tuple[Optional[str], bool]:
    """Create/update a Supabase Auth user for seeded test credentials."""
    try:
        response = supabase_client.auth.admin.create_user(
            {
                "email": email,
                "password": password,
                "email_confirm": True,
            }
        )
        auth_user = getattr(response, "user", None)
        if auth_user and getattr(auth_user, "id", None):
            return str(auth_user.id), True
    except Exception as e:
        print(f"⚠️  Could not create Supabase Auth user for {email}: {e}")
    return None, False


def upload_image_to_supabase(image_path: str, bucket_name: str = "post-images") -> str:
    """Upload image to Supabase Storage and return public URL."""
    print("\n📤 Uploading image to Supabase Storage...")

    if not SUPABASE_URL or not SERVICE_ROLE_KEY:
        print("⚠️  Supabase credentials not found!")
        print("Set SUPABASE_URL and SERVICE_ROLE_KEY in your environment variables.")
        print("Using placeholder URL instead...")
        return "https://i.ibb.co.com/Kx9bs0zv/Garuda-Icon-Featuring-Networked-Wings-and-Typography-2.png"

    try:
        print("🔑 Using service role key for admin access...")
        supabase = create_client(SUPABASE_URL, SERVICE_ROLE_KEY)

        if not os.path.exists(image_path):
            print(f"❌ Image file not found: {image_path}")
            return "https://i.ibb.co.com/Kx9bs0zv/Garuda-Icon-Featuring-Networked-Wings-and-Typography-2.png"

        with open(image_path, "rb") as f:
            image_data = f.read()

        file_name = "garuda_icon.png"

        try:
            buckets = supabase.storage.list_buckets()
            bucket_exists = any(_bucket_name(b) == bucket_name for b in (buckets or []))

            if not bucket_exists:
                print(f"📦 Creating bucket '{bucket_name}'...")
                supabase.storage.create_bucket(bucket_name, options={"public": True})
                print(f"✓ Bucket '{bucket_name}' created")
            else:
                print(f"✓ Bucket '{bucket_name}' already exists")
        except Exception as e:
            print(f"⚠️  Could not create/check bucket: {e}")
            print("Make sure you have the right permissions.")

        print(f"⬆️  Uploading {file_name}...")

        try:
            supabase.storage.from_(bucket_name).remove([file_name])
        except Exception:
            pass

        supabase.storage.from_(bucket_name).upload(
            file_name,
            image_data,
            file_options={"content-type": "image/png"},
        )

        public_url = supabase.storage.from_(bucket_name).get_public_url(file_name)

        print("✅ Image uploaded successfully!")
        print(f"📍 URL: {public_url}")
        return public_url

    except Exception as e:
        print(f"❌ Error uploading image: {e}")
        print("Using placeholder URL instead...")
        return "https://i.ibb.co.com/Kx9bs0zv/Garuda-Icon-Featuring-Networked-Wings-and-Typography-2.png"


def create_mock_users(db: Session) -> tuple[list[User], int]:
    """Create mock user accounts for testing."""
    print("\n👥 Creating mock users...")

    users_data = [
        {
            "username": "admin_nusa",
            "email": "admin@nusaconex.com",
            "plain_password": "password123",
            "real_name": "Admin Nusa CoNEX",
            "hashed_password": "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYzNb8Ow1u2",
            "is_active": True,
            "subscription": "Pro",
            "bio": "Official admin account for Nusa CoNEX platform.",
            "avatar_url": "https://api.dicebear.com/7.x/avataaars/svg?seed=admin",
        },
        {
            "username": "test_user1",
            "email": "user1@example.com",
            "plain_password": "password123",
            "real_name": "Test User One",
            "hashed_password": "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYzNb8Ow1u2",
            "is_active": True,
            "subscription": "Free",
            "bio": "Just testing out the platform!",
            "avatar_url": "https://api.dicebear.com/7.x/avataaars/svg?seed=user1",
        },
        {
            "username": "test_user2",
            "email": "user2@example.com",
            "plain_password": "password123",
            "real_name": "Test User Two",
            "hashed_password": "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYzNb8Ow1u2",
            "is_active": True,
            "subscription": "Free",
            "bio": "Another test user account.",
            "avatar_url": "https://api.dicebear.com/7.x/avataaars/svg?seed=user2",
        },
    ]

    users: list[User] = []
    login_ready_count = 0
    supabase_admin = None

    if SUPABASE_URL and SERVICE_ROLE_KEY:
        try:
            supabase_admin = create_client(SUPABASE_URL, SERVICE_ROLE_KEY)
            print("🔑 Supabase Auth sync enabled for seeded users")
        except Exception as e:
            print(f"⚠️  Supabase Auth sync disabled: {e}")

    for user_data in users_data:
        user_payload = dict(user_data)
        seed_password = user_payload.pop("plain_password")

        if supabase_admin:
            auth_user_id, is_login_ready = _provision_supabase_auth_user(
                supabase_admin,
                email=user_payload["email"],
                password=seed_password,
            )
            if auth_user_id:
                user_payload["id"] = auth_user_id
                user_payload["hashed_password"] = ""
            if is_login_ready:
                login_ready_count += 1

        user = User(**user_payload)
        db.add(user)
        users.append(user)

    db.commit()
    for user in users:
        db.refresh(user)

    print(f"✓ Created {len(users)} users")
    if supabase_admin:
        print(f"✓ {login_ready_count}/{len(users)} users are ready for /auth/login")
    else:
        print("⚠️  Seeded users were created in DB only (not Supabase Auth login-ready).")
    return users, login_ready_count


# ── Subject/Rank seeding ─────────────────────────────────────────────────────

def seed_subjects(db: Session) -> None:
    """Create academic categories, subjects, and rank ladders."""
    print("\n" + "=" * 60)
    print("📚 SEEDING ACADEMIC CATEGORIES & SUBJECTS")
    print("=" * 60)

    cat_map: dict[str, AcademicCategory] = {}
    for cat_data in CATEGORIES:
        existing = db.query(AcademicCategory).filter(
            AcademicCategory.slug == cat_data["slug"]
        ).first()
        if existing:
            cat_map[cat_data["slug"]] = existing
            print(f"  ✓ Category '{cat_data['name']}' already exists")
        else:
            cat = AcademicCategory(**cat_data)
            db.add(cat)
            db.flush()
            cat_map[cat_data["slug"]] = cat
            print(f"  ✓ Created category '{cat_data['name']}'")

    for cat_slug, subjects in SUBJECTS.items():
        category = cat_map[cat_slug]
        for name, slug, icon in subjects:
            existing = db.query(Subject).filter(Subject.slug == slug).first()
            if existing:
                print(f"  ✓ Subject '{name}' already exists")
                subject_obj = existing
            else:
                subject_obj = Subject(
                    academic_category_id=category.id,
                    name=name,
                    slug=slug,
                    icon=icon,
                )
                db.add(subject_obj)
                db.flush()
                print(f"  ✓ Created subject '{name}' → {category.name}")

            existing_ranks = db.query(SubjectRank).filter(
                SubjectRank.subject_id == subject_obj.id
            ).count()
            if existing_ranks == 0:
                for tier, rank_name, rank_icon, min_rp in DEFAULT_RANKS:
                    db.add(
                        SubjectRank(
                            subject_id=subject_obj.id,
                            tier=tier,
                            name=rank_name,
                            icon=rank_icon,
                            min_rp=min_rp,
                        )
                    )
                print(f"    ↳ Seeded {len(DEFAULT_RANKS)} rank tiers")

    db.commit()

    print("\n" + "=" * 60)
    print("✅ SEEDING COMPLETE!")
    print(f"  • {len(CATEGORIES)} categories")
    total_subjects = sum(len(v) for v in SUBJECTS.values())
    print(f"  • {total_subjects} subjects")
    print(f"  • {total_subjects * len(DEFAULT_RANKS)} rank tiers")
    print("=" * 60 + "\n")


def create_test_posts(db: Session, users: list[User], image_url: str) -> list[Post]:
    """Create test posts with the uploaded Garuda image."""
    print("\n📝 Creating test posts...")

    posts_data = [
        {
            "title": "Test Post 1: Welcome to Nusa CoNEX",
            "content": "This is the first test post for the Nusa CoNEX platform. Welcome!",
            "excerpt": "Welcome to Nusa CoNEX - Test Post 1",
            "is_published": True,
        },
        {
            "title": "Test Post 2: Platform Features",
            "content": "This test post showcases various features of our platform including image uploads and rich content.",
            "excerpt": "Testing platform features",
            "is_published": True,
        },
        {
            "title": "Test Post 3: Community Guidelines",
            "content": "Another test post demonstrating the content management system.",
            "excerpt": "Test post about community",
            "is_published": True,
        },
        {
            "title": "Test Post 4: Draft Example",
            "content": "This is a draft test post that is not published yet.",
            "excerpt": "Draft test post",
            "is_published": False,
        },
        {
            "title": "Test Post 5: Long Content Example",
            "content": """This is a longer test post with more content.

It has multiple paragraphs to demonstrate how the platform handles longer form content.

The Nusa CoNEX platform is designed to handle various types of content effectively.

This post also includes the Garuda logo image to show how media is integrated into posts.""",
            "excerpt": "Testing longer content with multiple paragraphs",
            "is_published": True,
        },
    ]

    subjects = db.query(Subject).order_by(Subject.name).all()

    posts: list[Post] = []
    for i, post_data in enumerate(posts_data):
        author = users[i % len(users)]
        created_at = datetime.utcnow() - timedelta(days=len(posts_data) - i, hours=i * 2)
        subject_id = subjects[i % len(subjects)].id if subjects else None

        post = Post(
            **post_data,
            image_url=image_url,
            author_id=author.id,
            subject_id=subject_id,
            created_at=created_at,
            updated_at=created_at,
        )
        db.add(post)
        posts.append(post)

    db.commit()
    for post in posts:
        db.refresh(post)

    published_count = sum(1 for p in posts if p.is_published)
    draft_count = len(posts) - published_count
    print(f"✓ Created {len(posts)} posts ({published_count} published, {draft_count} draft)")
    return posts


def seed_database(image_path: str = "garuda_icon.png") -> None:
    """Seed subjects/ranks, users, and posts in one flow."""
    print("\n" + "=" * 70)
    print("🌱 NUSA CONEX DATABASE SEEDER")
    print("=" * 70)

    db = SessionLocal()

    try:
        image_url = upload_image_to_supabase(image_path)

        seed_subjects(db)
        users, login_ready_count = create_mock_users(db)
        posts = create_test_posts(db, users, image_url)

        print("\n" + "=" * 70)
        print("✅ DATABASE SEEDING COMPLETED!")
        print("=" * 70)
        print("\n📊 Summary:")
        print(f"  • {len(users)} users created")
        print(f"  • {len(posts)} posts created")
        print(f"  • {sum(1 for p in posts if p.is_published)} posts published")
        print(f"  • {sum(1 for p in posts if not p.is_published)} drafts")
        print("\n🖼️  Image URL:")
        print(f"  {image_url}")
        print("\n🔑 Test Credentials:")
        print("  Email: admin@nusaconex.com")
        print("  Password: password123")
        if login_ready_count < len(users):
            print("  ⚠️  Some seeded users are not login-ready via Supabase Auth.")
            print("     Set SERVICE_ROLE_KEY to auto-provision auth users.")
        print("\n🚀 Next Steps:")
        print("  1. Run: uvicorn app.main:app --reload")
        print("  2. Visit: http://localhost:8000/docs")
        print("  3. Test: http://localhost:8000/homepage/posts")
        print("=" * 70 + "\n")

    except Exception as e:
        db.rollback()
        print(f"\n❌ Error seeding database: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        db.close()


# ── Orchestration ────────────────────────────────────────────────────────────

def setup_database(seed: bool = True, image_path: str = "garuda_icon.png", reset: bool = True) -> None:
    """
    Complete database setup orchestration.

    Args:
        seed: Whether to seed mock data after creating tables.
        image_path: Path to image file for seeding.
        reset: Whether to drop existing tables before creating new ones.
    """
    print("\n" + "🚀 " * 25)
    print("NUSA CONEX - DATABASE SETUP")
    print("🚀 " * 25 + "\n")

    try:
        if reset:
            reset_database()

        create_tables()

        if seed:
            seed_database(image_path=image_path)
        else:
            print("\n⚠️  Skipping data seeding")
            print("Run 'python setupdb.py --no-reset' with seeding enabled later")

        print("\n" + "🎉 " * 25)
        print("SETUP COMPLETE!")
        print("🎉 " * 25 + "\n")

    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        engine.dispose()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Setup Nusa CoNEX database")
    parser.add_argument(
        "--no-seed",
        action="store_true",
        help="Skip seeding data (only create tables)",
    )
    parser.add_argument(
        "--no-reset",
        action="store_true",
        help="Don't drop existing tables (may cause errors if schema changed)",
    )
    parser.add_argument(
        "--image",
        default="garuda_icon.png",
        help="Path to the Garuda image file",
    )

    args = parser.parse_args()

    base_dir = Path(__file__).resolve().parent
    image_path = str(base_dir / args.image)

    setup_database(
        seed=not args.no_seed,
        image_path=image_path,
        reset=not args.no_reset,
    )
