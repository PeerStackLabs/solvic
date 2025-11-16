"""
Google Drive transcript source integration.

Monitors specified Google Drive folders for meeting transcripts.
Supports multiple Google accounts.

Setup:
1. Create OAuth credentials in Google Cloud Console
2. Enable Google Drive API
3. Add test users (your email addresses)
4. Configure accounts in config.yml

OAuth credentials will be saved as token_*.pickle files after first authentication.
"""

import os
import pickle
import io
from datetime import datetime, timedelta
from typing import List, Dict, Any
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

from .base import TranscriptSource, Transcript


class GoogleDriveSource(TranscriptSource):
    """Google Drive implementation of TranscriptSource"""

    SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)

        # Get Google Drive config
        drive_config = config.get("google_drive", {})
        self.accounts = drive_config.get("accounts", [])

        if not self.accounts:
            raise ValueError("No Google Drive accounts configured")

        # Get client secret file path
        client_secret_file = drive_config.get("client_secret_file", "client_secret.json")
        self.client_secret_path = Path(client_secret_file)

        if not self.client_secret_path.exists():
            raise ValueError(f"Client secret file not found: {client_secret_file}")

        # Authenticate all accounts
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
                    "email": email,
                    "folder_name": account.get("folder_name", "meet recordings")
                }
            except Exception as e:
                print(f"Warning: Failed to authenticate {email}: {e}")

    def _authenticate_account(self, label: str):
        """Authenticate a Google Drive account using OAuth"""
        token_file = Path(f"token_{label}.pickle")
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

            # Save the credentials
            with open(token_file, 'wb') as token:
                pickle.dump(creds, token)

        return build('drive', 'v3', credentials=creds)

    def _find_folder(self, service, folder_name: str) -> str:
        """Find a folder by name (case-insensitive)"""
        query = f"name contains '{folder_name.split()[0].lower()}' and mimeType='application/vnd.google-apps.folder' and trashed=false"

        results = service.files().list(
            q=query,
            spaces='drive',
            fields='files(id, name)'
        ).execute()

        folders = results.get('files', [])

        # Try exact match first
        for folder in folders:
            if folder['name'].lower() == folder_name.lower():
                return folder['id']

        # Fall back to first match
        if folders:
            return folders[0]['id']

        return None

    def _get_transcripts_from_folder(
        self,
        service,
        folder_id: str,
        hours: int,
        account_label: str
    ) -> List[Transcript]:
        """Get transcript files from a folder"""

        # Calculate time threshold
        time_threshold = (datetime.utcnow() - timedelta(hours=hours)).isoformat() + 'Z'

        # Look for Google Docs (transcripts) in the folder
        query = (
            f"'{folder_id}' in parents and "
            f"mimeType='application/vnd.google-apps.document' and "
            f"modifiedTime > '{time_threshold}' and "
            f"trashed=false"
        )

        results = service.files().list(
            q=query,
            spaces='drive',
            fields='files(id, name, modifiedTime)',
            orderBy='modifiedTime desc'
        ).execute()

        files = results.get('files', [])
        transcripts = []

        for file in files:
            try:
                # Download transcript text
                text = self._download_transcript(service, file['id'])

                transcript = Transcript(
                    id=f"{account_label}:{file['id']}",
                    name=file['name'],
                    text=text,
                    source=f"google_drive:{account_label}",
                    modified_time=file['modifiedTime']
                )
                transcripts.append(transcript)

            except Exception as e:
                print(f"Warning: Failed to download transcript {file['name']}: {e}")

        return transcripts

    def _download_transcript(self, service, file_id: str) -> str:
        """Download a Google Doc as plain text"""
        request = service.files().export_media(
            fileId=file_id,
            mimeType='text/plain'
        )

        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)

        done = False
        while not done:
            status, done = downloader.next_chunk()

        return fh.getvalue().decode('utf-8')

    def get_recent_transcripts(self, hours: int = 24) -> List[Transcript]:
        """Get transcripts from all configured accounts"""
        all_transcripts = []

        for label, account_info in self.services.items():
            service = account_info["service"]
            folder_name = account_info["folder_name"]
            email = account_info["email"]

            try:
                # Find the transcript folder
                folder_id = self._find_folder(service, folder_name)

                if not folder_id:
                    print(f"Warning: '{folder_name}' folder not found in {email}")
                    continue

                # Get transcripts from folder
                transcripts = self._get_transcripts_from_folder(
                    service, folder_id, hours, label
                )

                all_transcripts.extend(transcripts)

            except Exception as e:
                print(f"Error checking {email}: {e}")

        return all_transcripts

    def test_connection(self) -> bool:
        """Test if we can connect to all configured accounts"""
        if not self.services:
            return False

        for label, account_info in self.services.items():
            try:
                service = account_info["service"]
                # Try to list files (minimal query)
                service.files().list(pageSize=1).execute()
            except Exception as e:
                print(f"Connection test failed for {label}: {e}")
                return False

        return True
