"""
Linear task manager integration.

Creates issues in Linear (popular with engineering teams).

Setup:
1. Get API key: https://linear.app/settings/api
2. Get team ID: https://linear.app/TEAMNAME/team/TEAM_ID
3. Optionally get project ID for default project
4. Configure in config.yml

Requires:
    No additional packages (uses requests)

Linear is popular with:
- Engineering teams
- Product teams
- Tech startups
- Fast-moving companies
"""

import os
import requests
from typing import Dict, Any, Optional
from datetime import datetime

from .base import Task, TaskManager


class LinearTaskManager(TaskManager):
    """Linear implementation of TaskManager"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)

        # Get API key from environment
        linear_config = config.get("linear", {})
        api_key_env = linear_config.get("api_key_env", "LINEAR_API_KEY")
        self.api_key = os.getenv(api_key_env)

        if not self.api_key:
            raise ValueError(
                f"Linear API key not found in environment variable: {api_key_env}"
            )

        # Get team ID (required)
        self.team_id = linear_config.get("team_id")

        if not self.team_id:
            raise ValueError("Linear team_id is required in config")

        # Optional: project ID for organizing tasks
        self.project_id = linear_config.get("project_id")

        # Linear API endpoint
        self.api_url = "https://api.linear.app/graphql"
        self.headers = {
            "Authorization": self.api_key,
            "Content-Type": "application/json"
        }

    def create_task(self, task: Task) -> Optional[Dict[str, Any]]:
        """Create an issue in Linear"""

        try:
            # Build GraphQL mutation
            mutation = """
            mutation IssueCreate($input: IssueCreateInput!) {
              issueCreate(input: $input) {
                success
                issue {
                  id
                  identifier
                  title
                  url
                }
              }
            }
            """

            # Build input variables
            variables = {
                "input": {
                    "title": task.name,
                    "teamId": self.team_id
                }
            }

            # Add description/notes
            if task.notes:
                variables["input"]["description"] = task.notes

            # Add due date if valid
            if task.due_date:
                try:
                    # Validate date format
                    datetime.strptime(task.due_date, "%Y-%m-%d")
                    variables["input"]["dueDate"] = task.due_date
                except ValueError:
                    # Invalid date - add to description instead
                    desc = variables["input"].get("description", "")
                    variables["input"]["description"] = f"Due: {task.due_date}\n\n{desc}"

            # Add to project if specified
            if self.project_id:
                variables["input"]["projectId"] = self.project_id

            # Map priority
            if task.priority:
                priority_map = {
                    "high": 1,    # Urgent
                    "medium": 2,  # High
                    "low": 3      # Normal
                }
                variables["input"]["priority"] = priority_map.get(task.priority.lower(), 3)

            # Execute mutation
            response = requests.post(
                self.api_url,
                json={"query": mutation, "variables": variables},
                headers=self.headers
            )

            if response.status_code == 200:
                data = response.json()

                if data.get("data", {}).get("issueCreate", {}).get("success"):
                    issue = data["data"]["issueCreate"]["issue"]
                    return {
                        "id": issue["id"],
                        "name": issue["title"],
                        "identifier": issue["identifier"],  # e.g., "ENG-123"
                        "url": issue["url"]
                    }
                else:
                    print(f"Linear API returned success=false")
                    return None
            else:
                print(f"Failed to create Linear issue: {response.status_code} - {response.text}")
                return None

        except Exception as e:
            print(f"Error creating Linear task: {e}")
            return None

    def get_project_info(self) -> Optional[Dict[str, Any]]:
        """Get information about the configured team/project"""

        try:
            # Query team info
            query = """
            query Team($id: String!) {
              team(id: $id) {
                id
                name
                key
              }
            }
            """

            response = requests.post(
                self.api_url,
                json={"query": query, "variables": {"id": self.team_id}},
                headers=self.headers
            )

            if response.status_code == 200:
                data = response.json()
                team = data.get("data", {}).get("team")

                if team:
                    return {
                        "id": team["id"],
                        "name": team["name"],
                        "key": team["key"]  # e.g., "ENG"
                    }

            return None

        except Exception as e:
            print(f"Error getting Linear team info: {e}")
            return None

    def test_connection(self) -> bool:
        """Test if Linear API connection is working"""

        try:
            # Try to get viewer (authenticated user) info
            query = """
            query {
              viewer {
                id
                name
              }
            }
            """

            response = requests.post(
                self.api_url,
                json={"query": query},
                headers=self.headers
            )

            if response.status_code == 200:
                data = response.json()
                return "data" in data and "viewer" in data["data"]

            return False

        except Exception as e:
            print(f"Linear connection test failed: {e}")
            return False
