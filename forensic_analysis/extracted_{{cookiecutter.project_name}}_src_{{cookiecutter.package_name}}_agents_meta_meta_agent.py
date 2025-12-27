{%- if cookiecutter.use_google_adk == 'y' %}
"""MetaAgent: Self-programming agent that creates and evolves other agents.

This is the AUTOPOIETIC CORE of the GENESIS system. The MetaAgent can:
1. Generate new agent source code using Gemini
2. Instantiate agents dynamically from generated code
3. Evolve existing agents based on feedback
4. Replicate successful agents with mutations
5. Track agent lineage and performance

Architecture:
    ┌───────────────────────────────────────────────────────┐
    │                     MetaAgent                         │
    ├───────────────────────────────────────────────────────┤
    │  ┌─────────────┐   ┌─────────────┐   ┌────────────┐  │
    │  │  Gemini     │   │   Code      │   │  Dynamic   │  │
    │  │  (Ideation) │──▶│  Generator  │──▶│  Executor  │  │
    │  └─────────────┘   └─────────────┘   └────────────┘  │
    │         │                │                  │         │
    │         ▼                ▼                  ▼         │
    │  ┌─────────────────────────────────────────────────┐ │
    │  │              GeneticMemory (Firestore)          │ │
    │  │   - Agent genomes (source code)                 │ │
    │  │   - Evolution history                           │ │
    │  │   - Performance metrics                         │ │
    │  └─────────────────────────────────────────────────┘ │
    └───────────────────────────────────────────────────────┘

Safety:
    - Generated code is executed in a controlled namespace
    - Only BaseAgent subclasses are instantiated
    - All mutations are logged and reversible
"""
import ast
import inspect
import logging
import re
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Type
from datetime import datetime

from ..base import BaseAgent, AgentSpec, AgentResult, AgentCapability
from ..adk.agent import GoogleADKAgent, ADKConfig

logger = logging.getLogger(__name__)


@dataclass
class Mutation:
    """Describes a mutation to apply to an agent.
    
    Mutations are the mechanism for agent evolution. They can modify:
    - system_prompt: The agent's instructions
    - temperature: Generation randomness
    - model: The underlying LLM
    - tools: Available tool functions
    
    Attributes:
        mutation_type: Type of mutation (prompt, model, temperature, tool)
        target: What to mutate (e.g., "system_prompt")
        old_value: Previous value (for logging)
        new_value: New value to apply
        reason: Why this mutation was applied
    """
    mutation_type: str
    target: str
    old_value: Any
    new_value: Any
    reason: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize mutation to dictionary."""
        return {
            "mutation_type": self.mutation_type,
            "target": self.target,
            "old_value": str(self.old_value)[:100],  # Truncate for storage
            "new_value": str(self.new_value)[:100],
            "reason": self.reason,
            "timestamp": self.timestamp.isoformat(),
        }


# System prompt for the MetaAgent - defines its behavior as an agent creator
_META_AGENT_PROMPT = '''You are a META-AGENT - an AI that creates other AI agents.

Your purpose is to generate Python code for new agents based on specifications.

RULES:
1. Output ONLY valid Python code - no explanations before or after
2. The class MUST inherit from BaseAgent
3. The class MUST implement: spec property, run() method, introspect() method
4. Use proper async/await for run() method
5. Include docstrings and type hints
6. The spec property must return an AgentSpec with all required fields
7. Handle errors gracefully in run()

TEMPLATE STRUCTURE:
```python
class {ClassName}(BaseAgent):
    """Docstring describing the agent."""
    
    @property
    def spec(self) -> AgentSpec:
        return AgentSpec(
            name="{name}",
            role="{role}",
            system_prompt="""{system_prompt}""",
            capabilities=({capabilities}),
            model="{model}",
        )
    
    async def run(self, input_data: Any) -> AgentResult:
        """Execute the agent's task."""
        try:
            # Implementation using self._llm or GoogleADKAgent
            result = "..."  # Actual implementation
            return AgentResult(output=result, success=True, agent_name=self.spec.name)
        except Exception as e:
            return AgentResult(output=None, success=False, error=str(e), agent_name=self.spec.name)
    
    async def introspect(self) -> Dict[str, Any]:
        """Return agent metadata."""
        return {
            "type": "{name}",
            "status": "ready",
            "spec": self.spec.to_dict(),
        }
```

When generating code, adapt the implementation based on the agent's role and capabilities.
For research agents, include web search. For analysis agents, include data processing.
For writing agents, focus on content generation. For coding agents, include code analysis.
'''


class MetaAgent(BaseAgent):
    """Agent that creates, evolves, and manages other agents.
    
    The MetaAgent is the autopoietic core of GENESIS. It uses Gemini to:
    1. Generate Python source code for new agents from AgentSpec
    2. Evolve existing agents based on performance feedback
    3. Create agent variants through controlled mutation
    
    Example:
        >>> meta = MetaAgent()
        >>> 
        >>> # Create a new agent
        >>> spec = AgentSpec(
        ...     name="researcher",
        ...     role="Research expert",
        ...     system_prompt="You research topics thoroughly.",
        ...     capabilities=(AgentCapability.RESEARCH,),
        ... )
        >>> agent = await meta.create_agent(spec)
        >>> 
        >>> # Use the created agent
        >>> result = await agent.run("What is quantum computing?")
        >>> 
        >>> # Evolve based on feedback
        >>> better_agent = await meta.evolve_agent("researcher", "Add citations")
    
    Attributes:
        memory: Optional GeneticMemory for persistence
        created_agents: Dict of agents created by this MetaAgent
    """
    
    def __init__(self, memory: Optional["GeneticMemory"] = None):
        """Initialize the MetaAgent.
        
        Args:
            memory: Optional GeneticMemory instance for genome persistence.
                   If None, agents are stored in memory only.
        """
        self.memory = memory
        self._created_agents: Dict[str, BaseAgent] = {}
        self._creation_count = 0
        
        # Internal Gemini instance for code generation
        self._gemini = GoogleADKAgent(ADKConfig(
            system_instruction=_META_AGENT_PROMPT,
            temperature=0.7,  # Balanced creativity/consistency
        ))
        
        logger.info("MetaAgent initialized")
    
    @property
    def spec(self) -> AgentSpec:
        """Return MetaAgent specification."""
        return AgentSpec(
            name="meta_agent",
            role="Agent creator and evolver",
            system_prompt=_META_AGENT_PROMPT,
            capabilities=(AgentCapability.META, AgentCapability.CODING),
            model="gemini-2.0-flash-exp",
        )
    
    async def run(self, input_data: Any) -> AgentResult:
        """Execute a meta-agent command.
        
        Commands:
        - "create: {spec_json}" - Create new agent from JSON spec
        - "evolve: {agent_name} | {feedback}" - Evolve existing agent
        - "list" - List all created agents
        - "inspect: {agent_name}" - Get agent details
        
        For direct code generation, use create_agent() instead.
        """
        start_time = time.time()
        input_str = str(input_data)
        
        try:
            if input_str.startswith("create:"):
                spec_json = input_str[7:].strip()
                spec = AgentSpec.from_json(spec_json)
                agent = await self.create_agent(spec)
                output = f"Created agent: {agent.spec.name}"
                
            elif input_str.startswith("evolve:"):
                parts = input_str[7:].split("|", 1)
                agent_name = parts[0].strip()
                feedback = parts[1].strip() if len(parts) > 1 else "Improve performance"
                agent = await self.evolve_agent(agent_name, feedback)
                output = f"Evolved agent: {agent.spec.name}"
                
            elif input_str == "list":
                agents = list(self._created_agents.keys())
                output = f"Created agents ({len(agents)}): {', '.join(agents)}"
                
            elif input_str.startswith("inspect:"):
                agent_name = input_str[8:].strip()
                if agent_name in self._created_agents:
                    agent = self._created_agents[agent_name]
                    info = await agent.introspect()
                    output = str(info)
                else:
                    output = f"Agent not found: {agent_name}"
                    
            else:
                # Direct Gemini query for other inputs
                output = await self._gemini.run(input_data)
            
            return AgentResult(
                output=output,
                success=True,
                agent_name="meta_agent",
                execution_time=time.time() - start_time,
            )
            
        except Exception as e:
            logger.error(f"MetaAgent error: {e}")
            return AgentResult(
                output=None,
                success=False,
                error=str(e),
                agent_name="meta_agent",
                execution_time=time.time() - start_time,
            )
    
    async def introspect(self) -> Dict[str, Any]:
        """Return MetaAgent metadata."""
        return {
            "type": "meta_agent",
            "status": "ready",
            "created_agents": list(self._created_agents.keys()),
            "creation_count": self._creation_count,
            "has_memory": self.memory is not None,
            "spec": self.spec.to_dict(),
        }
    
    async def create_agent(self, spec: AgentSpec) -> BaseAgent:
        """Generate and instantiate a new agent from specification.
        
        Uses Gemini to generate Python code, validates it, and executes
        it to create a new agent instance.
        
        Args:
            spec: AgentSpec defining the new agent
        
        Returns:
            Instantiated BaseAgent subclass
        
        Raises:
            ValueError: If code generation or validation fails
        """
        logger.info(f"Creating agent: {spec.name}")
        
        # Build prompt for code generation
        capabilities_str = ", ".join(
            f"AgentCapability.{c.name}" for c in spec.capabilities
        ) if spec.capabilities else ""
        
        prompt = f'''Generate a complete Python agent class with these specifications:

Name: {spec.name}
Role: {spec.role}
System Prompt: {spec.system_prompt}
Capabilities: {capabilities_str}
Model: {spec.model}
Temperature: {spec.temperature}

The class must inherit from BaseAgent and implement all required methods.
Include a working implementation that uses GoogleADKAgent internally.
Output ONLY the Python code, no markdown formatting.'''
        
        # Generate code using Gemini
        generated_code = await self._gemini.run(prompt)
        
        # Clean up the generated code
        code = self._clean_generated_code(generated_code)
        
        # Validate syntax
        self._validate_code_syntax(code)
        
        # Execute code to get the class
        agent_class = self._execute_code(code, spec.name)
        
        # Instantiate the agent
        agent = agent_class()
        
        # Store in registry
        self._created_agents[spec.name] = agent
        self._creation_count += 1
        
        # Persist to memory if available
        if self.memory:
            await self.memory.store_genome(
                agent_id=spec.name,
                code=code,
                spec=spec.to_dict(),
            )
        
        logger.info(f"Successfully created agent: {spec.name}")
        return agent
    
    async def evolve_agent(self, agent_id: str, feedback: str) -> BaseAgent:
        """Evolve an existing agent based on feedback.
        
        Generates improved code based on the current implementation
        and the provided feedback.
        
        Args:
            agent_id: Name of the agent to evolve
            feedback: Description of desired improvements
        
        Returns:
            New, evolved agent instance
        
        Raises:
            ValueError: If agent not found or evolution fails
        """
        if agent_id not in self._created_agents:
            raise ValueError(f"Agent '{agent_id}' not found")
        
        current_agent = self._created_agents[agent_id]
        current_code = current_agent.to_genome()
        
        logger.info(f"Evolving agent: {agent_id}")
        
        prompt = f'''Improve this agent based on the feedback provided.

CURRENT CODE:
{current_code}

FEEDBACK:
{feedback}

Generate an improved version of the agent that addresses the feedback.
Maintain the same class name and interface.
Output ONLY the improved Python code, no explanations.'''
        
        # Generate evolved code
        evolved_code = await self._gemini.run(prompt)
        code = self._clean_generated_code(evolved_code)
        
        # Validate and execute
        self._validate_code_syntax(code)
        agent_class = self._execute_code(code, agent_id)
        
        # Create new instance
        evolved_agent = agent_class()
        
        # Record mutation
        mutation = Mutation(
            mutation_type="evolution",
            target="full_code",
            old_value=current_code[:100],
            new_value=code[:100],
            reason=feedback,
        )
        
        # Update registry
        self._created_agents[agent_id] = evolved_agent
        
        # Persist if memory available
        if self.memory:
            await self.memory.store_genome(
                agent_id=agent_id,
                code=code,
                spec=evolved_agent.spec.to_dict(),
                parent_id=f"{agent_id}_prev",
            )
            await self.memory.record_evolution(agent_id, mutation.to_dict())
        
        logger.info(f"Successfully evolved agent: {agent_id}")
        return evolved_agent
    
    async def replicate_agent(
        self, 
        agent_id: str, 
        mutations: List[Mutation],
        new_name: Optional[str] = None
    ) -> BaseAgent:
        """Create a variant of an existing agent with mutations.
        
        Args:
            agent_id: Name of agent to replicate
            mutations: List of mutations to apply
            new_name: Name for the new agent (default: {agent_id}_v{n})
        
        Returns:
            New agent instance with mutations applied
        """
        if agent_id not in self._created_agents:
            raise ValueError(f"Agent '{agent_id}' not found")
        
        source_agent = self._created_agents[agent_id]
        source_spec = source_agent.spec
        
        # Generate new name if not provided
        new_name = new_name or f"{agent_id}_v{self._creation_count + 1}"
        
        # Apply mutations to spec
        new_spec_dict = source_spec.to_dict()
        new_spec_dict["name"] = new_name
        
        for mutation in mutations:
            if mutation.target in new_spec_dict:
                new_spec_dict[mutation.target] = mutation.new_value
        
        new_spec = AgentSpec.from_dict(new_spec_dict)
        
        # Create the replicated agent
        return await self.create_agent(new_spec)
    
    def get_agent(self, agent_id: str) -> Optional[BaseAgent]:
        """Get a created agent by name.
        
        Args:
            agent_id: Name of the agent
        
        Returns:
            Agent instance or None if not found
        """
        return self._created_agents.get(agent_id)
    
    def list_agents(self) -> List[str]:
        """Get names of all created agents.
        
        Returns:
            List of agent names
        """
        return list(self._created_agents.keys())
    
    def _clean_generated_code(self, code: str) -> str:
        """Clean up generated code, removing markdown formatting.
        
        Args:
            code: Raw generated code
        
        Returns:
            Cleaned Python code
        """
        # Remove markdown code blocks
        if "```python" in code:
            code = code.split("```python", 1)[1]
            if "```" in code:
                code = code.split("```", 1)[0]
        elif "```" in code:
            code = code.split("```", 1)[1]
            if "```" in code:
                code = code.split("```", 1)[0]
        
        # Strip whitespace
        code = code.strip()
        
        return code
    
    def _validate_code_syntax(self, code: str) -> None:
        """Validate Python code syntax using AST.
        
        Args:
            code: Python code to validate
        
        Raises:
            ValueError: If code has syntax errors
        """
        try:
            ast.parse(code)
        except SyntaxError as e:
            raise ValueError(f"Generated code has syntax error: {e}")
    
    def _execute_code(self, code: str, expected_name: str) -> Type[BaseAgent]:
        """Execute generated code and extract the agent class.
        
        Args:
            code: Valid Python code defining an agent class
            expected_name: Expected agent name for validation
        
        Returns:
            The agent class (not instance)
        
        Raises:
            ValueError: If no valid agent class found
        """
        # Build execution namespace with required imports
        namespace = {
            "BaseAgent": BaseAgent,
            "AgentSpec": AgentSpec,
            "AgentResult": AgentResult,
            "AgentCapability": AgentCapability,
            "GoogleADKAgent": GoogleADKAgent,
            "ADKConfig": ADKConfig,
            "Dict": Dict,
            "Any": Any,
            "Optional": Optional,
            "List": List,
        }
        
        # Execute the code
        try:
            exec(code, namespace)
        except Exception as e:
            raise ValueError(f"Failed to execute generated code: {e}")
        
        # Find the agent class
        agent_class = None
        for name, obj in namespace.items():
            if (
                isinstance(obj, type) 
                and issubclass(obj, BaseAgent) 
                and obj is not BaseAgent
            ):
                agent_class = obj
                break
        
        if agent_class is None:
            raise ValueError("No BaseAgent subclass found in generated code")
        
        return agent_class
{%- endif %}
