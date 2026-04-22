import random
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from backend.app.config import get_settings

logger = logging.getLogger("securewealth.email")
settings = get_settings()

class EmailService:
    """
    Handles secure communication for 2-Step Verification.
    Can send real emails via SMTP or simulate delivery in development.
    """

    @staticmethod
    def generate_otp() -> str:
        """Generate a random 6-digit numeric OTP."""
        return str(random.randint(100000, 999999))

    async def send_otp_email(self, recipient_email: str, otp_code: str):
        """
        Sends an OTP email from aanikabajaj290@gmail.com using real SMTP if password is provided.
        """
        subject = "Your SecureWealth Verification Code"
        body = f"Hello,\n\nYour verification code is: {otp_code}\n\nThis code will expire in 10 minutes.\n\nSecureWealth Digital Twin Team"

        # ── REAL SMTP DELIVERY ───────────────────────────────────────────────
        if settings.SMTP_PASSWORD:
            try:
                msg = MIMEMultipart()
                msg['From'] = settings.EMAIL_FROM
                msg['To'] = recipient_email
                msg['Subject'] = subject
                msg.attach(MIMEText(body, 'plain'))

                server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT)
                server.starttls() # Secure the connection
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                server.send_message(msg)
                server.quit()
                
                logger.info(f"REAL OTP email sent to {recipient_email} via {settings.SMTP_HOST}")
                return True
            except Exception as e:
                logger.error(f"Failed to send real email: {e}")
                # Fallback to simulation if real sending fails
        
        # ── SIMULATION FALLBACK ──────────────────────────────────────────────
        print("\n" + "="*50)
        print(f"📧 [SIMULATION] EMAIL SENT TO: {recipient_email}")
        print(f"FROM: {settings.EMAIL_FROM}")
        print(f"SUBJECT: {subject}")
        print(f"CODE: {otp_code}")
        print("="*50 + "\n")
        # ──────────────────────────────────────────────────────────────────────

        logger.info(f"Simulated OTP email logged for {recipient_email}")
        return True

email_service = EmailService()
