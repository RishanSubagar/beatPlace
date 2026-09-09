from __future__ import annotations

import asyncio
import os
import smtplib
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Any


async def send_mail(mail_options: dict[str, Any]) -> dict[str, str]:
    """
    Send an email with optional attachment.
    
    Args:
        mail_options: Dict with keys:
            - to: recipient email
            - subject: email subject
            - text: email body (plain text)
            - from: sender email
            - attachment_path: (optional) path to file to attach
    
    Returns:
        Dict with messageId
    """
    # Get SMTP config from environment
    smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")
    
    to_email = mail_options.get("to")
    subject = mail_options.get("subject", "Beats Submission")
    body = mail_options.get("text", "")
    from_email = mail_options.get("from") or smtp_user
    attachment_path = mail_options.get("attachment_path")
    
    if not to_email or not from_email:
        raise ValueError("to and from email addresses are required")
    
    # If no SMTP credentials, log and return a demo message ID
    if not smtp_user or not smtp_password:
        print(f"[DEMO MODE] Would send email:")
        print(f"  From: {from_email}")
        print(f"  To: {to_email}")
        print(f"  Subject: {subject}")
        if attachment_path:
            print(f"  Attachment: {attachment_path}")
        import time
        return {"messageId": f"demo-{int(time.time() * 1000)}"}
    
    # Run SMTP sending in thread pool to avoid blocking
    def _send_smtp() -> dict[str, str]:
        # Build email message
        msg = MIMEMultipart()
        msg["From"] = from_email
        msg["To"] = to_email
        msg["Subject"] = subject
        
        # Add body
        msg.attach(MIMEText(body, "plain"))
        
        # Add attachment if provided
        if attachment_path:
            attachment_file = Path(attachment_path)
            if attachment_file.exists():
                with open(attachment_file, "rb") as attachment:
                    part = MIMEApplication(attachment.read(), Name=attachment_file.name)
                    part["Content-Disposition"] = f"attachment; filename={attachment_file.name}"
                    msg.attach(part)
        
        # Send via SMTP
        try:
            with smtplib.SMTP(smtp_host, smtp_port, timeout=10) as server:
                server.starttls()
                server.login(smtp_user, smtp_password)
                result = server.sendmail(from_email, to_email, msg.as_string())
                
            message_id = msg.get("Message-ID", f"sent-{int(__import__('time').time() * 1000)}")
            print(f"Email sent to {to_email} with ID: {message_id}")
            return {"messageId": message_id}
        except Exception as e:
            print(f"Failed to send email to {to_email}: {e}")
            raise
    
    # Execute in thread pool
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _send_smtp)
