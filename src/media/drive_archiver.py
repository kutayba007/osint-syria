"""
OSINT Syria - Google Drive Media Archiver
Archives photos and documents from Telegram messages to Google Drive.
Uses Google Drive API v3 with service account or OAuth.
"""

import logging
import io
from datetime import datetime
from typing import Optional

logger = logging.getLogger("osint.media")


class DriveArchiver:
    """
    Archives media files to Google Drive.
    
    Setup:
    1. Go to https://console.cloud.google.com
    2. Create a project → Enable Google Drive API
    3. Create a Service Account → Download JSON key
    4. Share your Drive folder with the service account email
    
    Free tier: 15GB personal / 5TB shared drive
    """

    FOLDER_STRUCTURE = "OSINT_Syria/{year}/{month}/{day}/{channel}"

    def __init__(self):
        self._drive = None
        self._connected = False

    def connect(self, credentials_path: str):
        """
        Connect to Google Drive using service account credentials.
        Install: pip install google-api-python-client google-auth
        """
        try:
            from google.oauth2 import service_account
            from googleapiclient.discovery import build

            SCOPES = ['https://www.googleapis.com/auth/drive.file']
            creds = service_account.Credentials.from_service_account_file(
                credentials_path, scopes=SCOPES
            )
            self._drive = build('drive', 'v3', credentials=creds)
            self._connected = True
            logger.info("✅ Connected to Google Drive")
        except ImportError:
            logger.warning("⚠️ Google API client not installed. Run: pip install google-api-python-client google-auth")
        except Exception as e:
            logger.error(f"❌ Failed to connect to Google Drive: {e}")

    def upload_file(
        self,
        file_data: bytes,
        filename: str,
        channel: str,
        mime_type: str = "application/octet-stream"
    ) -> Optional[str]:
        """
        Upload a file to Google Drive with organized folder structure.
        Returns the file ID on success.
        """
        if not self._connected:
            logger.warning("Google Drive not connected — skipping upload")
            return None

        try:
            now = datetime.utcnow()
            folder_path = self.FOLDER_STRUCTURE.format(
                year=now.year,
                month=f"{now.month:02d}",
                day=f"{now.day:02d}",
                channel=channel
            )

            # Create folder structure if needed
            folder_id = self._ensure_folder_structure(folder_path)

            # Upload file
            file_metadata = {
                'name': filename,
                'parents': [folder_id],
            }

            media = io.BytesIO(file_data)
            from googleapiclient.http import MediaIoBaseUpload
            media_upload = MediaIoBaseUpload(media, mimetype=mime_type, resumable=True)

            file = self._drive.files().create(
                body=file_metadata,
                media_body=media_upload,
                fields='id'
            ).execute()

            file_id = file.get('id')
            logger.info(f"📤 Uploaded to Drive: {filename} → {file_id}")
            return file_id

        except Exception as e:
            logger.error(f"❌ Drive upload failed: {e}")
            return None

    def _ensure_folder_structure(self, path: str) -> str:
        """Create nested folder structure and return the leaf folder ID."""
        parts = path.split("/")
        parent_id = "root"

        for part in parts:
            # Check if folder exists
            query = f"name='{part}' and '{parent_id}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false"
            results = self._drive.files().list(q=query, fields='files(id)').execute()
            files = results.get('files', [])

            if files:
                parent_id = files[0]['id']
            else:
                # Create folder
                file_metadata = {
                    'name': part,
                    'mimeType': 'application/vnd.google-apps.folder',
                    'parents': [parent_id],
                }
                folder = self._drive.files().create(body=file_metadata, fields='id').execute()
                parent_id = folder['id']

        return parent_id
