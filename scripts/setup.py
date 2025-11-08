#!/usr/bin/env python3
"""
Setup script for the Adaptive Learning System

This script helps set up the development environment and initialize
the database with required collections and indexes.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.db.database import Database
from src.db.learner_repository import LearnerRepository


async def setup_database():
    """Set up database collections and indexes"""
    print("Setting up database...")
    
    # Initialize database connection
    db = Database()
    await db.connect_to_mongo()
    
    try:
        # Create learner profiles collection and indexes
        collection = db.get_collection("learner_profiles")
        repository = LearnerRepository(collection)
        await repository.create_indexes()
        
        print("✓ Learner profiles collection and indexes created")
        
        # Create other collections
        collections = [
            "learning_activities",
            "performance_data", 
            "competency_assessments",
            "learning_paths",
            "content_items"
        ]
        
        for collection_name in collections:
            collection = db.get_collection(collection_name)
            # Create collection by inserting and removing a dummy document
            await collection.insert_one({"_temp": True})
            await collection.delete_one({"_temp": True})
            print(f"✓ {collection_name} collection created")
        
        print("\n✅ Database setup completed successfully!")
        
    except Exception as e:
        print(f"❌ Database setup failed: {e}")
        raise
    finally:
        await db.close_mongo_connection()


def check_environment():
    """Check if required environment variables are set"""
    print("Checking environment variables...")
    
    required_vars = ["MONGODB_URI", "SECRET_KEY"]
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        print("Please set these variables in your .env file or environment")
        return False
    
    print("✓ All required environment variables are set")
    return True


def create_env_file():
    """Create .env file from template if it doesn't exist"""
    env_file = Path(".env")
    env_example = Path(".env.example")
    
    if not env_file.exists() and env_example.exists():
        print("Creating .env file from template...")
        env_file.write_text(env_example.read_text())
        print("✓ .env file created. Please update it with your configuration.")
        return True
    
    return False


async def main():
    """Main setup function"""
    print("🚀 Adaptive Learning System Setup")
    print("=" * 40)
    
    # Create .env file if needed
    if create_env_file():
        print("\n⚠️  Please update the .env file with your MongoDB URI and secret key")
        print("Then run this script again.")
        return
    
    # Load environment variables
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        print("⚠️  python-dotenv not installed. Make sure to set environment variables manually.")
    
    # Check environment
    if not check_environment():
        return
    
    # Setup database
    try:
        await setup_database()
    except Exception as e:
        print(f"❌ Setup failed: {e}")
        sys.exit(1)
    
    print("\n🎉 Setup completed successfully!")
    print("\nNext steps:")
    print("1. Start the application: uvicorn src.main:app --reload")
    print("2. Visit http://localhost:8000/docs for API documentation")
    print("3. Use the demo account: demo@example.com / password123")


if __name__ == "__main__":
    asyncio.run(main())