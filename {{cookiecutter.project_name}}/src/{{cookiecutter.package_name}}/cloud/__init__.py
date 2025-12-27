{%- if cookiecutter.use_google_cloud == 'y' %}
"""Google Cloud infrastructure modules.

Este paquete contiene clientes y utilidades para interactuar
con servicios de Google Cloud Platform.

Modules:
    firestore: Cliente Firestore para persistencia
    run: Deployer para Cloud Run
    pubsub: Cliente Pub/Sub para mensajeria
"""
from .firestore import FirestoreClient
from .run import CloudRunDeployer
from .pubsub import PubSubClient

__all__ = [
    "FirestoreClient",
    "CloudRunDeployer",
    "PubSubClient",
]
{%- endif %}
