{%- if cookiecutter.use_google_cloud == 'y' %}
"""Cliente Pub/Sub para mensajeria.

Proporciona una interfaz async para Google Cloud Pub/Sub
optimizada para comunicacion entre componentes de GENESIS.
"""
import json
import logging
import os
from dataclasses import dataclass
from datetime import datetime
from typing import Callable, Dict, Any, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class PubSubMessage:
    """Mensaje de Pub/Sub.
    
    Attributes:
        data: Datos del mensaje (dict serializado)
        attributes: Atributos/metadata del mensaje
        message_id: ID del mensaje (asignado por Pub/Sub)
        publish_time: Momento de publicacion
    """
    data: Dict[str, Any]
    attributes: Dict[str, str] = None
    message_id: Optional[str] = None
    publish_time: Optional[datetime] = None
    
    def __post_init__(self):
        if self.attributes is None:
            self.attributes = {}
    
    def to_bytes(self) -> bytes:
        """Serializa el mensaje a bytes."""
        return json.dumps(self.data).encode("utf-8")
    
    @classmethod
    def from_bytes(cls, data: bytes, **kwargs) -> "PubSubMessage":
        """Deserializa mensaje desde bytes."""
        return cls(data=json.loads(data.decode("utf-8")), **kwargs)


class PubSubClient:
    """Cliente async para Google Cloud Pub/Sub.
    
    Proporciona publicacion y suscripcion a topics
    con serialization automatica de mensajes.
    
    Example:
        >>> client = PubSubClient()
        >>> await client.publish("my-topic", {"event": "test"})
        >>> 
        >>> async for msg in client.subscribe("my-subscription"):
        ...     print(msg.data)
        ...     await msg.ack()
    """
    
    # Prefijo para topics de GENESIS
    GENESIS_PREFIX = "genesis-"
    
    def __init__(self, project_id: Optional[str] = None):
        """Inicializa cliente Pub/Sub.
        
        Args:
            project_id: ID del proyecto GCP
        """
        self._project_id = project_id or os.getenv("GOOGLE_CLOUD_PROJECT")
        self._publisher = None
        self._subscriber = None
    
    @property
    def publisher(self):
        """Lazy initialization del publisher."""
        if self._publisher is None:
            try:
                from google.cloud import pubsub_v1
                self._publisher = pubsub_v1.PublisherClient()
                logger.info("Pub/Sub publisher initialized")
            except ImportError:
                raise ImportError(
                    "Pub/Sub requires google-cloud-pubsub. "
                    "Install with: pip install google-cloud-pubsub"
                )
        return self._publisher
    
    @property
    def subscriber(self):
        """Lazy initialization del subscriber."""
        if self._subscriber is None:
            try:
                from google.cloud import pubsub_v1
                self._subscriber = pubsub_v1.SubscriberClient()
                logger.info("Pub/Sub subscriber initialized")
            except ImportError:
                raise ImportError(
                    "Pub/Sub requires google-cloud-pubsub. "
                    "Install with: pip install google-cloud-pubsub"
                )
        return self._subscriber
    
    def _topic_path(self, topic: str) -> str:
        """Construye path completo del topic.
        
        Args:
            topic: Nombre del topic
            
        Returns:
            Path completo del topic
        """
        return f"projects/{self._project_id}/topics/{topic}"
    
    def _subscription_path(self, subscription: str) -> str:
        """Construye path completo de la suscripcion.
        
        Args:
            subscription: Nombre de la suscripcion
            
        Returns:
            Path completo
        """
        return f"projects/{self._project_id}/subscriptions/{subscription}"
    
    async def publish(
        self,
        topic: str,
        data: Dict[str, Any],
        attributes: Optional[Dict[str, str]] = None,
    ) -> str:
        """Publica un mensaje a un topic.
        
        Args:
            topic: Nombre del topic
            data: Datos del mensaje
            attributes: Atributos opcionales
            
        Returns:
            ID del mensaje publicado
        """
        import asyncio
        
        message = PubSubMessage(data=data, attributes=attributes or {})
        
        # Agregar atributos por defecto
        message.attributes.setdefault("source", "genesis")
        message.attributes.setdefault("timestamp", datetime.utcnow().isoformat())
        
        topic_path = self._topic_path(topic)
        
        # Publicar (sync wrapper ya que publisher no es async nativo)
        future = self.publisher.publish(
            topic_path,
            message.to_bytes(),
            **message.attributes,
        )
        
        # Esperar resultado
        message_id = await asyncio.get_event_loop().run_in_executor(
            None, future.result
        )
        
        logger.debug(f"Published message {message_id} to {topic}")
        return message_id
    
    async def publish_batch(
        self,
        topic: str,
        messages: List[Dict[str, Any]],
    ) -> List[str]:
        """Publica multiples mensajes a un topic.
        
        Args:
            topic: Nombre del topic
            messages: Lista de datos a publicar
            
        Returns:
            Lista de IDs de mensajes publicados
        """
        import asyncio
        
        topic_path = self._topic_path(topic)
        futures = []
        
        for data in messages:
            message = PubSubMessage(data=data)
            message.attributes["source"] = "genesis"
            message.attributes["timestamp"] = datetime.utcnow().isoformat()
            
            future = self.publisher.publish(
                topic_path,
                message.to_bytes(),
                **message.attributes,
            )
            futures.append(future)
        
        # Esperar todos
        loop = asyncio.get_event_loop()
        message_ids = await asyncio.gather(*[
            loop.run_in_executor(None, f.result)
            for f in futures
        ])
        
        logger.debug(f"Published {len(message_ids)} messages to {topic}")
        return list(message_ids)
    
    async def subscribe(
        self,
        subscription: str,
        callback: Callable[[PubSubMessage], None],
        max_messages: int = 10,
        timeout: float = 30.0,
    ) -> None:
        """Suscribe a una subscription con callback.
        
        Args:
            subscription: Nombre de la suscripcion
            callback: Funcion a llamar por mensaje
            max_messages: Mensajes maximos en paralelo
            timeout: Timeout en segundos (None = indefinido)
        """
        import asyncio
        
        subscription_path = self._subscription_path(subscription)
        
        def message_callback(message):
            try:
                msg = PubSubMessage(
                    data=json.loads(message.data.decode("utf-8")),
                    attributes=dict(message.attributes),
                    message_id=message.message_id,
                    publish_time=message.publish_time,
                )
                callback(msg)
                message.ack()
            except Exception as e:
                logger.error(f"Error processing message: {e}")
                message.nack()
        
        streaming_pull_future = self.subscriber.subscribe(
            subscription_path,
            callback=message_callback,
        )
        
        logger.info(f"Subscribed to {subscription}")
        
        try:
            if timeout:
                await asyncio.wait_for(
                    asyncio.get_event_loop().run_in_executor(
                        None, streaming_pull_future.result
                    ),
                    timeout=timeout,
                )
            else:
                await asyncio.get_event_loop().run_in_executor(
                    None, streaming_pull_future.result
                )
        except asyncio.TimeoutError:
            streaming_pull_future.cancel()
            logger.info(f"Subscription timeout after {timeout}s")
    
    async def pull(
        self,
        subscription: str,
        max_messages: int = 10,
        timeout: float = 5.0,
    ) -> List[PubSubMessage]:
        """Pull mensajes de una suscripcion.
        
        Args:
            subscription: Nombre de la suscripcion
            max_messages: Numero maximo de mensajes
            timeout: Timeout de pull
            
        Returns:
            Lista de mensajes
        """
        import asyncio
        
        subscription_path = self._subscription_path(subscription)
        
        response = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: self.subscriber.pull(
                subscription=subscription_path,
                max_messages=max_messages,
            ),
        )
        
        messages = []
        ack_ids = []
        
        for received_message in response.received_messages:
            msg = PubSubMessage(
                data=json.loads(received_message.message.data.decode("utf-8")),
                attributes=dict(received_message.message.attributes),
                message_id=received_message.message.message_id,
                publish_time=received_message.message.publish_time,
            )
            messages.append(msg)
            ack_ids.append(received_message.ack_id)
        
        # Ack todos los mensajes
        if ack_ids:
            self.subscriber.acknowledge(
                subscription=subscription_path,
                ack_ids=ack_ids,
            )
        
        return messages
    
    async def create_topic(self, topic: str) -> str:
        """Crea un topic.
        
        Args:
            topic: Nombre del topic
            
        Returns:
            Path completo del topic creado
        """
        import asyncio
        
        topic_path = self._topic_path(topic)
        
        try:
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.publisher.create_topic(name=topic_path),
            )
            logger.info(f"Created topic: {topic}")
        except Exception as e:
            if "already exists" in str(e).lower():
                logger.debug(f"Topic already exists: {topic}")
            else:
                raise
        
        return topic_path
    
    async def create_subscription(
        self,
        subscription: str,
        topic: str,
        ack_deadline_seconds: int = 60,
    ) -> str:
        """Crea una suscripcion.
        
        Args:
            subscription: Nombre de la suscripcion
            topic: Topic al que suscribir
            ack_deadline_seconds: Deadline de ack
            
        Returns:
            Path completo de la suscripcion
        """
        import asyncio
        
        subscription_path = self._subscription_path(subscription)
        topic_path = self._topic_path(topic)
        
        try:
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.subscriber.create_subscription(
                    name=subscription_path,
                    topic=topic_path,
                    ack_deadline_seconds=ack_deadline_seconds,
                ),
            )
            logger.info(f"Created subscription: {subscription}")
        except Exception as e:
            if "already exists" in str(e).lower():
                logger.debug(f"Subscription already exists: {subscription}")
            else:
                raise
        
        return subscription_path
    
    # =================================================================
    # Topics predefinidos para GENESIS
    # =================================================================
    
    async def publish_cycle_event(
        self,
        cycle_id: str,
        event_type: str,
        data: Dict[str, Any],
    ) -> str:
        """Publica evento de ciclo GENESIS.
        
        Args:
            cycle_id: ID del ciclo
            event_type: Tipo de evento (started, completed, error)
            data: Datos del evento
            
        Returns:
            ID del mensaje
        """
        return await self.publish(
            f"{self.GENESIS_PREFIX}cycles",
            {
                "cycle_id": cycle_id,
                "event_type": event_type,
                **data,
            },
        )
    
    async def publish_agent_event(
        self,
        agent_name: str,
        event_type: str,
        data: Dict[str, Any],
    ) -> str:
        """Publica evento de agente.
        
        Args:
            agent_name: Nombre del agente
            event_type: Tipo de evento
            data: Datos del evento
            
        Returns:
            ID del mensaje
        """
        return await self.publish(
            f"{self.GENESIS_PREFIX}agents",
            {
                "agent_name": agent_name,
                "event_type": event_type,
                **data,
            },
        )
{%- endif %}
