"""
Email notification utility.

Sends email notifications when tasks are created.
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict, Any


def send_notification(
    tasks_created: List[Dict[str, Any]],
    transcript_name: str,
    config: Dict[str, Any]
) -> bool:
    """
    Send email notification about created tasks.

    Args:
        tasks_created: List of task dictionaries that were created
        transcript_name: Name of the transcript
        config: Notification configuration from config.yml

    Returns:
        True if email sent successfully, False otherwise
    """

    if not config.get("enabled", False):
        return False

    from_email = config.get("email_from")
    to_email = config.get("email_to")
    smtp_config = config.get("smtp", {})

    if not all([from_email, to_email, smtp_config]):
        print("Email notification skipped: incomplete configuration")
        return False

    # Get password from environment variable
    import os
    password_env = smtp_config.get("password_env", "GMAIL_APP_PASSWORD")
    password = os.getenv(password_env)

    if not password:
        print(f"Email notification skipped: {password_env} not set")
        return False

    # Build email
    msg = MIMEMultipart('alternative')
    msg['Subject'] = f"✅ {len(tasks_created)} tasks created from: {transcript_name}"
    msg['From'] = from_email
    msg['To'] = to_email

    text_body = f"""
Tasks Created from Transcript: {transcript_name}

{len(tasks_created)} tasks have been automatically created:

"""

    for i, task in enumerate(tasks_created, 1):
        text_body += f"{i}. {task.get('name', 'Untitled')}"
        if task.get('url'):
            text_body += f"\n   {task['url']}"
        text_body += "\n"

    text_body += "\n---\nAutomated by ai-task-automation\n"

    part = MIMEText(text_body, 'plain')
    msg.attach(part)

    # Send email
    try:
        server = smtplib.SMTP(
            smtp_config.get('server', 'smtp.gmail.com'),
            smtp_config.get('port', 587)
        )
        server.starttls()
        server.login(from_email, password)
        server.send_message(msg)
        server.quit()
        return True

    except Exception as e:
        print(f"Failed to send email notification: {e}")
        return False
