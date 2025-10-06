"""Tests for dataclassy serialization functionality."""

import pytest
from enum import Enum
from typing import List, Optional, Dict
from dataclasses import field

from dataclassy import dataclassy, asdict


class Color(Enum):
    RED = "red"
    GREEN = "green"
    BLUE = "blue"


class Priority(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3


def test_basic_from_dict():
    """Test basic dictionary to dataclass conversion."""
    
    @dataclassy
    class Person:
        name: str
        age: int
        active: bool = True
    
    # Test with all fields
    data = {"name": "Alice", "age": 30, "active": False}
    person = Person.from_dict(data)
    
    assert person.name == "Alice"
    assert person.age == 30
    assert person.active is False
    
    # Test with default value
    data2 = {"name": "Bob", "age": 25}
    person2 = Person.from_dict(data2)
    
    assert person2.name == "Bob"
    assert person2.age == 25
    assert person2.active is True


def test_nested_dataclass():
    """Test nested dataclass conversion."""
    
    @dataclassy
    class Address:
        street: str
        city: str
        zip_code: str
    
    @dataclassy
    class Employee:
        name: str
        employee_id: int
        address: Address
    
    data = {
        "name": "Charlie",
        "employee_id": 12345,
        "address": {
            "street": "123 Main St",
            "city": "Boston",
            "zip_code": "02101"
        }
    }
    
    employee = Employee.from_dict(data)
    
    assert employee.name == "Charlie"
    assert employee.employee_id == 12345
    assert employee.address.street == "123 Main St"
    assert employee.address.city == "Boston"
    assert employee.address.zip_code == "02101"


def test_enum_conversion():
    """Test enum conversion in from_dict."""
    
    @dataclassy
    class Task:
        title: str
        color: Color
        priority: Priority
    
    # Test string value conversion
    data = {
        "title": "Important Task",
        "color": "red",  # String value
        "priority": 3     # Numeric value
    }
    
    task = Task.from_dict(data)
    
    assert task.title == "Important Task"
    assert task.color == Color.RED
    assert task.priority == Priority.HIGH
    
    # Test enum name conversion
    data2 = {
        "title": "Another Task",
        "color": "GREEN",  # Enum name
        "priority": "MEDIUM"  # Enum name as string
    }
    
    task2 = Task.from_dict(data2)
    
    assert task2.color == Color.GREEN
    assert task2.priority == Priority.MEDIUM


def test_optional_fields():
    """Test Optional[T] field handling."""
    
    @dataclassy
    class Contact:
        name: str
        email: Optional[str] = None
        phone: Optional[str] = None
    
    # Test with None values
    data = {"name": "David", "email": None, "phone": "555-1234"}
    contact = Contact.from_dict(data)
    
    assert contact.name == "David"
    assert contact.email is None
    assert contact.phone == "555-1234"
    
    # Test with missing optional fields
    data2 = {"name": "Eve"}
    contact2 = Contact.from_dict(data2)
    
    assert contact2.name == "Eve"
    assert contact2.email is None
    assert contact2.phone is None


def test_list_of_dataclasses():
    """Test List[DataClass] conversion."""
    
    @dataclassy
    class Item:
        name: str
        quantity: int
        price: float
    
    @dataclassy
    class Order:
        order_id: int
        items: List[Item]
        notes: List[str] = field(default_factory=list)
    
    data = {
        "order_id": 1001,
        "items": [
            {"name": "Widget", "quantity": 2, "price": 19.99},
            {"name": "Gadget", "quantity": 1, "price": 39.99}
        ],
        "notes": ["Rush delivery", "Gift wrap"]
    }
    
    order = Order.from_dict(data)
    
    assert order.order_id == 1001
    assert len(order.items) == 2
    assert order.items[0].name == "Widget"
    assert order.items[0].quantity == 2
    assert order.items[0].price == 19.99
    assert order.items[1].name == "Gadget"
    assert order.notes == ["Rush delivery", "Gift wrap"]


def test_dict_with_dataclass_values():
    """Test Dict[str, DataClass] conversion."""
    
    @dataclassy
    class Product:
        name: str
        price: float
    
    @dataclassy
    class Inventory:
        warehouse: str
        products: Dict[str, Product]
    
    data = {
        "warehouse": "West Coast",
        "products": {
            "SKU001": {"name": "Laptop", "price": 999.99},
            "SKU002": {"name": "Mouse", "price": 29.99}
        }
    }
    
    inventory = Inventory.from_dict(data)
    
    assert inventory.warehouse == "West Coast"
    assert len(inventory.products) == 2
    assert inventory.products["SKU001"].name == "Laptop"
    assert inventory.products["SKU001"].price == 999.99
    assert inventory.products["SKU002"].name == "Mouse"


def test_type_coercion():
    """Test basic type coercion."""
    
    @dataclassy
    class Config:
        host: str
        port: int
        timeout: float
        debug: bool
    
    # Test string to other types
    data = {
        "host": "localhost",
        "port": "8080",      # String to int
        "timeout": "30.5",   # String to float
        "debug": "true"      # String to bool
    }
    
    config = Config.from_dict(data)
    
    assert config.host == "localhost"
    assert config.port == 8080
    assert config.timeout == 30.5
    assert config.debug is True


def test_missing_required_field():
    """Test that missing required fields raise an error."""
    
    @dataclassy
    class Required:
        name: str
        value: int
    
    data = {"name": "test"}  # Missing 'value'
    
    with pytest.raises(ValueError, match="Missing required field: value"):
        Required.from_dict(data)


def test_complex_nested_structure():
    """Test complex nested structures with multiple levels."""
    
    @dataclassy
    class Permission:
        action: str
        allowed: bool
    
    @dataclassy
    class Role:
        name: str
        permissions: List[Permission]
    
    @dataclassy
    class User:
        username: str
        roles: List[Role]
        metadata: Optional[Dict[str, str]] = None
    
    data = {
        "username": "admin",
        "roles": [
            {
                "name": "Administrator",
                "permissions": [
                    {"action": "read", "allowed": True},
                    {"action": "write", "allowed": True},
                    {"action": "delete", "allowed": True}
                ]
            },
            {
                "name": "Viewer",
                "permissions": [
                    {"action": "read", "allowed": True},
                    {"action": "write", "allowed": False}
                ]
            }
        ],
        "metadata": {
            "created": "2023-01-01",
            "department": "IT"
        }
    }
    
    user = User.from_dict(data)
    
    assert user.username == "admin"
    assert len(user.roles) == 2
    assert user.roles[0].name == "Administrator"
    assert len(user.roles[0].permissions) == 3
    assert user.roles[0].permissions[0].action == "read"
    assert user.roles[0].permissions[0].allowed is True
    assert user.metadata["department"] == "IT"


def test_to_dict_basic():
    """Test basic to_dict functionality."""
    
    @dataclassy
    class Point:
        x: float
        y: float
        label: str = "origin"
    
    point = Point(3.14, 2.71, "pi-e")
    data = point.to_dict()
    
    assert data == {
        "x": 3.14,
        "y": 2.71,
        "label": "pi-e"
    }


def test_roundtrip_conversion():
    """Test that from_dict and to_dict are inverses."""
    
    @dataclassy
    class Address:
        street: str
        city: str
    
    @dataclassy
    class Person:
        name: str
        age: int
        address: Address
        tags: List[str] = field(default_factory=list)
    
    original_data = {
        "name": "Frank",
        "age": 35,
        "address": {
            "street": "456 Oak Ave",
            "city": "Seattle"
        },
        "tags": ["developer", "python"]
    }
    
    # Convert to dataclass and back
    person = Person.from_dict(original_data)
    converted_data = person.to_dict()
    
    assert converted_data == original_data
    
    # Convert back to dataclass to ensure it still works
    person2 = Person.from_dict(converted_data)
    assert person2.name == person.name
    assert person2.age == person.age
    assert person2.address.street == person.address.street
    assert person2.tags == person.tags