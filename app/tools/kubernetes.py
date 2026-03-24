import os
from langchain_core.tools import tool
from kubernetes import client, config

if os.getenv("K8S_IN_CLUSTER", "false").lower() == "true":
    config.load_incluster_config()
else:
    config.load_kube_config()

k8s = client.CoreV1Api()
apps = client.AppsV1Api()

@tool
def restart_kubernetes_pod(pod_name: str, namespace: str = "default") -> str:
    """Restart a single pod by deleting it (Deployment/StatefulSet will recreate)."""
    try:
        k8s.delete_namespaced_pod(name=pod_name, namespace=namespace)
        return f"✅ Pod {pod_name} in {namespace} restarted successfully."
    except Exception as e:
        return f"❌ Failed to restart pod: {str(e)}"

@tool
def create_kubernetes_pod(pod_manifest: dict, namespace: str = "default") -> str:
    """Create a new pod from a full manifest dict."""
    try:
        k8s.create_namespaced_pod(namespace=namespace, body=pod_manifest)
        return f"✅ Pod created in {namespace}"
    except Exception as e:
        return f"❌ Failed to create pod: {str(e)}"

@tool
def scale_deployment(name: str, replicas: int, namespace: str = "default") -> str:
    """Scale a Deployment up or down."""
    try:
        apps.patch_namespaced_deployment_scale(
            name=name,
            namespace=namespace,
            body={"spec": {"replicas": replicas}}
        )
        return f"✅ Deployment {name} scaled to {replicas} replicas."
    except Exception as e:
        return f"❌ Scale failed: {str(e)}"