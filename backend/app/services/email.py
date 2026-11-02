"""Email sending via Resend.

For the free tier, Resend only delivers to the account owner's email
(onboarding@resend.dev sender). For production, verify a custom domain.
"""
import logging

import resend

from app.core.config import settings

logger = logging.getLogger(__name__)


def send_password_reset_email(to_email: str, reset_link: str) -> None:
    """Send a password reset email via Resend."""
    resend.api_key = settings.resend_api_key

    html = f"""
    <div style="font-family: sans-serif; max-width: 480px; margin: 0 auto; padding: 24px;">
      <h2 style="color: #1e293b;">Reset your password</h2>
      <p style="color: #475569;">
        You requested a password reset for your Document Intelligence account.
        Click the button below to set a new password. This link expires in 15 minutes.
      </p>
      <a href="{reset_link}"
         style="display: inline-block; margin: 16px 0; padding: 12px 24px;
                background: #2563eb; color: #fff; text-decoration: none;
                border-radius: 8px; font-weight: 600;">
        Reset Password
      </a>
      <p style="color: #94a3b8; font-size: 13px;">
        If you didn't request this, you can safely ignore this email.
      </p>
    </div>
    """

    try:
        resend.Emails.send({
            "from": "onboarding@resend.dev",
            "to": to_email,
            "subject": "Reset your password - Document Intelligence",
            "html": html,
        })
        logger.info(f"Password reset email sent to {to_email}")
    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {e}")
        raise
