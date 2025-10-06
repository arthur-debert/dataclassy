"""Tests for core dataclassy functionality."""

import pytest
from enum import Enum
from dataclasses import fields

from dataclassy import dataclassy, field


class Status(Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"


def test_basic_dataclassy():
    """Test basic dataclassy decorator functionality."""

    @dataclassy
    class User:
        name: str
        age: int
        status: Status = Status.ACTIVE

    # Test basic instantiation
    user = User("Alice", 25)
    assert user.name == "Alice"
    assert user.age == 25
    assert user.status == Status.ACTIVE

    # Test with explicit status
    user2 = User("Bob", 30, Status.PENDING)
    assert user2.name == "Bob"
    assert user2.age == 30
    assert user2.status == Status.PENDING


def test_enum_string_conversion():
    """Test automatic enum string conversion."""

    @dataclassy
    class Order:
        order_id: int
        status: Status

    # Test string value conversion
    order1 = Order(1, "active")
    assert order1.status == Status.ACTIVE

    # Test string name conversion (case-insensitive)
    order2 = Order(2, "PENDING")
    assert order2.status == Status.PENDING

    # Test existing enum passes through
    order3 = Order(3, Status.INACTIVE)
    assert order3.status == Status.INACTIVE


def test_to_dict():
    """Test to_dict method."""

    @dataclassy
    class Product:
        name: str
        price: float
        in_stock: bool = True

    product = Product("Widget", 19.99)
    data = product.to_dict()

    assert data == {"name": "Widget", "price": 19.99, "in_stock": True}


def test_dataclass_compatibility():
    """Test that dataclassy maintains dataclass compatibility."""

    @dataclassy
    class Point:
        x: float
        y: float
        label: str = "origin"

    # Should have all dataclass features
    p = Point(1.0, 2.0)

    # Test repr
    assert "Point" in repr(p)
    assert "x=1.0" in repr(p)

    # Test equality
    p2 = Point(1.0, 2.0)
    assert p == p2

    # Test fields
    field_names = [f.name for f in fields(p)]
    assert field_names == ["x", "y", "label"]


def test_frozen_dataclassy():
    """Test frozen dataclassy."""

    @dataclassy(frozen=True)
    class ImmutablePoint:
        x: float
        y: float

    p = ImmutablePoint(1.0, 2.0)

    # Should not be able to modify
    with pytest.raises(Exception):  # FrozenInstanceError
        p.x = 3.0


def test_with_default_factory():
    """Test field with default_factory."""

    @dataclassy
    class Container:
        items: list = field(default_factory=list)
        tags: set = field(default_factory=set)

    c1 = Container()
    c2 = Container()

    # Should have independent collections
    c1.items.append("item1")
    c1.tags.add("tag1")

    assert len(c2.items) == 0
    assert len(c2.tags) == 0


def test_inheritance():
    """Test dataclassy inheritance."""

    @dataclassy
    class Animal:
        name: str
        species: str

    @dataclassy
    class Dog(Animal):
        breed: str
        good_boy: bool = True

    dog = Dog("Buddy", "Canis familiaris", "Golden Retriever")
    assert dog.name == "Buddy"
    assert dog.species == "Canis familiaris"
    assert dog.breed == "Golden Retriever"
    assert dog.good_boy is True
