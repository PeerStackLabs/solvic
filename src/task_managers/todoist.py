"""
Todoist task manager integration - TEMPLATE / COMING SOON

This is a template for implementing Todoist support.
Contributions welcome!

Todoist API docs: https://developer.todoist.com/rest/v2/

To implement:
1. Get API token from environment variable
2. Implement create_task() to call Todoist API
3. Implement get_project_info() to fetch project details
4. Implement test_connection() to verify API access
5. Test thoroughly
6. Submit PR!

Todoist API endpoints needed:
- POST https://api.todoist.com/rest/v2/tasks (create task)
- GET https://api.todoist.com/rest/v2/projects/{id} (get project)
"""

import os
import requests
from typing import Dict, Any, Optional

from .base import Task, TaskManager


class TodoistTaskManager(TaskManager):
    """Todoist implementation of TaskManager - COMING SOON"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)

        # TODO: Get API token from environment
        api_key_env = config.get("todoist", {}).get("api_key_env", "TODOIST_API_KEY")
        self.api_token = os.getenv(api_key_env)

        if not self.api_token:
            raise ValueError(
                f"Todoist API token not found in environment variable: {api_key_env}"
            )

        # TODO: Get project ID from config
        todoist_config = config.get("todoist", {})
        self.project_id = todoist_config.get("project_id")

        if not self.project_id:
            raise ValueError("Todoist project_id is required in config")

        # Set up API headers
        self.headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json",
        }

        self.base_url = "https://api.todoist.com/rest/v2"

    def create_task(self, task: Task) -> Optional[Dict[str, Any]]:
        """
        Create a task in Todoist.

        Todoist API: POST /tasks
        Request body:
        {
            "content": "Task name",
            "project_id": "123456",
            "due_string": "tomorrow" or "2025-10-30",
            "description": "Task notes",
            "priority": 1-4 (1=normal, 4=urgent)
        }
        """

        # TODO: Implement Todoist task creation
        # See: https://developer.todoist.com/rest/v2/#create-a-new-task

        raise NotImplementedError("Todoist integration coming soon! Contributions welcome.")

    def get_project_info(self) -> Optional[Dict[str, Any]]:
        """
        Get information about the configured project.

        Todoist API: GET /projects/{project_id}
        """

        # TODO: Implement project info retrieval
        # See: https://developer.todoist.com/rest/v2/#get-a-project

        raise NotImplementedError("Todoist integration coming soon!")

    def test_connection(self) -> bool:
        """
        Test if the Todoist API connection is working.

        Can test by fetching the project info.
        """

        # TODO: Implement connection test

        raise NotImplementedError("Todoist integration coming soon!")


# Example implementation (pseudocode for contributors):
"""
def create_task(self, task: Task) -> Optional[Dict[str, Any]]:
    task_data = {
        "content": task.name,
        "project_id": self.project_id,
    }

    # Add due date if provided
    if task.due_date:
        task_data["due_string"] = task.due_date  # Todoist accepts YYYY-MM-DD

    # Add description/notes
    if task.notes:
        task_data["description"] = task.notes

    # Map priority
    if task.priority == "high":
        task_data["priority"] = 4
    elif task.priority == "medium":
        task_data["priority"] = 2
    else:
        task_data["priority"] = 1

    try:
        response = requests.post(
            f"{self.base_url}/tasks",
            json=task_data,
            headers=self.headers
        )

        if response.status_code == 200:
            created_task = response.json()
            return {
                "id": created_task["id"],
                "name": created_task["content"],
                "url": created_task["url"]
            }
        else:
            print(f"Failed to create Todoist task: {response.status_code}")
            return None

    except Exception as e:
        print(f"Error creating Todoist task: {e}")
        return None
"""
