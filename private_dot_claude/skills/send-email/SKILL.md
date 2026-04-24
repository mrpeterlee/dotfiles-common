---
name: send-email
description: Use when you need to send an email notification, alert, or message to one or more recipients. Triggers on phrases like "send email", "email them", "notify by email", "send a message to".
---

# Send Email

Send emails via SMTP using `hr-bot@tapai.cc` (Aliyun Qiye Mail).

## Usage

Run the included `send_email.py` script via Bash:

```bash
python3 ~/.claude/skills/send-email/send_email.py \
  --to "recipient@example.com" \
  --subject "Subject line" \
  --body "Plain text body"
```

### Options

| Flag | Required | Description |
|------|----------|-------------|
| `--to` | Yes | Recipient(s), comma-separated for multiple |
| `--subject` | Yes | Email subject line |
| `--body` | Yes | Email body (plain text) |
| `--html` | No | HTML body (sends multipart if provided) |
| `--cc` | No | CC recipient(s), comma-separated |

### Examples

```bash
# Simple text email
python3 ~/.claude/skills/send-email/send_email.py \
  --to "user@tapai.cc" \
  --subject "Deployment complete" \
  --body "Infisical has been deployed successfully."

# HTML email to multiple recipients
python3 ~/.claude/skills/send-email/send_email.py \
  --to "user1@tapai.cc,user2@tapai.cc" \
  --cc "admin@tapai.cc" \
  --subject "Weekly Report" \
  --body "See HTML version" \
  --html "<h1>Report</h1><p>All systems operational.</p>"
```

## Configuration

- **SMTP server:** `smtp.qiye.aliyun.com:465` (implicit SSL)
- **From:** `hr-bot@tapai.cc`
- **Credentials:** Fetched at runtime from Aliyun OOS (`prod/infisical/smtp-password`)
- Port 587 (STARTTLS) is blocked from Aliyun cloud hosts; always use 465
