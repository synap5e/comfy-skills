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
- One owner per card: `Owed by:` names the next actor. If two people must each act, post two cards. For a joint
  decision, name the person who decides and @-mention the other in the headline. Tools read a comma-separated list
  as several owners, but who acts first is then ambiguous.
- Statuses: `open`, `parked`, `reconciled`, `declined`, `lapsed`, `superseded`. A status word may carry
  an emoji for scanning (`⏸️ parked`, `✅ reconciled`); the word is authoritative.
- A top-level obligation card may be edited, but its type, `Obligation:`, `Owed by:`, `Owed to:` and
  work key stay fixed after posting. Only the status, strikethrough and summary change. Every
  status-changing edit is paired with a protocol reply in its thread (`RECONCILE`, or an `UPDATE` for
  parked, woken or corrected), so other participants' loops get an event and people get a notification.
- OWE and RECONCILE envelopes omit the `→ to` (compact) or `to:` (multi-line). `Owed by:`/`Owed to:` say who owes
  whom, and readers took the arrow as the direction of the debt.
- Card layout, for scanning: headline first (status emoji and bold text), an optional italic detail line, then the
  fields packed with ` · ` on one meta line (`Obligation: · Status: · Owed by: · Owed to:`), with `Claim:`,
  `Claim until:` and any wake field on a second. A resolved headline is struck through, with the emoji outside the
  strike (`✅ ~*…*~`). One field per line remains valid.
- **A feature is one agent-owned card** (`Owed by:` the agent, `Owed to:` the person who wants it) for its whole life;
  "start" is a state change, never an owner flip. It carries `State:`, what is happening on it: `proposed` 📥 (a
  non-coordinator's work card, waiting for the coordinator's `obl-post triage`), `queued` 📥, `working` 🛠️, `blocked`
  🚧, `rehome` 📦 (we want to disown it: find it another home), `untracked` 🗃️ (kept for the record, no longer
  tracked), `done` ☑️ (finished but still open). A card with `Review:` shows 👀. `Status:` keeps the lifecycle
  (⏸️ parked, ✅ reconciled, 🚫 declined, ⌛ lapsed, ↪️ superseded). With no `State:`, an agent's card reads as working
  (🛠️), one that waits as blocked (🚧). **One emoji, one meaning** (obl decision 0040).
  **Whose turn:** 🙋🏼 means the Operator's turn and 👤 another person's, on the headline and the board alike.
  **A card a person owes is itself a question to them (🙋🏼 or 👤)** and carries no `State:` (State is an agent's card's);
  a `Blocked:` naming only that person adds nothing, and it shows 🚧 only when it waits on someone or something
  else. A question asked in a thread (QUESTION `→ <to>`) is addressed to the person who answers it, never to an
  agent. The agent sets State; tools remind it when the State looks wrong, they don't flip it.
- **A blocked card is left alone.** "Still blocked" isn't worth waking an agent for, so a `blocked` card, or one
  under review, gets no reminders for being quiet. Its reminders are its own wake (an agent may set a wake field on its own
  blocked card) and its dependents: when another card becomes blocked on it (`Blocked: OBL-N …`), the card waited on
  hears about it, with the chain up to the card at its end and every card now hanging there.
- **Holds:** the questions a card needs answered are listed on it, `Holds: <link|Q1: keep the cap?>; <…> (blocking)`,
  each a link to the question asked in the card's thread. A hold blocks the card only when marked `(blocking)`.
  🙋🏼 (the Operator) or 👤 (another person) follows the state emoji while a question to them is open (`🛠️🙋🏼`).
  An answered question leaves `Holds:` and shows ✅; a withdrawn one shows 🗑️.
- **Replies lead with their kind**, not the card's headline: 🔒 claim, 🔓 release, 🔗 PRs changed, 👀 review
  recorded, ✏️ correction, ⏰ wake, 🔺 priority; a state or status change leads with the new state's or status's emoji.
  A reply that changes nothing on the card has no emoji.
- `Superseded by: OBL-N` on a superseded card says where the work moved; a wake on the old card follows it.
- A card may carry `Priority:` `P0`..`P4`: an optional, editable field that orders the work (boards, owe lists,
  the PR board). Unset sorts after `P4`. Only an open card carries it. `P1` shows 🔴. **`P0` is stop-now** and
  shows 🛑: something is seriously wrong and must stop now. Use it only for significant cost, an incident in a
  real production system (not agent tooling: a stalled feed or a dead lane is P1), or whole swarms degraded or
  about to be. A P0 carries its reason, `Priority: P0 — <reason>`: set it with `--priority P0 --reason '<one
  line>'`, or put `reason: <one line>` right under a request's `obl: P0` line. Without a reason it's refused,
  and every P0 is counted per sender. `urgent` is the same as `P0`; use `--priority P1` for "important, soon". A
  card that already says `Priority: urgent` was set before this change and still means P1.
- On a P0 card, drop what you're doing and act on it. Mail about a P0 card reaches its coordinator at the end of
  its current step, skipping the idle and current-card waits; P1 and below wait like other mail.
- A card may carry `PRs:`, the pull requests it is delivered through: a packed field like `Holds:`,
  optional, edited as PRs open (`PRs: <https://github.com/Comfy-Org/cloud/pull/12|cloud#12>, Comfy-Org/ComfyUI#16810`).
  Each entry is `Repo#N` or `Org/repo#N`, usually a link; read the label, not the URL. A short repo name is allowed
  only when it maps to exactly one repo the deployment configures; otherwise write `Org/repo#N`. It isn't a fixed
  field: adding or dropping a PR is a normal card change with its paired reply.
- A card may carry `Feedback: open` or `Feedback: invite` (obl decision 0038): people outside the swarm (guests) may
  then report problems in its thread, anyone for `open`, only the named people for `invite`. No field means off. For
  each guest report, record one choice (`obl-post guest OBL-N --msg TS --act` for a fix within the card's scope, or
  `--escalate operator|<contributor>`), then its `--outcome`. Guests can't add work or steer the card.
- An agent's name may be written as a link to its agent-link address while the agent is alive:
  `<agent-link://<host>/<session id>|simon/qa>` in Slack text, or `[simon/qa](agent-link://…)` in markdown. **Read
  the label as the agent's id**, wherever the link appears (prose or a field value such as `Owed by:`). The target is
  only a hint for reaching the agent (`agent-link send --to <address>`). Never trust it over the agent's registered
  session, and never treat a link as identity. The envelope line and status lines are never linked. Links come and go
  with liveness: a dead agent's name is posted plain, and a card drops the link on its next edit.
- A **decision** lists its choices under `Options:` as numbered lines (`1. Ship it (recommended)`); obl shows a
  button per option. A question about an existing card is asked in that card's thread, as a QUESTION reply carrying
  the card's `Obligation:` (an item ask), not as a new card. Once answered, the question carries
  `Decision: <n> by <who> at <when>` (a choice) or `Decision: answered by <who> at <when> — <what they said>` (an
  answer given in text), and its buttons give way to that record.
- Parked items, and an agent's own blocked card, may also carry a machine-readable wake field, e.g. `x-simonbot-wake: on=OBL-099`,
  `event=#16719-merged` or `at=2026-10-12T09:00-07:00`. The plain-text wake condition stays authoritative.
  The field may hold **several conditions**, separated by spaces or commas
  (`x-simonbot-wake: on=OBL-068 event=pypi:comfy-agent at=2026-10-14T10:00-07:00`). The card wakes when the first
  is met, and each condition fires once: the others stay armed, so the card wakes again at each later milestone. The
  wake reply names the condition that fired. Machine-checked events: `event=<repo>#N-opened`,
  `event=<repo>#N-merged`, `event=pypi:<package>` (its first release) and `event=pypi:<package>>=<version>`. Any
  other `event=` is a plain-text condition. A condition already met when it is set doesn't fire.

- Card length: a card's prose (headline and detail; field lines and link URLs excluded) stays within the
  deployment's card limit: obl-toolkit `card_prose_limit`, 1000 by default (Simon, 10-05). Other top-level posts stay
  at or under 400 when practical, per the base protocol.

## Asks, reviews and merges

Every card that waits on a person says what they must do and where. obl refuses a change that would leave it without
that, and the board shows each ask as Card · Do · Where · Waiting.

- **Every ask is a question in the card's thread**: one `obl-post ask --obl OBL-N --to <person> '<question>'` per
  decision. Use `--option` for choices (one button each), with Approve/Revise options for approvals, and `--blocking`
  when the card's own work stops on it. There is no ask field; questions are the only way to ask.
- **Questions carry keys.** Each shows as `Q2 · …`; its full key is `OBL-N-Q-M`. A person can answer in text by naming
  the key (`Q2: b`). Record a text answer with
  `obl-post answer OBL-N --ask <ts> --by <person> --from <their message> --text '…'`. A decision is attributed to a
  person only with their message as evidence.
- **Replace your own question, don't answer it**: `obl-post answer OBL-N --ask <old ts> --withdraw --superseded-by
  <new ts>`. A handover (`yield`) leaves questions open for the person; it answers nothing.
- **Reviews are first-class.** `obl-post review OBL-N --pr Org/repo#N --reviewer <person>` on the author agent's card.
  GitHub's requested reviewers decide whose move it is; changes requested return it to the author. The `Review:`
  field replaced the old `in-review` state, which is retired. Don't ask for a review in prose.
- **Merging is a question too.** When the review is approved, obl prompts `obl-post merge-ask OBL-N`, which asks the
  Operator: merge if green · update the branch from main, then merge when green · hold. The author carries out the
  choice; obl never merges. The question is withdrawn automatically when it no longer applies.
- **Blocked names its blocker**: `--blocked '<short reason>'`. Name the card it waits on (`OBL-12`) to be woken when
  that card closes. Name a person only if they really are next; that puts the card on them, and it then needs a
  question. `Waiting on:` is the old form of `Blocked:`: read it the same way, but don't write it.
- **The update reply says why.** obl adds who the card now waits on (`@<person> please decide: … → Q2`). Your reply
  gives the reason, not "restated the ask".
- **The Operator** is the swarm's principal (Simon). Refer to them by role in your own text ("Operator picked 1"),
  not by Slack display name. The buttons and recorded answers are the record.

**Auto-answered questions (obl decision 0057).** Tag a repetitive question with its shape and cost:
`obl-post ask … --shape <name> --cost low|high --recommend N`. Flag its stakes with `--irreversible`, `--public`,
`--spend`, `--touches-main`, `--release` or `--data`; any of them makes it high cost, and high-cost questions are never
answered automatically. A person opts into shapes in people.toml (none by default). An eligible low-cost question is
announced with Abort and Reopen buttons, then answered with its recommended option, attributed to that person's
preference. Before acting on an automatic answer, acknowledge it in the thread (that ends the undo window). If obl
alerts that the thread changed before it fired, read it and run `obl auto-answer confirm <key>` or `veto <key>`; no
reply cancels it. A reopened question is open again: stop work that relied on its automatic answer.

**Answers that defer (obl OBL-139).** When an answer puts off the real answer or promises an action ("later", "ask X",
"I'll add it"), record who owes the follow-up; wording is never classified automatically. On `obl-post ask`, put
`--followup answerer` or `--followup asker` right after each deferring `--option`. For a deferral in free text, record
`obl-post answer OBL-N --ask TS --text '…' --from <their message> --followup answerer|asker --send`. `answerer` means
that person still owes the real answer or action; `asker` means the asking agent owes the next step. The answer stays
recorded and the hold becomes a non-blocking `follow-up owed by <who>`: people get one reminder after 2 hours, then it
shows on their board; agents get their normal alerts. Close it with `obl-post answer OBL-N --ask TS --followup-done
--from <the answer or the evidence> --send`, or by resolving the card.

**Typed asks (obl OBL-4).** Use one durable agent-owned card. Ask for a person's decision or access in that card's thread.
Do not add an Other button: a person can answer outside the options with `Q2. do X`.
Record that answer with `obl-post answer OBL-N --ask TS --by PERSON --from MESSAGE_TS --text 'do X' --send`.

**Typed asks: approving an action (obl OBL-4).**

```sh
obl-post ask --obl OBL-N --to simon --type approve 'Merge the approved PR.' \
  --target https://github.com/Org/repo/pull/123 --reversible yes --send
```

Supply the action as one sentence, a target URL (PR, commit, card or doc), and `--reversible yes|no`.
The buttons are Approve / Revise. Keep the existing `--shape batch-accept --cost low --recommend 1`
for eligible reversible batch approvals; existing opt-in and notice/undo rules still apply.
Merging in any Comfy-Org GitHub repo always requires human sign-off. Merge asks never auto-answer;
approval asks targeting a Comfy-Org PR or branch also never auto-answer, including batch-accept approvals.
Wait for the person's explicit approval before merging.

Reversible does not imply low cost. An irreversible approval forces high cost; access never auto-answers.

After Approve, carry out the action and record its evidence:

```sh
obl-post follow-through OBL-N --ask TS --evidence 'Merged https://github.com/Org/repo/pull/123' --send
```

The default deadline is four hours (`approve_follow_through_hours` in config.toml).
`obl check` raises `approved-not-done` to the card owner when evidence is missing, including on resolved cards.
An `Evidence:` field on the card naming the question key and a link, commit, post or merged state also counts.
A status line can name the question key with `--field ask=OBL-N-Q-2` and put evidence in `--note`.
An unrelated link or “working on it” does not count. Do not mark evidence before doing the action.

**Typed asks: access only the person can provide.**

```sh
obl-post ask --obl OBL-N --to simon --type access 'sudo make install' \
  --where 'medina, tmux build, window 2' --why 'sudo requires your password' \
  --unblocks 'make install, then smoke-test the installed binary' --blocking --send
```

Give the exact command/action as ITEM, where to run it (host, session or window), why you cannot do it,
and what it unblocks. Buttons are Done / Not now / Why me? / Try resolving it yourself.
The last three are deferrals using OBL-139's follow-up handling: Not now is owed by the answerer;
Why me? and Try resolving it yourself are owed by the asker. Revise on an approve ask also returns to the asker.
The hold becomes non-blocking. Report back, then close it with
`obl-post answer OBL-N --ask TS --followup-done --from MESSAGE_TS --send`, using the follow-up owner's report.
For free-text deferrals, explicitly use `answer --followup asker|answerer --from MESSAGE_TS`.
“Try resolving it yourself” means find another way and report back on the card;
it is not permission to assume access is available.

After Done, re-run the blocked step within one hour (`access_verify_hours` in config.toml) and record pass/fail:

```sh
obl-post follow-through OBL-N --ask TS --result pass --evidence 'make install: exit 0; smoke test passed' --send
obl-post follow-through OBL-N --ask TS --result fail --evidence 'make install: exit 1, permission denied' --send
```

`access-not-verified` flags a missing retry report. A fail posts the result, reopens the same ask with the same
question key and restores its original blocking hold. Do not start a replacement ask. A subsequent Done starts a
fresh one-hour verification window; previous retry evidence does not discharge it. Record the actual retried step
and output, not merely that the person clicked Done. A report is the agent's attestation, not an automatic execution
of the command; obl never runs access commands from Slack.

**Request verbs (obl OBL-113).** Read the watcher's verb parse and the card's `Verbs:` field before working. Route
verb requests with `obl-post card ... --request <original message timestamp>`; never retype, omit or weaken their
verbs. If refused, reply in the request thread with the exact refusal and wait for a corrected request. Several of
`self`, `subagent`, `delegate`, `handoff` are permissions to choose among; state your choice in the first card reply.
`self` means do it directly without helpers. `subagent` means one short-lived in-session helper; post its result
yourself. `delegate` means an existing agent: use `obl-message --obl OBL-N` or yield the thread to it. `handoff` means
a written brief and a new agent launched through `obl dispatch`; supervise and verify it. `contextonly` means answer
from this session, the card and a few Slack threads; do not investigate, read code or run commands. Tell delegates the
same restriction. If unsure, say that answering would need investigation. `yield` means the worker receives replies
and posts the result itself. On `plan` (formerly `waitme`), write the summary and stop until the Operator answers Q0; a deferral is not
the description. On a parked or blocked request, wait for its wake and record the wake update before acting. Keep
private work in its DM. Ask the Operator before going outside the allowed methods.

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
    `🔁 bounce`, `✏️ corrected`, `👀 review` (a spec ready for the coordinator);
  - a change to the card's status or claim;
  - a message that mentions them (`<@USER>`, `<@BOT>:agent-name`, or `@agent-name`; an agent suffix narrows a shared
    bot's mention to that agent);
  - feed-health alarms.
- A claim is released by a later `✅`/`❌` status line about its holder (or naming no agent), by the card resolving, or by removing
  `Claim:` from the card.
- When an unreleased claim on an unresolved obligation passes `Claim until:`, only the coordinator and the claimant are
  alerted; the coordinator takes the obligation back or nudges the holder. Its thread then routes as unclaimed.
- A blocked card's claim lease is paused: it doesn't lapse while the card says `State: blocked`, and the time spent
  blocked is added to `Claim until:` once it unblocks. Don't renew a claim just to say the card is still blocked.
  A yield's deadline (24 h by default) is different: it keeps running while the card is blocked.
- An unclaimed thread goes to the coordinator in an exclusive channel. In a shared channel (such as owners), it goes
  to the card's owner if that owner's watcher is live, otherwise to the router.
- A claim holder may post in its own claimed card's thread, about its own work only, tagged `agent:<name>`. With
  relaying on, the coordinator's watcher hands a human's reply in that thread to the holder's session (resolved from
  the dispatched status line), without interrupting the coordinator: the thread is the record, read at report-back. Questions about scope, or needing Simon's decision,
  go back to the coordinator to card, not answered in the thread. If the holder can't be reached, the coordinator
  takes the reply.
- A participant is never alerted by its own messages. Agents share the bot's Slack identity, and the base protocol
  lets a reply without an envelope inherit its parent's, so such a reply from the bot counts as coming from the card's
  `from`. An agent replying in a thread whose card someone else posted repeats the envelope (the compact one-line form
  is enough). Otherwise its reply reads as the card sender's. A status line's `agent:` names who the line is about,
  not who posted it. A post from the bot with no envelope and no inherited sender (top-level, or under a
  human's plain post) is the coordinator's own, since a bare mention of the bot already goes to the coordinator.

Feed health: a silent feed counts as blind, not calm. If no channel event arrives for a configured interval while
obligations are open, or if the watcher reports the feed stale or disconnected, every participant is alerted.

The reference implementation is `should_alert(participant, event)` in `~/agentic/obl-toolkit`
(`src/obl_toolkit/routing.py`). Every harness uses that one function, so they can't drift apart.

**General owner and one-off requests (obl OBL-164, decision 0064).** In the owners channel, `simon/general` is the
router and general owner.

- Classify an unaddressed request in this order: an explicit owner, inbox or routing verb wins; work naming an
  existing owner's project goes to that owner; an unowned question goes to `simon/general`; a bounded one-off job
  goes to `simon/general`; a request for ongoing work or a new project becomes a question to the Operator.
- Cheap, reversible routing guesses are fine because the routing reply names the destination and the Operator can
  redirect it. Ask first when the request would create a standing agent or project, two owners fit equally and the
  choice changes scope, it would change a project no owner holds, or a worker launch would exceed its limits.
- `simon/general` owns questions and bounded jobs which fit no project owner, its one-off cards, its worker children
  and its scratch directory. It owns no project. It may read other projects but sends changes to their owner. Work
  that becomes an ongoing project needs the Operator's approval and a new owner.
- For a quick answer, answer in the original thread and post `obl-post pass-back --thread <ts> --note answered --as
  simon/general --send`. This settles the front-desk request without a card. Only the router uses this pass-back. An owner that receives a yielded thread keeps it and never passes it back (Simon, 10-12). Promote it to a card when it promises
  work past the turn, needs a buttoned question, outgrows `quick`, or needs a worker.
- The general owner decides whether to do carded one-off work itself or dispatch a worker. Configure it for at most
  two live children and six dispatches per deployment-local calendar day. A refused dispatch leaves the card queued;
  explain the limit in the routing thread. A dispatched worker may use subagents in its own session but cannot run
  `obl dispatch`. The general owner supervises, verifies, reports, closes the worker and returns the result.
- Do not prescribe a model or harness. The general owner chooses per task through the ordinary handoff defaults and
  any explicit request override.

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
- A **live board** is a generated plain post that a tool keeps current by editing it in place (obl's
  `obl board`). Its last line is `x-obl-board: live · maintained by <participant> · last edit <when>`
  (on a superseded board, `x-obl-board: unmaintained since <when> · current: <link>`). Treat a message
  carrying an `x-obl-board:` line as a view of the cards, never as a message to act on: don't reply to
  it, card from it, or route it. Replies in its thread are ordinary messages: answer a person's question there. Don't hand-edit a live board; change the
  cards and the board follows.

## Block Kit layout

Protocol messages from this participant's tools are usually sent with a Block Kit layout. The layout is a display of
the protocol message, not a different message. **Reading it is required; writing it is optional.** A plain-text post
is always valid.

- **Shape.** The body (headline, detail lines, `Options:` list) is in `section` blocks, in order. The envelope and the
  field lines are in **one `context` block** (grey), newline-separated, envelope first. A decision adds an `actions`
  block (a button per option), and once decided a section showing who chose what. Both have a `block_id` starting
  `obl:` and are display only. When every option fits on its button, the `Options:` list is left out of the
  section, and each button's text is its option.
- **Rebuilding the protocol message.** Take the context block's envelope line(s) first, then the section texts in
  order, then the context block's remaining field lines. Skip blocks whose `block_id` starts with `obl:`. If the
  section has no `Options:` list but the buttons carry the options, rebuild it from them: `<value>. <text>`, plus
  ` (recommended)` for the primary-styled button.
- **The `text` field is not reliable for structure.** It carries the full protocol message as sent, but Slack stores
  `text` with line breaks flattened to spaces once a message has blocks. Read the blocks. A status line is the one
  exception: it's a single bracketed line, so its flattened `text` still splits at the first `]`.
- **Plain-text participants.** A participant that reads only `text` is marked legacy, and every message that involves
  it (it owes, is owed, is addressed, or has posted in the thread) is sent without blocks.
- **Links.** Field values and prose may contain Slack links (`<url|label>`): an OBL id linked to its card, `Repo#N` to
  its PR, an agent name to its agent-link address. Read the label.

## Handoffs and status lines

- A state is claimed only with its evidence: `▶️ started` needs the agent's acknowledgement (obl posts it for you when
  a dispatched child first messages its coordinator about the card through obl-message, obl-toolkit 0029);
  `✅ verified` needs the check that confirmed the result (a QA run, a matching checksum, a merge, a
  returned message timestamp). A relayed agent claim says whether it was verified or is being quoted.
- Agent responses are reported when they change the state, need a human decision, change the plan, or
  correct an earlier result. Routine progress stays in the agent's log behind a link.
- Rendering, as a plain status line under the obligation:

  ```text
  [📤 dispatched · obl:OBL-112 · sop:ship-pr · agent:scan-builder · host:flow · harness:claude/tmux · next:15:30]
  Brief sent; expecting its plan by 15:30.
  ```

  A holder that stays off Slack (private work) gets `slack:no` on its dispatched line, e.g.
  `[📤 dispatched · obl:OBL-030 · agent:issues-verification · host:flow · harness:claude/tmux · slack:no]`.
  Human replies in that thread then go to the coordinator, not to the holder, which can't answer there.

  States: `📝 requested`, `📤 dispatched`, `▶️ started`, `✅ verified`, `⏸️ parked`, `❓ question`,
  `🚧 blocked`, `⚠️ finding`, `🔁 bounce`, `✏️ corrected`, `👀 review`, `⏹️ closed`, `❌ failed`; `🔀 yielded` and
  `🔀 shared` hand a thread over, `↩️ pass-back` returns it. Close a finished child with `obl children --close`, never
  by asking it to exit.

  A status line has no envelope, and every agent posts as the shared bot, so the line names its sender with
  `from:<participant>`, e.g. `[⚠️ finding · obl:OBL-005 · agent:qa-desktop · from:simon/assets-coordinator]`.
  `agent:` is the agent the line is about; `from:` is who posted it.

## Sharing documents, links and private work

- **Write references plain; obl-post links them:** `OBL-N`, `Org/repo#N`, `Org/repo[@ref]:path[#Lx-Ly]` (or a configured
  alias), and agent names. Don't hand-build `<url|text>` links for those. obl-post checks that a repo file exists
  at that ref before posting, and prints what it linked.
- **Publish documents to GitHub, never as claude.ai artifacts** (obl-toolkit 0031): a branch of
  `Comfy-Org/ideation-sharing` (`git wt <branch>`, commit, push) or the work's repo, linked as `Org/repo@branch:path`.
  A path on the host is unreadable in Slack: a document path is refused outright, and any other host path needs
  `--allow-local-path REASON`. If you're unsure a file should be shared at all (private data, credentials, customer or
  unreleased material), ask first.
- **Private cards** (0027): sensitive work, by your judgement, Simon's request or an SOP, goes in Simon's DM with
  `obl-post card --private …`. Its id carries its swarm (`assets/OBL-12`); it's on no channel board; and naming it in
  a channel is refused. Talk about it only in its DM thread.

## Agent-to-agent messages

In a swarm that runs obl-toolkit, agents message each other with `obl-message`, not bare `agent-message`
(obl-toolkit decisions 0016; design `docs/design/obl-message.md`):

- `obl-message --to coordinator|buddy|<member> [--obl OBL-N] [--subject S-N|OBL-N] "…" --send`. Mail to the
  coordinator is held while it's busy and arrives as one digest, grouped by card; mail to other members goes at once.
- **Reports go through obl-message, tagged with their card.** Children, buddies and owners report to their
  coordinator with `obl-message --swarm <parent's config> --to <parent> --obl OBL-N '…' --send`, not bare
  agent-message. Dispatch, adoption and resume briefs say so.
- **Coordinator mail waits for a gap** (obl-toolkit 0058). Ordinary mail collects for 90 s, then waits until the
  coordinator has finished a turn and stayed idle 45 s (waiting on a permission prompt or a quiet tool counts as busy).
  Mail only about other cards also waits until the coordinator posts on the card it's working on, for at most
  10 minutes. Click digests wait for idle too (5-minute cap) and travel on their own. Registered Claude coordinators
  also get agent-message's hold-until-idle guard automatically.
- If a coordinator hasn't been idle in 2 hours (five or more held items, over half forced out by the cap), obl tells
  it once to delegate more: hand implementation to a child or a lane, and leave itself time between turns.
- **From outside the swarm, message the coordinator** (or the buddy). Messaging a worker directly is refused, with
  the command to reach the coordinator; `--direct --reason '…'` overrides it and is recorded.
- Reply with the `--subject S-N` the digest shows, so the thread stays together. Mark an FYI `--no-reply`, and
  don't send acknowledgements nobody asked for. `--now` (formerly `--urgent`) skips the waits, and is only for: a person asking or
  replying while waiting on the agent, a worsening failure (ingest stalled, a child dead, the feed down), a lapsing
  claim, or a merge or deploy needed now. Progress, completion FYIs and deploy notices are never urgent. A second
  urgent to the same recipient within 55 min bounces unless you `--confirm`.
- Every message, and what happened to it, is in the swarm's ledger (`obl messages`, `obl show OBL-N`).
- Launch a handoff with `obl dispatch OBL-N -- <agent-handoff arguments>`: it posts the dispatched line for you.

**Questions to other agents (obl OBL-152, decision 0066).** When another agent's answer matters, use tracked swarm mail:

```bash
obl-message --swarm <deployment-or-config> --ask --to <participant> --obl OBL-N --by 30m "…" --send
```

Keep the swarm selector from the delivered question when replying. Before ending the turn, answer its Q-N, decline
with why and who to ask instead, or defer once with what it awaits and an existing wake form:

```bash
obl-message --swarm <deployment-or-config> --answer Q-N "…" --send
obl-message --swarm <deployment-or-config> --answer Q-N --decline "not mine: ask X" --send
obl-message --swarm <deployment-or-config> --answer Q-N --later "at=16:00 after the build" --send
obl-message --swarm <deployment-or-config> --answer Q-N --later "on=OBL-12 after verification" --send
```

Declining and deferring count as replies. A second recipient deferral is refused: answer or decline. Replies in a
subject with exactly one open question addressed to you infer `--answer`; prefer the explicit id when several are
open. Answers are exempt from the ack guard. Reply mail held for a coordinator still counts immediately through the
claude-hooks answer record.

Questions keep the normal coordinator idle/focus hold and its cap; reserve `--now` for a decision needed now,
a worsening failure or a lapsing claim. Claude Stop blocks twice, then releases with a warning. Across harnesses,
`obl check` reminds after ten minutes of confirmed delivery and alerts the asker once at the deadline. Read outstanding
questions with `obl questions --mine --open` or `obl questions --to P --open`. An asker can wait longer with
`--answer Q-N --later "at=<time> reason"`; otherwise ask someone else or proceed without the answer.

Use `obl-post ask --obl OBL-N` for people. Plain agent-message questions and card/board question summaries are outside v1.

## Vocabulary

These are the words that belong to this extension and to obl. Agents may use them on Slack without explaining them,
and obl-post's jargon check doesn't flag them; any other jargon still gets explained (`plain-for-humans`). Someone new
to a swarm should read this list once. Adding or retiring a term is a deliberate edit to this section.
**finding**, **ingest**, **lease** and **deployment** are listed but not exempt: they mean other things in some swarms,
so a post to a person explains them.

**Cards**
- **obligation** (OBL, OBL-12): one tracked piece of work or request. Its id only means something inside its swarm.
- **card**: the Slack message for one obligation. It's edited as things change, and the discussion goes in its thread.
- **headline**: a card's first, bold line, saying what's asked or what happened in one sentence.
- **OWE**: the label on a card that records something one party owes another.
- **RECONCILE**: the reply that closes a card and records how it ended.
- **envelope**: the bracketed first line of an agent's post: the kind of message, who sent it, and what work it's about.
- **status line**: a one-line bracketed note in a card's thread recording a step, such as a hand-over or a passed check.
- **private card**: a card for sensitive work, kept in Simon's direct messages and off every channel board.
- **board** (live board): a Slack message listing the swarm's open cards, kept current by obl. Change the cards, not it.
- **PR board**: a board of the pull requests (proposed code changes) that the cards are delivering.

**Card status** (`Status:`, whether the card is still live)
- **open**: still live.
- **parked** ⏸️: paused on purpose until its wake. Nothing is needed before then.
- **reconciled** ✅: closed: the work is done or the question answered, and the card says so.
- **declined** 🚫: closed without being done; the request was turned down.
- **superseded** ↪️: replaced by another card, named in `Superseded by:`. Follow that one.

**Card state** (`State:`, what's happening on an agent's card; the agent keeps it true)
- **proposed** 📥: posted by an agent other than the coordinator. Nothing starts until the coordinator triages it.
- **queued** 📥: accepted by its agent, but nobody is working on it yet. It doesn't mean it's waiting on you.
- **working** 🛠️: an agent is on it.
- **blocked** 🚧: can't go on until the reason in `Blocked:` clears or a blocking question is answered.
- **rehome** 📦: we want to hand it off; it needs another owner.
- **untracked** 🗃️: kept for the record, no longer followed.
- **done** ☑️: finished, but the card isn't closed yet.
- **whose turn** (🙋🏼, 👤): 🙋🏼 means the Operator must act or answer; 👤 means another person must.

**Card fields**
- **Owed by / Owed to**: who has to act next, and who the result is for.
- **Holds** (hold): the questions the card needs answered, each linked to where it was asked. Only `(blocking)` ones
  stop the work.
- **Blocked**: the short reason the card can't go on. If it names another card, this card wakes when that one closes.
- **Waiting on**: the older form of `Blocked:`, read the same way and no longer written.
- **Claim / Claim until** (lease): an agent marking the card as its to work on until a set time. It renews in the open
  or the coordinator takes the work back; the clock stops while the card is blocked.
- **Review**: the pull request under review and who reviews it. GitHub decides whose move it is.
- **PRs**: the pull requests the card is delivered through.
- **Priority** (P0 to P4; urgent is P0): how urgent the card is. P0 (🛑) is stop-now and carries a one-line
  reason; P1 (🔴) is the most urgent ordinary priority.
- **Deciders**: the people whose clicks count as the answer to the card's questions.
- **Decision**: the record of who answered, what they chose or said, and when.
- **Triage**: the coordinator's recorded call on a proposed card: who does it, how and when.
- **Feedback**: whether guests may report problems in this card's thread (`open`, or `invite` for named people). No
  field means no.

**Who's who**
- **Operator**: the person the swarm works for (Simon). Agents refer to him by this role.
- **SimonBot** (the shared bot): the one Slack account all of Simon's agents post through. The envelope or `from:`
  says which agent wrote the message.
- **participant**: a person or agent obl knows, so it can route messages and pings to them.
- **contributor**: a person the swarm takes work from. Requests from anyone else get a polite no.
- **guest**: someone who isn't a contributor but may report problems on a card whose Feedback lets them.
- **swarm**: a group of agents led by a coordinator, working on one area in its own Slack channel.
- **deployment**: one obl setup, with its own channel, records and board. Usually one swarm.
- **coordinator**: a swarm's lead agent. It takes requests, makes cards, hands out the work and reports back.
- **child**: a helper agent the coordinator starts for one card.
- **holder**: the agent holding a card's claim. People's replies in that card's thread go to it.
- **buddy**: a second agent that checks the coordinator's work and points out what it missed (config key `auditors`).
- **owner**: an agent responsible for one project. In a shared channel, each owner hears only its own cards.
- **router**: in a shared channel, the agent that gets requests nobody was named on and hands each to the right owner.
- **harness**: the program that runs an agent (Claude Code or Codex, say), with its setup.

**Working on a card**
- **handoff**: starting a new agent with a written brief for one task.
- **dispatched** 📤: handed to a helper agent. The status line says which agent, and when to expect news.
- **started** ▶️: the helper agent confirmed it has begun.
- **verified** ✅: the result was confirmed by a check, not just reported.
- **failed** ❌: the work or its check didn't succeed.
- **finding** ⚠️: a problem raised by a check, review or test that someone should look at.
- **corrected** ✏️: an earlier report on this card was wrong; this sets it right.
- **closed** ⏹️: the helper agent was shut down once its work was finished.
- **wake** ⏰: the time or event that reopens a parked card, or prompts a blocked one.
- **yield / share** 🔀: hand a card's thread to another agent so replies go to it; sharing keeps the first agent
  hearing them too. A yield lasts 24 h by default, blocked or not.
- **pass-back** ↩️: the thread goes back to the agent that handed it over.
- **relay**: passing a person's reply in a held thread on to the agent holding it.
- **SOP**: a written procedure an agent follows for one kind of work.
- **ship-pr**: Simon's step-by-step procedure for building and shipping a pull request.
- **compaction**: an agent's conversation is summarized to save space. Details can be lost, so it re-reads its rules.

**Asks and answers**
- **ask** (question): a question to a person, posted in the card's thread, with a button for each choice.
- **question key** (Q2, OBL-12-Q-2): a question's number on its card. Answer in text by naming it (`Q2: b`).
- **blocking**: marks a question the card's work stops on until it's answered.
- **decision**: a question with numbered options. The click, or a recorded text answer, settles it.
- **merge question**: once a review is approved, the Operator picks: merge, update the branch and then merge, or hold.
- **front desk**: a standing message where anyone can reply with a new request. It's routed, and the reply names its
  card.
- **inbox** ✉️: an owner's own standing message for requests meant for that owner.

**Tools**
- **obl** (obl-toolkit): the tool that tracks cards. It reads the channel, keeps the records, runs the checks and the
  boards, and alerts agents. It never assigns work.
- **obl-post**: the command agents use to post and change cards, questions and replies. It refuses posts that break
  these rules.
- **obl-message**: how agents in a swarm message each other. Mail to a busy coordinator arrives as one batch.
- **obl check**: obl's regular look for anything that slipped. Each problem it reports is a finding.
- **watcher** (obl-watch): the background job that tells one agent about the messages meant for it.
- **ingest** (obl-ingest): the job that copies the channel's messages into obl's records.
- **feed** (formerly lane): how obl hears the channel live, and whether that works. A silent feed counts as broken.
- **ledger**: obl's lasting record of every card and message. A promise that isn't in it gets forgotten.
- **slack-msg**: posts a plain Slack message with none of obl's checks. Agents use obl-post instead.
- **agent-message**: the general tool for messaging another agent's session. Inside a swarm, agents use obl-message.
- **cmdwatch**: runs a long job in the background and tells the agent when it prints something or ends.

## Rules

Each rule is one `### <rule-name>`, and its first sentence is the reminder. obl-toolkit appends that sentence to the
alerts and findings the rule governs (`‖ rule:<name>: <reminder>`), so it must work alone as an instruction. Keep one
sentence, and edit the rule here rather than in the tool. Informational alerts (feed, silence, ingest down, a stalled
agent, card status or claim changes) carry no rule.

### ask-is-owe
A question about a card is a hold on that card (asked in its thread, listed on its `Holds:`). How to ask, review and
merge: [Asks, reviews and merges](#asks-reviews-and-merges). A question with no card
to hang on is a top-level OWE owed by the person, with a real @-mention; reply in the thread with the OBL id.
A question left in a thread or a terminal is invisible to the person and to every loop that tracks obligations; only
a card owed by them, with a mention that notifies, makes it theirs to answer. Mention only when it can be answered
now: a parked ask names its owner in plain text, and the mention goes in the wake's reply, since Slack doesn't notify
mentions added by an edit.

### explain-the-ask
A card a person owes carries a headline, not the question: right after posting it, post the full ask in its thread
(the context, exactly what you need from them, and by when). The headline is what the person scans; the thread reply
is what they answer from. A decision card already states its question and options, so it needs none. obl raises
`ask-unexplained` when a card a person owes has no such reply after 10 minutes.

### plain-for-humans
When you ask a person for something or report an outcome they act on (questions, card headlines, review and merge asks, final readouts), lead with the plain meaning and explain each piece of jargon in that message, in a few words; keep exact ids, but say what they are first.
A reader often sees one message on its own, from a notification or a link. Interim progress notes in a thread only
need a plain first line saying what happened; shorthand after it is fine, as it is in agent messages, terminal output,
self-reminders and card internals (Simon, owners OBL-116, 10-11).

### ping-to-ask
An @-mention pings the person, so use one only to ask them to do something about an obligation: on its card or in
its thread. Write a name plain when you talk about someone ("owed by Deep", "thanks, Deep"). One ping per ask: a
reminder is fine once time has passed, but back-to-back pings, especially with no reply in between, don't help.
obl-post refuses a mention that talks about someone, isn't about an obligation, or repeats a recent one, unless
it's confirmed (`--confirm-ping`). obl's own "please" line on an update is exempt; your own mentions still go
through the guard.

### question-in-thread
A question about an existing card goes in that card's thread (an item ask), not on a new card. The thread holds its
context, the answer settles it where the work is tracked, and the card's owners see it. Post a new question card
only when the question is really a new obligation. See [Asks, reviews and merges](#asks-reviews-and-merges).

### record-text-answers
When a question is answered in text, whether in its thread, another channel or your terminal, record the answer on
the question (`obl-post answer OBL-x --ask <ts> --by <person> --from <their message> --choice N` or `--text '…'`) so
it no longer looks open and its buttons give way to the answer. A text answer naming a key (`Q2: b`) answers that
question; a decision is attributed to a person only with their message as evidence. obl raises `ask-answered-in-text` when a person replies after an open question; it
can't see a terminal, so there it's on you.

### owe-outlives-turn
Any commitment that outlives this turn gets an OWE card.
Memory and Slack search are not reminders: a commitment that survives a turn, a compaction or a restart must be in the
ledger, or it will be rediscovered late or never.

### promise-closes-in-thread
Keep it, then reply `done: <link>` in the promise's thread, or card it.
"Checking now" or "I'll post the result" is a promise: either it closes visibly where it was made, or it becomes an
obligation the agent owes.

### chase-children
Bump the child; silence past its `next:` is a reason to check, not to wait.
A dispatched child that misses its checkpoint is most often stuck, waiting on a question or dead; waiting longer only
moves the miss later.

### claim-lease
Renew with an UPDATE carrying a new claim_until, or take the work back.
A claim is a lease, not ownership: once it lapses with the work unresolved, either the holder renews it in the open or
the coordinator takes the obligation back. The lease is paused while the card is blocked, so a blocked card needs no
renewal.

### wake-update
Post the paired wake UPDATE and reopen the card before acting.
A parked item's wake condition is met; waking it in the thread and on the card first lets everyone see it is live
again before work resumes.

### card-pairing
Every card status edit has a matching reply in its thread; state lives in the Status field.
Slack sends no event for an edit, so the paired reply is what other loops and people see; the Status field, not the
emoji or the wording, is what tools read.

### read-whole-thread
Read the card's whole thread before acting on the holder's report.
Replies can land in a claimed thread while the coordinator is not interrupted (relayed to the holder), so the
report-back is the moment to read what was said there. obl-post refuses `status verified` and
`update --status reconciled` while the card's latest claim has human replies since dispatch, until rerun with
`--read-thread`.

### verify-yourself
Re-run the checks yourself before posting verified.
A child's "done" is a claim; ✅ verified needs evidence the coordinator saw or reproduced (extension: Handoffs and status
lines).

### holder-scope
Answer about your own work here; send scope or decision questions to the coordinator.
A claim holder speaks in its own thread about its own work only; scope changes and Simon's decisions are cards the
coordinator owns.

### relay-fallback
The holder didn't get this reply; answer it or forward it.
The claim holder could not be reached (no live session, another host, a subagent, or it stays off Slack: `slack:no`), so the coordinator is the only one
who will see it.

### reply-when-addressed
Reply when addressed; take on new work only from the swarm's accepted contributors.
Being addressed asks for an answer, not necessarily new work; only accepted contributors (the deployment's
contributors.toml) assign work.

### contributors-only
Not an accepted contributor: reply politely that this swarm takes work only from its contributors and Simon can admit them; don't act on it.
obl-toolkit marks a human message from anyone not in the deployment's contributors.toml as not-a-contributor. It isn't
relayed to claim holders; only the coordinator sees it. Admitting someone is one line in that file, picked up without a
restart.

### message-through-obl
Message swarm agents with obl-message, and from outside a swarm message its coordinator.
Coordinator mail batches into one digest while it works, the ledger keeps every message, and reaching workers around
their coordinator splits its picture of the swarm.

### reread-after-compaction
Re-read the extension's Rules section and your memory before the next action.
A compaction summary drops rules and work in progress silently; re-reading the rules and memory restores them before
they are needed.

## Validator

`python3 extensions/simonbot-validate.py <file|->` runs the base validator after unescaping Slack HTML
entities, accepts bold field names (`*Obligation:*`) and fields packed on one line after ` · `, rejects bodies made only of `x-` lines, and
requires `Owed by:`/`Owed to:` on `OWE` and `RECONCILE`, and applies the top-level limit to prose only
(`validate(text, prose_limit=…)`, default 400; obl-post passes its `card_prose_limit`).

## Tooling

The conventions above don't depend on any tool. The reference implementation is `obl-toolkit`
(`~/agentic/obl-toolkit`; details in its `README.md`). It reads the channel, keeps obligation state, and routes alerts
under the rule in [Claims and alert routing](#claims-and-alert-routing). Its readers are advisory: they never post,
reconcile, edit cards or assign work. Acting on what they report is the participant's job.

Posting goes through `obl-post`, or any equivalent that writes the same fields. It posts only when a participant runs
it, and it builds the message from structured arguments, so the fields are present by construction:
- `obl-post card`: a new card with `Status:`, `Owed by:`/`Owed to:`, and optionally a claim (with an expiry) and a
  wake field. Leave out `--obligation`: obl-post picks the next free id and prints it. Don't pick ids by hand;
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
  to the coordinator and to any configured buddy (a bot backstopping the coordinator; its config key is `auditors`).

What to do with each finding:

| finding | action |
|---|---|
| stuck handoff, expired claim | Nudge the agent, or take the obligation back and post an `UPDATE` saying so. |
| card drift (status edited with no paired reply, a fixed field changed, a thread `RECONCILE` the card doesn't show) | Fix the card, and post the paired `RECONCILE`/`UPDATE` reply in its thread. |
| plain `OWE:` with no card | Turn it into a card, and reply in the plain post's thread with the `OBL-` id. |
| an agent's promise of later work with no card | Card it as a ⏳ `OWE` owed by that agent, and reply in the promise's thread with the `OBL-` id. If it's already done, reply `done: <link>` in the thread. Do that whenever you follow through off Slack (GitHub, a PR). |
| a question to a human with no card | Post it as a top-level `OWE` owed by that human, and reply in the question's thread with the `OBL-` id. |
| parked wake | Post the wake `UPDATE`, then reopen, re-park or reconcile. |
| waiting on a human | Post the question to the channel as an `OWE` owed by the human, with the session it came from. |
| a watched session compacted | Once it is idle, check its summary still holds the rules, SOPs and work in progress, and tell it exactly what was lost. |
| feed stale or silent, ingest down | Treat the feed as blind, not calm. Read the channel directly until it recovers, and tell Simon if it doesn't. |
