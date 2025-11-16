"""
Plain text input source.

Simply paste or provide text content, and tasks will be extracted.
Great for:
- Notes you've taken
- Brain dumps
- Copy-pasted content from anywhere
- Documents you've read

Usage:
    python src/main.py --text "Meeting notes: Need to send report by Friday. Follow up with client next week."

Or provide a text file:
    python src/main.py --file notes.txt
"""

from typing import List, Dict, Any
from pathlib import Path

from .base import TranscriptSource, Transcript


class PlainTextSource(TranscriptSource):
    """Plain text input implementation"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)

        # Get text from config (passed from CLI)
        plain_text_config = config.get("plain_text", {})
        self.text_content = plain_text_config.get("text", "")
        self.file_path = plain_text_config.get("file")

    def get_recent_transcripts(self, hours: int = 24) -> List[Transcript]:
        """Get text content as a 'transcript'"""

        # Read from file if provided
        if self.file_path:
            file_path = Path(self.file_path)
            if not file_path.exists():
                print(f"Error: File not found: {self.file_path}")
                return []

            with open(file_path, 'r') as f:
                text = f.read()

            return [
                Transcript(
                    id=f"file:{file_path.name}",
                    name=file_path.name,
                    text=text,
                    source="plain_text:file"
                )
            ]

        # Use direct text input
        elif self.text_content:
            return [
                Transcript(
                    id="cli:text",
                    name="CLI Text Input",
                    text=self.text_content,
                    source="plain_text:cli"
                )
            ]

        return []

    def test_connection(self) -> bool:
        """Always returns True - no connection needed"""
        return True
