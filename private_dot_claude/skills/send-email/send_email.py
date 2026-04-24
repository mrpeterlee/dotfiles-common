#!/usr/bin/env python3
"""Send email via hr-bot@tapai.cc SMTP (Aliyun Qiye Mail).

SMTP password is fetched from Aliyun OOS at runtime.
"""
import argparse
import json
import smtplib
import subprocess
import sys
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

SMTP_HOST = "smtp.qiye.aliyun.com"
SMTP_PORT = 465
SMTP_USER = "hr-bot@tapai.cc"
FROM_NAME = "Tapai Bot"
OOS_PASSWORD_KEY = "prod/infisical/smtp-password"


def get_smtp_password() -> str:
    """Fetch SMTP password from Aliyun OOS SecretParameter."""
    result = subprocess.run(
        [
            "aliyun", "oos", "GetSecretParameter",
            "--RegionId", "cn-shenzhen",
            "--Name", OOS_PASSWORD_KEY,
            "--WithDecryption", "true",
        ],
        capture_output=True, text=True, check=True,
    )
    data = json.loads(result.stdout)
    return data["Parameter"]["Value"]


def send_email(
    to: list[str],
    subject: str,
    body: str,
    html: str | None = None,
    cc: list[str] | None = None,
) -> None:
    password = get_smtp_password()

    msg = MIMEMultipart("alternative")
    msg["From"] = f"{FROM_NAME} <{SMTP_USER}>"
    msg["To"] = ", ".join(to)
    if cc:
        msg["Cc"] = ", ".join(cc)
    msg["Subject"] = subject

    msg.attach(MIMEText(body, "plain", "utf-8"))
    if html:
        msg.attach(MIMEText(html, "html", "utf-8"))

    all_recipients = to + (cc or [])

    with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT) as server:
        server.login(SMTP_USER, password)
        server.sendmail(SMTP_USER, all_recipients, msg.as_string())

    print(f"Email sent to {', '.join(all_recipients)}")
    print(f"Subject: {subject}")


def main():
    parser = argparse.ArgumentParser(description="Send email via hr-bot@tapai.cc")
    parser.add_argument("--to", required=True, help="Recipient(s), comma-separated")
    parser.add_argument("--subject", required=True, help="Email subject")
    parser.add_argument("--body", required=True, help="Plain text body")
    parser.add_argument("--html", help="HTML body (optional)")
    parser.add_argument("--cc", help="CC recipient(s), comma-separated")
    args = parser.parse_args()

    to = [addr.strip() for addr in args.to.split(",")]
    cc = [addr.strip() for addr in args.cc.split(",")] if args.cc else None

    send_email(to, args.subject, args.body, args.html, cc)


if __name__ == "__main__":
    main()
