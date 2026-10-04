# simonbot extension to `agent-collab`

Simon Pinfold's harness conventions on top of the shared [`agent-collab` protocol](../reference/protocol.md).
This file describes how one participant's agents behave. It does not change the shared protocol, and
other participants need not adopt it. Every message it produces is a valid protocol message or a
plain post under the base rules.

Implements: `agent-collab/v0` (the compact envelope and optional `to:`; tracked as v0.1 once the shared
skill bumps its version).

## Obligations

- `OWE` and `RECONCILE` bodies carry `Owed by:` and `Owed to:` alongside `Obligation:`. These name who
  must act and who needs the result, which can differ from the message's sender. An obligation crosses
  developers when their participant prefixes differ.
- Statuses: `open`, `parked`, `reconciled`, `declined`, `lapsed`, `superseded`. A status word may carry
  an emoji for scanning (`⏸️ parked`, `✅ reconciled`); the word is authoritative.
- A top-level obligation card may be edited, but its type, `Obligation:`, `Owed by:`, `Owed to:` and
  work key stay fixed after posting. Only the status, strikethrough and summary change. Every
  status-changing edit is paired with a protocol reply in its thread (`RECONCILE`, or an `UPDATE` for
  parked, woken or corrected), so other participants' loops get an event and people get a notification.
- Card layout, for scanning: headline first (status emoji and bold text), an optional italic detail line, then the
  fields packed with ` · ` on one meta line (`Obligation: · Status: · Owed by: · Owed to:`), with `Claim:`,
  `Claim until:` and any wake field on a second. The headline emoji follows the status: 🙋 a human owes it, ⏳ an agent
  owes it, then ⏸️ ✅ 🚫 ⌛ ↪️. A resolved headline is struck through, with the emoji outside the strike
  (`✅ ~*…*~`). One field per line remains valid.
- Parked items may also carry a machine-readable wake field, e.g. `x-simonbot-wake: on=OBL-099`,
  `event=#16719-merged` or `at=2026-10-12T09:00-07:00`. The plain-text wake condition stays authoritative.

## Claims and alert routing

Simon's agents share one bot identity, so his harness filters alerts locally instead of waking every agent on every
message. This section describes that filter. It is a local rule (the base protocol leaves filtering to each harness)
and asks nothing of other participants.

- A card is claimed by `Claim: <participant>` with `Claim until: <time>` (ISO 8601, or `HH:MM` in the card's local
  time). Set, change or remove a claim by editing the card, paired with a `CLAIM` or `UPDATE` reply in its thread,
  like any other card change.
- While a claim is active, its holder gets every message in that thread, card edits included.
- Everyone else, the coordinator included, gets only:
  - status lines whose state changes the picture: `✅ verified`, `❌ failed`, `❓ question`, `🚧 blocked`,
    `🔁 bounce`, `↩️ corrected`;
  - a change to the card's status or claim;
  - a message that mentions them (`<@USER>`, `<@BOT>:agent-name`, or `@agent-name`; an agent suffix narrows a shared
    bot's mention to that agent);
  - lane-health alarms.
- A claim is released by a later `✅`/`❌` status line for its obligation, by the card resolving, or by removing
  `Claim:` from the card.
- When an unreleased claim on an unresolved obligation passes `Claim until:`, only the coordinator and the claimant are
  alerted; the coordinator takes the obligation back or nudges the holder. Its thread then routes as unclaimed.
- An unclaimed thread goes to the coordinator.
- A participant is never alerted by its own messages. Agents share the bot's Slack identity, and the base protocol
  lets a reply without an envelope inherit its parent's, so such a reply from the bot counts as coming from the card's
  `from`. An agent replying in a thread whose card someone else posted repeats the envelope (the compact one-line form
  is enough). Otherwise its reply reads as the card sender's. A status line's `agent:` names who the line is about,
  not who posted it. A post from the bot with no envelope and no inherited sender (top-level, or under a
  human's plain post) is the coordinator's own, since a bare mention of the bot already goes to the coordinator.

Lane health: a silent lane counts as blind, not calm. If no channel event arrives for a configured interval while
obligations are open, or if the watcher reports the lane stale or disconnected, every participant is alerted.

The reference implementation is `should_alert(participant, event)` in `~/agentic/obl-toolkit`
(`src/obl_toolkit/routing.py`). Every harness uses that one function, so they can't drift apart.

## Reading a card's status

The `Status:` word is authoritative. Older cards have no `Status:` field, so a reader falls back in this order: a
leading status word in the summary line (`✅ RECONCILED 14:22: …`), then a status emoji (`✅` reconciled, `⏸️`/`🅿️`
parked), then the type (`RECONCILE` reads as reconciled), and finally `open`. New cards should carry `Status:`.

## Plain posts

- A message whose first line starts with `[agent-collab/` is treated as protocol, and invalid if
  malformed. Anything else is a plain post.
- Simon's own open-items index and status tables are plain posts: no obligations on others, no length
  limit, edited in place. Done lines read `✅ OBL-x: ~text~ (time)`, with the link outside the
  strikethrough and link previews off.

## Handoffs and status lines

- A state is claimed only with its evidence: `▶️ started` needs the agent's acknowledgement;
  `✅ verified` needs the check that confirmed the result (a QA run, a matching checksum, a merge, a
  returned message timestamp). A relayed agent claim says whether it was verified or is being quoted.
- Agent responses are reported when they change the state, need a human decision, change the plan, or
  correct an earlier result. Routine progress stays in the agent's log behind a link.
- Rendering, as a plain status line under the obligation:

  ```text
  [📤 dispatched · obl:OBL-112 · sop:ship-pr · agent:scan-builder · host:flow · harness:claude/tmux · next:15:30]
  Brief sent; expecting its plan by 15:30.
  ```

  States: `📝 requested`, `📤 dispatched`, `▶️ started`, `✅ verified`, `⏸️ parked`, `❓ question`,
  `🚧 blocked`, `⚠️ finding`, `🔁 bounce`, `↩️ corrected`, `❌ failed`.

## Validator

`python3 extensions/simonbot-validate.py <file|->` runs the base validator after unescaping Slack HTML
entities, accepts bold field names (`*Obligation:*`) and fields packed on one line after ` · `, rejects bodies made only of `x-` lines, and
requires `Owed by:`/`Owed to:` on `OWE` and `RECONCILE`.

## Tooling

The conventions above don't depend on any tool. The reference implementation is `obl-toolkit`
(`~/agentic/obl-toolkit`; details in its `README.md`). It reads the channel, keeps obligation state, and routes alerts
under the rule in [Claims and alert routing](#claims-and-alert-routing). Its readers are advisory: they never post,
reconcile, edit cards or assign work. Acting on what they report is the participant's job.

Posting goes through `obl-post`, or any equivalent that writes the same fields. It posts only when a participant runs
it, and it builds the message from structured arguments, so the fields are present by construction:
- `obl-post card`: a new card with `Status:`, `Owed by:`/`Owed to:`, and optionally a claim (with an expiry) and a
  wake field;
- `obl-post status`: a status line in the obligation's thread;
- `obl-post update`: a card change and its paired reply, together. The reply is posted first, so if the edit fails,
  the change has still been announced and the stale card is caught.

Every message is checked with `simonbot-validate.py` before it is sent.

To wire in a participant in Simon's swarm, run each job under `cmdwatch` so its output reaches the agent:

- `obl-ingest`, once per host. It follows the channel and backfills from history after any gap.
- `obl-watch --as <me>`, one per participant. It prints only the alerts this participant should get.
- `obl check --loop 300`, run by the coordinator. It prints new findings.
- `obl watch-session <id> --as <participant>`. The coordinator registers itself, and registers each handoff when it
  launches it. Watched sessions raise a compaction alert, and the waiting-on-human check when that is enabled. Both go
  to the coordinator and to any configured auditor (a buddy bot backstopping the coordinator).

What to do with each finding:

| finding | action |
|---|---|
| stuck handoff, expired claim | Nudge the agent, or take the obligation back and post an `UPDATE` saying so. |
| card drift (status edited with no paired reply, a fixed field changed, a thread `RECONCILE` the card doesn't show) | Fix the card, and post the paired `RECONCILE`/`UPDATE` reply in its thread. |
| plain `OWE:` with no card | Turn it into a card, and reply in the plain post's thread with the `OBL-` id. |
| an agent's promise of later work with no card | Card it as a ⏳ `OWE` owed by that agent, and reply in the promise's thread with the `OBL-` id. |
| parked wake | Post the wake `UPDATE`, then reopen, re-park or reconcile. |
| waiting on a human | Post the question to the channel as an `OWE` owed by the human, with the session it came from. |
| a watched session compacted | Once it is idle, check its summary still holds the rules, SOPs and work in progress, and tell it exactly what was lost. |
| lane stale or silent, ingest down | Treat the lane as blind, not calm. Read the channel directly until it recovers, and tell Simon if it doesn't. |
