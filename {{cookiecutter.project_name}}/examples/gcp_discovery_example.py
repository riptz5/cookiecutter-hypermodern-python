{%- if cookiecutter.use_google_cloud == 'y' %}
"""Example: Discover Google Cloud resources automatically.

This script demonstrates automatic discovery of GCP resources using
Application Default Credentials (ADC).

Setup:
1. Install gcloud CLI: https://cloud.google.com/sdk/docs/install
2. Authenticate: gcloud auth application-default login
3. Set project: gcloud config set project YOUR_PROJECT_ID
4. Run this script

No hardcoded credentials needed!
"""
import asyncio
import logging
from {{cookiecutter.package_name}}.core.gcp_discovery import discover_gcp_resources


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


async def main():
    """Discover and display GCP resources."""
    print("\n" + "=" * 80)
    print("GOOGLE CLOUD AUTOMATIC DISCOVERY")
    print("=" * 80)
    
    try:
        # Discover all resources automatically
        resources = discover_gcp_resources()
        
        # Display project info
        print(f"\n📦 Project: {resources.project.project_id}")
        print(f"📍 Region: {resources.project.region}")
        
        # Display enabled services
        print(f"\n🔧 Enabled Services ({len([s for s in resources.services if s.enabled])}):")
        for service in sorted(resources.services, key=lambda s: s.display_name):
            if service.enabled:
                print(f"  {service}")
        
        # Display secrets
        if resources.secrets:
            print(f"\n🔐 Secrets ({len(resources.secrets)}):")
            for secret in resources.secrets[:10]:  # Show first 10
                print(f"  - {secret}")
            if len(resources.secrets) > 10:
                print(f"  ... and {len(resources.secrets) - 10} more")
        
        # Display storage buckets
        if resources.storage_buckets:
            print(f"\n🪣 Storage Buckets ({len(resources.storage_buckets)}):")
            for bucket in resources.storage_buckets[:10]:
                print(f"  - {bucket}")
            if len(resources.storage_buckets) > 10:
                print(f"  ... and {len(resources.storage_buckets) - 10} more")
        
        # Display Firestore collections
        if resources.firestore_collections:
            print(f"\n🔥 Firestore Collections ({len(resources.firestore_collections)}):")
            for collection in resources.firestore_collections:
                print(f"  - {collection}")
        
        # Display BigQuery datasets
        if resources.bigquery_datasets:
            print(f"\n📊 BigQuery Datasets ({len(resources.bigquery_datasets)}):")
            for dataset in resources.bigquery_datasets:
                print(f"  - {dataset}")
        
        # Display Vertex AI models
        if resources.vertex_models:
            print(f"\n🤖 Vertex AI Models ({len(resources.vertex_models)}):")
            for model in resources.vertex_models[:5]:
                print(f"  - {model}")
            if len(resources.vertex_models) > 5:
                print(f"  ... and {len(resources.vertex_models) - 5} more")
        
        # Summary
        print("\n" + "=" * 80)
        print("DISCOVERY SUMMARY")
        print("=" * 80)
        summary = resources.to_dict()
        for key, value in summary.items():
            print(f"{key}: {value}")
        
        print("\n✅ Discovery complete!")
        print("\nNext steps:")
        print("1. Use these resources in your agents")
        print("2. Access secrets with: discovery.get_secret('secret-id')")
        print("3. Connect to databases automatically")
        print("4. Deploy to Cloud Run with zero config")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nTroubleshooting:")
        print("1. Run: gcloud auth application-default login")
        print("2. Run: gcloud config set project YOUR_PROJECT_ID")
        print("3. Enable required APIs in Cloud Console")
        print("4. Check IAM permissions")


if __name__ == "__main__":
    asyncio.run(main())
{%- endif %}
