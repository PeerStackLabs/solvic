"""
Slack integration for extracting tasks from conversations.

Two modes:
1. Slash command: /extract-tasks in any channel
2. Monitoring: Watch specific channels for action items

Setup:
1. Create Slack app: https://api.slack.com/apps
2. Add Bot Token Scopes:
   - channels:history (read public channels)
   - channels:read (view public channels)
   - chat:write (post messages)
   - commands (add slash commands)
3. Install app to workspace
4. Get Bot User OAuth Token
5. Add to config:
   - SLACK_BOT_TOKEN environment variable
   - channels_to_monitor in config.yml

Requires:
    pip install slack-sdk
"""

import os
from datetime import datetime, timedelta
from typing import List, Dict, Any

from .base import TranscriptSource, Transcript

try:
    from slack_sdk import WebClient
    from slack_sdk.errors import SlackApiError
    SLACK_AVAILABLE = True
except ImportError:
    SLACK_AVAILABLE = False


class SlackSource(TranscriptSource):
    """Slack integration for task extraction"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)

        if not SLACK_AVAILABLE:
            raise ImportError(
                "Slack integration requires slack-sdk. Install with: pip install slack-sdk"
            )

        slack_config = config.get("slack", {})

        # Get workspaces to monitor
        self.workspaces = slack_config.get("workspaces", [])

        if not self.workspaces:
            raise ValueError("No Slack workspaces configured")

        # Initialize clients for each workspace
        self.workspace_clients = {}
        for workspace in self.workspaces:
            workspace_name = workspace.get("name")
            token_env = workspace.get("bot_token_env")

            if not workspace_name or not token_env:
                print(f"Warning: Skipping workspace with missing name or token_env")
                continue

            bot_token = os.getenv(token_env)
            if not bot_token:
                print(f"Warning: Slack token not found for {workspace_name}: {token_env}")
                continue

            self.workspace_clients[workspace_name] = {
                "client": WebClient(token=bot_token),
                "channels": workspace.get("channels_to_monitor", [])
            }

        if not self.workspace_clients:
            raise ValueError("No valid Slack workspaces configured")

        # Message lookback settings
        self.max_messages = slack_config.get("max_messages_per_channel", 100)

    def get_recent_transcripts(self, hours: int = 24) -> List[Transcript]:
        """Get recent Slack messages from all monitored workspaces and channels"""

        transcripts = []

        # Calculate time threshold (Slack uses Unix timestamps)
        oldest_timestamp = (datetime.utcnow() - timedelta(hours=hours)).timestamp()

        # Process each workspace
        for workspace_name, workspace_info in self.workspace_clients.items():
            client = workspace_info["client"]
            channels = workspace_info["channels"]

            if not channels:
                print(f"No channels configured for workspace: {workspace_name}")
                continue

            # Process each channel in this workspace
            for channel_config in channels:
                channel_id = channel_config.get("id")
                channel_name = channel_config.get("name", channel_id)

                try:
                    # Get channel history
                    result = client.conversations_history(
                        channel=channel_id,
                        oldest=str(oldest_timestamp),
                        limit=self.max_messages
                    )

                    messages = result.get("messages", [])

                    if not messages:
                        continue

                    # Convert messages to readable text
                    conversation_text = self._format_messages(messages, client, channel_id)

                    transcript = Transcript(
                        id=f"slack:{workspace_name}:{channel_id}:{int(oldest_timestamp)}",
                        name=f"{workspace_name} #{channel_name} - Last {hours}h",
                        text=conversation_text,
                        source=f"slack:{workspace_name}:{channel_name}"
                    )

                    transcripts.append(transcript)

                except SlackApiError as e:
                    print(f"Error fetching Slack channel {workspace_name}/{channel_name}: {e.response['error']}")

        return transcripts

    def _format_messages(self, messages: List[Dict[str, Any]], client: WebClient, channel_id: str) -> str:
        """Format Slack messages into readable text"""

        # Sort by timestamp (oldest first)
        messages = sorted(messages, key=lambda m: float(m.get("ts", 0)))

        formatted = []

        for msg in messages:
            user = msg.get("user", "Unknown")
            text = msg.get("text", "")
            timestamp = msg.get("ts", "")

            # Skip bot messages unless they're important
            if msg.get("bot_id") and not text.strip():
                continue

            # Convert timestamp to readable format
            try:
                dt = datetime.fromtimestamp(float(timestamp))
                time_str = dt.strftime("%Y-%m-%d %H:%M")
            except:
                time_str = "Unknown time"

            formatted.append(f"[{time_str}] {user}: {text}")

            # Include thread replies if any
            if msg.get("thread_ts") and msg.get("reply_count", 0) > 0:
                try:
                    thread_result = client.conversations_replies(
                        channel=channel_id,
                        ts=msg["thread_ts"]
                    )

                    for reply in thread_result.get("messages", [])[1:]:  # Skip original
                        reply_user = reply.get("user", "Unknown")
                        reply_text = reply.get("text", "")
                        formatted.append(f"  ↳ {reply_user}: {reply_text}")

                except SlackApiError:
                    pass

        return "\n".join(formatted)

    def test_connection(self) -> bool:
        """Test if Slack API connection is working for all workspaces"""

        if not self.workspace_clients:
            return False

        # Test each workspace
        for workspace_name, workspace_info in self.workspace_clients.items():
            try:
                client = workspace_info["client"]
                # Try to get bot info
                response = client.auth_test()
                if not response.get("ok", False):
                    print(f"Slack connection test failed for workspace: {workspace_name}")
                    return False

            except SlackApiError as e:
                print(f"Slack connection test failed for {workspace_name}: {e.response['error']}")
                return False

        return True


# Helper function for slash command (to be used in a separate bot server)
def extract_tasks_from_channel(
    client: WebClient,
    channel_id: str,
    hours: int = 24
) -> str:
    """
    Helper function to extract tasks from a channel.
    Can be called from a Slack slash command handler.

    Returns formatted text with extracted tasks.
    """

    # This would be called from your Slack bot's slash command handler
    # Example usage in a Flask/FastAPI app:
    #
    # @app.post("/slack/commands/extract-tasks")
    # def handle_extract_tasks(request):
    #     channel_id = request.form["channel_id"]
    #     tasks = extract_tasks_from_channel(client, channel_id)
    #     return {"text": tasks}

    pass  # Implementation depends on your bot setup
