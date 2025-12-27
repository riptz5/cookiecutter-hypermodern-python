"""Agent2Agent (A2A) protocol implementation.

This module implements Google's A2A protocol for agent interoperability:
- Standardized message format
- Agent discovery and capability cards
- Secure inter-agent communication
- Framework-agnostic design

Reference: https://google.github.io/A2A/
"""
from .protocol import (
    A2AMessage,
    A2AMessageType,
    AgentCard,
    A2AProtocol,
    create_protocol,
)

__all__ = [
    "A2AMessage",
    "A2AMessageType",
    "AgentCard",
    "A2AProtocol",
    "create_protocol",
]
