---
name: send-wecom
description: Use when you need to send a message to the WeCom (WeChat Work) group chat. Triggers on phrases like "send wecom", "notify the group", "post to wecom", "message the team chat", "send to wechat group".
---

# Send WeCom Message

Send messages to the team WeCom group chat via webhook robot.

## Usage

Run the included `send_wecom.py` script via Bash:

```bash
python3 ~/.claude/skills/send-wecom/send_wecom.py \
  --content "Message content here" \
  --type markdown
```

### Options

| Flag | Required | Default | Description |
|------|----------|-------------|-------------|
| `--content` | Yes | — | Message content (plain text or markdown) |
| `--type` | No | `markdown` | Message type: `markdown` or `text` |
| `--mention` | No | — | Comma-separated userids to @mention |
| `--mention-all` | No | false | Mention everyone (@all) |

### Examples

```bash
# Markdown notification with color highlights
python3 ~/.claude/skills/send-wecom/send_wecom.py \
  --content '实时新增用户反馈<font color="warning">132例</font>，请相关同事注意。
> 类型:<font color="comment">用户反馈</font>
> 普通用户反馈:<font color="comment">117例</font>
> VIP用户反馈:<font color="comment">15例</font>'

# Plain text with @mentions
python3 ~/.claude/skills/send-wecom/send_wecom.py \
  --type text \
  --content "Deployment complete for v2.1.0" \
  --mention "peter,alice"

# Mention everyone
python3 ~/.claude/skills/send-wecom/send_wecom.py \
  --content "**紧急通知:** 系统维护将在30分钟后开始" \
  --mention-all
```

## Markdown Formatting

Supported in `--type markdown`:
- **Bold:** `**text**`
- **Links:** `[text](url)`
- **Quotes:** `> quoted text`
- **Font colors:** `<font color="info">green</font>`, `<font color="comment">gray</font>`, `<font color="warning">orange</font>`
- **Mentions:** Handled via `--mention` flag (appends `<@userid>` automatically)
- **Max content:** 4096 bytes (UTF-8)

## Configuration

- **Webhook:** WeCom group robot (`qyapi.weixin.qq.com`)
- **Webhook key:** Hardcoded in script
- **No external dependencies** — Python 3 stdlib only
