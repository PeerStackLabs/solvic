#!/usr/bin/env python3
"""
Transcript to Task Automation - Main Orchestrator

Watches for new meeting transcripts, extracts tasks using AI,
and creates them in your task manager automatically.
"""

import os
import sys
import json
import yaml
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List
from difflib import SequenceMatcher

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Import plugins
from transcript_sources.google_drive import GoogleDriveSource
from transcript_sources.plain_text import PlainTextSource
from transcript_sources.email import EmailSource
from transcript_sources.slack import SlackSource
from llm_providers.gemini import GeminiProvider
from task_managers.asana import AsanaTaskManager
from task_managers.notion import NotionTaskManager
from task_managers.linear import LinearTaskManager
from task_managers.base import Task
from utils.email_notifier import send_notification


class TranscriptAutomation:
    """Main automation orchestrator"""

    def __init__(self, config_path: str = "config.yml"):
        """Initialize with configuration file"""

        # Load config
        config_file = Path(config_path)
        if not config_file.exists():
            raise FileNotFoundError(
                f"Config file not found: {config_path}\n"
                f"Copy config.example.yml to config.yml and fill in your details."
            )

        with open(config_file, 'r') as f:
            self.config = yaml.safe_load(f)

        # Initialize components based on config
        self.transcript_source = self._init_transcript_source()
        self.llm_provider = self._init_llm_provider()
        self.task_manager = self._init_task_manager()

        # Processed transcripts log
        advanced_config = self.config.get('advanced', {})
        self.processed_log_path = Path(
            advanced_config.get('processed_log', 'processed_transcripts.json')
        )
        self.processed_transcripts = self._load_processed_log()

        # Automation settings
        automation_config = self.config.get('automation', {})
        self.check_interval = automation_config.get('check_interval', 3600)
        self.initial_lookback = automation_config.get('initial_lookback', 24)

    def _init_transcript_source(self):
        """Initialize transcript source based on config"""
        source_config = self.config.get('transcript_source', {})
        source_type = source_config.get('type')

        if source_type == 'google_drive':
            return GoogleDriveSource(source_config)
        elif source_type == 'plain_text':
            return PlainTextSource(source_config)
        elif source_type == 'email':
            return EmailSource(source_config)
        elif source_type == 'slack':
            return SlackSource(source_config)
        else:
            raise ValueError(f"Unsupported transcript source: {source_type}")

    def _init_llm_provider(self):
        """Initialize LLM provider based on config"""
        llm_config = self.config.get('llm_provider', {})
        llm_type = llm_config.get('type')

        if llm_type == 'gemini':
            return GeminiProvider(llm_config)
        # elif llm_type == 'openai':
        #     return OpenAIProvider(llm_config)
        else:
            raise ValueError(f"Unsupported LLM provider: {llm_type}")

    def _init_task_manager(self):
        """Initialize task manager based on config"""
        tm_config = self.config.get('task_manager', {})
        tm_type = tm_config.get('type')

        if tm_type == 'asana':
            return AsanaTaskManager(tm_config)
        elif tm_type == 'notion':
            return NotionTaskManager(tm_config)
        elif tm_type == 'linear':
            return LinearTaskManager(tm_config)
        # elif tm_type == 'todoist':
        #     return TodoistTaskManager(tm_config)
        else:
            raise ValueError(f"Unsupported task manager: {tm_type}")

    def _load_processed_log(self) -> Dict[str, Any]:
        """Load log of processed transcripts"""
        if self.processed_log_path.exists():
            with open(self.processed_log_path, 'r') as f:
                return json.load(f)
        return {}

    def _save_processed_log(self):
        """Save processed transcripts log"""
        with open(self.processed_log_path, 'w') as f:
            json.dump(self.processed_transcripts, f, indent=2)

    def _mark_processed(self, transcript_id: str, transcript_name: str, source: str):
        """Mark a transcript as processed"""
        self.processed_transcripts[transcript_id] = {
            'name': transcript_name,
            'source': source,
            'processed_at': datetime.now().isoformat()
        }
        self._save_processed_log()

    def _is_duplicate_task(self, task_name: str, threshold: float = 0.85) -> bool:
        """
        Check if a task is a duplicate of recently created tasks.

        Args:
            task_name: Name of the task to check
            threshold: Similarity threshold (0-1). Default 0.85 = 85% similar

        Returns:
            True if duplicate found, False otherwise
        """
        # Get tasks created in last 24 hours
        cutoff_time = datetime.now() - timedelta(hours=24)

        for transcript_id, info in self.processed_transcripts.items():
            # Check if this transcript was processed recently
            try:
                processed_time = datetime.fromisoformat(info.get('processed_at', ''))
                if processed_time < cutoff_time:
                    continue
            except:
                continue

            # Check tasks from this transcript
            for created_task in info.get('tasks_created', []):
                existing_name = created_task.get('name', '')

                # Calculate similarity
                similarity = SequenceMatcher(
                    None,
                    task_name.lower().strip(),
                    existing_name.lower().strip()
                ).ratio()

                if similarity >= threshold:
                    print(f"         ⏭️  Skipping duplicate (similar to: '{existing_name}')")
                    return True

        return False

    def _record_created_task(self, transcript_id: str, task_name: str):
        """Record a task that was successfully created"""
        if transcript_id in self.processed_transcripts:
            if 'tasks_created' not in self.processed_transcripts[transcript_id]:
                self.processed_transcripts[transcript_id]['tasks_created'] = []

            self.processed_transcripts[transcript_id]['tasks_created'].append({
                'name': task_name,
                'created_at': datetime.now().isoformat()
            })
            self._save_processed_log()

    def process_transcripts(self, lookback_hours: int = None):
        """
        Main processing loop.

        Args:
            lookback_hours: How many hours back to look for transcripts.
                           Uses initial_lookback from config if not specified.
        """

        if lookback_hours is None:
            lookback_hours = self.initial_lookback

        print("=" * 70)
        print("Transcript to Task Automation")
        print(f"Running at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 70)

        # Get recent transcripts
        print(f"\n📁 Checking for transcripts (last {lookback_hours} hours)...")
        transcripts = self.transcript_source.get_recent_transcripts(hours=lookback_hours)

        if not transcripts:
            print("   ℹ️  No new transcripts found")
            print("\n" + "=" * 70)
            print("✅ Done - No transcripts to process")
            print("=" * 70)
            return

        print(f"   📄 Found {len(transcripts)} transcript(s)")

        # Process each transcript
        total_tasks_created = 0

        for transcript in transcripts:
            # Skip if already processed
            if transcript.id in self.processed_transcripts:
                print(f"\n   ⏭️  Skipping (already processed): {transcript.name}")
                continue

            print(f"\n   🔄 Processing: {transcript.name}")
            print(f"      Source: {transcript.source}")

            try:
                # Extract tasks using LLM
                print(f"      Extracting tasks...")
                task_dicts = self.llm_provider.extract_tasks(transcript.text)

                if not task_dicts:
                    print(f"      ⚠️  No tasks found")
                    self._mark_processed(transcript.id, transcript.name, transcript.source)
                    continue

                print(f"      ✓ Found {len(task_dicts)} task(s)")

                # Convert to Task objects
                tasks = [
                    Task(
                        name=td.get('name', 'Untitled'),
                        due_date=td.get('due_date'),
                        notes=td.get('notes'),
                        priority=td.get('priority')
                    )
                    for td in task_dicts
                ]

                # Create tasks in task manager
                print(f"      Creating tasks...")
                created_tasks = []

                for task in tasks:
                    # Check for duplicates (skip if similar task created in last 24h)
                    if self._is_duplicate_task(task.name):
                        continue

                    # Create task
                    result = self.task_manager.create_task(task)
                    if result:
                        created_tasks.append(result)
                        # Record that we created this task
                        self._record_created_task(transcript.id, task.name)
                        print(f"         ✓ {task.name}")
                    else:
                        print(f"         ✗ Failed: {task.name}")

                # Send notification
                if created_tasks:
                    notification_config = self.config.get('notifications', {})
                    if send_notification(created_tasks, transcript.name, notification_config):
                        print(f"      📧 Email notification sent")

                # Mark as processed
                self._mark_processed(transcript.id, transcript.name, transcript.source)
                total_tasks_created += len(created_tasks)

                print(f"      ✅ Completed: {len(created_tasks)}/{len(tasks)} tasks created")

            except Exception as e:
                print(f"      ❌ Error processing transcript: {e}")
                import traceback
                traceback.print_exc()

        # Summary
        print("\n" + "=" * 70)
        print(f"✅ Automation complete: {total_tasks_created} total tasks created")
        print("=" * 70)

    def test_setup(self):
        """Test that all components are configured correctly"""
        print("🔧 Testing Setup...\n")

        # Test transcript source
        print("1. Testing transcript source connection...")
        if self.transcript_source.test_connection():
            print("   ✅ Transcript source connected")
        else:
            print("   ❌ Transcript source connection failed")
            return False

        # Test LLM provider
        print("\n2. Testing LLM provider connection...")
        if self.llm_provider.test_connection():
            print("   ✅ LLM provider connected")
        else:
            print("   ❌ LLM provider connection failed")
            return False

        # Test task manager
        print("\n3. Testing task manager connection...")
        if self.task_manager.test_connection():
            print("   ✅ Task manager connected")

            # Get project info
            project_info = self.task_manager.get_project_info()
            if project_info:
                print(f"   ✓ Project: {project_info.get('name')}")
                print(f"   ✓ Workspace: {project_info.get('workspace')}")
        else:
            print("   ❌ Task manager connection failed")
            return False

        print("\n✅ All tests passed! Ready to process transcripts.")
        return True


def main():
    """Main entry point"""

    # Check for config file
    if not Path("config.yml").exists():
        print("❌ Error: config.yml not found")
        print("\nTo get started:")
        print("1. Copy config.example.yml to config.yml")
        print("2. Fill in your API keys and settings")
        print("3. Run: python src/main.py --test")
        sys.exit(1)

    # Parse command line args
    import argparse
    parser = argparse.ArgumentParser(description="Transcript to Task Automation")
    parser.add_argument(
        '--test',
        action='store_true',
        help='Test configuration and connections'
    )
    parser.add_argument(
        '--hours',
        type=int,
        help='How many hours back to look for transcripts (default: from config)'
    )

    args = parser.parse_args()

    try:
        # Initialize automation
        automation = TranscriptAutomation()

        if args.test:
            # Test mode
            automation.test_setup()
        else:
            # Process transcripts
            automation.process_transcripts(lookback_hours=args.hours)

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
