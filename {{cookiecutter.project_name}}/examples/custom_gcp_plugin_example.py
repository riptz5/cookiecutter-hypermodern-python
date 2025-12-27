{%- if cookiecutter.use_google_cloud == 'y' %}
"""Example: Create custom GCP service plugin.

This example shows how to create a plugin for a NEW Google Cloud service
that doesn't have built-in support yet.

When Google launches a new service, you just:
1. Create a plugin (this file)
2. Drop it in gcp_plugins/ directory
3. It's automatically discovered - NO core code changes needed

Philosophy: ZERO HARDCODING in core. Everything is plugins.
"""
from typing import Dict, Any, List
from {{cookiecutter.package_name}}.core.gcp_plugins import BaseGCPPlugin
from {{cookiecutter.package_name}}.core.gcp_discovery import GCPDiscovery


class CloudRunPlugin(BaseGCPPlugin):
    """Plugin for Cloud Run services.
    
    Example of a custom plugin for a specific GCP service.
    """
    
    @property
    def service_patterns(self) -> List[str]:
        """Patterns to match Cloud Run service."""
        return ['run', 'cloudrun']
    
    @property
    def required_packages(self) -> List[str]:
        """Required packages for Cloud Run."""
        return ['google-cloud-run']
    
    def discover_resources(
        self,
        project_id: str,
        credentials: Any,
        region: str
    ) -> Dict[str, Any]:
        """Discover Cloud Run services."""
        # Try to import Cloud Run client
        module = self._try_import('google.cloud.run_v2')
        if not module:
            return {"error": "google-cloud-run not installed"}
        
        try:
            client = module.ServicesClient(credentials=credentials)
            parent = f"projects/{project_id}/locations/{region}"
            
            services = []
            for service in client.list_services(parent=parent):
                services.append(service.name.split("/")[-1])
            
            return {
                "type": "services",
                "count": len(services),
                "resources": services
            }
        except Exception as e:
            return {"error": str(e)}


class PubSubPlugin(BaseGCPPlugin):
    """Plugin for Pub/Sub topics and subscriptions."""
    
    @property
    def service_patterns(self) -> List[str]:
        return ['pubsub', 'pub/sub']
    
    @property
    def required_packages(self) -> List[str]:
        return ['google-cloud-pubsub']
    
    def discover_resources(
        self,
        project_id: str,
        credentials: Any,
        region: str
    ) -> Dict[str, Any]:
        """Discover Pub/Sub topics."""
        module = self._try_import('google.cloud.pubsub_v1')
        if not module:
            return {"error": "google-cloud-pubsub not installed"}
        
        try:
            publisher = module.PublisherClient(credentials=credentials)
            project_path = f"projects/{project_id}"
            
            topics = []
            for topic in publisher.list_topics(request={"project": project_path}):
                topics.append(topic.name.split("/")[-1])
            
            return {
                "type": "topics",
                "count": len(topics),
                "resources": topics
            }
        except Exception as e:
            return {"error": str(e)}


class ComputeEnginePlugin(BaseGCPPlugin):
    """Plugin for Compute Engine instances."""
    
    @property
    def service_patterns(self) -> List[str]:
        return ['compute', 'gce']
    
    @property
    def required_packages(self) -> List[str]:
        return ['google-cloud-compute']
    
    def discover_resources(
        self,
        project_id: str,
        credentials: Any,
        region: str
    ) -> Dict[str, Any]:
        """Discover Compute Engine instances."""
        module = self._try_import('google.cloud.compute_v1')
        if not module:
            return {"error": "google-cloud-compute not installed"}
        
        try:
            client = module.InstancesClient(credentials=credentials)
            
            instances = []
            # List instances in all zones
            for zone in ['us-central1-a', 'us-central1-b', 'us-central1-c']:
                try:
                    for instance in client.list(project=project_id, zone=zone):
                        instances.append(instance.name)
                except:
                    pass
            
            return {
                "type": "instances",
                "count": len(instances),
                "resources": instances
            }
        except Exception as e:
            return {"error": str(e)}


def main():
    """Example of using custom plugins."""
    print("\n" + "=" * 80)
    print("CUSTOM GCP PLUGIN EXAMPLE")
    print("=" * 80)
    
    # Create discovery with custom plugins
    custom_plugins = [
        CloudRunPlugin(),
        PubSubPlugin(),
        ComputeEnginePlugin(),
    ]
    
    discovery = GCPDiscovery(custom_plugins=custom_plugins)
    
    print(f"\n✓ Registered {len(custom_plugins)} custom plugins")
    print("  - CloudRunPlugin (handles: run, cloudrun)")
    print("  - PubSubPlugin (handles: pubsub, pub/sub)")
    print("  - ComputeEnginePlugin (handles: compute, gce)")
    
    # Discover all resources (including custom ones)
    print("\nDiscovering resources...")
    resources = discovery.discover_all()
    
    print("\n" + "=" * 80)
    print("DISCOVERY RESULTS")
    print("=" * 80)
    print(f"Project: {resources.project.project_id}")
    print(f"Total services with resources: {len(resources.service_resources)}")
    
    # Show resources discovered by custom plugins
    for service_name, service_data in resources.service_resources.items():
        service_key = service_name.split('.')[0]
        print(f"\n{service_key}:")
        print(f"  Type: {service_data.get('type', 'unknown')}")
        print(f"  Count: {service_data.get('count', 0)}")
        if service_data.get('resources'):
            print(f"  Resources: {service_data['resources'][:5]}")  # Show first 5
    
    print("\n" + "=" * 80)
    print("HOW TO ADD YOUR OWN PLUGIN")
    print("=" * 80)
    print("""
1. Create a class inheriting from BaseGCPPlugin
2. Implement service_patterns (what services it handles)
3. Implement required_packages (what to install)
4. Implement discover_resources (how to discover)
5. Drop it in gcp_plugins/ directory OR pass to GCPDiscovery()

That's it! NO core code changes needed.

When Google launches a new service tomorrow:
- Someone creates a plugin
- Shares it as a Python file
- Everyone can use it immediately
- Zero waiting for core updates
    """)


if __name__ == "__main__":
    main()
{%- endif %}
