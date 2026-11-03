#!/usr/bin/env python3

from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import os
import unittest
from pathlib import Path
from unittest import mock


SCRIPT = Path(__file__).with_name("collab-msg.py")
SPEC = importlib.util.spec_from_file_location("collab_msg", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
FIXTURE = json.loads(
    (Path(__file__).parent / "fixtures/collab-msg.json").read_text(encoding="utf-8")
)


def run_cli(*argv: str, stdin: str = "", token: str = "") -> tuple[int, str]:
    env = {k: v for k, v in os.environ.items() if k != "SLACK_BOT_TOKEN"}
    if token:
        env["SLACK_BOT_TOKEN"] = token
    stdout = io.StringIO()
    with (
        mock.patch.dict(os.environ, env, clear=True),
        mock.patch("sys.stdin", io.StringIO(stdin)),
        contextlib.redirect_stdout(stdout),
        contextlib.redirect_stderr(io.StringIO()),
    ):
        code = MODULE.main(list(argv))
    return code, stdout.getvalue()


MESSAGE_ARGS = (
    "hello",
    "--channel", "C123",
    "--thread", "1770000000.000001",
    "--section", "Choose a path.",
    "--context", "[agent-collab/v0] QUESTION",
    "--button", "Approve=approve",
    "--event-type", "agent_collab_v0",
    "--payload", '{"message_type":"QUESTION"}',
)


class CollabMessageTest(unittest.TestCase):
    def test_build_matches_payload_snapshot(self) -> None:
        expected = FIXTURE["payload"]
        actual = MODULE.build_payload(
            channel="C123",
            text=expected["text"],
            sections=["Choose <https://example.test|the review path> &amp; verify."],
            contexts=[
                "[agent-collab/v0] QUESTION",
                "from: dev-a/frontend",
                "to: dev-b/reviewer",
                "work: primevue-overlay",
                "Obligation: TEST-1",
            ],
            buttons=[("Approve", "approve"), ("Request changes", "request_changes")],
            metadata=expected["metadata"],
            thread="1770000000.000001",
        )
        self.assertEqual(actual, expected)

    def test_default_section_uses_text(self) -> None:
        payload = MODULE.build_payload(
            channel="C123",
            text="hello",
            sections=[],
            contexts=[],
            buttons=[],
            metadata=None,
        )
        self.assertEqual(payload["blocks"], [
            {"type": "section", "text": {"type": "mrkdwn", "text": "hello"}}
        ])
        self.assertNotIn("metadata", payload)

    def test_metadata_pairs_are_typed_and_empty_values_are_removed(self) -> None:
        metadata = MODULE.metadata_from_args(
            None,
            None,
            [
                "event_type=example_event",
                "name=test",
                "count=2",
                "enabled=true",
                "empty=",
                "items=[]",
            ],
        )
        self.assertEqual(metadata, {
            "event_type": "example_event",
            "event_payload": {"name": "test", "count": 2, "enabled": True},
        })

    def test_json_payload_compacts_nested_empty_values(self) -> None:
        metadata = MODULE.metadata_from_args(
            "example_event", '{"keep":"yes","drop":"","nested":{"drop":null}}', []
        )
        self.assertEqual(metadata["event_payload"], {"keep": "yes"})

    def test_payload_and_meta_are_mutually_exclusive(self) -> None:
        with self.assertRaisesRegex(MODULE.MessageError, "either"):
            MODULE.metadata_from_args("example", "{}", ["key=value"])

    def test_button_value_defaults_to_label(self) -> None:
        self.assertEqual(MODULE.button("Approve"), ("Approve", "Approve"))
        self.assertEqual(MODULE.button("Approve=yes"), ("Approve", "yes"))

    def test_validator_is_optional_and_reuses_existing_rules(self) -> None:
        MODULE.validate(FIXTURE["payload"]["text"], threaded=True)
        with self.assertRaisesRegex(MODULE.MessageError, "invalid protocol"):
            MODULE.validate("not a protocol message", threaded=False)

    def test_json_read_contains_only_the_full_public_view(self) -> None:
        self.assertEqual(MODULE.message_json(FIXTURE["slack_message"]), {
            "text": FIXTURE["slack_message"]["text"],
            "blocks": [],
            "metadata": FIXTURE["slack_message"]["metadata"],
            "thread": "1770000000.000001",
            "user": "U123",
            "ts": "1770000000.000002",
        })

    def test_markdown_renders_content_in_order_and_decodes_slack_text(self) -> None:
        message = dict(FIXTURE["slack_message"])
        message["blocks"] = FIXTURE["payload"]["blocks"]
        rendered = MODULE.message_markdown(message)
        headings = ["## Text", "## Sections", "## Context", "## Buttons", "## Metadata"]
        positions = [rendered.index(item) for item in headings]
        self.assertEqual(positions, sorted(positions))
        self.assertIn("Choose the review path & verify.", rendered)
        self.assertIn("- Approve (`approve`)", rendered)
        self.assertIn('```json\n{\n  "event_payload"', rendered)

    def test_permalink_reply_locator(self) -> None:
        locator = (
            "https://example.slack.com/archives/C123/p1770000000000002"
            "?thread_ts=1770000000.000001&cid=C123"
        )
        self.assertEqual(
            MODULE.parse_locator(locator),
            ("C123", "1770000000.000002", "1770000000.000001"),
        )

    def test_channel_timestamp_finds_thread_reply_with_metadata(self) -> None:
        calls = []

        def fake_api(method, token, *, payload=None, query=None):
            calls.append((method, query))
            if method == "conversations.history":
                return {
                    "ok": True,
                    "messages": [{
                        "ts": "1770000000.000001",
                        "reply_count": 1,
                        "latest_reply": "1770000000.000002",
                    }],
                }
            return {
                "ok": True,
                "messages": [{"ts": "1770000000.000002", "metadata": {}}],
            }

        original = MODULE.slack_api
        MODULE.slack_api = fake_api
        try:
            message = MODULE.fetch_message("C123:1770000000.000002", "secret")
        finally:
            MODULE.slack_api = original
        self.assertEqual(message["ts"], "1770000000.000002")
        self.assertEqual(
            [query["include_all_metadata"] for _, query in calls],
            ["true", "true"],
        )

    def test_build_needs_no_token_or_network_and_matches_post(self) -> None:
        with mock.patch.object(
            MODULE.urllib.request, "urlopen", side_effect=AssertionError("network")
        ):
            code, built = run_cli("build", *MESSAGE_ARGS)
        self.assertEqual(code, 0)
        api = mock.Mock(return_value={"channel": "C123", "ts": "1.2"})
        with mock.patch.object(MODULE, "slack_api", api):
            code, posted = run_cli("post", *MESSAGE_ARGS, token="secret")
        self.assertEqual(code, 0)
        self.assertEqual(posted, "C123 1.2\n")
        self.assertEqual(api.call_args.kwargs["payload"], json.loads(built))

    def test_build_rejects_an_invalid_protocol_message(self) -> None:
        code, built = run_cli("build", "not protocol", "--channel", "C1", "--validate")
        self.assertEqual((code, built), (1, ""))

    def test_parse_matches_read_in_both_formats(self) -> None:
        message = dict(FIXTURE["slack_message"], blocks=FIXTURE["payload"]["blocks"])
        api = mock.Mock(return_value={"ok": True, "messages": [message]})
        for output in ("json", "md"):
            with mock.patch.object(MODULE, "slack_api", api):
                _, read = run_cli(
                    "read", f"C123:{message['ts']}", "--format", output, token="secret"
                )
            code, parsed = run_cli(
                "parse", "--format", output, stdin=json.dumps(message)
            )
            self.assertEqual(code, 0)
            self.assertEqual(parsed, read)
            self.assertIn("Choose the review path" if output == "md" else "TEST-1", parsed)

    def test_parse_accepts_a_single_message_history_response(self) -> None:
        message = FIXTURE["slack_message"]
        _, bare = run_cli("parse", stdin=json.dumps(message))
        _, wrapped = run_cli(
            "parse", stdin=json.dumps({"ok": True, "messages": [message]})
        )
        self.assertEqual(wrapped, bare)

    def test_parse_without_metadata(self) -> None:
        message = {"text": "plain", "ts": "1.2", "user": "U1"}
        code, parsed = run_cli("parse", stdin=json.dumps(message))
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(parsed)["metadata"], {})
        self.assertEqual(json.loads(parsed)["text"], "plain")
        code, rendered = run_cli("parse", "--format", "md", stdin=json.dumps(message))
        self.assertEqual(code, 0)
        self.assertIn("## Metadata\n\n```json\n{}\n```", rendered)

    def test_parse_tolerates_null_blocks_and_metadata(self) -> None:
        message = {"text": "plain", "ts": "1.2", "blocks": None, "metadata": None}
        code, rendered = run_cli("parse", "--format", "md", stdin=json.dumps(message))
        self.assertEqual(code, 0)
        self.assertIn("plain", rendered)

    def test_parse_rejects_anything_but_one_message(self) -> None:
        one = {"text": "a", "ts": "1.1"}
        for stdin in (
            "not json",
            "[]",
            '{"unrelated": true}',
            json.dumps({"messages": []}),
            json.dumps({"messages": [one, one]}),
        ):
            with self.subTest(stdin=stdin):
                self.assertEqual(run_cli("parse", stdin=stdin), (1, ""))


if __name__ == "__main__":
    unittest.main()
