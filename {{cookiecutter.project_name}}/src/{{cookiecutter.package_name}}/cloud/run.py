{%- if cookiecutter.use_google_cloud == 'y' %}
"""Cloud Run deployment operations.

Proporciona utilidades para desplegar y gestionar
servicios en Google Cloud Run.
"""
import logging
import os
import subprocess
from dataclasses import dataclass
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)


@dataclass
class DeploymentConfig:
    """Configuracion de deployment.
    
    Attributes:
        service_name: Nombre del servicio Cloud Run
        region: Region de deployment
        image: Imagen de contenedor
        memory: Memoria asignada
        cpu: CPUs asignados
        min_instances: Instancias minimas
        max_instances: Instancias maximas
        env_vars: Variables de entorno
        allow_unauthenticated: Si permite acceso publico
    """
    service_name: str = "genesis"
    region: str = "us-central1"
    image: Optional[str] = None
    memory: str = "256Mi"
    cpu: str = "1"
    min_instances: int = 0
    max_instances: int = 1
    env_vars: Dict[str, str] = None
    allow_unauthenticated: bool = False
    
    def __post_init__(self):
        if self.env_vars is None:
            self.env_vars = {}


class CloudRunDeployer:
    """Deployer para Google Cloud Run.
    
    Gestiona el deployment de servicios usando gcloud CLI
    o la API de Cloud Run directamente.
    
    Example:
        >>> deployer = CloudRunDeployer()
        >>> url = await deployer.deploy()
        >>> print(f"Service deployed at: {url}")
    """
    
    def __init__(
        self,
        project_id: Optional[str] = None,
        config: Optional[DeploymentConfig] = None,
    ):
        """Inicializa el deployer.
        
        Args:
            project_id: ID del proyecto GCP
            config: Configuracion de deployment
        """
        self._project_id = project_id or os.getenv("GOOGLE_CLOUD_PROJECT")
        self._config = config or DeploymentConfig()
        self._client = None
    
    @property
    def config(self) -> DeploymentConfig:
        """Retorna configuracion actual."""
        return self._config
    
    async def deploy(
        self,
        image: Optional[str] = None,
        env_vars: Optional[Dict[str, str]] = None,
    ) -> str:
        """Despliega servicio a Cloud Run.
        
        Args:
            image: Imagen de contenedor (override config)
            env_vars: Variables de entorno adicionales
            
        Returns:
            URL del servicio desplegado
        """
        logger.info(f"[CLOUDRUN] Deploying {self._config.service_name}...")
        
        # Usar imagen del config o la proporcionada
        deploy_image = image or self._config.image
        if not deploy_image:
            raise ValueError("No image specified for deployment")
        
        # Combinar env vars
        all_env_vars = {**self._config.env_vars}
        if env_vars:
            all_env_vars.update(env_vars)
        
        # Intentar usar API primero, fallback a gcloud
        try:
            url = await self._deploy_via_api(deploy_image, all_env_vars)
        except ImportError:
            logger.info("[CLOUDRUN] API not available, using gcloud CLI")
            url = await self._deploy_via_gcloud(deploy_image, all_env_vars)
        
        logger.info(f"[CLOUDRUN] Deployed successfully: {url}")
        return url
    
    async def _deploy_via_api(
        self,
        image: str,
        env_vars: Dict[str, str],
    ) -> str:
        """Despliega usando la API de Cloud Run.
        
        Args:
            image: Imagen de contenedor
            env_vars: Variables de entorno
            
        Returns:
            URL del servicio
        """
        from google.cloud import run_v2
        
        client = run_v2.ServicesAsyncClient()
        
        # Construir especificacion del servicio
        service = run_v2.Service(
            template=run_v2.RevisionTemplate(
                containers=[
                    run_v2.Container(
                        image=image,
                        resources=run_v2.ResourceRequirements(
                            limits={
                                "memory": self._config.memory,
                                "cpu": self._config.cpu,
                            },
                        ),
                        env=[
                            run_v2.EnvVar(name=k, value=v)
                            for k, v in env_vars.items()
                        ],
                    ),
                ],
                scaling=run_v2.RevisionScaling(
                    min_instance_count=self._config.min_instances,
                    max_instance_count=self._config.max_instances,
                ),
            ),
        )
        
        parent = f"projects/{self._project_id}/locations/{self._config.region}"
        
        # Crear o actualizar servicio
        operation = await client.create_service(
            parent=parent,
            service=service,
            service_id=self._config.service_name,
        )
        
        result = await operation.result()
        return result.uri
    
    async def _deploy_via_gcloud(
        self,
        image: str,
        env_vars: Dict[str, str],
    ) -> str:
        """Despliega usando gcloud CLI.
        
        Args:
            image: Imagen de contenedor
            env_vars: Variables de entorno
            
        Returns:
            URL del servicio
        """
        import asyncio
        
        # Construir comando
        cmd = [
            "gcloud", "run", "deploy", self._config.service_name,
            "--image", image,
            "--region", self._config.region,
            "--memory", self._config.memory,
            "--cpu", self._config.cpu,
            "--min-instances", str(self._config.min_instances),
            "--max-instances", str(self._config.max_instances),
            "--quiet",
        ]
        
        # Agregar proyecto si esta definido
        if self._project_id:
            cmd.extend(["--project", self._project_id])
        
        # Agregar env vars
        if env_vars:
            env_str = ",".join(f"{k}={v}" for k, v in env_vars.items())
            cmd.extend(["--set-env-vars", env_str])
        
        # Agregar flag de acceso
        if self._config.allow_unauthenticated:
            cmd.append("--allow-unauthenticated")
        else:
            cmd.append("--no-allow-unauthenticated")
        
        # Ejecutar comando
        logger.debug(f"[CLOUDRUN] Running: {' '.join(cmd)}")
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            raise RuntimeError(
                f"gcloud deploy failed: {stderr.decode()}"
            )
        
        # Obtener URL del servicio
        return await self.get_service_url()
    
    async def get_service_url(self) -> str:
        """Obtiene URL del servicio desplegado.
        
        Returns:
            URL del servicio
        """
        import asyncio
        
        cmd = [
            "gcloud", "run", "services", "describe",
            self._config.service_name,
            "--region", self._config.region,
            "--format", "value(status.url)",
        ]
        
        if self._project_id:
            cmd.extend(["--project", self._project_id])
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            raise RuntimeError(f"Failed to get service URL: {stderr.decode()}")
        
        return stdout.decode().strip()
    
    async def get_service_status(self) -> Dict[str, Any]:
        """Obtiene estado del servicio.
        
        Returns:
            Informacion del servicio
        """
        import asyncio
        import json
        
        cmd = [
            "gcloud", "run", "services", "describe",
            self._config.service_name,
            "--region", self._config.region,
            "--format", "json",
        ]
        
        if self._project_id:
            cmd.extend(["--project", self._project_id])
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            raise RuntimeError(f"Failed to get service status: {stderr.decode()}")
        
        return json.loads(stdout.decode())
    
    async def list_revisions(self) -> List[Dict[str, Any]]:
        """Lista revisiones del servicio.
        
        Returns:
            Lista de revisiones
        """
        import asyncio
        import json
        
        cmd = [
            "gcloud", "run", "revisions", "list",
            "--service", self._config.service_name,
            "--region", self._config.region,
            "--format", "json",
        ]
        
        if self._project_id:
            cmd.extend(["--project", self._project_id])
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            return []
        
        return json.loads(stdout.decode())
    
    async def delete_service(self) -> bool:
        """Elimina el servicio.
        
        Returns:
            True si se elimino exitosamente
        """
        import asyncio
        
        cmd = [
            "gcloud", "run", "services", "delete",
            self._config.service_name,
            "--region", self._config.region,
            "--quiet",
        ]
        
        if self._project_id:
            cmd.extend(["--project", self._project_id])
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        
        await process.communicate()
        return process.returncode == 0
{%- endif %}
