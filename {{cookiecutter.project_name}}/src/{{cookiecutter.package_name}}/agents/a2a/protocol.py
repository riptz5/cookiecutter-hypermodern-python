"""Agent2Agent (A2A) protocol implementation.

This module implements the A2A protocol for inter-agent communication.

A2A Protocol Features:
- Standardized message format for agent communication
- Agent discovery via capability cards
- Asynchronous message passing
- Support for tasks, results, and status updates

Design Principles:
- Framework-agnostic (works with ADK, LangGraph, etc.)
- Async-first for performance
- Extensible message types
- Zero coupling to specific implementations

Reference: Based on Google's A2A specification
"""
import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Callable, Awaitable
from uuid import uuid4
import logging
import json

logger = logging.getLogger(__name__)


class A2AMessageType(Enum):
    """Types of A2A messages."""
    
    # Task lifecycle
    TASK_REQUEST = "task_request"      # Request to perform a task
    TASK_RESPONSE = "task_response"    # Response with result
    TASK_STATUS = "task_status"        # Status update
    TASK_CANCEL = "task_cancel"        # Cancel a task
    
    # Agent discovery
    DISCOVER = "discover"              # Request agent cards
    AGENT_CARD = "agent_card"          # Agent capability card
    
    # Control
    PING = "ping"                      # Health check
    PONG = "pong"                      # Health check response
    ERROR = "error"                    # Error message


class TaskStatus(Enum):
    """Status of a task."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class A2AMessage:
    """Standard A2A message format.
    
    All inter-agent communication uses this format.
    
    Attributes:
        id: Unique message identifier
        type: Message type
        sender: Sender agent ID
        receiver: Target agent ID (None for broadcast)
        payload: Message data
        timestamp: When message was created
        correlation_id: ID to correlate request/response
        metadata: Additional metadata
    """
    id: str = field(default_factory=lambda: str(uuid4()))
    type: A2AMessageType = A2AMessageType.TASK_REQUEST
    sender: str = ""
    receiver: Optional[str] = None
    payload: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    correlation_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "type": self.type.value,
            "sender": self.sender,
            "receiver": self.receiver,
            "payload": self.payload,
            "timestamp": self.timestamp.isoformat(),
            "correlation_id": self.correlation_id,
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "A2AMessage":
        """Create from dictionary."""
        return cls(
            id=data.get("id", str(uuid4())),
            type=A2AMessageType(data["type"]),
            sender=data.get("sender", ""),
            receiver=data.get("receiver"),
            payload=data.get("payload", {}),
            timestamp=datetime.fromisoformat(data["timestamp"]) if "timestamp" in data else datetime.utcnow(),
            correlation_id=data.get("correlation_id"),
            metadata=data.get("metadata", {}),
        )
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict())
    
    @classmethod
    def from_json(cls, json_str: str) -> "A2AMessage":
        """Create from JSON string."""
        return cls.from_dict(json.loads(json_str))
    
    def create_response(
        self,
        payload: Dict[str, Any],
        msg_type: A2AMessageType = A2AMessageType.TASK_RESPONSE
    ) -> "A2AMessage":
        """Create a response to this message.
        
        Args:
            payload: Response payload
            msg_type: Response message type
            
        Returns:
            Response message with correlation_id set
        """
        return A2AMessage(
            type=msg_type,
            sender=self.receiver or "",
            receiver=self.sender,
            payload=payload,
            correlation_id=self.id,
        )


@dataclass
class AgentCard:
    """Agent capability card (A2A spec).
    
    Describes an agent's capabilities for discovery.
    
    Attributes:
        agent_id: Unique agent identifier
        name: Human-readable name
        description: What the agent does
        capabilities: List of capability strings
        input_schema: JSON schema for input
        output_schema: JSON schema for output
        version: Agent version
        metadata: Additional metadata
    """
    agent_id: str
    name: str
    description: str = ""
    capabilities: List[str] = field(default_factory=list)
    input_schema: Dict[str, Any] = field(default_factory=dict)
    output_schema: Dict[str, Any] = field(default_factory=dict)
    version: str = "1.0.0"
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "description": self.description,
            "capabilities": self.capabilities,
            "input_schema": self.input_schema,
            "output_schema": self.output_schema,
            "version": self.version,
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentCard":
        """Create from dictionary."""
        return cls(**data)
    
    def matches_capability(self, capability: str) -> bool:
        """Check if agent has a capability.
        
        Args:
            capability: Capability to check
            
        Returns:
            True if agent has capability
        """
        return capability in self.capabilities


# Type alias for message handler
MessageHandler = Callable[[A2AMessage], Awaitable[Optional[A2AMessage]]]


class A2AProtocol:
    """Implementation of A2A protocol.
    
    Provides:
    - Message queuing and delivery
    - Agent registration and discovery
    - Request/response correlation
    - Broadcast support
    
    Example:
        >>> protocol = A2AProtocol()
        >>> 
        >>> # Register agents
        >>> protocol.register_agent(AgentCard(
        ...     agent_id="research",
        ...     name="ResearchAgent",
        ...     capabilities=["research", "search"]
        ... ))
        >>> 
        >>> # Send message
        >>> msg = A2AMessage(
        ...     type=A2AMessageType.TASK_REQUEST,
        ...     sender="supervisor",
        ...     receiver="research",
        ...     payload={"task": "Find AI trends"}
        ... )
        >>> await protocol.send(msg)
        >>> 
        >>> # Receive message
        >>> response = await protocol.receive("research")
    """
    
    def __init__(self):
        """Initialize A2A protocol."""
        self._agents: Dict[str, AgentCard] = {}
        self._queues: Dict[str, asyncio.Queue] = {}
        self._handlers: Dict[str, MessageHandler] = {}
        self._pending_requests: Dict[str, asyncio.Future] = {}
        self._running = False
        
        logger.info("A2A Protocol initialized")
    
    def register_agent(self, card: AgentCard) -> None:
        """Register an agent with the protocol.
        
        Args:
            card: Agent capability card
        """
        self._agents[card.agent_id] = card
        self._queues[card.agent_id] = asyncio.Queue()
        logger.info(f"Registered agent: {card.agent_id} with capabilities {card.capabilities}")
    
    def unregister_agent(self, agent_id: str) -> None:
        """Unregister an agent.
        
        Args:
            agent_id: Agent to unregister
        """
        self._agents.pop(agent_id, None)
        self._queues.pop(agent_id, None)
        self._handlers.pop(agent_id, None)
        logger.info(f"Unregistered agent: {agent_id}")
    
    def set_handler(self, agent_id: str, handler: MessageHandler) -> None:
        """Set message handler for an agent.
        
        Args:
            agent_id: Agent ID
            handler: Async function to handle messages
        """
        self._handlers[agent_id] = handler
        logger.debug(f"Set handler for agent: {agent_id}")
    
    async def send(self, message: A2AMessage) -> None:
        """Send a message to an agent.
        
        Args:
            message: Message to send
            
        Raises:
            ValueError: If receiver not registered
        """
        if message.receiver and message.receiver not in self._queues:
            raise ValueError(f"Agent not registered: {message.receiver}")
        
        if message.receiver:
            # Direct message
            await self._queues[message.receiver].put(message)
            logger.debug(f"Sent message {message.id} to {message.receiver}")
        else:
            # Broadcast to all agents except sender
            for agent_id, queue in self._queues.items():
                if agent_id != message.sender:
                    await queue.put(message)
            logger.debug(f"Broadcast message {message.id} to {len(self._queues) - 1} agents")
    
    async def receive(
        self,
        agent_id: str,
        timeout: Optional[float] = None
    ) -> Optional[A2AMessage]:
        """Receive a message for an agent.
        
        Args:
            agent_id: Agent to receive for
            timeout: Timeout in seconds (None = wait forever)
            
        Returns:
            Message if available, None if timeout
        """
        if agent_id not in self._queues:
            raise ValueError(f"Agent not registered: {agent_id}")
        
        try:
            if timeout:
                message = await asyncio.wait_for(
                    self._queues[agent_id].get(),
                    timeout=timeout
                )
            else:
                message = await self._queues[agent_id].get()
            
            logger.debug(f"Agent {agent_id} received message {message.id}")
            return message
            
        except asyncio.TimeoutError:
            return None
    
    async def request(
        self,
        message: A2AMessage,
        timeout: float = 30.0
    ) -> A2AMessage:
        """Send a request and wait for response.
        
        Correlates request and response by message ID.
        
        Args:
            message: Request message
            timeout: Response timeout in seconds
            
        Returns:
            Response message
            
        Raises:
            asyncio.TimeoutError: If no response within timeout
        """
        # Create future for response
        future = asyncio.get_event_loop().create_future()
        self._pending_requests[message.id] = future
        
        try:
            # Send request
            await self.send(message)
            
            # Wait for response
            response = await asyncio.wait_for(future, timeout=timeout)
            return response
            
        finally:
            self._pending_requests.pop(message.id, None)
    
    def _handle_response(self, message: A2AMessage) -> bool:
        """Handle a response message.
        
        Resolves pending request future if correlation matches.
        
        Args:
            message: Response message
            
        Returns:
            True if response was handled
        """
        if message.correlation_id and message.correlation_id in self._pending_requests:
            future = self._pending_requests[message.correlation_id]
            if not future.done():
                future.set_result(message)
            return True
        return False
    
    def discover_agents(self, capability: Optional[str] = None) -> List[AgentCard]:
        """Discover registered agents.
        
        Args:
            capability: Filter by capability (optional)
            
        Returns:
            List of matching agent cards
        """
        if capability:
            return [
                card for card in self._agents.values()
                if card.matches_capability(capability)
            ]
        return list(self._agents.values())
    
    def get_agent_card(self, agent_id: str) -> Optional[AgentCard]:
        """Get agent card by ID.
        
        Args:
            agent_id: Agent ID
            
        Returns:
            Agent card if found
        """
        return self._agents.get(agent_id)
    
    async def start_message_loop(self, agent_id: str) -> None:
        """Start processing messages for an agent.
        
        Runs until stop() is called.
        
        Args:
            agent_id: Agent to process messages for
        """
        if agent_id not in self._handlers:
            raise ValueError(f"No handler set for agent: {agent_id}")
        
        self._running = True
        handler = self._handlers[agent_id]
        
        logger.info(f"Starting message loop for {agent_id}")
        
        while self._running:
            try:
                message = await self.receive(agent_id, timeout=1.0)
                if message:
                    # Check if this is a response to a pending request
                    if message.type == A2AMessageType.TASK_RESPONSE:
                        if self._handle_response(message):
                            continue
                    
                    # Process with handler
                    response = await handler(message)
                    
                    # Send response if handler returned one
                    if response:
                        await self.send(response)
                        
            except Exception as e:
                logger.error(f"Error in message loop: {e}", exc_info=True)
    
    def stop(self) -> None:
        """Stop all message loops."""
        self._running = False
        logger.info("A2A Protocol stopped")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get protocol statistics.
        
        Returns:
            Dictionary of stats
        """
        return {
            "registered_agents": len(self._agents),
            "pending_requests": len(self._pending_requests),
            "queue_sizes": {
                agent_id: queue.qsize()
                for agent_id, queue in self._queues.items()
            },
        }


# Global protocol instance
_protocol: Optional[A2AProtocol] = None


def create_protocol() -> A2AProtocol:
    """Get or create global A2A protocol instance.
    
    Returns:
        Global A2AProtocol instance
    """
    global _protocol
    if _protocol is None:
        _protocol = A2AProtocol()
    return _protocol
