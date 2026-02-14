"""
Complete database setup script with FULL RESET.
This will:
1. DROP all existing tables (clean slate)
2. CREATE all tables fresh
3. Seed with mock data
"""
import sys
from pathlib import Path

# Add the app directory to the path
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import text
from app.db.session import engine, SessionLocal
from app.db.base import Base

# Import all models to ensure they're registered
from app.models.user import User
from app.models.post import Post
from app.models.quiz import Quiz
from app.models.admin import Admin
from app.models.friendship import Friendship
from app.models.assets import Asset

from seed_db import seed_database


def reset_database():
    """Drop all existing tables for a clean reset."""
    print("\n" + "="*70)
    print("🗑️  RESETTING DATABASE (Dropping all tables)")
    print("="*70 + "\n")
    
    try:
        # Drop all tables
        Base.metadata.drop_all(bind=engine)
        print("✓ All existing tables dropped successfully")
        
        # Dispose the engine to clear any cached connections
        engine.dispose()
        print("✓ Database connections cleared\n")
        
    except Exception as e:
        print(f"⚠️  Note: {e}")
        print("(This is OK if tables didn't exist yet)\n")


def create_tables():
    """Create all database tables fresh."""
    print("="*70)
    print("📊 CREATING DATABASE TABLES")
    print("="*70 + "\n")
    
    try:
        # Create all tables
        Base.metadata.create_all(bind=engine)
        print("✓ All tables created successfully:")
        for table in Base.metadata.sorted_tables:
            print(f"  • {table.name}")
        print()
        
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        raise


def setup_database(seed: bool = True, image_path: str = "garuda_icon.png", reset: bool = True):
    """Complete database setup with optional reset."""
    print("\n" + "🚀 "*25)
    print("NUSA CONEX - DATABASE SETUP")
    print("🚀 "*25 + "\n")
    
    try:
        # Step 1: Reset database (drop all tables)
        if reset:
            reset_database()
        
        # Step 2: Create tables fresh
        create_tables()
        
        # Step 3: Seed data (optional)
        if seed:
            seed_database(image_path=image_path)
        else:
            print("\n⚠️  Skipping data seeding")
            print("Run 'python seed_db.py' to seed data later")
        
        print("\n" + "🎉 "*25)
        print("SETUP COMPLETE!")
        print("🎉 "*25 + "\n")
        
    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        # Clean up any remaining connections
        engine.dispose()


if __name__ == "__main__":
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
    
    setup_database(
        seed=not args.no_seed,
        image_path=args.image,
        reset=not args.no_reset
    )