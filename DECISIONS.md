# Decisions

A record of the choices made in this project and why. Each entry states the
decision, the reasoning and, where relevant, the alternatives considered.

---

## 1. Domain and data

**Decision:** The agent supports customers of a fictional digital bank. Customer
messages come from BANKING77 (see `evals/data/banking77/`), restricted to 25 of
its 77 intents. The development set is sampled from the original `train` split
and the test set from the original `test` split.

**Why:** BANKING77 is written by people and labelled by experts, unlike most
public "support ticket" datasets, which are synthetic. Keeping the original
splits guarantees that no test message is seen while tuning the agent.

---

## 2. Categories

**Decision:** The agent classifies every message into one category:

| Category | Covers |
| --- | --- |
| `cards` | Card activation, delivery, PIN and cards that don't work |
| `payments` | Card payments: declined, pending, fees, duplicates, refunds |
| `top_up` | Adding money to the account |
| `transfers` | Sending money: timing and failures |
| `account` | Passcode, personal details, closing the account |
| `security` | Unrecognised payments, compromised, lost or stolen cards |
| `other` | Anything outside the bank's support topics |

**Why:** BANKING77's intents are very fine-grained, and some are hard to tell
apart even for a person (e.g. `card_arrival` and `card_delivery_estimate`).
Seven categories are coarse enough to classify reliably, and each maps to a
distinct part of the knowledge base.

---

## 3. Selected intents

**Decision:** The exact mapping from each BANKING77 intent to its category,
expected action and hand-off reason lives in `evals/intent_map.json`, which is
the source of truth. In summary:

- **14 intents the agent answers** from the knowledge base, across `cards`,
  `payments`, `top_up`, `transfers` and `account`.
- **6 intents that are always handed off** (section 4).
- **5 intents with no knowledge base article** (`exchange_rate`,
  `atm_support`, `country_support`, `age_limit`, `getting_virtual_card`). They
  are legitimate banking questions the knowledge base deliberately doesn't
  cover; the agent must recognise this and hand off instead of guessing.

**Why:** 25 intents fit a 5-day scope while covering every behaviour that
matters: answering, mandatory hand-off, and admitting that the knowledge base
doesn't cover a question.

---

## 4. Always hand off to a human

**Decision:** These cases are always handed off, whatever the classification
confidence. Each has a reason code.

| Reason code | Rule | Intents |
| --- | --- | --- |
| `refund_or_dispute` | The customer asks for money back or says a charge is wrong. | `request_refund`, `transaction_charged_twice` |
| `fraud_or_security` | Possible fraud, or a card at risk. Flagged as urgent. | `card_payment_not_recognised`, `compromised_card`, `lost_or_stolen_card` |
| `account_closure` | The customer wants to close the account. | `terminate_account` |
| `human_requested` | The customer explicitly asks for a person. | (no BANKING77 intent; covered by hand-written cases) |
| `out_of_scope` | The message is classified as `other`. | (no BANKING77 intent) |
| `kb_not_covered` | The question is in scope, but no article covers it. | The 5 intents in section 3 |

**Why:** These involve money, fraud, legal obligations or an explicit request
for a person. A wrong automated answer costs far more than a slower human one.
The agent has read-only access to banking data, so it can't block a card or
issue a refund anyway.

---

## 5. Explaining a charge vs. disputing it

**Decision:** The agent may **explain** a charge (why a payment is pending, why
a fee was applied) but never **decides** on one. `pending_card_payment` and
`card_payment_fee_charged` are answered; `transaction_charged_twice` and
`request_refund` are handed off.

**Why:** Explaining uses public rules from the knowledge base. Deciding whether
money should be returned requires investigation and authority the agent
doesn't have.

---

## 6. What an automated answer may contain

**Decision:** An answer may only use the knowledge base articles the agent
retrieved and the results of its tools. It must cite the articles used and must
never promise refunds, credits or timelines that aren't in an article.

**Why:** Grounded answers are checkable: an answer without a citation, or citing
an article that wasn't retrieved, can be detected and blocked automatically.

---

## 7. What counts as a correct answer in evaluation

**Decision:** The agent is evaluated on the **category** and the **action**
(answer or hand off, and the reason), not on the exact BANKING77 intent.

**Why:** Confusing two intents in the same category with the same action
doesn't harm the customer. Confusing an answerable intent with one that must be
handed off does, and that is what the evaluation must catch.

---

## 8. Conditional hand-off (to be decided after measuring)

The agent will also hand off when it is unsure. Thresholds are placeholders
until measured on the development set:

- Classification confidence below a threshold — *TBD*
- Best retrieval similarity below a threshold — *TBD*
- The model reports that the knowledge base doesn't cover the question
- A tool fails, or the agent hits its iteration or time limit
- Suspected prompt injection
- The final answer fails validation (schema, citations)

---

## 10. Tickets API

**Decision:** `POST /api/tickets/` stores the ticket and returns
`202 Accepted` with a `Location` header; the agent processes it
asynchronously. `GET /api/tickets/<id>/` returns the ticket's status and the
latest agent result. Ticket ids are UUIDs, and messages are limited to 5,000
characters.

**Why:** `202` is the honest answer for queued work: the ticket was accepted,
not yet handled. UUIDs can't be guessed, so one ticket's id reveals nothing
about others. The length limit caps the cost of a single message and the room
for injected instructions.

**What the API exposes:** the decision (outcome, category, hand-off reason,
answer and cited articles). Operational data such as tokens, latency, prompt
version and trace ids stays in the admin, for the team.

**Out of scope:** authentication and rate limiting. In production the API would
sit behind the bank's API gateway, which would handle both.

---

## 11. Processing tickets

**Decision:** Tickets are queued only after they are committed, and processed
by a Celery task that claims a ticket by moving it from `received` to
`processing` in a single conditional update. Every agent execution is stored as
an `AgentRun`. Any error, including a result that violates the database
constraints, is stored as a `failed` run and the ticket is marked `failed`.

**Why:** A queue may deliver the same message twice; the conditional update
makes processing idempotent, so a ticket is never answered twice. Recording
every failure means no ticket is left in `processing` because of an error.

**Stuck tickets:** a ticket that couldn't be queued, or whose worker died,
is re-queued by `manage.py requeue_stale_tickets`. In production this would
run every few minutes with Celery Beat or cron; here it is run manually.

**Baseline agent:** until the LLM agent exists, a baseline agent hands every
ticket off with `low_confidence`. It is the safest possible behaviour and the
reference point for evaluation: the real agent must answer more without
handing off fewer of the cases that require a human.

---

## 12. Evaluation metrics

**Decision:** Every evaluation reports three groups of metrics.

- **Safety:** hand-off recall (of the cases that require a person, how many
  were handed off) and the number of unsafe answers (cases that required a
  person but were answered). Unsafe answers must be zero.
- **Usefulness:** automation rate (of the cases the agent could answer, how
  many it answered) and citation hit rate (of those answers, how many cited an
  expected article).
- **Classification:** action, category and hand-off reason accuracy, plus
  hand-offs broken down by expected reason.

Failures, latency (p50 and p95) and tokens are reported alongside.

**Why:** Safety and usefulness pull in opposite directions: an agent that never
answers is perfectly safe and useless. Reporting both, with the absolute counts
next to every rate, makes trade-offs visible. The breakdown by reason exposes
a weak rule that a good overall recall would hide.

**Baseline:** the baseline agent has 100% hand-off recall, 0 unsafe answers
and 0% automation on the development set. Any change to the agent must raise
automation while keeping unsafe answers at zero.

---

## 13. Language

**Decision:** Messages, knowledge base and answers are in English only.

**Why:** BANKING77 is in English, and one language keeps the scope realistic.

