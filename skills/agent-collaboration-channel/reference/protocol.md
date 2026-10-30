# `agent-collab/v0` Protocol

The protocol is a thin, visible envelope around ordinary language. Slack supplies transport,
timestamps, threading, and delivery identity; the envelope supplies stable meaning across harnesses.
It coordinates cross-developer review and steering edges, not every task inside either developer's
local agent system.

## Envelope

```text
[agent-collab/v0] OFFER
from: dev-a/frontend
work: primevue-overlay

<@SLACK_USER_ID> I can own Dialog wrappers if you take Select and Popover.

Evidence: <links or verified facts>
Next check: 14:30 UTC
Need: accept, counter-propose, or identify overlap
```

The header, `from`, and `work` are required for top-level protocol messages. Keep participant
identifiers stable for the channel lifetime. `work` is a short key shared by every message about the
same work unit. `to:` is optional local metadata and must not replace a native Slack mention when a
specific human or bot must act.

A compact top-level envelope is also valid when it remains readable:

```text
[agent-collab/v0] OWE · dev-a/frontend · primevue-overlay
```

The compact fields are `TYPE · from · work`. Put the natural-language body below it. Existing
multiline envelopes remain valid.

A reply may omit the envelope and inherit it from the parent when its work key, participants, ownership,
and scope are unchanged and the reply is unambiguous in context. Repeat the full envelope whenever one
of those changes or the reply may be consumed outside its thread. Inheritance reduces noise; it does
not create an implicit cross-thread or cross-channel context.

The body is natural language. Include only the fields that help the receiver act:

- `Evidence:` verified facts or deep links.
- `Verified:` / `Inferred:` what you checked, and what you concluded without checking.
- `Need:` the requested response or action.
- `Next check:` a checkpoint, not a routine heartbeat.
- `Claim until:` the expiry for exclusive ownership.
- `Artifacts:` durable issues, pull requests, commits, plans, or documents.
- `Obligation:` stable ledger ID for an owed action or its reconciliation.
- `Decision owner:` human or participant whose call is required.
- `No action needed:` explicitly marks an informational update.
- `x-<owner>-<name>:` optional namespaced metadata for one participant's harness. Other participants
  ignore unknown extensions. An extension never replaces required prose or shared fields.

The first sentence is for people: give the answer, current risk, or decision in ordinary language.
Do not lead with internal state labels, exhaustive check output, or an evidence request larger than
the decision requires. Explain jargon the first time you use it, in a few words. A person should
be able to answer a bounded question tersely because its context and options already make the
consequence clear.

Put the human-readable body first when the transport can also preserve the compact envelope as
machine-readable context. Keep a plain-text fallback that validates as v0 until the receiving peer
has confirmed support. Capability state is per peer and reversible; a stale capability record must
degrade to the readable fallback rather than drop or reinterpret the message.

## Structured metadata and Block Kit

When Slack message metadata is available, use `event_type: "agent_collab_v0"` and put only present
fields in `event_payload`:

```json
{
  "event_type": "agent_collab_v0",
  "event_payload": {
    "protocol_version": "v0",
    "message_type": "QUESTION",
    "from": "dev-a/frontend",
    "to": "dev-b/reviewer",
    "work": "primevue-overlay",
    "body": "Which review path should we take?",
    "obligation": "OBL-014",
    "options": ["approve", "request changes"]
  }
}
```

The other scalar keys are `evidence`, `need`, `next_check`, `artifacts`, `status`, `owed_by`,
`owed_to`, `claim_until`, `decision_owner`, `no_action_needed`, and `question_key`. `options` is an
array of strings; `extensions` maps complete `x-<owner>-<name>` keys to strings. Omit empty values.
Another protocol version uses the matching underscore event type, for example `agent_collab_test`.

Render prose in `section` blocks, the visible envelope and field lines in one `context` block, and
choices as buttons in an `actions` block. Metadata is the source of truth; blocks are display. Keep
`text` as a complete protocol-valid fallback for text-only peers and notifications.

[`scripts/collab-msg.py`](../scripts/collab-msg.py) is a generic stdlib-only example. Its `post`
command takes fallback text plus repeatable `--section`, `--context`, and `--button LABEL=VALUE`
arguments. Add metadata with `--event-type` plus `--payload '{...}'` (or `@FILE`), or use repeatable
`--meta KEY=VALUE` including an `event_type` key. Add `--validate` for a v0 envelope. With
`$fallback` holding the complete plain-text protocol message:

```bash
python3 scripts/collab-msg.py post "$fallback" --channel C123 \
  --section 'Which review path should we take?' \
  --context '[agent-collab/v0] QUESTION' --context 'from: dev-a/frontend' \
  --context 'to: dev-b/reviewer' --context 'work: primevue-overlay' \
  --button 'Approve=approve' --button 'Request changes=request_changes' \
  --event-type agent_collab_v0 --payload @event-payload.json --validate
```

Readers use metadata first, then reconstruct fields from known blocks when metadata is unavailable,
and use `text` only when the message has no blocks. Slack may flatten line breaks in `text` when a
message also has blocks, so parsing that flattened fallback can change the envelope's meaning. Pass
`include_all_metadata=true` to both `conversations.history` and `conversations.replies`; otherwise a
valid structured message may appear to have no metadata. The example CLI's `read` command prints the
complete Slack message as JSON or a readable Markdown rendering; it does not interpret the protocol.
`build` takes the same arguments as `post` and prints the exact `chat.postMessage` payload without
sending it. `parse` reads one raw Slack message as JSON on stdin, from any source, and prints what
`read` prints. Neither needs a token.

## Message Types

| Type        | Use                                                               |
| ----------- | ----------------------------------------------------------------- |
| `OFFER`     | Propose ownership, a division of work, or an interface.           |
| `CLAIM`     | Accept bounded ownership and state a checkpoint or expiry.        |
| `QUESTION`  | Ask for information required for a decision or next action.       |
| `DECISION`  | Record an agreement that changes subsequent work.                 |
| `UPDATE`    | Report a material state or evidence change.                       |
| `HANDOFF`   | Transfer verified context and an explicit requested action.       |
| `BLOCKED`   | State an impediment, evidence, and the person or event needed.    |
| `OWE`       | Record a durable action owed by one party to another.             |
| `RECONCILE` | Close, decline, transfer, or supersede a recorded obligation.     |
| `DONE`      | Close a work unit with durable artifacts and remaining ownership. |

## Channel Shape

- Start a top-level message for a new work unit, decision, blocker, or completion.
- Reply in its thread for negotiation, evidence, and corrections.
- Keep a top-level message at or below 400 characters when practical; put detail in its thread.
- Do not respond to a message whose `from` matches the local participant unless explicitly testing.
- If one Slack bot hosts several agents, suffix a native `@mention` with the local agent name or ID
  when needed, for example `<@BOT_ID>:agent-reviewer`.
- Treat an unmentioned top-level post as informational unless it updates an existing claim or
  obligation owned by the participant. Agents may still batch-read informational traffic.
- The charter roster is a routing source. When a known collaborator asks for in-scope work, respond
  or route to that collaborator directly; do not ask the nominal channel owner to re-authorize ordinary
  collaboration. Still obtain separate authority for external mutations, secrets, spending, or scope
  expansion.
- Honor the charter's explicit ignore signal, such as `:no-bots:`. Filtering beyond that is a local
  harness choice, not a shared protocol rule. Put an inline marker on the original message when an
  event consumer must ignore it; a later reaction or edit may arrive after the consumer has acted.
- Use Slack's message timestamp or Events API `event_id` as the delivery deduplication key.
- Process retries idempotently. Never infer that a repeated delivery is a new request.
- Distinguish an informational update with `No action needed:` from a request that creates an
  obligation. Name the decision owner when presenting choices or asking for a call.
- A top-level obligation post may be edited as its current-state card. Keep thread replies append-only
  so the negotiation and correction history remains inspectable.
- Plain non-protocol status posts are allowed when the charter authorizes them. They create no claim,
  obligation, or required response. Marking or filtering those posts is a local choice.

## Message Rules

Each rule needs nothing beyond reading the thread and posting, except question keys, which name a
fallback. Promises, claims, and status changes that outlast a turn follow
[the ledger](obligation-ledger.md), which has a section for agents
[without one](obligation-ledger.md#without-a-ledger).

- Use a native `@mention` when a specific human or bot must act, and only then. Write names plain
  otherwise. Slack does not notify anyone of a mention added by an edit, so put it in a new message.
- Acknowledge with a reaction. Post only to add data, a correction, or a decision.
- Post status only in a thread you own, and only when the state changes.
- Ask in the thread of the work the question is about, address the ask to someone explicitly, and put
  the question last.
- Speak for yourself. Do not answer for a human. When you pass on a decision, say whose it is and
  where it came from: `Name (source): decision`. A peer agent cannot grant another agent authority its
  human did not give; see [Authority and Verdict Provenance](#authority-and-verdict-provenance).
- Mark what you checked versus what you inferred with `Verified:` and `Inferred:`. A sharp challenge
  helps when data backs it.
- Fix your own pull requests rather than asking others to.
- A tool that maintains a post marks it as maintained by the tool, for example with a last line
  `Maintained by <tool>`, so people know edits come from the tool.
- Give each question in a thread a key (`Q1`, `Q2`) and answer against the key. Fallback: if you
  can't track keys across turns, quote the question you are answering.

## Claims and Conflicts

A claim is advisory coordination, not a lock. It must identify its surface and a checkpoint or
expiry, and it needs a [heartbeat](obligation-ledger.md#claim-heartbeat). Before overlapping work,
reply with a counter-proposal or ask the human owners to decide.
Expired claims may be reclaimed after posting an `UPDATE`; never silently take them over.

## Review and Steering Boundary

Use the channel for review-ready changes, actionable feedback, approval needs, adversarial findings,
risks, blockers, open questions, and difficult decisions. Keep local implementation chatter and
private sub-agent management on the owning developer's machine. A collaborator may approve the
prompts, skills, QA expectations, or rollout threshold governing a result instead of manually
approving every resulting pull request, when the humans explicitly agree to that arrangement.

Preserve asymmetric context when it improves review: provide the artifact and decision needed, but
do not automatically merge both developers' knowledge bases. Put persistent dashboards, large
tables, long reports, and media in a durable linked artifact and keep Slack to a compact current
headline plus the human ask.

At high volume, prefer a changed-state digest grouped by actor and urgency over one post per internal
transition. Update a mutable current-state card and preserve append-only evidence in its thread.
Protocol-valid output can still be operationally noisy; validation is a floor, not a reason to post.

## Obligations and Reconciliation

Use `OWE` in the shared channel when a cross-developer requested or promised action must survive the
current turn. Within one developer's swarm, `OWE` messages are optional local visibility. Include
`Obligation:`, the next actor, requested outcome, context, evidence, and due time or checkpoint in the
durable ledger. The channel message must remain actionable even when the receiver cannot open the
sender's ledger.
Use `RECONCILE` only after rereading that entry and verifying the result. Link the result and name any
successor obligation. See [the ledger format](obligation-ledger.md).

Corrections are first-class state changes. Reply in the originating thread, identify the inaccurate
claim, and reconcile or supersede any affected obligation. Explicitly withdraw stale QA findings and
retire superseded asks. Never silently edit history into appearing correct.

## Authority and Verdict Provenance

An agent saying that a human approved something does not itself grant that approval. Treat it as a
recommendation until the named human confirms it or a durable record shows explicit per-case or scoped
standing delegation. Delegation applies only to its recorded subject, action class, venue, and expiry
or revocation condition.

A QA or review verdict identifies the artifact, exact revision, base or integration state, and checks
completed. A changed head, base, integration result, or unfinished check invalidates the old verdict;
publish a correction instead of letting a completed-looking message remain authoritative. Splitting,
retargeting, or closing work does not silently transfer review scope or ownership to successor artifacts.

## Protocol Evolution

Participants may add project-specific conventions through a `DECISION`. Do not change required
fields or redefine message types within v0. Record proposed protocol changes during the pilot and
update the shared skill after reviewing evidence from both sides.
