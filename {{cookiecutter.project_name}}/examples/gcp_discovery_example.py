{%- if cookiecutter.use_google_cloud == 'y' %}
"""Example: Discover Google Cloud resources automatically.

This script demonstrates automatic discovery of GCP resources using
Application Default Credentials (ADC) and the plugin-based discovery system.

Setup:
1. Install gcloud CLI: https://cloud.google.com/sdk/docs/install
2. Authenticate: gcloud auth application-default login
3. Set project: gcloud config set project YOUR_PROJECT_ID
4. Run this script

No hardcoded credentials needed!
"""
import asyncio
import logging
from {{cookiecutter.package_name}}.core.gcp_discovery import discover_gcp_resources, GCPDiscovery

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


def get_service_resources(resources, service_pattern: str):
    """Helper to get resources for a service pattern.
    
    Args:
        resources: GCPResources object
        service_pattern: Pattern to match service name
        
    Returns:
        Dict of resources or None
    """
    for service_name, data in resources.service_resources.items():
        if service_pattern.lower() in service_name.lower():
            return data
    return None


async def main():
    """Discover and display GCP resources."""
    print("\n" + "=" * 80)
    print("GOOGLE CLOUD AUTOMATIC DISCOVERY (PLUGIN-BASED)")
    print("=" * 80)
    
    try:
        # Discover all resources automatically
        resources = discover_gcp_resources()
        
        # Display project info
        print(f"\n📦 Project: {resources.project.project_id}")
        print(f"📍 Region: {resources.project.region}")
        
        # Display enabled services
        enabled_services = [s for s in resources.services if s.enabled]
        print(f"\n🔧 Enabled Services ({len(enabled_services)}):")
        for service in sorted(enabled_services, key=lambda s: s.display_name)[:15]:
            print(f"  {service}")
        if len(enabled_services) > 15:
            print(f"  ... and {len(enabled_services) - 15} more")
        
        # Display discovered resources dynamically
        print(f"\n📂 Discovered Resources ({len(resources.service_resources)} services):")
        
        for service_name, data in resources.service_resources.items():
            # Extract clean service name
            service_key = service_name.split('.')[-1].replace('.googleapis.com', '')
            resource_type = data.get('type', 'resources')
            count = data.get('count', 0)
            
            # Get emoji based on service
            emoji_map = {
                'secret': '🔐',
                'storage': '🪣',
                'firestore': '🔥',
                'bigquery': '📊',
                'vertex': '🤖',
                'compute': '🖥️',
                'run': '🏃',
                'pubsub': '📨',
                'spanner': '🗄️',
            }
            emoji = '📁'
            for pattern, e in emoji_map.items():
                if pattern in service_key.lower():
                    emoji = e
                    break
            
            print(f"\n  {emoji} {service_key.title()} ({count} {resource_type}):")
            
            # Show resource items (limited)
            items = data.get('resources', [])
            for item in items[:5]:
                if isinstance(item, dict):
                    name = item.get('name', item.get('id', str(item)))
                else:
                    name = str(item)
                print(f"     - {name}")
            
            if len(items) > 5:
                print(f"     ... and {len(items) - 5} more")
        
        # Summary
        print("\n" + "=" * 80)
        print("DISCOVERY SUMMARY")
        print("=" * 80)
        summary = resources.to_dict()
        for key, value in summary.items():
            if isinstance(value, list):
                print(f"{key}: [{len(value)} items]")
            else:
                print(f"{key}: {value}")
        
        print("\n✅ Discovery complete!")
        print("\nNext steps:")
        print("1. Use these resources in your agents")
        print("2. Access resources via: discovery.get_service_resources('secretmanager')")
        print("3. Add custom plugins for new services")
        print("4. Deploy to Cloud Run with zero config")
        
        # Show usage example
        print("\n" + "-" * 40)
        print("Usage Example:")
        print("-" * 40)
        print("""
>>> from {{cookiecutter.package_name}}.core.gcp_discovery import GCPDiscovery
>>> 
>>> discovery = GCPDiscovery()
>>> resources = discovery.discover_all()
>>> 
>>> # Get specific service resources
>>> secrets = discovery.get_service_resources('secretmanager')
>>> if secrets:
...     print(f"Found {secrets['count']} secrets")
>>> 
>>> # Iterate all services
>>> for service, data in resources.service_resources.items():
...     print(f"{service}: {data['count']} {data['type']}")
""")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nTroubleshooting:")
        print("1. Run: gcloud auth application-default login")
        print("2. Run: gcloud config set project YOUR_PROJECT_ID")
        print("3. Enable required APIs in Cloud Console")
        print("4. Check IAM permissions")
        
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
{%- endif %}
