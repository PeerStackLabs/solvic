"""
Base class for task manager plugins.

To add support for a new task manager, create a new file in this directory
and implement the TaskManager interface.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional


class Task:
    """Represents a task extracted from a transcript"""

    def __init__(
        self,
        name: str,
        due_date: Optional[str] = None,
        notes: Optional[str] = None,
        priority: Optional[str] = None,
    ):
        self.name = name
        self.due_date = due_date  # Format: YYYY-MM-DD or None
        self.notes = notes
        self.priority = priority  # high, medium, low

    def to_dict(self) -> Dict[str, Any]:
        """Convert task to dictionary"""
        return {
            "name": self.name,
            "due_date": self.due_date,
            "notes": self.notes,
            "priority": self.priority,
        }


class TaskManager(ABC):
    """Abstract base class for task manager integrations"""

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize task manager with configuration.

        Args:
            config: Configuration dictionary from config.yml
        """
        self.config = config

    @abstractmethod
    def create_task(self, task: Task) -> Optional[Dict[str, Any]]:
        """
        Create a task in the task manager.

        Args:
            task: Task object to create

        Returns:
            Dictionary containing created task info (including ID), or None if failed

        Example return:
            {
                "id": "123456",
                "name": "Write report",
                "url": "https://taskmanager.com/tasks/123456"
            }
        """
        pass

    @abstractmethod
    def get_project_info(self) -> Optional[Dict[str, Any]]:
        """
        Get information about the configured project/workspace.

        Returns:
            Dictionary with project info, or None if not found

        Example return:
            {
                "id": "123",
                "name": "My Project",
                "workspace": "My Workspace"
            }
        """
        pass

    @abstractmethod
    def test_connection(self) -> bool:
        """
        Test if the connection to the task manager is working.

        Returns:
            True if connection successful, False otherwise
        """
        pass

    def create_tasks_bulk(self, tasks: List[Task]) -> List[Dict[str, Any]]:
        """
        Create multiple tasks. Default implementation calls create_task() for each.
        Override this if your task manager supports bulk creation.

        Args:
            tasks: List of Task objects to create

        Returns:
            List of created task info dictionaries
        """
        created = []
        for task in tasks:
            result = self.create_task(task)
            if result:
                created.append(result)
        return created
