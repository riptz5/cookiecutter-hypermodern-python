{%- if cookiecutter.use_google_cloud == 'y' %}
"""Cliente Firestore para persistencia.

Proporciona una interfaz async para Firestore con
operaciones optimizadas para GENESIS.
"""
import logging
import os
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class FirestoreClient:
    """Cliente async para Google Cloud Firestore.
    
    Proporciona operaciones CRUD con manejo automatico de
    conexion y errores.
    
    Example:
        >>> client = FirestoreClient()
        >>> await client.set("collection/doc_id", {"key": "value"})
        >>> doc = await client.get("collection/doc_id")
        >>> print(doc)
    """
    
    def __init__(self, project_id: Optional[str] = None):
        """Inicializa cliente Firestore.
        
        Args:
            project_id: ID del proyecto GCP. Si es None, usa
                        GOOGLE_CLOUD_PROJECT o credenciales por defecto.
        """
        self._project_id = project_id or os.getenv("GOOGLE_CLOUD_PROJECT")
        self._client = None
        self._initialized = False
    
    @property
    def client(self):
        """Lazy initialization del cliente Firestore."""
        if self._client is None:
            try:
                from google.cloud import firestore
                
                if self._project_id:
                    self._client = firestore.AsyncClient(project=self._project_id)
                else:
                    self._client = firestore.AsyncClient()
                
                self._initialized = True
                logger.info(f"Firestore client initialized for project: {self._project_id or 'default'}")
                
            except ImportError:
                logger.error("google-cloud-firestore not installed")
                raise ImportError(
                    "Firestore requires google-cloud-firestore. "
                    "Install with: pip install google-cloud-firestore"
                )
            except Exception as e:
                logger.error(f"Failed to initialize Firestore: {e}")
                raise
        
        return self._client
    
    async def get(self, path: str) -> Optional[Dict[str, Any]]:
        """Obtiene un documento.
        
        Args:
            path: Ruta del documento (collection/doc_id)
            
        Returns:
            Datos del documento o None si no existe
        """
        try:
            parts = path.split("/")
            if len(parts) < 2:
                raise ValueError(f"Invalid path: {path}")
            
            collection = parts[0]
            doc_id = "/".join(parts[1:])
            
            doc_ref = self.client.collection(collection).document(doc_id)
            doc = await doc_ref.get()
            
            if doc.exists:
                return doc.to_dict()
            return None
            
        except Exception as e:
            logger.error(f"Failed to get document {path}: {e}")
            raise
    
    async def set(self, path: str, data: Dict[str, Any], merge: bool = True) -> None:
        """Guarda un documento.
        
        Args:
            path: Ruta del documento (collection/doc_id)
            data: Datos a guardar
            merge: Si hacer merge con datos existentes
        """
        try:
            parts = path.split("/")
            if len(parts) < 2:
                raise ValueError(f"Invalid path: {path}")
            
            collection = parts[0]
            doc_id = "/".join(parts[1:])
            
            doc_ref = self.client.collection(collection).document(doc_id)
            await doc_ref.set(data, merge=merge)
            
            logger.debug(f"Document saved: {path}")
            
        except Exception as e:
            logger.error(f"Failed to set document {path}: {e}")
            raise
    
    async def add(self, collection: str, data: Dict[str, Any]) -> str:
        """Agrega un documento con ID auto-generado.
        
        Args:
            collection: Nombre de la coleccion
            data: Datos del documento
            
        Returns:
            ID del documento creado
        """
        try:
            from datetime import datetime
            
            # Agregar timestamp automatico
            if "created_at" not in data:
                data["created_at"] = datetime.utcnow().isoformat()
            
            doc_ref = self.client.collection(collection).document()
            await doc_ref.set(data)
            
            logger.debug(f"Document added: {collection}/{doc_ref.id}")
            return doc_ref.id
            
        except Exception as e:
            logger.error(f"Failed to add document to {collection}: {e}")
            raise
    
    async def delete(self, path: str) -> None:
        """Elimina un documento.
        
        Args:
            path: Ruta del documento
        """
        try:
            parts = path.split("/")
            if len(parts) < 2:
                raise ValueError(f"Invalid path: {path}")
            
            collection = parts[0]
            doc_id = "/".join(parts[1:])
            
            doc_ref = self.client.collection(collection).document(doc_id)
            await doc_ref.delete()
            
            logger.debug(f"Document deleted: {path}")
            
        except Exception as e:
            logger.error(f"Failed to delete document {path}: {e}")
            raise
    
    async def query(
        self,
        collection: str,
        filters: Optional[List[tuple]] = None,
        order_by: Optional[str] = None,
        order_direction: str = "asc",
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Consulta documentos con filtros.
        
        Args:
            collection: Nombre de la coleccion
            filters: Lista de (field, operator, value)
            order_by: Campo para ordenar
            order_direction: "asc" o "desc"
            limit: Numero maximo de resultados
            
        Returns:
            Lista de documentos
        """
        try:
            from google.cloud.firestore import Query
            
            query = self.client.collection(collection)
            
            # Aplicar filtros
            if filters:
                for field, op, value in filters:
                    query = query.where(field, op, value)
            
            # Ordenar
            if order_by:
                direction = (
                    Query.DESCENDING 
                    if order_direction.lower() == "desc" 
                    else Query.ASCENDING
                )
                query = query.order_by(order_by, direction=direction)
            
            # Limitar
            query = query.limit(limit)
            
            # Ejecutar
            docs = await query.get()
            
            return [
                {"id": doc.id, **doc.to_dict()}
                for doc in docs
            ]
            
        except Exception as e:
            logger.error(f"Failed to query {collection}: {e}")
            raise
    
    async def list(self, collection: str, limit: int = 1000) -> List[Dict[str, Any]]:
        """Lista todos los documentos de una coleccion.
        
        Args:
            collection: Nombre de la coleccion
            limit: Numero maximo de documentos
            
        Returns:
            Lista de documentos
        """
        return await self.query(collection, limit=limit)
    
    async def get_genesis_state(self) -> Dict[str, Any]:
        """Obtiene estado actual de GENESIS desde Firestore.
        
        Returns:
            Estado del sistema
        """
        state = await self.get("genesis_state/current")
        return state or {}
    
    async def update_genesis_state(self, state: Dict[str, Any]) -> None:
        """Actualiza estado de GENESIS en Firestore.
        
        Args:
            state: Nuevo estado
        """
        from datetime import datetime
        state["updated_at"] = datetime.utcnow().isoformat()
        await self.set("genesis_state/current", state)
    
    async def close(self) -> None:
        """Cierra la conexion."""
        if self._client:
            # Note: AsyncClient no tiene metodo close explicito
            # pero es buena practica tenerlo para consistencia
            self._client = None
            self._initialized = False
{%- endif %}
