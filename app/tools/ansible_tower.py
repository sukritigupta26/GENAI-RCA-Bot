from langchain_core.tools import tool
import requests
import os

TOWER_URL = os.getenv("ANSIBLE_TOWER_URL").rstrip("/")
auth = (os.getenv("ANSIBLE_TOWER_USERNAME"), os.getenv("ANSIBLE_TOWER_PASSWORD"))

@tool
def launch_ansible_tower_job(template_id: int, extra_vars: dict = None) -> str:
    """Launch a job template in Ansible Tower / AWX."""
    url = f"{TOWER_URL}/api/v2/job_templates/{template_id}/launch/"
    payload = {"extra_vars": extra_vars} if extra_vars else {}
    try:
        r = requests.post(url, auth=auth, json=payload, verify=False)
        r.raise_for_status()
        return f"✅ Ansible Tower job launched (ID: {r.json().get('id')})"
    except Exception as e:
        return f"❌ Failed to launch Tower job: {str(e)}"