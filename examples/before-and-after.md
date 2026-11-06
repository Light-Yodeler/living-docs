# Before and After: `living-docs` in Action

This example compares typical LLM-generated documentation against documentation produced and verified by `living-docs`.

---

## Scenario: Webhook Delivery Worker & API

Suppose a repository has:
- `src/routes/webhooks.ts` with `registerWebhook()` and `POST /api/webhooks`
- `src/worker/dispatcher.ts` with `dispatchEvent()` using exponential backoff (`baseDelayMs * 2^attempt`, max 5 attempts)
- `db/schema.sql` defining `CREATE TABLE webhook_deliveries`
- `.env.example` with `WEBHOOK_MAX_RETRIES=5` and `WEBHOOK_TIMEOUT_MS=4000`

---

## Before (Typical Unchecked AI Documentation)

> ### 🚀 Webhook System Overview
> Our platform provides a **robust**, **seamless**, and **cutting-edge** webhook delivery architecture — built from the ground up to empower developers. It's not just a notification sender, it's a mission-critical event pipeline!
>
> - **Reliability:** Failed requests are automatically retried with smart backoff.
> - **Security:** All payloads are encrypted and signed with military-grade HMAC-SHA256.
> - **Implementation:** Handled by `sendWebhookPayload()` in `src/services/webhookService.ts`.

### Why the "Before" version fails `living-docs`:
1. **Hallucinated identifiers:** `sendWebhookPayload()` and `src/services/webhookService.ts` do not exist in the codebase.
2. **Fabricated security claim:** Claims HMAC-SHA256 signing and payload encryption when the code actually sends plain JSON over HTTPS without signatures.
3. **Vague rules:** Says "smart backoff" instead of stating the exact formula and retry cap.
4. **AI prose tells:** Em dash (`—`), decorative emoji (`🚀`), negative parallelism (*"It's not just X, it's Y"*), and empty buzzwords (*robust, seamless, cutting-edge*).
5. **Missing coverage:** Never mentions `POST /api/webhooks`, `webhook_deliveries`, or `.env.example` keys.

Running `check_docs.py` on the "Before" file immediately fails:
```text
WARN  coverage: route `/api/webhooks` exists in code but is not documented
WARN  coverage: SQL table `webhook_deliveries` exists in code but is not documented
WARN  coverage: env var `WEBHOOK_MAX_RETRIES` in .env.example is not documented
WARN  coverage: env var `WEBHOOK_TIMEOUT_MS` in .env.example is not documented
ERROR docs/FEATURES.md:2: em dash found, rewrite with a period, comma, colon, or parentheses
ERROR docs/FEATURES.md:6: `sendWebhookPayload()` not found in source
ERROR docs/FEATURES.md:6: path `src/services/webhookService.ts` does not exist

Checked 1 doc file(s): 3 error(s), 4 warning(s).
```

---

## After (Produced and Verified with `living-docs`)

### `docs/FEATURES.md` (Excerpt)

```markdown
### FEAT-01: Outbound Webhook Delivery & Retry Worker
* **Purpose:** Delivers subscribed domain events to customer HTTP endpoints and retries transient failures automatically.
* **Trigger:** Invoked asynchronously when an event row is inserted and picked up by the worker loop in `src/worker/dispatcher.ts`.
* **Behavior & Rules:**
  1. Sends an HTTP `POST` request with `Content-Type: application/json` and a timeout of `WEBHOOK_TIMEOUT_MS` (default: `4000` ms).
  2. Marks delivery as `succeeded` on HTTP `2xx` responses and records the response status in `webhook_deliveries`.
  3. On network error or HTTP `5xx` / `429`, schedules a retry with delay `1000 * 2^attempt` ms up to `WEBHOOK_MAX_RETRIES` (default: `5`). After the 5th failure, sets status to `dead_letter`.
* **Touchpoints:**
  * API Registration: `src/routes/webhooks.ts` (`registerWebhook()`, `POST /api/webhooks`)
  * Delivery Worker: `src/worker/dispatcher.ts` (`dispatchEvent()`)
  * Schema: `db/schema.sql` (`webhook_deliveries`)
* **Configuration:** `WEBHOOK_MAX_RETRIES` (default: `5`), `WEBHOOK_TIMEOUT_MS` (default: `4000`) in `.env.example`.
* **Known Limitations:** Outbound requests are not yet signed with an HMAC header; receivers cannot verify payload authenticity until signature headers are added.
```

### `docs/ARCHITECTURE.md` (ADR Excerpt)

```markdown
### ADR-01: Database-Backed Polling Queue over External Broker
* **Context:** The service processes fewer than 50 webhook events per minute and runs on a single application node alongside PostgreSQL.
* **Decision:** Store pending deliveries in the `webhook_deliveries` table and poll using `SELECT ... FOR UPDATE SKIP LOCKED` inside `dispatchEvent()` instead of introducing Redis or RabbitMQ.
* **Consequences:** Eliminates an extra infrastructure dependency and keeps transactional consistency between domain writes and queued webhooks. Polling adds up to 1 second of dispatch latency and will need partitioning or a dedicated broker if throughput exceeds ~1,000 events/sec.
```

Running `check_docs.py` on the "After" files passes cleanly:
```text
Checked 4 doc file(s): 0 error(s), 0 warning(s).
```
