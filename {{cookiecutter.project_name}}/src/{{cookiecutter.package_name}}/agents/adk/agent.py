{%- if cookiecutter.use_google_adk == 'y' %}
"""Google ADK agent implementation."""
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
import os

try:
    from google import genai
    from google.genai import types
except ImportError:
    raise ImportError(
        "Google GenAI SDK not installed. "
        "Install with: pip install google-genai"
    )


@dataclass
class ADKConfig:
    """Configuration for Google ADK agent.
    
    Attributes:
        model: Model name (e.g., 'gemini-2.0-flash-exp')
        api_key: Google API key (defaults to GOOGLE_API_KEY env var)
        temperature: Sampling temperature (0.0-2.0)
        max_tokens: Maximum tokens to generate
        system_instruction: System instruction for the agent
    """
    model: str = "gemini-2.0-flash-exp"
    api_key: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 8192
    system_instruction: Optional[str] = None
    
    def __post_init__(self):
        """Validate and set defaults."""
        if self.api_key is None:
            self.api_key = os.getenv("GOOGLE_API_KEY")
        
        if not self.api_key:
            raise ValueError(
                "Google API key required. Set GOOGLE_API_KEY environment "
                "variable or pass api_key parameter."
            )


class GoogleADKAgent:
    """Agent using Google's Agent Development Kit (ADK).
    
    This agent uses Google's Gemini models through the ADK for
    advanced agentic capabilities including function calling,
    multi-turn conversations, and structured outputs.
    
    Example:
        >>> config = ADKConfig(
        ...     model="gemini-2.0-flash-exp",
        ...     temperature=0.7
        ... )
        >>> agent = GoogleADKAgent(config)
        >>> response = await agent.run("What is the capital of France?")
        >>> print(response)
        "The capital of France is Paris."
    """
    
    def __init__(self, config: ADKConfig):
        """Initialize the Google ADK agent.
        
        Args:
            config: Agent configuration
        """
        self.config = config
        self.client = genai.Client(api_key=config.api_key)
        self.history: List[Dict[str, Any]] = []
        
        # Configure generation
        self.generation_config = types.GenerateContentConfig(
            temperature=config.temperature,
            max_output_tokens=config.max_tokens,
            system_instruction=config.system_instruction,
        )
    
    async def run(self, prompt: str, **kwargs) -> str:
        """Run the agent with a prompt.
        
        Args:
            prompt: User prompt/query
            **kwargs: Additional generation parameters
            
        Returns:
            Agent response as string
            
        Example:
            >>> response = await agent.run("Explain quantum computing")
        """
        # Update config with kwargs
        config = self.generation_config
        if kwargs:
            config = types.GenerateContentConfig(
                temperature=kwargs.get('temperature', self.config.temperature),
                max_output_tokens=kwargs.get('max_tokens', self.config.max_tokens),
                system_instruction=kwargs.get('system_instruction', self.config.system_instruction),
            )
        
        # Generate response
        response = self.client.models.generate_content(
            model=self.config.model,
            contents=prompt,
            config=config,
        )
        
        # Extract text
        result = response.text
        
        # Update history
        self.history.append({
            "role": "user",
            "content": prompt
        })
        self.history.append({
            "role": "assistant",
            "content": result
        })
        
        return result
    
    async def run_with_tools(
        self,
        prompt: str,
        tools: List[types.Tool],
        **kwargs
    ) -> str:
        """Run agent with function calling tools.
        
        Args:
            prompt: User prompt
            tools: List of tools/functions the agent can call
            **kwargs: Additional parameters
            
        Returns:
            Agent response after tool execution
            
        Example:
            >>> def get_weather(location: str) -> str:
            ...     return f"Weather in {location}: Sunny, 72°F"
            >>> 
            >>> tool = types.Tool(
            ...     function_declarations=[
            ...         types.FunctionDeclaration(
            ...             name="get_weather",
            ...             description="Get weather for a location",
            ...             parameters={
            ...                 "type": "object",
            ...                 "properties": {
            ...                     "location": {"type": "string"}
            ...                 }
            ...             }
            ...         )
            ...     ]
            ... )
            >>> response = await agent.run_with_tools(
            ...     "What's the weather in Paris?",
            ...     tools=[tool]
            ... )
        """
        config = types.GenerateContentConfig(
            temperature=kwargs.get('temperature', self.config.temperature),
            max_output_tokens=kwargs.get('max_tokens', self.config.max_tokens),
            system_instruction=kwargs.get('system_instruction', self.config.system_instruction),
            tools=tools,
        )
        
        response = self.client.models.generate_content(
            model=self.config.model,
            contents=prompt,
            config=config,
        )
        
        return response.text
    
    async def run_streaming(self, prompt: str, **kwargs):
        """Run agent with streaming response.
        
        Args:
            prompt: User prompt
            **kwargs: Additional parameters
            
        Yields:
            Response chunks as they're generated
            
        Example:
            >>> async for chunk in agent.run_streaming("Write a story"):
            ...     print(chunk, end="", flush=True)
        """
        config = types.GenerateContentConfig(
            temperature=kwargs.get('temperature', self.config.temperature),
            max_output_tokens=kwargs.get('max_tokens', self.config.max_tokens),
            system_instruction=kwargs.get('system_instruction', self.config.system_instruction),
        )
        
        response = self.client.models.generate_content_stream(
            model=self.config.model,
            contents=prompt,
            config=config,
        )
        
        full_response = []
        for chunk in response:
            if chunk.text:
                full_response.append(chunk.text)
                yield chunk.text
        
        # Update history
        self.history.append({
            "role": "user",
            "content": prompt
        })
        self.history.append({
            "role": "assistant",
            "content": "".join(full_response)
        })
    
    def clear_history(self):
        """Clear conversation history."""
        self.history = []
    
    def get_history(self) -> List[Dict[str, Any]]:
        """Get conversation history.
        
        Returns:
            List of conversation turns
        """
        return self.history.copy()


# Convenience function for quick usage
async def create_adk_agent(
    model: str = "gemini-2.0-flash-exp",
    temperature: float = 0.7,
    system_instruction: Optional[str] = None,
) -> GoogleADKAgent:
    """Create a Google ADK agent with default configuration.
    
    Args:
        model: Model name
        temperature: Sampling temperature
        system_instruction: System instruction
        
    Returns:
        Configured GoogleADKAgent instance
        
    Example:
        >>> agent = await create_adk_agent(
        ...     model="gemini-2.0-flash-exp",
        ...     system_instruction="You are a helpful assistant."
        ... )
        >>> response = await agent.run("Hello!")
    """
    config = ADKConfig(
        model=model,
        temperature=temperature,
        system_instruction=system_instruction,
    )
    return GoogleADKAgent(config)
{%- endif %}
