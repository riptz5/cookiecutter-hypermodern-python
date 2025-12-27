{%- if cookiecutter.use_google_adk == 'y' and cookiecutter.use_google_cloud == 'y' %}
"""GeneticMemory: Persistent storage for agent evolution using Firestore.

This module provides durable storage for the GENESIS autopoietic system:
- Agent genomes (source code)
- Evolution history (mutations, lineage)
- Performance metrics

Schema Design:
    agent_genomes/{agent_id}
        ├── code: str           # Python source code
        ├── spec: dict          # AgentSpec as dictionary
        ├── version: int        # Monotonic version counter
        ├── parent_id: str      # ID of parent agent (for lineage)
        ├── created_at: datetime
        └── metrics: dict       # Performance metrics
    
    agent_genomes/{agent_id}_v{version}
        └── (versioned snapshot)
    
    evolution_history/{event_id}
        ├── agent_id: str
        ├── event_type: str     # create, evolve, replicate, kill
        ├── timestamp: datetime
        └── details: dict

Why Firestore?
    - Native Python SDK with async support
    - Automatic scaling
    - Real-time listeners (for future hot-reload)
    - Document-based model fits agent genomes well
    - Free tier (1GB storage, 50K reads/day) is sufficient for development
"""
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Try to import Firestore
try:
    from google.cloud import firestore
    from google.cloud.firestore_v1.base_query import FieldFilter
    HAS_FIRESTORE = True
except ImportError:
    HAS_FIRESTORE = False
    logger.warning("google-cloud-firestore not installed. GeneticMemory will be in-memory only.")


@dataclass
class AgentGenome:
    """Stored representation of an agent.
    
    This is the "DNA" of an agent - everything needed to recreate it.
    
    Attributes:
        agent_id: Unique identifier for the agent
        code: Python source code of the agent class
        spec: AgentSpec as dictionary
        version: Version number (incremented on evolution)
        created_at: When this version was created
        parent_id: ID of parent agent (for lineage tracking)
        metrics: Performance metrics (success_rate, avg_time, etc.)
    """
    agent_id: str
    code: str
    spec: Dict[str, Any]
    version: int = 1
    created_at: datetime = field(default_factory=datetime.utcnow)
    parent_id: Optional[str] = None
    metrics: Dict[str, float] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to Firestore-compatible dictionary."""
        return {
            "agent_id": self.agent_id,
            "code": self.code,
            "spec": self.spec,
            "version": self.version,
            "created_at": self.created_at,
            "parent_id": self.parent_id,
            "metrics": self.metrics,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentGenome":
        """Create from Firestore document."""
        # Handle Firestore timestamp
        created_at = data.get("created_at")
        if hasattr(created_at, "timestamp"):
            created_at = datetime.fromtimestamp(created_at.timestamp())
        elif isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        elif created_at is None:
            created_at = datetime.utcnow()
        
        return cls(
            agent_id=data["agent_id"],
            code=data["code"],
            spec=data.get("spec", {}),
            version=data.get("version", 1),
            created_at=created_at,
            parent_id=data.get("parent_id"),
            metrics=data.get("metrics", {}),
        )


@dataclass
class EvolutionEvent:
    """Record of an evolution event.
    
    Tracks all changes to agents for auditability and debugging.
    
    Attributes:
        event_id: Unique event identifier
        agent_id: Agent that was modified
        event_type: Type of event (create, evolve, replicate, kill)
        timestamp: When the event occurred
        details: Event-specific details (mutations, feedback, etc.)
    """
    event_id: str
    agent_id: str
    event_type: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    details: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "event_id": self.event_id,
            "agent_id": self.agent_id,
            "event_type": self.event_type,
            "timestamp": self.timestamp,
            "details": self.details,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EvolutionEvent":
        """Create from dictionary."""
        timestamp = data.get("timestamp")
        if hasattr(timestamp, "timestamp"):
            timestamp = datetime.fromtimestamp(timestamp.timestamp())
        elif isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)
        elif timestamp is None:
            timestamp = datetime.utcnow()
        
        return cls(
            event_id=data["event_id"],
            agent_id=data["agent_id"],
            event_type=data["event_type"],
            timestamp=timestamp,
            details=data.get("details", {}),
        )


class GeneticMemory:
    """Persistent storage for agent genomes and evolution history.
    
    Uses Firestore for durable storage, with in-memory fallback
    if Firestore is not available.
    
    Example:
        >>> memory = GeneticMemory()
        >>> 
        >>> # Store an agent genome
        >>> await memory.store_genome(
        ...     agent_id="researcher",
        ...     code="class Researcher(BaseAgent): ...",
        ...     spec={"name": "researcher", ...}
        ... )
        >>> 
        >>> # Retrieve genome
        >>> genome = await memory.get_genome("researcher")
        >>> 
        >>> # Track evolution
        >>> lineage = await memory.get_lineage("researcher")
        >>> 
        >>> # Find best performing agents
        >>> top_agents = await memory.find_fittest(metric="success_rate", limit=5)
    """
    
    def __init__(self, project_id: Optional[str] = None):
        """Initialize GeneticMemory.
        
        Args:
            project_id: GCP project ID. If None, uses default from environment.
        """
        self._use_firestore = HAS_FIRESTORE
        
        if self._use_firestore:
            try:
                self.db = firestore.Client(project=project_id)
                self.genomes = self.db.collection("agent_genomes")
                self.evolution = self.db.collection("evolution_history")
                logger.info(f"GeneticMemory connected to Firestore (project: {project_id or 'default'})")
            except Exception as e:
                logger.warning(f"Could not connect to Firestore: {e}. Using in-memory storage.")
                self._use_firestore = False
        
        # In-memory fallback
        if not self._use_firestore:
            self._memory_genomes: Dict[str, AgentGenome] = {}
            self._memory_evolution: List[EvolutionEvent] = []
            logger.info("GeneticMemory using in-memory storage")
    
    async def store_genome(
        self,
        agent_id: str,
        code: str,
        spec: Optional[Dict[str, Any]] = None,
        parent_id: Optional[str] = None
    ) -> AgentGenome:
        """Store an agent genome.
        
        Creates a new versioned entry. The latest version is always
        stored at agent_id, with versioned snapshots at agent_id_v{n}.
        
        Args:
            agent_id: Unique agent identifier
            code: Python source code
            spec: AgentSpec as dictionary
            parent_id: ID of parent agent (for evolution lineage)
        
        Returns:
            The stored AgentGenome
        """
        # Get current version
        existing = await self.get_genome(agent_id)
        version = existing.version + 1 if existing else 1
        
        genome = AgentGenome(
            agent_id=agent_id,
            code=code,
            spec=spec or {},
            version=version,
            created_at=datetime.utcnow(),
            parent_id=parent_id,
        )
        
        if self._use_firestore:
            # Store versioned snapshot
            self.genomes.document(f"{agent_id}_v{version}").set(genome.to_dict())
            # Store/update latest
            self.genomes.document(agent_id).set(genome.to_dict())
        else:
            # In-memory storage
            self._memory_genomes[f"{agent_id}_v{version}"] = genome
            self._memory_genomes[agent_id] = genome
        
        # Record evolution event
        event_type = "create" if version == 1 else "evolve"
        await self.record_evolution(agent_id, {
            "event_type": event_type,
            "version": version,
            "parent_id": parent_id,
        })
        
        logger.info(f"Stored genome: {agent_id} v{version}")
        return genome
    
    async def get_genome(
        self, 
        agent_id: str, 
        version: Optional[int] = None
    ) -> Optional[AgentGenome]:
        """Retrieve an agent genome.
        
        Args:
            agent_id: Agent identifier
            version: Specific version to retrieve. If None, gets latest.
        
        Returns:
            AgentGenome if found, None otherwise
        """
        doc_id = f"{agent_id}_v{version}" if version else agent_id
        
        if self._use_firestore:
            doc = self.genomes.document(doc_id).get()
            if doc.exists:
                return AgentGenome.from_dict(doc.to_dict())
        else:
            if doc_id in self._memory_genomes:
                return self._memory_genomes[doc_id]
        
        return None
    
    async def get_lineage(self, agent_id: str) -> List[AgentGenome]:
        """Get the evolution lineage of an agent.
        
        Returns the chain of ancestors from oldest to newest.
        
        Args:
            agent_id: Agent to trace lineage for
        
        Returns:
            List of AgentGenome instances, oldest first
        """
        lineage = []
        current_id = agent_id
        
        while current_id:
            genome = await self.get_genome(current_id)
            if genome:
                lineage.append(genome)
                current_id = genome.parent_id
            else:
                break
        
        return list(reversed(lineage))
    
    async def get_all_versions(self, agent_id: str) -> List[AgentGenome]:
        """Get all versions of an agent.
        
        Args:
            agent_id: Agent identifier
        
        Returns:
            List of all versions, oldest first
        """
        versions = []
        
        if self._use_firestore:
            # Query for all versioned documents
            query = self.genomes.where(
                filter=FieldFilter("agent_id", "==", agent_id)
            ).order_by("version")
            
            for doc in query.stream():
                versions.append(AgentGenome.from_dict(doc.to_dict()))
        else:
            # In-memory: filter by agent_id
            for key, genome in self._memory_genomes.items():
                if genome.agent_id == agent_id and "_v" in key:
                    versions.append(genome)
            versions.sort(key=lambda g: g.version)
        
        return versions
    
    async def update_metrics(
        self, 
        agent_id: str, 
        metrics: Dict[str, float]
    ) -> None:
        """Update performance metrics for an agent.
        
        Args:
            agent_id: Agent identifier
            metrics: Dict of metric name -> value
        """
        if self._use_firestore:
            self.genomes.document(agent_id).update({"metrics": metrics})
        else:
            if agent_id in self._memory_genomes:
                self._memory_genomes[agent_id].metrics = metrics
        
        logger.debug(f"Updated metrics for {agent_id}: {metrics}")
    
    async def find_fittest(
        self, 
        metric: str = "success_rate", 
        limit: int = 5
    ) -> List[AgentGenome]:
        """Find agents with best performance on a metric.
        
        Args:
            metric: Metric to rank by (e.g., "success_rate", "avg_time")
            limit: Maximum number of results
        
        Returns:
            List of top-performing AgentGenomes
        """
        results = []
        
        if self._use_firestore:
            try:
                query = (
                    self.genomes
                    .where(filter=FieldFilter(f"metrics.{metric}", ">", 0))
                    .order_by(f"metrics.{metric}", direction=firestore.Query.DESCENDING)
                    .limit(limit)
                )
                
                for doc in query.stream():
                    results.append(AgentGenome.from_dict(doc.to_dict()))
            except Exception as e:
                logger.warning(f"Firestore query failed: {e}")
        else:
            # In-memory: sort by metric
            genomes = [
                g for g in self._memory_genomes.values()
                if metric in g.metrics and "_v" not in g.agent_id
            ]
            genomes.sort(key=lambda g: g.metrics.get(metric, 0), reverse=True)
            results = genomes[:limit]
        
        return results
    
    async def record_evolution(
        self, 
        agent_id: str, 
        details: Dict[str, Any]
    ) -> EvolutionEvent:
        """Record an evolution event.
        
        Args:
            agent_id: Agent that was modified
            details: Event details including event_type
        
        Returns:
            The recorded EvolutionEvent
        """
        import uuid
        
        event = EvolutionEvent(
            event_id=str(uuid.uuid4()),
            agent_id=agent_id,
            event_type=details.get("event_type", "unknown"),
            timestamp=datetime.utcnow(),
            details=details,
        )
        
        if self._use_firestore:
            self.evolution.document(event.event_id).set(event.to_dict())
        else:
            self._memory_evolution.append(event)
        
        return event
    
    async def get_evolution_history(
        self, 
        agent_id: Optional[str] = None,
        limit: int = 100
    ) -> List[EvolutionEvent]:
        """Get evolution history.
        
        Args:
            agent_id: Filter by agent ID. If None, returns all events.
            limit: Maximum number of events to return
        
        Returns:
            List of EvolutionEvents, newest first
        """
        events = []
        
        if self._use_firestore:
            query = self.evolution.order_by("timestamp", direction=firestore.Query.DESCENDING)
            
            if agent_id:
                query = query.where(filter=FieldFilter("agent_id", "==", agent_id))
            
            query = query.limit(limit)
            
            for doc in query.stream():
                events.append(EvolutionEvent.from_dict(doc.to_dict()))
        else:
            # In-memory
            filtered = self._memory_evolution
            if agent_id:
                filtered = [e for e in filtered if e.agent_id == agent_id]
            filtered.sort(key=lambda e: e.timestamp, reverse=True)
            events = filtered[:limit]
        
        return events
    
    async def delete_genome(self, agent_id: str, keep_versions: bool = True) -> bool:
        """Delete an agent genome.
        
        Args:
            agent_id: Agent to delete
            keep_versions: If True, keeps versioned snapshots
        
        Returns:
            True if deletion was successful
        """
        try:
            if self._use_firestore:
                self.genomes.document(agent_id).delete()
                
                if not keep_versions:
                    # Delete all versions
                    versions = await self.get_all_versions(agent_id)
                    for v in versions:
                        self.genomes.document(f"{agent_id}_v{v.version}").delete()
            else:
                if agent_id in self._memory_genomes:
                    del self._memory_genomes[agent_id]
                
                if not keep_versions:
                    to_delete = [
                        k for k in self._memory_genomes 
                        if k.startswith(f"{agent_id}_v")
                    ]
                    for k in to_delete:
                        del self._memory_genomes[k]
            
            # Record kill event
            await self.record_evolution(agent_id, {"event_type": "kill"})
            
            logger.info(f"Deleted genome: {agent_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete genome {agent_id}: {e}")
            return False
{%- elif cookiecutter.use_google_adk == 'y' %}
"""GeneticMemory stub - requires use_google_cloud=y for Firestore integration.

Currently using in-memory storage only. To enable persistence:
1. Regenerate project with use_google_cloud=y
2. Or install google-cloud-firestore and set GOOGLE_CLOUD_PROJECT
"""
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class AgentGenome:
    """In-memory genome representation."""
    agent_id: str
    code: str
    spec: Dict[str, Any]
    version: int = 1
    created_at: datetime = field(default_factory=datetime.utcnow)
    parent_id: Optional[str] = None
    metrics: Dict[str, float] = field(default_factory=dict)


@dataclass  
class EvolutionEvent:
    """In-memory evolution event."""
    event_id: str
    agent_id: str
    event_type: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    details: Dict[str, Any] = field(default_factory=dict)


class GeneticMemory:
    """In-memory genetic memory (Firestore not available)."""
    
    def __init__(self, project_id: Optional[str] = None):
        self._genomes: Dict[str, AgentGenome] = {}
        self._events: List[EvolutionEvent] = []
        logger.info("GeneticMemory: Using in-memory storage (Firestore not enabled)")
    
    async def store_genome(self, agent_id: str, code: str, spec: Dict = None, parent_id: str = None) -> AgentGenome:
        existing = self._genomes.get(agent_id)
        version = existing.version + 1 if existing else 1
        genome = AgentGenome(agent_id=agent_id, code=code, spec=spec or {}, version=version, parent_id=parent_id)
        self._genomes[agent_id] = genome
        return genome
    
    async def get_genome(self, agent_id: str, version: int = None) -> Optional[AgentGenome]:
        return self._genomes.get(agent_id)
    
    async def get_lineage(self, agent_id: str) -> List[AgentGenome]:
        lineage = []
        current = agent_id
        while current and current in self._genomes:
            genome = self._genomes[current]
            lineage.append(genome)
            current = genome.parent_id
        return list(reversed(lineage))
    
    async def update_metrics(self, agent_id: str, metrics: Dict[str, float]) -> None:
        if agent_id in self._genomes:
            self._genomes[agent_id].metrics = metrics
    
    async def find_fittest(self, metric: str = "success_rate", limit: int = 5) -> List[AgentGenome]:
        sorted_genomes = sorted(
            self._genomes.values(),
            key=lambda g: g.metrics.get(metric, 0),
            reverse=True
        )
        return sorted_genomes[:limit]
    
    async def record_evolution(self, agent_id: str, details: Dict[str, Any]) -> EvolutionEvent:
        import uuid
        event = EvolutionEvent(
            event_id=str(uuid.uuid4()),
            agent_id=agent_id,
            event_type=details.get("event_type", "unknown"),
            details=details,
        )
        self._events.append(event)
        return event
    
    async def get_evolution_history(self, agent_id: str = None, limit: int = 100) -> List[EvolutionEvent]:
        events = self._events if not agent_id else [e for e in self._events if e.agent_id == agent_id]
        return sorted(events, key=lambda e: e.timestamp, reverse=True)[:limit]
{%- else %}
"""GeneticMemory stub - requires use_google_adk=y."""
{%- endif %}
