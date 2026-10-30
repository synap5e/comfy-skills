#!/usr/bin/env python3
"""Regression tests for trial-derived collaboration guidance."""

from __future__ import annotations

import unittest
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]


class GuidanceTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.skill = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
        cls.protocol = (SKILL_DIR / "reference/protocol.md").read_text(encoding="utf-8")
        cls.charter = (SKILL_DIR / "reference/channel-charter.md").read_text(
            encoding="utf-8"
        )
        cls.ledger = (SKILL_DIR / "reference/obligation-ledger.md").read_text(
            encoding="utf-8"
        )
        cls.harness = (SKILL_DIR / "reference/harness-integration.md").read_text(
            encoding="utf-8"
        )

    def test_v0_compatibility_floor_is_preserved(self) -> None:
        self.assertIn("Follow [`agent-collab/v0`]", self.skill)
        self.assertNotIn("agent-collab/v1", self.skill + self.protocol + self.harness)

    def test_authority_requires_scoped_provenance(self) -> None:
        self.assertIn("scoped standing delegation", self.skill)
        self.assertIn("subject, action class, venue", self.protocol)

    def test_review_verdict_is_revision_specific(self) -> None:
        self.assertIn("exact artifact revision", self.skill)
        self.assertIn("changed head, base, integration result", self.protocol)

    def test_root_and_reply_cursors_are_independent(self) -> None:
        for key in (
            "coordination_roots",
            "coordination_replies",
            "learning_roots",
            "learning_replies",
        ):
            self.assertIn(key, self.harness)

    def test_no_delta_path_is_quiet_but_observable(self) -> None:
        self.assertIn("liveness receipt", self.harness)
        self.assertIn("healthy ticks remain silent", self.harness)

    def test_rostered_collaborators_route_directly(self) -> None:
        self.assertIn("Collaborators:", self.charter)
        self.assertIn("charter roster is a routing source", self.protocol)
        self.assertIn("Do not funnel a known collaborator", self.skill)

    def test_human_answer_precedes_machine_detail(self) -> None:
        self.assertIn("first sentence is for people", self.protocol)
        self.assertIn("plain-language answer", self.skill)

    def test_obligations_are_deduplicated_by_outcome(self) -> None:
        self.assertIn("one independently decidable outcome", self.ledger)
        self.assertIn("Merge duplicates", self.skill)

    def test_protocol_validity_does_not_justify_noise(self) -> None:
        self.assertIn("validation is a floor, not a reason to post", self.protocol)
        self.assertIn("Structured messages do not make a noisy channel", self.skill)

    def test_message_rules_stay_stateless_except_question_keys(self) -> None:
        rules = self.protocol.split("## Message Rules")[1].split("\n## ")[0]
        self.assertIn("Acknowledge with a reaction", rules)
        self.assertIn("`Name (source): decision`", rules)
        fallbacks = [item for item in rules.split("\n- ") if "Fallback:" in item]
        self.assertEqual(len(fallbacks), 1)
        self.assertIn("(`Q1`, `Q2`)", fallbacks[0])

    def test_mentions_ask_for_action_and_edits_do_not_notify(self) -> None:
        self.assertIn("and only then", self.protocol)
        self.assertIn("mention added by an edit", self.protocol)

    def test_follow_through_rules_live_in_the_ledger(self) -> None:
        for phrase in ("checking now", "Claim until:", "follow-up you owe"):
            self.assertIn(phrase, self.ledger)
        self.assertNotIn("follow-up you owe", self.protocol)
        self.assertIn("## Claim Heartbeat", self.ledger)

    def test_agents_without_a_ledger_have_fallbacks(self) -> None:
        section = self.ledger.split("## Without a Ledger")[1].split("\n## ")[0]
        self.assertIn("if you\ncan't act later, don't promise", section)
        self.assertIn("let them lapse", section)
        self.assertIn("#without-a-ledger", self.skill)

    def test_silent_feed_is_a_fault(self) -> None:
        self.assertIn("A silent feed means you are blind", self.harness)
        self.assertNotIn("silent feed", self.protocol)


if __name__ == "__main__":
    unittest.main()
