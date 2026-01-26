"""
Django management command to send a test email using AWS Federation.

This command sends a simple test email to verify the email system is working.
"""

import logging

from django.conf import settings
from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Send a test email to verify AWS SES Federation is working"

    def add_arguments(self, parser):
        parser.add_argument(
            "--to",
            type=str,
            required=True,
            help="Recipient email address",
        )
        parser.add_argument(
            "--subject",
            type=str,
            default="[ComicChase] 測試郵件 - Test Email",
            help="Email subject",
        )

    def handle(self, *args, **options):
        to_email = options["to"]
        subject = options["subject"]

        from_email = settings.DEFAULT_FROM_EMAIL
        use_federation = getattr(settings, "AWS_USE_FEDERATION", False)

        self.stdout.write("=" * 60)
        self.stdout.write("ComicChase Test Email")
        self.stdout.write("=" * 60)
        self.stdout.write(f"From: {from_email}")
        self.stdout.write(f"To: {to_email}")
        self.stdout.write(f"Subject: {subject}")
        self.stdout.write(f"Federation: {use_federation}")
        self.stdout.write("=" * 60)

        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; padding: 20px;">
            <h1 style="color: #4a90d9;">🎉 ComicChase 測試郵件</h1>
            <p>這是一封測試郵件，用於驗證 Google-to-AWS Federation 郵件系統。</p>
            <hr>
            <h2>系統資訊</h2>
            <ul>
                <li><strong>發件人:</strong> {from_email}</li>
                <li><strong>收件人:</strong> {to_email}</li>
                <li><strong>使用 Federation:</strong> {use_federation}</li>
            </ul>
            <hr>
            <p style="color: #666;">如果您收到這封郵件，表示郵件系統運作正常！</p>
            <p style="color: #4a90d9;"><strong>ComicChase Team</strong></p>
        </body>
        </html>
        """

        try:
            if use_federation:
                self.stdout.write("📧 Sending via Federation...")
                from config.aws_federation import send_email_with_federation

                result = send_email_with_federation(
                    source=from_email,
                    to_addresses=[to_email],
                    subject=subject,
                    body_text=(
                        "This is a test email to verify the "
                        "Google-to-AWS Federation email system."
                    ),
                    body_html=html_content,
                )
                self.stdout.write(
                    self.style.SUCCESS(
                        f"✅ Email sent! MessageId: {result['MessageId']}"
                    )
                )
            else:
                self.stdout.write("📧 Sending via django-ses...")
                from django.core.mail import EmailMultiAlternatives

                msg = EmailMultiAlternatives(
                    subject=subject,
                    body="這是一封測試郵件，用於驗證郵件系統。",
                    from_email=from_email,
                    to=[to_email],
                )
                msg.attach_alternative(html_content, "text/html")
                msg.send(fail_silently=False)
                self.stdout.write(self.style.SUCCESS("✅ Email sent successfully!"))

        except Exception as e:
            self.stderr.write(self.style.ERROR(f"❌ Failed to send email: {e}"))
            logger.exception("Test email failed")
            raise
