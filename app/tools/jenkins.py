from langchain_core.tools import tool
import jenkins
import os

jenkins_server = jenkins.Jenkins(
    os.getenv("JENKINS_URL"),
    username=os.getenv("JENKINS_USERNAME"),
    password=os.getenv("JENKINS_API_TOKEN")
)

@tool
def trigger_jenkins_job(job_name: str, parameters: dict = None) -> str:
    """Trigger a Jenkins job (with optional parameters)."""
    try:
        if parameters:
            jenkins_server.build_job(job_name, parameters)
        else:
            jenkins_server.build_job(job_name)
        return f"✅ Jenkins job '{job_name}' triggered successfully."
    except Exception as e:
        return f"❌ Failed to trigger job: {str(e)}"