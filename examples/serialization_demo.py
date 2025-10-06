"""Demo of dataclassy serialization features."""

from enum import Enum
from typing import List, Optional
from dataclasses import field

# Add parent directory to path for imports
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from dataclassy import dataclassy


class Status(Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class Priority(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3


@dataclassy
class Tag:
    name: str
    color: str = "blue"


@dataclassy
class Author:
    name: str
    email: str
    verified: bool = False


@dataclassy
class Article:
    title: str
    content: str
    author: Author
    status: Status
    priority: Priority = Priority.MEDIUM
    tags: List[Tag] = field(default_factory=list)
    metadata: Optional[dict] = None


def main():
    # Create article from dictionary
    article_data = {
        "title": "Introduction to Dataclassy",
        "content": "Dataclassy makes working with data classes easier...",
        "author": {
            "name": "Alice Developer",
            "email": "alice@example.com",
            "verified": True
        },
        "status": "published",  # String will be converted to enum
        "priority": 3,          # Number will be converted to enum
        "tags": [
            {"name": "python", "color": "blue"},
            {"name": "tutorial"},  # Will use default color
            {"name": "dataclasses", "color": "green"}
        ],
        "metadata": {
            "views": 1250,
            "likes": 47
        }
    }
    
    # Convert from dictionary
    article = Article.from_dict(article_data)
    
    print("=== Article Created from Dictionary ===")
    print(f"Title: {article.title}")
    print(f"Author: {article.author.name} ({article.author.email})")
    print(f"Status: {article.status} (type: {type(article.status)})")
    print(f"Priority: {article.priority} (value: {article.priority.value})")
    print(f"Tags: {[f'{tag.name} ({tag.color})' for tag in article.tags]}")
    print(f"Metadata: {article.metadata}")
    
    # Convert back to dictionary
    article_dict = article.to_dict()
    
    print("\n=== Article Converted to Dictionary ===")
    import json
    # Note: asdict() returns enums as enum objects, not values
    # For JSON serialization, you'd need a custom encoder
    print(f"Title: {article_dict['title']}")
    print(f"Status: {article_dict['status']} (enum object)")
    print(f"Author: {article_dict['author']}")
    
    # Demonstrate missing field handling
    print("\n=== Missing Field Handling ===")
    
    minimal_data = {
        "title": "Minimal Article",
        "content": "Just the required fields",
        "author": {
            "name": "Bob",
            "email": "bob@example.com"
        },
        "status": "draft"
        # priority will use default
        # tags will use default_factory
        # metadata will be None
    }
    
    minimal_article = Article.from_dict(minimal_data)
    print(f"Priority (default): {minimal_article.priority}")
    print(f"Tags (default factory): {minimal_article.tags}")
    print(f"Metadata (None): {minimal_article.metadata}")
    
    # Demonstrate enum flexibility
    print("\n=== Enum Conversion Flexibility ===")
    
    # Different ways to specify enum values
    enum_test_data = {
        "title": "Enum Test",
        "content": "Testing enum conversion",
        "author": {"name": "Charlie", "email": "charlie@example.com"},
        "status": "PUBLISHED",  # By name (uppercase)
        "priority": "high"      # By name (lowercase)
    }
    
    enum_article = Article.from_dict(enum_test_data)
    print(f"Status from 'PUBLISHED': {enum_article.status}")
    print(f"Priority from 'high': {enum_article.priority}")


if __name__ == "__main__":
    main()