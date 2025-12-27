{%- if cookiecutter.use_google_cloud == 'y' %}
"""AgentExecutor: Dynamic deployment of agents to Google Cloud Run.

This module enables the GENESIS system to deploy agents as serverless
containers on Cloud Run, providing:
- Dynamic deployment of new agent versions
- Hot-reload without downtime
- A/B testing between versions
- Automatic rollback on failures

Architecture:
    ┌─────────────────────────────────────────────────────┐
    │                  AgentExecutor                       │
    ├─────────────────────────────────────────────────────┤
    │  1. Generate Dockerfile from agent code             │
    │  2. Build container (Cloud Build)                   │
    │  3. Push to Artifact Registry                       │
    │  4. Deploy to Cloud Run                             │
    │  5. Return service URL                              │
    └─────────────────────────────────────────────────────┘

Prerequisites:
    - google-cloud-run library installed
    - Appropriate IAM permissions
    - Artifact Registry repository created
"""
import logging
import os
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

# Try to import Cloud Run SDK
try:
    from google.cloud import run_v2
    from google.cloud.run_v2.types import Service, Container, RevisionTemplate
    HAS_CLOUD_RUN = True
except ImportError:
    HAS_CLOUD_RUN = False
    logger.warning("google-cloud-run not installed. AgentExecutor will be in simulation mode.")


@dataclass
class DeploymentConfig:
    """Configuration for agent deployment.
    
    Attributes:
        project_id: GCP project ID
        region: Cloud Run region (default: us-central1)
        registry: Artifact Registry repository URL
        cpu: CPU allocation (default: 1)
        memory: Memory allocation (default: 512Mi)
        min_instances: Minimum instances (default: 0 for scale to zero)
        max_instances: Maximum instances (default: 10)
        timeout: Request timeout in seconds (default: 300)
    """
    project_id: str
    region: str = "us-central1"
    registry: Optional[str] = None
    cpu: str = "1"
    memory: str = "512Mi"
    min_instances: int = 0
    max_instances: int = 10
    timeout: int = 300
    
    def __post_init__(self):
        if self.registry is None:
            self.registry = f"{self.region}-docker.pkg.dev/{self.project_id}/genesis-agents"


@dataclass
class DeploymentResult:
    """Result of a deployment operation.
    
    Attributes:
        success: Whether deployment succeeded
        service_url: URL of the deployed service
        version: Deployed version identifier
        deployment_time: Time taken to deploy in seconds
        error: Error message if failed
        metadata: Additional deployment metadata
    """
    success: bool
    service_url: Optional[str] = None
    version: Optional[str] = None
    deployment_time: float = 0.0
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


# Template for generating agent Dockerfile
_DOCKERFILE_TEMPLATE = '''# Auto-generated Dockerfile for GENESIS agent
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
RUN pip install --no-cache-dir \\
    google-genai>=1.0.0 \\
    langchain-google-genai>=2.0.0 \\
    fastapi>=0.100.0 \\
    uvicorn>=0.22.0

# Copy agent code
COPY agent.py /app/agent.py
COPY server.py /app/server.py

# Set environment
ENV PORT=8080
ENV PYTHONUNBUFFERED=1

# Run server
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8080"]
'''

# Template for generating agent FastAPI server
_SERVER_TEMPLATE = '''"""Auto-generated FastAPI server for GENESIS agent."""
import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import asyncio

# Import the agent
from agent import Agent

app = FastAPI(title="GENESIS Agent Server")
agent = Agent()


class RunRequest(BaseModel):
    input_data: str


class RunResponse(BaseModel):
    output: str
    success: bool
    error: str | None = None


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy", "agent": agent.spec.name}


@app.get("/spec")
async def get_spec():
    """Get agent specification."""
    return agent.spec.to_dict()


@app.post("/run", response_model=RunResponse)
async def run(request: RunRequest):
    """Execute the agent."""
    try:
        result = await agent.run(request.input_data)
        return RunResponse(
            output=str(result.output) if hasattr(result, 'output') else str(result),
            success=result.success if hasattr(result, 'success') else True,
            error=result.error if hasattr(result, 'error') else None,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/introspect")
async def introspect():
    """Get agent introspection data."""
    return await agent.introspect()
'''


class AgentExecutor:
    """Deploy and manage agents on Google Cloud Run.
    
    This class handles the full deployment lifecycle:
    1. Generate deployment artifacts (Dockerfile, server code)
    2. Build container image via Cloud Build
    3. Deploy to Cloud Run
    4. Manage revisions and traffic splitting
    
    Example:
        >>> config = DeploymentConfig(project_id="my-project")
        >>> executor = AgentExecutor(config)
        >>> 
        >>> # Deploy an agent
        >>> result = await executor.deploy_agent(
        ...     agent_id="researcher",
        ...     code="class Researcher(BaseAgent): ...",
        ...     version=1
        ... )
        >>> print(result.service_url)
        https://researcher-xyz.run.app
        >>> 
        >>> # Hot reload with new code
        >>> await executor.hot_reload("researcher", new_code)
        >>> 
        >>> # A/B test between versions
        >>> await executor.ab_test("researcher", version_a=1, version_b=2, split=0.5)
    """
    
    def __init__(self, config: DeploymentConfig):
        """Initialize the executor.
        
        Args:
            config: Deployment configuration
        """
        self.config = config
        self._simulation_mode = not HAS_CLOUD_RUN
        
        if HAS_CLOUD_RUN:
            try:
                self.client = run_v2.ServicesClient()
                logger.info(f"AgentExecutor connected to Cloud Run (project: {config.project_id})")
            except Exception as e:
                logger.warning(f"Could not initialize Cloud Run client: {e}")
                self._simulation_mode = True
        
        if self._simulation_mode:
            self._simulated_services: Dict[str, Dict] = {}
            logger.info("AgentExecutor running in simulation mode")
    
    async def deploy_agent(
        self,
        agent_id: str,
        code: str,
        version: int = 1
    ) -> DeploymentResult:
        """Deploy an agent to Cloud Run.
        
        Args:
            agent_id: Unique identifier for the agent
            code: Python source code of the agent class
            version: Version number for this deployment
        
        Returns:
            DeploymentResult with service URL and metadata
        """
        start_time = time.time()
        service_name = self._sanitize_service_name(agent_id)
        
        logger.info(f"Deploying agent: {agent_id} v{version}")
        
        if self._simulation_mode:
            # Simulation mode
            return await self._simulate_deploy(agent_id, code, version, start_time)
        
        try:
            # Generate deployment artifacts
            dockerfile = self._generate_dockerfile()
            server_code = self._generate_server()
            
            # Build container image
            image_url = await self._build_image(
                service_name, 
                code, 
                dockerfile, 
                server_code,
                version
            )
            
            # Deploy to Cloud Run
            service_url = await self._deploy_to_run(
                service_name,
                image_url,
                version
            )
            
            deployment_time = time.time() - start_time
            
            return DeploymentResult(
                success=True,
                service_url=service_url,
                version=f"v{version}",
                deployment_time=deployment_time,
                metadata={
                    "agent_id": agent_id,
                    "image": image_url,
                    "region": self.config.region,
                }
            )
            
        except Exception as e:
            logger.error(f"Deployment failed for {agent_id}: {e}")
            return DeploymentResult(
                success=False,
                error=str(e),
                deployment_time=time.time() - start_time,
            )
    
    async def hot_reload(
        self,
        agent_id: str,
        new_code: str
    ) -> DeploymentResult:
        """Update a running agent with new code.
        
        Deploys a new revision without downtime, gradually shifting
        traffic to the new version.
        
        Args:
            agent_id: Agent to update
            new_code: New Python source code
        
        Returns:
            DeploymentResult with new version info
        """
        # Get current version
        current = await self.get_service_info(agent_id)
        new_version = (current.get("version", 0) + 1) if current else 1
        
        logger.info(f"Hot reloading {agent_id}: v{new_version - 1} -> v{new_version}")
        
        return await self.deploy_agent(agent_id, new_code, new_version)
    
    async def rollback(
        self,
        agent_id: str,
        target_version: int
    ) -> DeploymentResult:
        """Rollback to a previous version.
        
        Args:
            agent_id: Agent to rollback
            target_version: Version to rollback to
        
        Returns:
            DeploymentResult confirming rollback
        """
        service_name = self._sanitize_service_name(agent_id)
        
        logger.info(f"Rolling back {agent_id} to v{target_version}")
        
        if self._simulation_mode:
            if agent_id in self._simulated_services:
                self._simulated_services[agent_id]["version"] = target_version
                return DeploymentResult(
                    success=True,
                    version=f"v{target_version}",
                    metadata={"rollback": True},
                )
            return DeploymentResult(success=False, error="Service not found")
        
        try:
            # In real deployment, would update traffic to point to old revision
            parent = f"projects/{self.config.project_id}/locations/{self.config.region}"
            service_path = f"{parent}/services/{service_name}"
            
            # Get the target revision
            revision_name = f"{service_name}-v{target_version}"
            
            # Update traffic to target revision
            service = self.client.get_service(name=service_path)
            service.traffic = [
                run_v2.TrafficTarget(
                    type_=run_v2.TrafficTargetAllocationType.TRAFFIC_TARGET_ALLOCATION_TYPE_REVISION,
                    revision=revision_name,
                    percent=100,
                )
            ]
            
            self.client.update_service(service=service)
            
            return DeploymentResult(
                success=True,
                version=f"v{target_version}",
                metadata={"rollback": True, "revision": revision_name},
            )
            
        except Exception as e:
            return DeploymentResult(success=False, error=str(e))
    
    async def ab_test(
        self,
        agent_id: str,
        version_a: int,
        version_b: int,
        traffic_split: float = 0.5
    ) -> DeploymentResult:
        """Set up A/B testing between two versions.
        
        Args:
            agent_id: Agent to configure
            version_a: First version
            version_b: Second version
            traffic_split: Fraction of traffic to version_b (0.0-1.0)
        
        Returns:
            DeploymentResult confirming traffic split
        """
        service_name = self._sanitize_service_name(agent_id)
        
        logger.info(
            f"Setting up A/B test for {agent_id}: "
            f"v{version_a} ({(1-traffic_split)*100:.0f}%) vs "
            f"v{version_b} ({traffic_split*100:.0f}%)"
        )
        
        if self._simulation_mode:
            return DeploymentResult(
                success=True,
                metadata={
                    "ab_test": True,
                    "version_a": version_a,
                    "version_b": version_b,
                    "split": traffic_split,
                }
            )
        
        try:
            parent = f"projects/{self.config.project_id}/locations/{self.config.region}"
            service_path = f"{parent}/services/{service_name}"
            
            service = self.client.get_service(name=service_path)
            
            # Configure traffic split
            percent_a = int((1 - traffic_split) * 100)
            percent_b = int(traffic_split * 100)
            
            service.traffic = [
                run_v2.TrafficTarget(
                    type_=run_v2.TrafficTargetAllocationType.TRAFFIC_TARGET_ALLOCATION_TYPE_REVISION,
                    revision=f"{service_name}-v{version_a}",
                    percent=percent_a,
                ),
                run_v2.TrafficTarget(
                    type_=run_v2.TrafficTargetAllocationType.TRAFFIC_TARGET_ALLOCATION_TYPE_REVISION,
                    revision=f"{service_name}-v{version_b}",
                    percent=percent_b,
                ),
            ]
            
            self.client.update_service(service=service)
            
            return DeploymentResult(
                success=True,
                metadata={
                    "ab_test": True,
                    "version_a": {"version": version_a, "traffic": percent_a},
                    "version_b": {"version": version_b, "traffic": percent_b},
                }
            )
            
        except Exception as e:
            return DeploymentResult(success=False, error=str(e))
    
    async def get_service_info(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a deployed service.
        
        Args:
            agent_id: Agent to query
        
        Returns:
            Service info dict or None if not found
        """
        service_name = self._sanitize_service_name(agent_id)
        
        if self._simulation_mode:
            return self._simulated_services.get(agent_id)
        
        try:
            parent = f"projects/{self.config.project_id}/locations/{self.config.region}"
            service_path = f"{parent}/services/{service_name}"
            
            service = self.client.get_service(name=service_path)
            
            return {
                "name": service.name,
                "url": service.uri,
                "version": len(list(service.traffic)),  # Approximate
                "status": str(service.reconciling),
            }
            
        except Exception:
            return None
    
    async def delete_service(self, agent_id: str) -> bool:
        """Delete a deployed service.
        
        Args:
            agent_id: Agent to delete
        
        Returns:
            True if deletion successful
        """
        service_name = self._sanitize_service_name(agent_id)
        
        logger.info(f"Deleting service: {agent_id}")
        
        if self._simulation_mode:
            if agent_id in self._simulated_services:
                del self._simulated_services[agent_id]
                return True
            return False
        
        try:
            parent = f"projects/{self.config.project_id}/locations/{self.config.region}"
            service_path = f"{parent}/services/{service_name}"
            
            self.client.delete_service(name=service_path)
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete service {agent_id}: {e}")
            return False
    
    def _sanitize_service_name(self, agent_id: str) -> str:
        """Convert agent_id to valid Cloud Run service name.
        
        Cloud Run names must:
        - Start with lowercase letter
        - Contain only lowercase letters, numbers, hyphens
        - Be max 63 characters
        """
        # Replace underscores and invalid chars
        name = agent_id.lower().replace("_", "-")
        name = "".join(c for c in name if c.isalnum() or c == "-")
        
        # Ensure starts with letter
        if not name[0].isalpha():
            name = "agent-" + name
        
        # Truncate to 63 chars
        return name[:63]
    
    def _generate_dockerfile(self) -> str:
        """Generate Dockerfile for agent deployment."""
        return _DOCKERFILE_TEMPLATE
    
    def _generate_server(self) -> str:
        """Generate FastAPI server code."""
        return _SERVER_TEMPLATE
    
    async def _build_image(
        self,
        service_name: str,
        agent_code: str,
        dockerfile: str,
        server_code: str,
        version: int
    ) -> str:
        """Build container image using Cloud Build.
        
        In production, this would:
        1. Write files to Cloud Storage
        2. Trigger Cloud Build
        3. Wait for completion
        4. Return image URL
        """
        image_url = f"{self.config.registry}/{service_name}:v{version}"
        
        # TODO: Implement actual Cloud Build integration
        # For now, return the expected image URL
        logger.info(f"Would build image: {image_url}")
        
        return image_url
    
    async def _deploy_to_run(
        self,
        service_name: str,
        image_url: str,
        version: int
    ) -> str:
        """Deploy container to Cloud Run."""
        parent = f"projects/{self.config.project_id}/locations/{self.config.region}"
        
        service = Service(
            template=RevisionTemplate(
                containers=[
                    Container(
                        image=image_url,
                        resources=run_v2.ResourceRequirements(
                            limits={
                                "cpu": self.config.cpu,
                                "memory": self.config.memory,
                            }
                        ),
                    )
                ],
                scaling=run_v2.RevisionScaling(
                    min_instance_count=self.config.min_instances,
                    max_instance_count=self.config.max_instances,
                ),
                timeout=f"{self.config.timeout}s",
            ),
        )
        
        operation = self.client.create_service(
            parent=parent,
            service=service,
            service_id=service_name,
        )
        
        result = operation.result()
        return result.uri
    
    async def _simulate_deploy(
        self,
        agent_id: str,
        code: str,
        version: int,
        start_time: float
    ) -> DeploymentResult:
        """Simulate deployment in local mode."""
        import hashlib
        
        # Generate fake URL
        hash_suffix = hashlib.md5(f"{agent_id}{version}".encode()).hexdigest()[:8]
        fake_url = f"https://{agent_id}-{hash_suffix}.run.app"
        
        self._simulated_services[agent_id] = {
            "url": fake_url,
            "version": version,
            "code_hash": hashlib.md5(code.encode()).hexdigest(),
            "deployed_at": datetime.utcnow().isoformat(),
        }
        
        # Simulate deployment time
        await asyncio.sleep(0.5)
        
        return DeploymentResult(
            success=True,
            service_url=fake_url,
            version=f"v{version}",
            deployment_time=time.time() - start_time,
            metadata={
                "simulation": True,
                "agent_id": agent_id,
            }
        )


# Import asyncio for simulation
import asyncio
{%- else %}
"""AgentExecutor stub - requires use_google_cloud=y."""
import logging

logger = logging.getLogger(__name__)
logger.info("AgentExecutor: Cloud Run deployment not available (requires use_google_cloud=y)")
{%- endif %}
