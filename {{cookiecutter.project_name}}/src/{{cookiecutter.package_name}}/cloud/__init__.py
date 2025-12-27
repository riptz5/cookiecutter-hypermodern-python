"""Google Cloud integration module.

This module provides integration with Google Cloud services:
- Firestore for persistent memory
- Cloud Storage for artifacts
- Pub/Sub for event-driven architecture
- Cloud Scheduler for automated cycles
- Vertex AI for advanced ML capabilities

All services use the GCP discovery system for automatic configuration.
"""
from .memory_store import (
    MemoryStore,
    MemoryEntry,
    get_memory_store,
)

__all__ = [
    "MemoryStore",
    "MemoryEntry",
    "get_memory_store",
]
