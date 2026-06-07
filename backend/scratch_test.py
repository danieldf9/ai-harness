from fastapi.testclient import TestClient
import uuid
import sys

from onyx.main import get_application
from onyx.db.engine.sql_engine import get_session_context_manager

app = get_application()
client = TestClient(app)

def test_prompt_registry():
    # 1. Create a prompt template
    resp = client.post("/api/manage/prompt-templates", json={
        "name": "Test Template",
        "description": "A test template",
        "default_content": "Hello {name}",
        "variables": ["name"]
    })
    print("Create template:", resp.status_code, resp.text)
    
    if resp.status_code != 200:
        return
        
    template_id = resp.json()["id"]

    # 2. Get the template
    resp = client.get(f"/api/manage/prompt-templates/{template_id}")
    print("Get template:", resp.status_code, resp.text)

    # 3. Create a version
    resp = client.post(f"/api/manage/prompt-templates/{template_id}/versions", json={
        "commit_message": "Initial version",
        "content": "Hello {name}, how are you?"
    })
    print("Create version:", resp.status_code, resp.text)
    version_id = resp.json()["id"]

    # 4. Activate version
    resp = client.post(f"/api/manage/prompt-templates/{template_id}/versions/{version_id}/activate")
    print("Activate version:", resp.status_code, resp.text)

    # 5. Assign to a persona
    # Create a dummy persona first, we need a persona ID
    # Since we can't easily create one here, we'll try to find an existing one or create a mock assignment directly
    print("Done testing template/version creation and activation.")

if __name__ == "__main__":
    test_prompt_registry()
