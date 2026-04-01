import logging
import os
from typing import Optional

from langchain_core.tools import tool

from kubernetes import client, config
from kubernetes.config.config_exception import ConfigException

logger = logging.getLogger(__name__)

# Module-level flag telling whether kube config is available
KUBECONFIG_LOADED: bool = False

# Always try to load local kube-config first
try:
    config.load_kube_config()
    KUBECONFIG_LOADED = True
    logger.info("Loaded local kube-config")
except ConfigException:
    KUBECONFIG_LOADED = False
    logger.warning(
        "No kube-config found. Kubernetes functions will be unavailable. "
        "Please ensure you have a valid kube-config file at ~/.kube/config or run minikube/start cluster."
    )

k8s = client.CoreV1Api()
apps = client.AppsV1Api()

@tool
def ensure_kubeconfig():
    """
    Helper to be called at the start of runtime functions that require Kubernetes.
    Raises RuntimeError with a clear message if kube-config is not available.
    """
    if not KUBECONFIG_LOADED:
        raise RuntimeError(
            "Kubernetes is not configured (no kube-config and not running in-cluster). "
            "Set KUBECONFIG or run minikube/start cluster, or update app/tools/kubernetes.py to handle Noop behavior."
        )


def restart_kubernetes_pod(namespace: str, pod_name: str, grace_period_seconds: Optional[int] = 0):
    """
    Restart a pod by deleting it (a new pod will be created by its controller).
    This function will raise RuntimeError if kubeconfig is not available.
    """
    ensure_kubeconfig()
    v1 = client.CoreV1Api()
    try:
        # delete the pod to cause restart
        body = client.V1DeleteOptions(grace_period_seconds=grace_period_seconds)
        return v1.delete_namespaced_pod(name=pod_name, namespace=namespace, body=body)
    except Exception as e:
        logger.exception("Failed to restart pod %s/%s: %s", namespace, pod_name, e)
        raise

@tool
def create_kubernetes_pod(pod_manifest: dict, namespace: str = "default") -> str:
    """Create a new pod from a full manifest dict."""
    try:
        k8s.create_namespaced_pod(namespace=namespace, body=pod_manifest)
        return f"✅ Pod created in {namespace}"
    except Exception as e:
        return f"❌ Failed to create pod: {str(e)}"

@tool
def scale_deployment(namespace: str, deployment_name: str, replicas: int):
    """
    Scale a deployment to `replicas`.
    Raises RuntimeError if kubeconfig is not available.
    """
    ensure_kubeconfig()
    apps_v1 = client.AppsV1Api()
    try:
        # fetch current deployment
        dep = apps_v1.read_namespaced_deployment(name=deployment_name, namespace=namespace)
        dep.spec.replicas = replicas
        return apps_v1.replace_namespaced_deployment(name=deployment_name, namespace=namespace, body=dep)
    except Exception as e:
        logger.exception("Failed to scale deployment %s/%s: %s", namespace, deployment_name, e)
        raise