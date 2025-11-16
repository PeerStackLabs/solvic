"""
Base class for LLM provider plugins.

To add support for a new LLM, create a new file in this directory
and implement the LLMProvider interface.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any


class LLMProvider(ABC):
    """Abstract base class for LLM integrations"""

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize LLM provider with configuration.

        Args:
            config: Configuration dictionary from config.yml
        """
        self.config = config

    @abstractmethod
    def extract_tasks(self, transcript_text: str) -> List[Dict[str, Any]]:
        """
        Extract tasks from a transcript using the LLM.

        Args:
            transcript_text: The meeting transcript text

        Returns:
            List of task dictionaries with format:
            [
                {
                    "name": "Task name",
                    "due_date": "2025-10-30" or "",
                    "notes": "Context and details",
                    "priority": "high" or "medium" or "low"
                },
                ...
            ]

        The LLM should:
        - Extract all actionable tasks, deliverables, and to-dos
        - Provide clear, action-oriented task names
        - Include YYYY-MM-DD dates only (or empty string if no date)
        - Add relevant context in notes
        """
        pass

    @abstractmethod
    def test_connection(self) -> bool:
        """
        Test if the connection to the LLM API is working.

        Returns:
            True if connection successful, False otherwise
        """
        pass

    def get_extraction_prompt(self, transcript_text: str) -> str:
        """
        Generate the prompt for task extraction.
        Override this to customize the prompt for specific LLM models.

        Args:
            transcript_text: The meeting transcript

        Returns:
            Formatted prompt string
        """
        return f"""Analyze this meeting transcript and extract ALL actionable tasks, deliverables, and to-dos.

For each task, provide:
1. Task name (clear, action-oriented)
2. Due date in YYYY-MM-DD format ONLY (if mentioned) - leave EMPTY if no specific date mentioned
3. Any relevant notes or context

Format your response as a JSON array like this:
[
  {{
    "name": "Write Q4 marketing strategy deck",
    "due_date": "2025-10-30",
    "notes": "Include competitive analysis and budget breakdown"
  }},
  {{
    "name": "Schedule follow-up call with stakeholders",
    "due_date": "2025-10-26",
    "notes": "Discuss timeline and milestones"
  }},
  {{
    "name": "Task with no specific date",
    "due_date": "",
    "notes": "Do this ASAP"
  }}
]

CRITICAL RULES:
- due_date must be YYYY-MM-DD format (e.g. "2025-10-30") or empty string ""
- NEVER use words like "ASAP", "soon", "next week" in due_date field
- If no specific date mentioned, leave due_date as ""
- Return ONLY the JSON array, no other text

Transcript:
{transcript_text}
"""
