#!/usr/bin/env python3
"""
Seed script to populate the database with initial test data.
Run this after the application has started at least once to create tables.
"""

import asyncio
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.future import select
from db import async_session
from models import User, Post, Category, Tag, SiteInfo, Menu
from utils.auth import get_password_hash
import datetime


async def seed_data():
    """Seed the database with initial data"""
    async with async_session() as session:
        print("Starting database seeding...")
        
        # Check if data already exists
        result = await session.execute(select(User))
        if result.scalars().first():
            print("Database already has data. Skipping seeding.")
            return
        
        # Create admin user
        print("Creating admin user...")
        admin = User(
            username="admin",
            password_hash=get_password_hash("admin123"),
            created_at=datetime.date.today()
        )
        session.add(admin)
        await session.flush()
        
        # Create categories
        print("Creating categories...")
        categories_data = ["Technology", "Programming", "Web Development", "Database", "DevOps"]
        categories = []
        for cat_name in categories_data:
            cat = Category(name=cat_name)
            session.add(cat)
            categories.append(cat)
        await session.flush()
        
        # Create tags
        print("Creating tags...")
        tags_data = ["Python", "JavaScript", "FastAPI", "MySQL", "React", "Vue", "Docker", "AWS"]
        tags = []
        for tag_name in tags_data:
            tag = Tag(name=tag_name)
            session.add(tag)
            tags.append(tag)
        await session.flush()
        
        # Create sample posts
        print("Creating sample posts...")
        posts_data = [
            {
                "title": "Welcome to Our Blog",
                "summary": "This is our first blog post introducing our new platform",
                "content": "Welcome to our new blog platform! This is a comprehensive blogging system built with FastAPI and MySQL. We'll be sharing articles about technology, programming, and web development.",
                "category": categories[0],
                "tags": [tags[0], tags[2], tags[3]]
            },
            {
                "title": "Getting Started with FastAPI",
                "summary": "Learn how to build modern web APIs with FastAPI",
                "content": "FastAPI is a modern, fast (high-performance) web framework for building APIs with Python 3.7+ based on standard Python type hints. In this article, we'll explore the key features and benefits of using FastAPI for your next project.",
                "category": categories[1],
                "tags": [tags[0], tags[2]]
            },
            {
                "title": "Understanding Async MySQL with SQLAlchemy",
                "summary": "Deep dive into asynchronous database operations",
                "content": "Asynchronous database operations can significantly improve the performance of your web applications. In this guide, we'll explore how to use SQLAlchemy's async features with MySQL.",
                "category": categories[3],
                "tags": [tags[0], tags[3]]
            },
            {
                "title": "Modern Frontend Development with React",
                "summary": "Building interactive user interfaces with React",
                "content": "React has revolutionized frontend development with its component-based architecture. Learn the fundamentals of React and how to build modern web applications.",
                "category": categories[2],
                "tags": [tags[1], tags[4]]
            },
            {
                "title": "Docker for Developers",
                "summary": "Containerize your applications with Docker",
                "content": "Docker containers provide a consistent environment for your applications across development and production. This guide covers the essentials of Docker for web developers.",
                "category": categories[4],
                "tags": [tags[6]]
            }
        ]
        
        for i, post_data in enumerate(posts_data, 1):
            post = Post(
                title=post_data["title"],
                summary=post_data["summary"],
                content=post_data["content"],
                category=post_data["category"],
                author=admin,
                date=datetime.date.today() - datetime.timedelta(days=len(posts_data) - i),
                views=10 * i,
                likes=5 * i
            )
            post.tags = post_data["tags"]
            session.add(post)
        
        # Create site info
        print("Creating site info...")
        siteinfo = SiteInfo(
            title="My Awesome Blog",
            description="A modern blog platform built with FastAPI and MySQL",
            icp="备案号-12345678",
            footer="© 2024 My Awesome Blog. All rights reserved."
        )
        session.add(siteinfo)
        
        # Create menu items
        print("Creating menu items...")
        menus_data = [
            {"title": "Home", "path": "/"},
            {"title": "Posts", "path": "/posts"},
            {"title": "Categories", "path": "/categories"},
            {"title": "Tags", "path": "/tags"},
            {"title": "Archive", "path": "/archive"},
            {"title": "About", "path": "/about"},
        ]
        
        for menu_data in menus_data:
            menu = Menu(**menu_data)
            session.add(menu)
        
        # Commit all changes
        await session.commit()
        
        print("\n" + "=" * 60)
        print("Database seeding completed successfully!")
        print("=" * 60)
        print("\nCreated:")
        print(f"  - 1 admin user (username: 'admin', password: 'admin123')")
        print(f"  - {len(categories_data)} categories")
        print(f"  - {len(tags_data)} tags")
        print(f"  - {len(posts_data)} sample posts")
        print(f"  - 1 site info record")
        print(f"  - {len(menus_data)} menu items")
        print("\nYou can now login with:")
        print("  Username: admin")
        print("  Password: admin123")
        print("\nAPI Documentation: http://localhost:8000/docs")


async def main():
    """Main function"""
    try:
        await seed_data()
    except Exception as e:
        print(f"Error seeding database: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
