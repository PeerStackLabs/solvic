"""
Asana task manager integration.

Requires:
- ASANA_TOKEN environment variable (Personal Access Token)
- workspace_id in config
- project_id in config

Get your Personal Access Token: https://app.asana.com/0/my-apps
Find workspace/project IDs: https://app.asana.com/api/1.0/workspaces
"""

import os
import re
import requests
from typing import Dict, Any, Optional

from .base import Task, TaskManager


class AsanaTaskManager(TaskManager):
    """Asana implementation of TaskManager"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)

        # Get API token from environment
        api_key_env = config.get("asana", {}).get("api_key_env", "ASANA_TOKEN")
        self.api_token = os.getenv(api_key_env)

        if not self.api_token:
            raise ValueError(
                f"Asana API token not found in environment variable: {api_key_env}"
            )

        # Get workspace and project IDs
        asana_config = config.get("asana", {})
        self.workspace_id = asana_config.get("workspace_id")
        self.project_id = asana_config.get("project_id")

        if not self.workspace_id or not self.project_id:
            raise ValueError("Asana workspace_id and project_id are required in config")

        # Set up API headers
        self.headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json",
        }

        self.base_url = "https://app.asana.com/api/1.0"

    def create_task(self, task: Task) -> Optional[Dict[str, Any]]:
        """Create a task in Asana"""

        # Build task payload
        task_data = {
            "data": {
                "name": task.name,
                "workspace": self.workspace_id,
                "projects": [self.project_id],
            }
        }

        # Add due date if provided and valid (YYYY-MM-DD format)
        if task.due_date:
            if re.match(r"^\d{4}-\d{2}-\d{2}$", task.due_date):
                task_data["data"]["due_on"] = task.due_date
            else:
                # Invalid date format - add to notes instead
                if task.notes:
                    task.notes = f"Due: {task.due_date}\n\n{task.notes}"
                else:
                    task.notes = f"Due: {task.due_date}"

        # Add notes if provided
        if task.notes:
            task_data["data"]["notes"] = task.notes

        # Create task via API
        try:
            response = requests.post(
                f"{self.base_url}/tasks", json=task_data, headers=self.headers
            )

            if response.status_code == 201:
                created_task = response.json()["data"]
                return {
                    "id": created_task["gid"],
                    "name": created_task["name"],
                    "url": f"https://app.asana.com/0/{self.project_id}/{created_task['gid']}",
                }
            else:
                print(
                    f"Failed to create Asana task: {response.status_code} - {response.text}"
                )
                return None

        except Exception as e:
            print(f"Error creating Asana task: {e}")
            return None

    def get_project_info(self) -> Optional[Dict[str, Any]]:
        """Get information about the configured project"""

        try:
            response = requests.get(
                f"{self.base_url}/projects/{self.project_id}", headers=self.headers
            )

            if response.status_code == 200:
                project = response.json()["data"]
                return {
                    "id": project["gid"],
                    "name": project["name"],
                    "workspace": project.get("workspace", {}).get("name", "Unknown"),
                }
            else:
                return None

        except Exception as e:
            print(f"Error getting Asana project info: {e}")
            return None

    def test_connection(self) -> bool:
        """Test if the Asana API connection is working"""

        try:
            # Try to get workspace info
            response = requests.get(
                f"{self.base_url}/workspaces/{self.workspace_id}",
                headers=self.headers,
            )
            return response.status_code == 200

        except Exception as e:
            print(f"Asana connection test failed: {e}")
            return False
