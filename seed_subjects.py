"""
seed_subjects.py — Seed academic categories, subjects, and rank ladders.

Based on Indonesia national curriculum (SMA level).
Idempotent: skips existing records so you can safely re-run.

Usage:
    python seed_subjects.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy.orm import Session
from app.db.session import SessionLocal, engine
from app.db.init_db import init_db
from app.models.academic_category import AcademicCategory
from app.models.subject import Subject
from app.models.subject_rank import SubjectRank


# ── Data ──────────────────────────────────────────────────────────────────────

CATEGORIES = [
    {"name": "Science",            "slug": "science",            "icon": "🔬", "description": "Ilmu Pengetahuan Alam (IPA)"},
    {"name": "Social",             "slug": "social",             "icon": "🌍", "description": "Ilmu Pengetahuan Sosial (IPS)"},
    {"name": "Language",           "slug": "language",           "icon": "📖", "description": "Bahasa dan Sastra"},
    {"name": "Technology",         "slug": "technology",         "icon": "💻", "description": "Teknologi Informasi"},
    {"name": "Civic & Character",  "slug": "civic-character",    "icon": "🇮🇩", "description": "Pendidikan Kewarganegaraan dan Karakter"},
]

SUBJECTS = {
    # category_slug -> list of (name, slug, icon)
    "science": [
        ("Matematika",       "matematika",       "📐"),
        ("Fisika",           "fisika",           "⚛️"),
        ("Kimia",            "kimia",            "🧪"),
        ("Biologi",          "biologi",          "🧬"),
    ],
    "social": [
        ("Ekonomi",          "ekonomi",          "📊"),
        ("Geografi",         "geografi",         "🗺️"),
        ("Sosiologi",        "sosiologi",        "👥"),
        ("Sejarah",          "sejarah",          "📜"),
    ],
    "language": [
        ("Bahasa Indonesia", "bahasa-indonesia", "🇮🇩"),
        ("Bahasa Inggris",   "bahasa-inggris",   "🇬🇧"),
    ],
    "technology": [
        ("Informatika",      "informatika",      "🖥️"),
    ],
    "civic-character": [
        ("PPKn",             "ppkn",             "⚖️"),
    ],
}

# Default rank ladder applied to every subject
DEFAULT_RANKS = [
    # (tier, name,       icon,  min_rp)
    (1, "Bronze",   "🥉", 0),
    (2, "Silver",   "🥈", 100),
    (3, "Gold",     "🥇", 500),
    (4, "Platinum", "⚡",  1500),
    (5, "Diamond",  "💎",  5000),
]


# ── Seed function ─────────────────────────────────────────────────────────────

def seed_subjects(db: Session | None = None) -> None:
    """Create academic categories, subjects, and rank ladders."""
    own_session = db is None
    if own_session:
        db = SessionLocal()

    try:
        print("\n" + "=" * 60)
        print("📚 SEEDING ACADEMIC CATEGORIES & SUBJECTS")
        print("=" * 60)

        # ── 1. Categories ─────────────────────────────────────────────
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
                db.flush()  # get the ID
                cat_map[cat_data["slug"]] = cat
                print(f"  ✓ Created category '{cat_data['name']}'")

        # ── 2. Subjects ───────────────────────────────────────────────
        subject_count = 0
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
                    subject_count += 1
                    print(f"  ✓ Created subject '{name}' → {category.name}")

                # ── 3. Rank ladder per subject ────────────────────────
                existing_ranks = db.query(SubjectRank).filter(
                    SubjectRank.subject_id == subject_obj.id
                ).count()
                if existing_ranks == 0:
                    for tier, rank_name, rank_icon, min_rp in DEFAULT_RANKS:
                        db.add(SubjectRank(
                            subject_id=subject_obj.id,
                            tier=tier,
                            name=rank_name,
                            icon=rank_icon,
                            min_rp=min_rp,
                        ))
                    print(f"    ↳ Seeded {len(DEFAULT_RANKS)} rank tiers")

        db.commit()

        print("\n" + "=" * 60)
        print("✅ SEEDING COMPLETE!")
        print(f"  • {len(CATEGORIES)} categories")
        total_subjects = sum(len(v) for v in SUBJECTS.values())
        print(f"  • {total_subjects} subjects")
        print(f"  • {total_subjects * len(DEFAULT_RANKS)} rank tiers")
        print("=" * 60 + "\n")

    except Exception as e:
        db.rollback()
        print(f"\n❌ Seeding failed: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        if own_session:
            db.close()
            engine.dispose()


if __name__ == "__main__":
    init_db()  # ensure tables exist
    seed_subjects()
