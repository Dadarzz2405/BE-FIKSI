"""
Complete database setup script with FULL RESET.
This script performs a clean database initialization:
1. DROP all existing tables (clean slate)
2. CREATE all tables fresh
3. Seed with mock data
"""
# Standard library imports
import sys
from pathlib import Path

# Add the parent directory to the path so imports work
sys.path.insert(0, str(Path(__file__).parent))

# SQLAlchemy imports
from sqlalchemy import text
# Database session and engine imports
from app.db.session import engine, SessionLocal
from app.db.base import Base

# Import all models to ensure they're registered with SQLAlchemy
from app.models.user import User
from app.models.post import Post
from app.models.quiz import Quiz
from app.models.admin import Admin
from app.models.friendship import Friendship
from app.models.assets import Asset
from app.models.academic_category import AcademicCategory
from app.models.subject import Subject
from app.models.subject_rank import SubjectRank
from app.models.user_subject_progress import UserSubjectProgress

# Import seeding functions
from seed_db import seed_database
from seed_subjects import seed_subjects


def reset_database():
    """
    Drop all existing tables for a clean database reset.
    Useful when you need to completely wipe the schema and start fresh.
    """
    print("\n" + "="*70)
    print("🗑️  RESETTING DATABASE (Dropping all tables)")
    print("="*70 + "\n")
    
    try:
        # Drop all tables defined in models
        Base.metadata.drop_all(bind=engine)
        print("✓ All existing tables dropped successfully")
        
        # Dispose the engine to clear any cached connections
        engine.dispose()
        print("✓ Database connections cleared\n")
        
    except Exception as e:
        print(f"⚠️  Note: {e}")
        print("(This is OK if tables didn't exist yet)\n")


def create_tables():
    """Create all database tables from model definitions."""
    print("="*70)
    print("📊 CREATING DATABASE TABLES")
    print("="*70 + "\n")
    
    try:
        # Create all tables based on model metadata
        Base.metadata.create_all(bind=engine)
        print("✓ All tables created successfully:")
        # List all created tables
        for table in Base.metadata.sorted_tables:
            print(f"  • {table.name}")
        print()
        
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        raise


def setup_database(seed: bool = True, image_path: str = "garuda_icon.png", reset: bool = True):
    """
    Complete database setup orchestration.
    
    Args:
        seed: Whether to seed mock data after creating tables
        image_path: Path to image file for seeding
        reset: Whether to drop existing tables before creating new ones
    """
    print("\n" + "🚀 "*25)
    print("NUSA CONEX - DATABASE SETUP")
    print("🚀 "*25 + "\n")
    
    try:
        # Step 1: Reset database (optionally drop all tables)
        if reset:
            reset_database()
        
        # Step 2: Create tables fresh
        create_tables()
        
        # Step 3: Seed data (optional)
        if seed:
            seed_database(image_path=image_path)
            seed_subjects()
        else:
            print("\n⚠️  Skipping data seeding")
            print("Run 'python seed_db.py' to seed data later")
        
        print("\n" + "🎉 "*25)
        print("SETUP COMPLETE!")
        print("🎉 "*25 + "\n")
        
    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        # Print full traceback for debugging
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        # Always clean up any remaining connections
        engine.dispose()


# Script entry point
if __name__ == "__main__":
    # Parse command line arguments
    import argparse
    
    parser = argparse.ArgumentParser(description="Setup Nusa CoNEX database")
    parser.add_argument(
        "--no-seed",
        action="store_true",
        help="Skip seeding data (only create tables)"
    )
    parser.add_argument(
        "--no-reset",
        action="store_true",
        help="Don't drop existing tables (may cause errors if schema changed)"
    )
    parser.add_argument(
        "--image",
        default="garuda_icon.png",
        help="Path to the Garuda image file (default: garuda-icon.png)"
    )
    
    args = parser.parse_args()
    
    # Execute setup with parsed arguments
    setup_database(
        seed=not args.no_seed,
        image_path=args.image,
        reset=not args.no_reset
    )