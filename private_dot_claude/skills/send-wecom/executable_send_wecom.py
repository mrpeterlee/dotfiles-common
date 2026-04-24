#!/usr/bin/env python3
"""Send message to WeCom group chat via webhook.

Supports markdown and text message types.
API docs: https://developer.work.weixin.qq.com/document/path/99110
"""
import argparse
import json
import sys
import urllib.request
import urllib.error

WEBHOOK_URL = (
    "https://qyapi.weixin.qq.com/cgi-bin/webhook/send"
    "?key=38342716-68a7-4454-a28a-69c45133ded5"
)
MAX_CONTENT_BYTES = 4096


def build_markdown_payload(
    content: str,
    mentions: list[str] | None = None,
    mention_all: bool = False,
) -> dict:
    """Build markdown message payload."""
    if mentions or mention_all:
        mention_tags = []
        if mention_all:
            mention_tags.append("<@all>")
        if mentions:
            mention_tags.extend(f"<@{uid}>" for uid in mentions)
        content = content + "\n" + " ".join(mention_tags)
    return {"msgtype": "markdown", "markdown": {"content": content}}


def build_text_payload(
    content: str,
    mentions: list[str] | None = None,
    mention_all: bool = False,
) -> dict:
    """Build text message payload."""
    mentioned_list = list(mentions) if mentions else []
    if mention_all:
        mentioned_list.append("@all")
    payload: dict = {"msgtype": "text", "text": {"content": content}}
    if mentioned_list:
        payload["text"]["mentioned_list"] = mentioned_list
    return payload


def send_message(payload: dict) -> None:
    """POST payload to WeCom webhook."""
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")

    content_bytes = len(
        payload.get("markdown", payload.get("text", {}))
        .get("content", "")
        .encode("utf-8")
    )
    if content_bytes > MAX_CONTENT_BYTES:
        print(
            f"Warning: content is {content_bytes} bytes "
            f"(max {MAX_CONTENT_BYTES})",
            file=sys.stderr,
        )

    req = urllib.request.Request(
        WEBHOOK_URL,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req) as resp:
            result = json.loads(resp.read().decode("utf-8"))
    except urllib.error.URLError as e:
        print(f"Network error: {e}", file=sys.stderr)
        sys.exit(1)
    except (json.JSONDecodeError, ValueError) as e:
        print(f"Unexpected response from WeCom API: {e}", file=sys.stderr)
        sys.exit(1)

    if result.get("errcode") != 0:
        print(
            f"API error: {result.get('errmsg', 'unknown')} "
            f"(errcode={result.get('errcode')})",
            file=sys.stderr,
        )
        sys.exit(1)

    print("Message sent to WeCom group")


def main():
    parser = argparse.ArgumentParser(
        description="Send message to WeCom group chat"
    )
    parser.add_argument("--content", required=True, help="Message content")
    parser.add_argument(
        "--type",
        default="markdown",
        choices=["markdown", "text"],
        help="Message type (default: markdown)",
    )
    parser.add_argument(
        "--mention", help="Comma-separated userids to @mention"
    )
    parser.add_argument(
        "--mention-all",
        action="store_true",
        help="Mention everyone (@all)",
    )
    args = parser.parse_args()

    if not args.content.strip():
        parser.error("--content must not be empty")

    mentions = (
        [uid.strip() for uid in args.mention.split(",") if uid.strip()]
        if args.mention
        else None
    )

    if args.type == "markdown":
        payload = build_markdown_payload(
            args.content, mentions, args.mention_all
        )
    else:
        payload = build_text_payload(args.content, mentions, args.mention_all)

    send_message(payload)


if __name__ == "__main__":
    main()
