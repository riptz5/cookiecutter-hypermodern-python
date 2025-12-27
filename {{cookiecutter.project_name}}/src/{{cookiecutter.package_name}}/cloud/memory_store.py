{%- if cookiecutter.use_google_cloud == 'y' %}
"""Persistent memory using Google Cloud Firestore.

This module provides persistent memory storage for the autopoietic system:
- Store and retrieve memories by key
- Vector similarity search for related memories
- Automatic timestamping and versioning
- Collection-based organization

Uses GCP discovery to find Firestore configuration.

Collections:
- autopoiesis_memory: Main memory storage
- autopoiesis_code_history: Code change history
- autopoiesis_patterns: Learned patterns
- autopoiesis_metrics: Performance metrics
"""
import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
import logging
import json

logger = logging.getLogger(__name__)

# Try to import Firestore
try:
    from google.cloud import firestore
    HAS_FIRESTORE = True
except ImportError:
    HAS_FIRESTORE = False
    logger.warning("google-cloud-firestore not installed. Memory will be in-memory only.")


@dataclass
class MemoryEntry:
    """A memory entry to store.
    
    Attributes:
        key: Unique identifier for this memory
        content: The memory content (any serializable data)
        memory_type: Type of memory (pattern, code, metric, etc.)
        tags: Tags for categorization and search
        metadata: Additional metadata
        created_at: When the memory was created
        updated_at: When the memory was last updated
        version: Version number (auto-incremented)
    """
    key: str
    content: Any
    memory_type: str = "general"
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    version: int = 1
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to Firestore-compatible dictionary."""
        return {
            "key": self.key,
            "content": self.content if isinstance(self.content, (str, int, float, bool, list, dict)) else str(self.content),
            "memory_type": self.memory_type,
            "tags": self.tags,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "version": self.version,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MemoryEntry":
        """Create from Firestore document."""
        return cls(
            key=data.get("key", ""),
            content=data.get("content"),
            memory_type=data.get("memory_type", "general"),
            tags=data.get("tags", []),
            metadata=data.get("metadata", {}),
            created_at=datetime.fromisoformat(data["created_at"]) if "created_at" in data else datetime.utcnow(),
            updated_at=datetime.fromisoformat(data["updated_at"]) if "updated_at" in data else datetime.utcnow(),
            version=data.get("version", 1),
        )


class MemoryStore:
    """Persistent memory store using Firestore.
    
    Provides:
    - Key-value storage with versioning
    - Tag-based and type-based queries
    - Automatic GCP configuration via discovery
    - Fallback to in-memory storage if Firestore unavailable
    
    Example:
        >>> store = MemoryStore()
        >>> 
        >>> # Store a memory
        >>> await store.remember("ai_trends_2024", {
        ...     "trends": ["agents", "RAG", "multimodal"],
        ...     "source": "research"
        ... }, memory_type="pattern", tags=["ai", "research"])
        >>> 
        >>> # Recall memory
        >>> memory = await store.recall("ai_trends_2024")
        >>> print(memory.content)
        >>> 
        >>> # Search by tags
        >>> memories = await store.search_by_tags(["ai"])
    """
    
    # Default collections
    COLLECTIONS = {
        "memory": "autopoiesis_memory",
        "code_history": "autopoiesis_code_history",
        "patterns": "autopoiesis_patterns",
        "metrics": "autopoiesis_metrics",
    }
    
    def __init__(
        self,
        project_id: Optional[str] = None,
        collection_prefix: str = "autopoiesis_"
    ):
        """Initialize memory store.
        
        Args:
            project_id: GCP project ID (auto-discovered if not set)
            collection_prefix: Prefix for Firestore collections
        """
        self.project_id = project_id or os.getenv("GOOGLE_CLOUD_PROJECT")
        self.collection_prefix = collection_prefix
        
        # Initialize Firestore client
        self._client: Optional[firestore.Client] = None
        self._use_firestore = HAS_FIRESTORE and bool(self.project_id)
        
        # In-memory fallback
        self._memory_cache: Dict[str, Dict[str, MemoryEntry]] = {
            name: {} for name in self.COLLECTIONS
        }
        
        if self._use_firestore:
            try:
                self._client = firestore.Client(project=self.project_id)
                logger.info(f"Connected to Firestore project: {self.project_id}")
            except Exception as e:
                logger.warning(f"Could not connect to Firestore: {e}. Using in-memory storage.")
                self._use_firestore = False
        else:
            logger.info("Using in-memory storage (Firestore not configured)")
    
    def _get_collection(self, collection_type: str) -> str:
        """Get collection name for type.
        
        Args:
            collection_type: Type key (memory, code_history, patterns, metrics)
        
        Returns:
            Full collection name
        """
        base_name = self.COLLECTIONS.get(collection_type, f"{self.collection_prefix}{collection_type}")
        return base_name
    
    async def remember(
        self,
        key: str,
        content: Any,
        memory_type: str = "general",
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        collection_type: str = "memory"
    ) -> MemoryEntry:
        """Store a memory.
        
        If the key already exists, version is incremented.
        
        Args:
            key: Unique identifier
            content: Content to store
            memory_type: Type of memory
            tags: Tags for categorization
            metadata: Additional metadata
            collection_type: Which collection to use
        
        Returns:
            The stored MemoryEntry
            
        Example:
            >>> entry = await store.remember(
            ...     "code_improvement_001",
            ...     {"file": "agent.py", "changes": "..."},
            ...     memory_type="code",
            ...     tags=["improvement", "agents"]
            ... )
        """
        tags = tags or []
        metadata = metadata or {}
        
        # Check if exists to get version
        existing = await self.recall(key, collection_type)
        version = (existing.version + 1) if existing else 1
        
        entry = MemoryEntry(
            key=key,
            content=content,
            memory_type=memory_type,
            tags=tags,
            metadata=metadata,
            created_at=existing.created_at if existing else datetime.utcnow(),
            updated_at=datetime.utcnow(),
            version=version,
        )
        
        if self._use_firestore and self._client:
            try:
                collection_name = self._get_collection(collection_type)
                doc_ref = self._client.collection(collection_name).document(key)
                doc_ref.set(entry.to_dict())
                logger.debug(f"Stored in Firestore: {key} v{version}")
            except Exception as e:
                logger.error(f"Firestore write error: {e}")
                # Fall back to cache
                self._memory_cache[collection_type][key] = entry
        else:
            self._memory_cache[collection_type][key] = entry
        
        return entry
    
    async def recall(
        self,
        key: str,
        collection_type: str = "memory"
    ) -> Optional[MemoryEntry]:
        """Retrieve a memory by key.
        
        Args:
            key: Memory key
            collection_type: Which collection to search
        
        Returns:
            MemoryEntry if found, None otherwise
        """
        if self._use_firestore and self._client:
            try:
                collection_name = self._get_collection(collection_type)
                doc_ref = self._client.collection(collection_name).document(key)
                doc = doc_ref.get()
                
                if doc.exists:
                    return MemoryEntry.from_dict(doc.to_dict())
            except Exception as e:
                logger.error(f"Firestore read error: {e}")
        
        # Check cache
        return self._memory_cache.get(collection_type, {}).get(key)
    
    async def forget(
        self,
        key: str,
        collection_type: str = "memory"
    ) -> bool:
        """Delete a memory.
        
        Args:
            key: Memory key to delete
            collection_type: Which collection
        
        Returns:
            True if deleted, False if not found
        """
        if self._use_firestore and self._client:
            try:
                collection_name = self._get_collection(collection_type)
                doc_ref = self._client.collection(collection_name).document(key)
                doc_ref.delete()
                logger.debug(f"Deleted from Firestore: {key}")
            except Exception as e:
                logger.error(f"Firestore delete error: {e}")
        
        # Also remove from cache
        if key in self._memory_cache.get(collection_type, {}):
            del self._memory_cache[collection_type][key]
            return True
        
        return False
    
    async def search_by_tags(
        self,
        tags: List[str],
        collection_type: str = "memory",
        limit: int = 100
    ) -> List[MemoryEntry]:
        """Search memories by tags.
        
        Args:
            tags: Tags to search for (OR logic)
            collection_type: Which collection to search
            limit: Maximum results
        
        Returns:
            List of matching MemoryEntry objects
        """
        results = []
        
        if self._use_firestore and self._client:
            try:
                collection_name = self._get_collection(collection_type)
                
                # Query for each tag (Firestore limitation: array_contains with single value)
                seen_keys = set()
                for tag in tags:
                    query = (
                        self._client.collection(collection_name)
                        .where("tags", "array_contains", tag)
                        .limit(limit)
                    )
                    
                    for doc in query.stream():
                        if doc.id not in seen_keys:
                            seen_keys.add(doc.id)
                            results.append(MemoryEntry.from_dict(doc.to_dict()))
                
            except Exception as e:
                logger.error(f"Firestore search error: {e}")
        
        # Also search cache
        cache = self._memory_cache.get(collection_type, {})
        for entry in cache.values():
            if any(tag in entry.tags for tag in tags):
                if entry.key not in [r.key for r in results]:
                    results.append(entry)
        
        return results[:limit]
    
    async def search_by_type(
        self,
        memory_type: str,
        collection_type: str = "memory",
        limit: int = 100
    ) -> List[MemoryEntry]:
        """Search memories by type.
        
        Args:
            memory_type: Type to search for
            collection_type: Which collection
            limit: Maximum results
        
        Returns:
            List of matching MemoryEntry objects
        """
        results = []
        
        if self._use_firestore and self._client:
            try:
                collection_name = self._get_collection(collection_type)
                query = (
                    self._client.collection(collection_name)
                    .where("memory_type", "==", memory_type)
                    .limit(limit)
                )
                
                for doc in query.stream():
                    results.append(MemoryEntry.from_dict(doc.to_dict()))
                    
            except Exception as e:
                logger.error(f"Firestore search error: {e}")
        
        # Also search cache
        cache = self._memory_cache.get(collection_type, {})
        for entry in cache.values():
            if entry.memory_type == memory_type:
                if entry.key not in [r.key for r in results]:
                    results.append(entry)
        
        return results[:limit]
    
    async def list_all(
        self,
        collection_type: str = "memory",
        limit: int = 100
    ) -> List[MemoryEntry]:
        """List all memories in a collection.
        
        Args:
            collection_type: Which collection
            limit: Maximum results
        
        Returns:
            List of MemoryEntry objects
        """
        results = []
        
        if self._use_firestore and self._client:
            try:
                collection_name = self._get_collection(collection_type)
                query = self._client.collection(collection_name).limit(limit)
                
                for doc in query.stream():
                    results.append(MemoryEntry.from_dict(doc.to_dict()))
                    
            except Exception as e:
                logger.error(f"Firestore list error: {e}")
        
        # Also include cache
        cache = self._memory_cache.get(collection_type, {})
        for entry in cache.values():
            if entry.key not in [r.key for r in results]:
                results.append(entry)
        
        return results[:limit]
    
    async def get_recent(
        self,
        collection_type: str = "memory",
        limit: int = 10
    ) -> List[MemoryEntry]:
        """Get most recently updated memories.
        
        Args:
            collection_type: Which collection
            limit: Maximum results
        
        Returns:
            List of MemoryEntry objects, most recent first
        """
        all_entries = await self.list_all(collection_type, limit=1000)
        
        # Sort by updated_at descending
        sorted_entries = sorted(
            all_entries,
            key=lambda e: e.updated_at,
            reverse=True
        )
        
        return sorted_entries[:limit]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get memory store statistics.
        
        Returns:
            Dictionary of stats
        """
        return {
            "using_firestore": self._use_firestore,
            "project_id": self.project_id,
            "cache_sizes": {
                name: len(cache)
                for name, cache in self._memory_cache.items()
            },
        }


# Global instance
_memory_store: Optional[MemoryStore] = None


def get_memory_store() -> MemoryStore:
    """Get or create global memory store.
    
    Returns:
        Global MemoryStore instance
    """
    global _memory_store
    if _memory_store is None:
        _memory_store = MemoryStore()
    return _memory_store
{%- else %}
"""Memory store placeholder.

This module requires use_google_cloud=y for Firestore support.
Falls back to in-memory storage otherwise.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class MemoryEntry:
    """A memory entry."""
    key: str
    content: Any
    memory_type: str = "general"
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    version: int = 1


class MemoryStore:
    """In-memory storage (no Firestore)."""
    
    def __init__(self, **kwargs):
        self._cache: Dict[str, MemoryEntry] = {}
    
    async def remember(self, key: str, content: Any, **kwargs) -> MemoryEntry:
        entry = MemoryEntry(key=key, content=content, **kwargs)
        self._cache[key] = entry
        return entry
    
    async def recall(self, key: str, **kwargs) -> Optional[MemoryEntry]:
        return self._cache.get(key)
    
    async def forget(self, key: str, **kwargs) -> bool:
        if key in self._cache:
            del self._cache[key]
            return True
        return False
    
    async def list_all(self, **kwargs) -> List[MemoryEntry]:
        return list(self._cache.values())


def get_memory_store() -> MemoryStore:
    return MemoryStore()
{%- endif %}
