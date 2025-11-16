"""
Notion task manager integration.

Creates tasks as pages in a Notion database.

Setup:
1. Create internal integration: https://www.notion.so/my-integrations
2. Get integration token
3. Create a database in Notion for tasks
4. Share database with your integration
5. Get database ID from URL:
   https://notion.so/workspace/DATABASE_ID?v=...
6. Configure in config.yml

Requires:
    pip install notion-client

Database should have these properties (will auto-create if missing):
- Name (title) - Task name
- Due Date (date) - When it's due
- Notes (rich_text) - Additional context
- Status (select) - Todo, In Progress, Done
"""

import os
from typing import Dict, Any, Optional
from datetime import datetime

from .base import Task, TaskManager

try:
    from notion_client import Client
    NOTION_AVAILABLE = True
except ImportError:
    NOTION_AVAILABLE = False


class NotionTaskManager(TaskManager):
    """Notion implementation of TaskManager"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)

        if not NOTION_AVAILABLE:
            raise ImportError(
                "Notion integration requires notion-client. Install with: pip install notion-client"
            )

        # Get API token from environment
        notion_config = config.get("notion", {})
        token_env = notion_config.get("api_key_env", "NOTION_API_KEY")
        self.api_token = os.getenv(token_env)

        if not self.api_token:
            raise ValueError(
                f"Notion API token not found in environment variable: {token_env}"
            )

        self.client = Client(auth=self.api_token)

        # Get database ID
        self.database_id = notion_config.get("database_id")

        if not self.database_id:
            raise ValueError("Notion database_id is required in config")

    def create_task(self, task: Task) -> Optional[Dict[str, Any]]:
        """Create a task (page) in Notion database"""

        try:
            # Build page properties
            properties = {
                "Name": {
                    "title": [
                        {
                            "text": {
                                "content": task.name
                            }
                        }
                    ]
                }
            }

            # Add due date if valid
            if task.due_date:
                try:
                    # Validate date format
                    datetime.strptime(task.due_date, "%Y-%m-%d")
                    properties["Due Date"] = {
                        "date": {
                            "start": task.due_date
                        }
                    }
                except ValueError:
                    # Invalid date - add to notes instead
                    if task.notes:
                        task.notes = f"Due: {task.due_date}\n\n{task.notes}"
                    else:
                        task.notes = f"Due: {task.due_date}"

            # Add notes if provided
            if task.notes:
                properties["Notes"] = {
                    "rich_text": [
                        {
                            "text": {
                                "content": task.notes[:2000]  # Notion limit
                            }
                        }
                    ]
                }

            # Add status (default to Todo)
            properties["Status"] = {
                "select": {
                    "name": "Todo"
                }
            }

            # Create page in database
            response = self.client.pages.create(
                parent={"database_id": self.database_id},
                properties=properties
            )

            return {
                "id": response["id"],
                "name": task.name,
                "url": response["url"]
            }

        except Exception as e:
            print(f"Failed to create Notion task: {e}")
            return None

    def get_project_info(self) -> Optional[Dict[str, Any]]:
        """Get information about the configured database"""

        try:
            database = self.client.databases.retrieve(database_id=self.database_id)

            return {
                "id": database["id"],
                "name": database.get("title", [{}])[0].get("plain_text", "Unnamed Database"),
                "url": database["url"]
            }

        except Exception as e:
            print(f"Error getting Notion database info: {e}")
            return None

    def test_connection(self) -> bool:
        """Test if Notion API connection is working"""

        try:
            # Try to retrieve the database
            self.client.databases.retrieve(database_id=self.database_id)
            return True

        except Exception as e:
            print(f"Notion connection test failed: {e}")
            return False
