"""
Base class for transcript source plugins.

To add support for a new transcript source, create a new file in this directory
and implement the TranscriptSource interface.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class Transcript:
    """Represents a meeting transcript"""

    id: str  # Unique identifier
    name: str  # Transcript name/title
    text: str  # Full transcript text
    source: str  # Source identifier (e.g., "google_drive:account1")
    modified_time: Optional[str] = None  # ISO format timestamp


class TranscriptSource(ABC):
    """Abstract base class for transcript source integrations"""

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize transcript source with configuration.

        Args:
            config: Configuration dictionary from config.yml
        """
        self.config = config

    @abstractmethod
    def get_recent_transcripts(self, hours: int = 24) -> List[Transcript]:
        """
        Get transcripts modified in the last N hours.

        Args:
            hours: Lookback window in hours

        Returns:
            List of Transcript objects
        """
        pass

    @abstractmethod
    def test_connection(self) -> bool:
        """
        Test if the connection to the transcript source is working.

        Returns:
            True if connection successful, False otherwise
        """
        pass

    def mark_processed(self, transcript_id: str):
        """
        Mark a transcript as processed (optional, handled by main script).

        Args:
            transcript_id: The transcript ID to mark
        """
        pass
