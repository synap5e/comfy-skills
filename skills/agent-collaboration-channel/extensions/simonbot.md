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
- Parked items may also carry a machine-readable wake field, e.g. `x-simonbot-wake: on=OBL-099`,
  `event=#16719-merged` or `at=2026-10-12T09:00-07:00`. The plain-text wake condition stays authoritative.

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
entities, accepts bold field names (`*Obligation:*`), rejects bodies made only of `x-` lines, and
requires `Owed by:`/`Owed to:` on `OWE` and `RECONCILE`.
