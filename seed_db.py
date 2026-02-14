"""
Database seeder with Supabase Storage image upload.
This will:
1. Upload the Garuda image to Supabase Storage
2. Create mock users
3. Create mock posts using the uploaded image
"""
import os
import sys
from pathlib import Path
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.db.session import SessionLocal, engine
from app.models.user import User
from app.models.post import Post
from app.core.config import SUPABASE_URL, SUPABASE_KEY

# Import Supabase client for storage
from supabase import create_client


def upload_image_to_supabase(image_path: str, bucket_name: str = "post-images") -> str:
    """
    Upload image to Supabase Storage and return public URL.
    
    Args:
        image_path: Path to the image file
        bucket_name: Name of the Supabase storage bucket
    
    Returns:
        Public URL of the uploaded image
    """
    print(f"\n📤 Uploading image to Supabase Storage...")
    
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("⚠️  Supabase credentials not found!")
        print("Set SUPABASE_URL and SUPABASE_KEY in your environment variables.")
        print("Using placeholder URL instead...")
        return "https://i.ibb.co.com/Kx9bs0zv/Garuda-Icon-Featuring-Networked-Wings-and-Typography-2.png"
    
    try:
        # Create Supabase client
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        # Check if image file exists
        if not os.path.exists(image_path):
            print(f"❌ Image file not found: {image_path}")
            return "https://i.ibb.co.com/Kx9bs0zv/Garuda-Icon-Featuring-Networked-Wings-and-Typography-2.png"
        
        # Read the image file
        with open(image_path, 'rb') as f:
            image_data = f.read()
        
        # Get file name
        file_name = "garuda_icon.png"
        
        # Check if bucket exists, create if not
        try:
            buckets = supabase.storage.list_buckets()
            bucket_exists = any(b['name'] == bucket_name for b in buckets)
            
            if not bucket_exists:
                print(f"📦 Creating bucket '{bucket_name}'...")
                supabase.storage.create_bucket(bucket_name, options={"public": True})
                print(f"✓ Bucket '{bucket_name}' created")
            else:
                print(f"✓ Bucket '{bucket_name}' already exists")
        except Exception as e:
            print(f"⚠️  Could not create/check bucket: {e}")
            print("Make sure you have the right permissions.")
        
        # Upload the image
        print(f"⬆️  Uploading {file_name}...")
        
        # Delete if exists (to allow re-upload)
        try:
            supabase.storage.from_(bucket_name).remove([file_name])
        except:
            pass  # File might not exist yet
        
        # Upload the file
        result = supabase.storage.from_(bucket_name).upload(
            file_name,
            image_data,
            file_options={"content-type": "image/png"}
        )
        
        # Get public URL
        public_url = supabase.storage.from_(bucket_name).get_public_url(file_name)
        
        print(f"✅ Image uploaded successfully!")
        print(f"📍 URL: {public_url}")
        
        return public_url
        
    except Exception as e:
        print(f"❌ Error uploading image: {e}")
        print("Using placeholder URL instead...")
        return "https://i.ibb.co.com/Kx9bs0zv/Garuda-Icon-Featuring-Networked-Wings-and-Typography-2.png"


def create_mock_users(db: Session) -> list[User]:
    """Create mock users."""
    print("\n👥 Creating mock users...")
    
    users_data = [
        {
            "username": "admin_nusa",
            "email": "admin@nusaconex.com",
            "real_name": "Admin Nusa CoNEX",
            "hashed_password": "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYzNb8Ow1u2",  # "password123"
            "is_active": True,
            "subscription": "Pro",
            "bio": "Official admin account for Nusa CoNEX platform.",
            "avatar_url": "https://api.dicebear.com/7.x/avataaars/svg?seed=admin"
        },
        {
            "username": "test_user1",
            "email": "user1@example.com",
            "real_name": "Test User One",
            "hashed_password": "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYzNb8Ow1u2",
            "is_active": True,
            "subscription": "Free",
            "bio": "Just testing out the platform!",
            "avatar_url": "https://api.dicebear.com/7.x/avataaars/svg?seed=user1"
        },
        {
            "username": "test_user2",
            "email": "user2@example.com",
            "real_name": "Test User Two",
            "hashed_password": "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYzNb8Ow1u2",
            "is_active": True,
            "subscription": "Free",
            "bio": "Another test user account.",
            "avatar_url": "https://api.dicebear.com/7.x/avataaars/svg?seed=user2"
        }
    ]
    
    users = []
    for user_data in users_data:
        user = User(**user_data)
        db.add(user)
        users.append(user)
    
    db.commit()
    for user in users:
        db.refresh(user)
    
    print(f"✓ Created {len(users)} users")
    return users


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
        }
    ]
    
    posts = []
    for i, post_data in enumerate(posts_data):
        # Assign posts to users round-robin
        author = users[i % len(users)]
        
        # Create posts with staggered timestamps
        created_at = datetime.utcnow() - timedelta(days=len(posts_data) - i, hours=i * 2)
        
        post = Post(
            **post_data,
            image=image_url,  # All posts use the Garuda image
            author_id=author.id,
            created_at=created_at,
            updated_at=created_at
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


def seed_database(image_path: str = "garuda_icon.png"):
    """Main seeder function."""
    print("\n" + "="*70)
    print("🌱 NUSA CONEX DATABASE SEEDER")
    print("="*70)
    
    # Create a fresh session
    db = SessionLocal()
    
    try:
        # Step 1: Upload image to Supabase Storage
        image_url = upload_image_to_supabase(image_path)
        
        # Step 2: Create users
        users = create_mock_users(db)
        
        # Step 3: Create posts
        posts = create_test_posts(db, users, image_url)
        
        # Summary
        print("\n" + "="*70)
        print("✅ DATABASE SEEDING COMPLETED!")
        print("="*70)
        print(f"\n📊 Summary:")
        print(f"  • {len(users)} users created")
        print(f"  • {len(posts)} posts created")
        print(f"  • {sum(1 for p in posts if p.is_published)} posts published")
        print(f"  • {sum(1 for p in posts if not p.is_published)} drafts")
        print(f"\n🖼️  Image URL:")
        print(f"  {image_url}")
        print(f"\n🔑 Test Credentials:")
        print(f"  Email: admin@nusaconex.com")
        print(f"  Password: password123")
        print(f"\n🚀 Next Steps:")
        print(f"  1. Run: uvicorn app.main:app --reload")
        print(f"  2. Visit: http://localhost:8000/docs")
        print(f"  3. Test: http://localhost:8000/homepage/posts")
        print("="*70 + "\n")
        
    except Exception as e:
        db.rollback()
        print(f"\n❌ Error seeding database: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        db.close()
        # Clean up connections
        engine.dispose()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Seed Nusa CoNEX database")
    parser.add_argument(
        "--image",
        default="garuda_icon.png",
        help="Path to the Garuda image file"
    )
    
    args = parser.parse_args()
    
    BASE_DIR = Path(__file__).resolve().parent
    image_path = BASE_DIR / args.image
    seed_database(image_path=str(image_path))
