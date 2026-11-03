#!/usr/bin/env python3

from __future__ import annotations

import argparse
import html
import importlib.util
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any


VALIDATOR = Path(__file__).with_name("validate-message.py")


class MessageError(ValueError):
    pass


def compact(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: compact(item)
            for key, item in value.items()
            if compact(item) not in (None, "", [], {})
        }
    if isinstance(value, list):
        return [
            cleaned
            for item in value
            if (cleaned := compact(item)) not in (None, "", [], {})
        ]
    return value


def json_object(value: str) -> dict[str, Any]:
    if value.startswith("@"):
        parsed = json.loads(Path(value[1:]).read_text(encoding="utf-8"))
    else:
        parsed = json.loads(value)
    if not isinstance(parsed, dict):
        raise MessageError("metadata payload must be a JSON object")
    return parsed


def metadata_from_args(
    event_type: str | None, payload: str | None, pairs: list[str]
) -> dict[str, Any] | None:
    if payload and pairs:
        raise MessageError("use either --payload or --meta, not both")
    event_payload: dict[str, Any] = json_object(payload) if payload else {}
    for pair in pairs:
        if "=" not in pair:
            raise MessageError(f"metadata must be KEY=VALUE: {pair}")
        key, value = pair.split("=", 1)
        if not key.strip():
            raise MessageError("metadata key must not be empty")
        try:
            parsed_value = json.loads(value)
        except json.JSONDecodeError:
            parsed_value = value
        event_payload[key.strip()] = parsed_value
    pair_event_type = event_payload.pop("event_type", None) if pairs else None
    if event_type and pair_event_type and event_type != pair_event_type:
        raise MessageError("conflicting event types")
    event_type = event_type or pair_event_type
    if not event_type and (payload or pairs):
        raise MessageError("metadata requires an event type")
    if event_type and not (payload or pairs):
        raise MessageError("--event-type requires --payload or --meta")
    if not event_type:
        return None
    if not isinstance(event_type, str):
        raise MessageError("event type must be a string")
    event_type = event_type.strip()
    if not event_type:
        raise MessageError("event type must not be empty")
    return {"event_type": event_type, "event_payload": compact(event_payload)}


def button(value: str) -> tuple[str, str]:
    label, separator, action_value = value.partition("=")
    label = label.strip()
    if not label:
        raise MessageError("button label must not be empty")
    return label, action_value if separator else label


def build_payload(
    *,
    channel: str,
    text: str,
    sections: list[str],
    contexts: list[str],
    buttons: list[tuple[str, str]],
    metadata: dict[str, Any] | None,
    thread: str = "",
) -> dict[str, Any]:
    if not text.strip():
        raise MessageError("text must not be empty")
    blocks: list[dict[str, Any]] = [
        {"type": "section", "text": {"type": "mrkdwn", "text": section}}
        for section in (sections or [text])
    ]
    if contexts:
        blocks.append(
            {
                "type": "context",
                "elements": [{"type": "mrkdwn", "text": "\n".join(contexts)}],
            }
        )
    if buttons:
        blocks.append(
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "action_id": f"collab_msg_{index}",
                        "text": {"type": "plain_text", "text": label},
                        "value": action_value,
                    }
                    for index, (label, action_value) in enumerate(buttons)
                ],
            }
        )
    payload: dict[str, Any] = {"channel": channel, "text": text, "blocks": blocks}
    if metadata:
        payload["metadata"] = metadata
    if thread:
        payload["thread_ts"] = thread
    return payload


def validate(text: str, threaded: bool) -> None:
    spec = importlib.util.spec_from_file_location("collab_validator", VALIDATOR)
    if not spec or not spec.loader:
        raise RuntimeError(f"cannot import {VALIDATOR}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    errors = module.validate(text, threaded=threaded)
    if errors:
        raise MessageError("invalid protocol message: " + "; ".join(errors))


def slack_api(
    method: str,
    token: str,
    *,
    payload: dict[str, Any] | None = None,
    query: dict[str, Any] | None = None,
) -> dict[str, Any]:
    url = "https://slack.com/api/" + method
    data = None
    headers = {"Authorization": f"Bearer {token}"}
    if query:
        url += "?" + urllib.parse.urlencode(query)
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json; charset=utf-8"
    request = urllib.request.Request(
        url, data=data, headers=headers, method="POST" if data else "GET"
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            result = json.load(response)
    except (urllib.error.URLError, json.JSONDecodeError) as exc:
        raise MessageError(f"Slack request failed: {exc}") from exc
    if not result.get("ok"):
        raise MessageError(
            f"Slack {method} failed: {result.get('error', 'unknown error')}"
        )
    return result


def parse_locator(locator: str) -> tuple[str, str, str]:
    direct = re.fullmatch(r"([^:]+):(\d+\.\d+)", locator)
    if direct:
        return direct.group(1), direct.group(2), ""
    parsed = urllib.parse.urlparse(locator)
    permalink = re.search(r"/archives/([^/]+)/p(\d+)", parsed.path)
    if not permalink or len(permalink.group(2)) <= 6:
        raise MessageError("locator must be CHANNEL:TS or a Slack permalink")
    digits = permalink.group(2)
    query = urllib.parse.parse_qs(parsed.query)
    return (
        permalink.group(1),
        digits[:-6] + "." + digits[-6:],
        query.get("thread_ts", [""])[0],
    )


def thread_message(
    channel: str, root: str, target: str, token: str
) -> dict[str, Any] | None:
    cursor = ""
    while True:
        query = {
            "channel": channel,
            "ts": root,
            "limit": 200,
            "include_all_metadata": "true",
        }
        if cursor:
            query["cursor"] = cursor
        result = slack_api("conversations.replies", token, query=query)
        for message in result.get("messages", []):
            if message.get("ts") == target:
                return message
        cursor = result.get("response_metadata", {}).get("next_cursor", "")
        if not cursor:
            return None


def fetch_message(locator: str, token: str) -> dict[str, Any]:
    channel, target, root = parse_locator(locator)
    if root:
        message = thread_message(channel, root, target, token)
        if message:
            return message
        raise MessageError(f"message {channel}:{target} was not returned by Slack")
    cursor = ""
    while True:
        query = {
            "channel": channel,
            "latest": target,
            "inclusive": "true",
            "limit": 100,
            "include_all_metadata": "true",
        }
        if cursor:
            query["cursor"] = cursor
        result = slack_api("conversations.history", token, query=query)
        for candidate in result.get("messages", []):
            if candidate.get("ts") == target:
                return candidate
            latest = candidate.get("latest_reply", "")
            if candidate.get("reply_count") and (not latest or latest >= target):
                message = thread_message(channel, candidate["ts"], target, token)
                if message:
                    return message
        cursor = result.get("response_metadata", {}).get("next_cursor", "")
        if not cursor:
            raise MessageError(f"message {channel}:{target} was not returned by Slack")


def message_json(message: dict[str, Any]) -> dict[str, Any]:
    return {
        "text": message.get("text", ""),
        "blocks": message.get("blocks") or [],
        "metadata": message.get("metadata") or {},
        "thread": message.get("thread_ts", ""),
        "user": message.get("user", message.get("bot_id", "")),
        "ts": message.get("ts", ""),
    }


def readable(value: Any) -> str:
    text = html.unescape(str(value))
    return re.sub(r"<[^>|]+\|([^>]+)>", r"\1", text)


def message_markdown(message: dict[str, Any]) -> str:
    view = message_json(message)
    sections: list[str] = []
    contexts: list[list[str]] = []
    buttons: list[str] = []
    for block in view["blocks"]:
        if block.get("type") == "section":
            sections.append(readable(block.get("text", {}).get("text", "")))
        elif block.get("type") == "context":
            contexts.extend(
                readable(element.get("text", "")).splitlines()
                for element in block.get("elements", [])
            )
        elif block.get("type") == "actions":
            for element in block.get("elements", []):
                label = readable(element.get("text", {}).get("text", ""))
                value = readable(element.get("value", ""))
                buttons.append(label if label == value else f"{label} (`{value}`)")
    context_lines = [line for group in contexts for line in group]
    parts = [
        f"Slack message `{view['ts']}` by `{view['user']}` in thread `{view['thread'] or '—'}`",
        "## Text",
        readable(view["text"]),
        "## Sections",
        "\n\n".join(sections) or "—",
        "## Context",
        "\n".join(f"- {line}" for line in context_lines) or "—",
        "## Buttons",
        "\n".join(f"- {item}" for item in buttons) or "—",
        "## Metadata",
        "```json\n"
        + json.dumps(view["metadata"], indent=2, ensure_ascii=False, sort_keys=True)
        + "\n```",
    ]
    return "\n\n".join(parts)


def parse_message(raw: str) -> dict[str, Any]:
    parsed = json.loads(raw)
    if isinstance(parsed, dict) and "messages" in parsed:
        messages = parsed["messages"]
        if not isinstance(messages, list) or len(messages) != 1:
            raise MessageError("expected exactly one message")
        parsed = messages[0]
    if not isinstance(parsed, dict) or not {"text", "blocks", "ts"} & parsed.keys():
        raise MessageError("input must be one Slack message as JSON")
    return parsed


def to_json(value: dict[str, Any]) -> str:
    return json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True)


def render(message: dict[str, Any], output: str) -> str:
    return message_markdown(message) if output == "md" else to_json(message_json(message))


def payload_from_args(args: argparse.Namespace) -> dict[str, Any]:
    metadata = metadata_from_args(args.event_type, args.payload, args.meta)
    if args.validate:
        validate(args.text, bool(args.thread))
    return build_payload(
        channel=args.channel,
        text=args.text,
        sections=args.section,
        contexts=args.context,
        buttons=[button(item) for item in args.button],
        metadata=metadata,
        thread=args.thread,
    )


def slack_token() -> str:
    token = os.environ.get("SLACK_BOT_TOKEN", "")
    if not token:
        raise MessageError("SLACK_BOT_TOKEN is not set")
    return token


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(
        description="Post and read generic structured Slack messages."
    )
    message = argparse.ArgumentParser(add_help=False)
    message.add_argument("text")
    message.add_argument("--channel", required=True)
    message.add_argument("--thread", default="")
    message.add_argument("--section", action="append", default=[])
    message.add_argument("--context", action="append", default=[])
    message.add_argument("--button", action="append", default=[])
    message.add_argument("--event-type")
    message.add_argument("--payload", help="JSON object, or @FILE")
    message.add_argument("--meta", action="append", default=[], metavar="KEY=VALUE")
    message.add_argument("--validate", action="store_true")
    output = argparse.ArgumentParser(add_help=False)
    output.add_argument("--format", choices=("json", "md"), default="json")
    commands = root.add_subparsers(dest="command", required=True)
    commands.add_parser("post", parents=[message])
    commands.add_parser(
        "build", parents=[message], help="print the chat.postMessage JSON; no token"
    )
    read = commands.add_parser("read", parents=[output])
    read.add_argument("locator")
    commands.add_parser(
        "parse", parents=[output], help="render one Slack message from stdin; no token"
    )
    return root


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        if args.command == "build":
            print(to_json(payload_from_args(args)))
        elif args.command == "post":
            payload = payload_from_args(args)
            result = slack_api("chat.postMessage", slack_token(), payload=payload)
            print(f"{result['channel']} {result['ts']}")
        elif args.command == "parse":
            print(render(parse_message(sys.stdin.read()), args.format))
        else:
            print(render(fetch_message(args.locator, slack_token()), args.format))
        return 0
    except (MessageError, OSError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
