"""
Email integration for extracting tasks from email threads.

Monitors Gmail for emails containing action items, requests, or tasks.

Setup:
1. Use same Google Cloud project as Google Drive
2. Enable Gmail API: https://console.cloud.google.com/apis/library/gmail.googleapis.com
3. Use same OAuth credentials (client_secret.json)
4. Configure in config.yml:
   - Email addresses to monitor
   - Labels to watch (e.g., "needs-action", "client-requests")
   - Keywords to filter by

Great for:
- Client requests via email
- Internal team coordination
- External partner communications
- Follow-up actions

Extracts tasks from:
- Email body
- Thread conversations
- Subject lines with action words
"""

import os
import pickle
import base64
from datetime import datetime, timedelta
from typing import List, Dict, Any
from pathlib import Path
import re

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from .base import TranscriptSource, Transcript


class EmailSource(TranscriptSource):
    """Gmail integration for task extraction"""

    SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)

        email_config = config.get("email", {})

        # Get Gmail accounts to monitor
        self.accounts = email_config.get("accounts", [])

        if not self.accounts:
            raise ValueError("No email accounts configured")

        # Get client secret file
        client_secret_file = email_config.get("client_secret_file", "client_secret.json")
        self.client_secret_path = Path(client_secret_file)

        if not self.client_secret_path.exists():
            raise ValueError(f"Client secret file not found: {client_secret_file}")

        # Search configuration
        self.search_query = email_config.get(
            "search_query",
            "is:unread"  # Default: only unread emails
        )

        # Authenticate accounts
        self.services = {}
        for account in self.accounts:
            email = account.get("email")
            label = account.get("label")

            if not email or not label:
                print(f"Warning: Skipping account with missing email or label")
                continue

            try:
                service = self._authenticate_account(label)
                self.services[label] = {
                    "service": service,
                    "email": email
                }
            except Exception as e:
                print(f"Warning: Failed to authenticate {email}: {e}")

    def _authenticate_account(self, label: str):
        """Authenticate Gmail account using OAuth"""

        token_file = Path(f"token_gmail_{label}.pickle")
        creds = None

        # Load existing token
        if token_file.exists():
            with open(token_file, 'rb') as token:
                creds = pickle.load(token)

        # Refresh or get new token
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    str(self.client_secret_path), self.SCOPES
                )
                creds = flow.run_local_server(port=0)

            # Save credentials
            with open(token_file, 'wb') as token:
                pickle.dump(creds, token)

        return build('gmail', 'v1', credentials=creds)

    def get_recent_transcripts(self, hours: int = 24) -> List[Transcript]:
        """Get recent emails from all configured accounts"""

        all_transcripts = []

        # Calculate time filter (Gmail uses seconds since epoch)
        after_timestamp = int((datetime.utcnow() - timedelta(hours=hours)).timestamp())

        for label, account_info in self.services.items():
            service = account_info["service"]
            email = account_info["email"]

            try:
                # Build search query with time filter
                query = f"{self.search_query} after:{after_timestamp}"

                # Search for messages
                results = service.users().messages().list(
                    userId='me',
                    q=query,
                    maxResults=50  # Limit to prevent overload
                ).execute()

                messages = results.get('messages', [])

                if not messages:
                    continue

                # Process each email
                for msg in messages:
                    try:
                        email_transcript = self._process_email(service, msg['id'])

                        if email_transcript:
                            transcript = Transcript(
                                id=f"email:{label}:{msg['id']}",
                                name=email_transcript['subject'],
                                text=email_transcript['body'],
                                source=f"email:{email}"
                            )
                            all_transcripts.append(transcript)

                    except Exception as e:
                        print(f"Warning: Failed to process email {msg['id']}: {e}")

            except Exception as e:
                print(f"Error checking email {email}: {e}")

        return all_transcripts

    def _process_email(self, service, msg_id: str) -> Dict[str, str]:
        """Process a single email and extract content"""

        # Get full message
        message = service.users().messages().get(
            userId='me',
            id=msg_id,
            format='full'
        ).execute()

        # Extract subject
        headers = message.get('payload', {}).get('headers', [])
        subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
        from_email = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown')

        # Extract body
        body = self._get_email_body(message.get('payload', {}))

        if not body:
            return None

        # Format as readable text
        formatted_body = f"From: {from_email}\nSubject: {subject}\n\n{body}"

        return {
            'subject': subject,
            'body': formatted_body
        }

    def _get_email_body(self, payload: Dict[str, Any]) -> str:
        """Extract email body from payload"""

        body = ""

        # Check for plain text part
        if 'parts' in payload:
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain':
                    data = part.get('body', {}).get('data', '')
                    if data:
                        body = base64.urlsafe_b64decode(data).decode('utf-8')
                        break

                # Recursively check nested parts
                elif 'parts' in part:
                    nested_body = self._get_email_body(part)
                    if nested_body:
                        body = nested_body
                        break

        # Fallback to body data if no parts
        if not body and 'body' in payload:
            data = payload['body'].get('data', '')
            if data:
                body = base64.urlsafe_b64decode(data).decode('utf-8')

        # Clean up body (remove excessive newlines, etc.)
        body = re.sub(r'\n{3,}', '\n\n', body)

        return body.strip()

    def test_connection(self) -> bool:
        """Test if Gmail API connection is working"""

        if not self.services:
            return False

        for label, account_info in self.services.items():
            try:
                service = account_info["service"]
                # Try to get profile (minimal query)
                service.users().getProfile(userId='me').execute()
            except Exception as e:
                print(f"Gmail connection test failed for {label}: {e}")
                return False

        return True
