# Dataclassy Cookbook

Common patterns and recipes for using dataclassy effectively.

## Table of Contents

1. [Configuration Management](#configuration-management)
2. [API Integration](#api-integration)
3. [Data Validation](#data-validation)
4. [File Processing](#file-processing)
5. [Testing Patterns](#testing-patterns)
6. [Advanced Patterns](#advanced-patterns)

## Configuration Management

### Multi-Environment Configuration

```python
from dataclassy import settings
from pathlib import Path

@settings(
    config_name="config",
    search_dirs=[".", "./config", "/etc/myapp"],
    env_prefix="MYAPP_"
)
class Config:
    """
    Application configuration.
    
    environment : str
        Current environment (dev, staging, prod)
    debug : bool
        Enable debug logging
    database_url : str
        Database connection string
    """
    environment: str = "dev"
    debug: bool = True
    database_url: str = "sqlite:///dev.db"
    api_key: str = ""
    
    def __post_init__(self):
        # Validate environment
        if self.environment not in ("dev", "staging", "prod"):
            raise ValueError(f"Invalid environment: {self.environment}")

# Usage
config = Config()  # Auto-loads from files and env vars

# Override for testing
test_config = Config(environment="test", debug=True)

# Save current config
config.save_config("config.backup.json")
```

### Layered Configuration

```python
from dataclassy import settings

@settings
class DatabaseConfig:
    host: str = "localhost"
    port: int = 5432
    name: str = "myapp"
    pool_size: int = 10

@settings
class CacheConfig:
    backend: str = "redis"
    host: str = "localhost"
    port: int = 6379
    ttl: int = 3600

@settings(config_name="app")
class AppConfig:
    """Main application configuration."""
    database: DatabaseConfig = None
    cache: CacheConfig = None
    debug: bool = False
    
    def __post_init__(self):
        if self.database is None:
            self.database = DatabaseConfig()
        if self.cache is None:
            self.cache = CacheConfig()

# Load with cascading
config = AppConfig.load_config([
    "defaults.json",
    f"{config.environment}.json",
    "local.json"  # Local overrides
])
```

### Dynamic Reloading

```python
import signal
from dataclassy import settings

@settings(config_name="app", auto_load=True)
class Config:
    log_level: str = "INFO"
    timeout: int = 30

config = Config()

def reload_config(signum, frame):
    """Reload configuration on SIGHUP."""
    print("Reloading configuration...")
    config.reload()
    print(f"New log level: {config.log_level}")

# Register signal handler
signal.signal(signal.SIGHUP, reload_config)
```

## API Integration

### REST API Client

```python
from dataclassy import dataclassy
from typing import List, Optional
from datetime import datetime
import requests

@dataclassy
class User:
    id: int
    username: str
    email: str
    created_at: datetime
    is_active: bool = True

@dataclassy
class Post:
    id: int
    title: str
    content: str
    author: User
    tags: List[str] = None

class APIClient:
    def __init__(self, base_url: str):
        self.base_url = base_url
    
    def get_user(self, user_id: int) -> User:
        response = requests.get(f"{self.base_url}/users/{user_id}")
        response.raise_for_status()
        return User.from_dict(response.json())
    
    def get_posts(self, limit: int = 10) -> List[Post]:
        response = requests.get(f"{self.base_url}/posts", params={"limit": limit})
        response.raise_for_status()
        return [Post.from_dict(post) for post in response.json()]

# Usage
client = APIClient("https://api.example.com")
user = client.get_user(123)
posts = client.get_posts(limit=20)
```

### GraphQL Response Handling

```python
from dataclassy import dataclassy
from typing import List

@dataclassy
class PageInfo:
    hasNextPage: bool
    endCursor: str

@dataclassy
class Repository:
    name: str
    description: str
    stargazers: int
    language: str

@dataclassy
class GitHubResponse:
    viewer: dict
    repositories: List[Repository]
    pageInfo: PageInfo

# Parse GraphQL response
query_result = {
    "viewer": {"login": "octocat"},
    "repositories": [
        {"name": "Hello-World", "description": "My first repo", 
         "stargazers": 100, "language": "Python"}
    ],
    "pageInfo": {"hasNextPage": True, "endCursor": "xyz123"}
}

response = GitHubResponse.from_dict(query_result)
```

## Data Validation

### Custom Validators

```python
from dataclassy import dataclassy, Path
from dataclassy.fields import Validator
import re

class Email(Validator):
    """Email field with validation."""
    
    def __init__(self, required: bool = True):
        super().__init__()
        self.required = required
    
    def validate(self, value):
        if value is None and not self.required:
            return
        
        if not isinstance(value, str):
            raise TypeError(f"{self.public_name} must be a string")
        
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, value):
            raise ValueError(f"{self.public_name} is not a valid email address")

@dataclassy
class User:
    username: str
    email: Email = Email()
    avatar: Path = Path(extensions=[".jpg", ".png"], must_exist=False)
    
# Usage
user = User(username="alice", email="alice@example.com", avatar="avatar.png")
```

### Conditional Validation

```python
from dataclassy import dataclassy
from typing import Optional

@dataclassy
class PaymentInfo:
    method: str  # "card" or "bank"
    card_number: Optional[str] = None
    bank_account: Optional[str] = None
    
    def __post_init__(self):
        if self.method == "card" and not self.card_number:
            raise ValueError("Card number required for card payments")
        elif self.method == "bank" and not self.bank_account:
            raise ValueError("Bank account required for bank payments")

# Valid
payment1 = PaymentInfo(method="card", card_number="1234-5678-9012-3456")
payment2 = PaymentInfo(method="bank", bank_account="12345678")
```

## File Processing

### Batch Configuration Processing

```python
from dataclassy import dataclassy
from pathlib import Path
from typing import List

@dataclassy
class ServerConfig:
    name: str
    host: str
    port: int
    enabled: bool = True

@dataclassy
class ClusterConfig:
    name: str
    servers: List[ServerConfig]

def load_all_configs(config_dir: Path) -> List[ClusterConfig]:
    """Load all cluster configurations from a directory."""
    clusters = []
    
    for config_file in config_dir.glob("cluster-*.yaml"):
        cluster = ClusterConfig.from_path(config_file)
        clusters.append(cluster)
    
    return clusters

# Process configs
configs = load_all_configs(Path("./configs"))
active_servers = [
    server 
    for cluster in configs 
    for server in cluster.servers 
    if server.enabled
]
```

### Configuration Templates

```python
from dataclassy import dataclassy
import os

@dataclassy
class DeploymentConfig:
    app_name: str
    version: str
    replicas: int = 3
    cpu_limit: str = "500m"
    memory_limit: str = "512Mi"
    environment: dict = None

def generate_configs(template: DeploymentConfig, environments: List[str]):
    """Generate environment-specific configs from template."""
    for env in environments:
        config = DeploymentConfig(
            app_name=template.app_name,
            version=template.version,
            replicas=template.replicas if env != "dev" else 1,
            cpu_limit=template.cpu_limit,
            memory_limit="2Gi" if env == "prod" else template.memory_limit,
            environment={
                "ENV": env,
                "DEBUG": str(env == "dev").lower()
            }
        )
        config.to_path(f"deploy-{env}.json")

# Generate configs for all environments
template = DeploymentConfig(app_name="myapp", version="1.2.3")
generate_configs(template, ["dev", "staging", "prod"])
```

## Testing Patterns

### Fixture-Based Testing

```python
import pytest
from dataclassy import dataclassy

@dataclassy
class TestData:
    user_id: int
    username: str
    email: str
    is_admin: bool = False

@pytest.fixture
def test_user():
    return TestData(
        user_id=123,
        username="testuser",
        email="test@example.com"
    )

@pytest.fixture
def admin_user():
    return TestData(
        user_id=1,
        username="admin",
        email="admin@example.com",
        is_admin=True
    )

def test_user_creation(test_user):
    assert test_user.username == "testuser"
    assert not test_user.is_admin
    
def test_admin_privileges(admin_user):
    assert admin_user.is_admin
    assert admin_user.user_id == 1
```

### Mock Data Generation

```python
from dataclassy import dataclassy
from typing import List
import random
import string

@dataclassy
class MockUser:
    id: int
    username: str
    email: str
    age: int
    tags: List[str]

def generate_mock_users(count: int) -> List[MockUser]:
    """Generate mock users for testing."""
    users = []
    tags_pool = ["python", "javascript", "docker", "kubernetes", "aws"]
    
    for i in range(count):
        username = ''.join(random.choices(string.ascii_lowercase, k=8))
        users.append(MockUser(
            id=i + 1,
            username=username,
            email=f"{username}@example.com",
            age=random.randint(18, 65),
            tags=random.sample(tags_pool, k=random.randint(1, 3))
        ))
    
    return users

# Generate test data
test_users = generate_mock_users(100)

# Save for later use
for i, user in enumerate(test_users[:10]):
    user.to_path(f"test_data/user_{i}.json")
```

## Advanced Patterns

### Plugin System

```python
from dataclassy import dataclassy
from typing import Protocol, List
from pathlib import Path
import importlib.util

class PluginProtocol(Protocol):
    name: str
    version: str
    def execute(self, context: dict) -> dict: ...

@dataclassy
class PluginConfig:
    name: str
    enabled: bool = True
    config: dict = None

@dataclassy
class PluginRegistry:
    plugins: List[PluginConfig]

def load_plugins(registry_path: Path) -> List[PluginProtocol]:
    """Load plugins based on registry configuration."""
    registry = PluginRegistry.from_path(registry_path)
    loaded_plugins = []
    
    for plugin_config in registry.plugins:
        if not plugin_config.enabled:
            continue
            
        # Load plugin module
        module_path = Path("plugins") / f"{plugin_config.name}.py"
        spec = importlib.util.spec_from_file_location(plugin_config.name, module_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Initialize plugin with config
        plugin = module.Plugin(plugin_config.config or {})
        loaded_plugins.append(plugin)
    
    return loaded_plugins
```

### Event Sourcing

```python
from dataclassy import dataclassy
from datetime import datetime
from typing import List, Any
from enum import Enum

class EventType(Enum):
    CREATED = "created"
    UPDATED = "updated"
    DELETED = "deleted"

@dataclassy
class Event:
    id: str
    timestamp: datetime
    event_type: EventType
    entity_id: str
    data: dict

@dataclassy
class EventStore:
    events: List[Event] = None
    
    def __post_init__(self):
        if self.events is None:
            self.events = []
    
    def add_event(self, event_type: EventType, entity_id: str, data: dict):
        event = Event(
            id=f"{entity_id}_{datetime.now().timestamp()}",
            timestamp=datetime.now(),
            event_type=event_type,
            entity_id=entity_id,
            data=data
        )
        self.events.append(event)
    
    def get_entity_history(self, entity_id: str) -> List[Event]:
        return [e for e in self.events if e.entity_id == entity_id]
    
    def save_snapshot(self, path: Path):
        """Save current state to disk."""
        self.to_path(path)
    
    @classmethod
    def load_snapshot(cls, path: Path) -> 'EventStore':
        """Load state from disk."""
        return cls.from_path(path)

# Usage
store = EventStore()
store.add_event(EventType.CREATED, "user_123", {"name": "Alice"})
store.add_event(EventType.UPDATED, "user_123", {"email": "alice@example.com"})
store.save_snapshot("events.json")
```

### Type-Safe Configuration DSL

```python
from dataclassy import dataclassy, settings
from typing import List, Union

@dataclassy
class Rule:
    field: str
    operator: str  # "eq", "gt", "lt", "contains"
    value: Union[str, int, float]

@dataclassy
class Filter:
    rules: List[Rule]
    combinator: str = "AND"  # "AND" or "OR"

@settings
class QueryConfig:
    """
    Query configuration with filtering rules.
    
    filters : List[Filter]
        List of filter groups to apply
    limit : int
        Maximum number of results
    """
    filters: List[Filter] = None
    limit: int = 100
    offset: int = 0
    
    def to_sql_where(self) -> str:
        """Convert filters to SQL WHERE clause."""
        if not self.filters:
            return ""
        
        conditions = []
        for filter_group in self.filters:
            group_conditions = []
            for rule in filter_group.rules:
                if rule.operator == "eq":
                    group_conditions.append(f"{rule.field} = '{rule.value}'")
                elif rule.operator == "gt":
                    group_conditions.append(f"{rule.field} > {rule.value}")
                # ... more operators
            
            combinator = f" {filter_group.combinator} "
            conditions.append(f"({combinator.join(group_conditions)})")
        
        return " AND ".join(conditions)

# Build complex queries
query = QueryConfig(
    filters=[
        Filter(rules=[
            Rule(field="age", operator="gt", value=18),
            Rule(field="status", operator="eq", value="active")
        ]),
        Filter(rules=[
            Rule(field="country", operator="eq", value="US")
        ], combinator="OR")
    ],
    limit=50
)

print(query.to_sql_where())
# Output: (age > 18 AND status = 'active') AND (country = 'US')
```

## Best Practices

1. **Use Type Hints**: Always specify types for better IDE support and validation
2. **Document Fields**: Use docstrings to document configuration fields
3. **Validate Early**: Add validation in `__post_init__` for complex rules
4. **Layer Configurations**: Use composition for complex configurations
5. **Version Your Configs**: Include version fields for backward compatibility
6. **Test Serialization**: Always test round-trip serialization
7. **Handle Errors Gracefully**: Provide meaningful error messages for validation failures