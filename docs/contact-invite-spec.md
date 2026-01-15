# Contact Invite & Real-Time Notifications – Spec

## Intent
Provide a simple, reliable way for users to connect with each other via contact invites, enforce relationship rules (no self-invites, no duplicates, no re-invites after rejection), and deliver real-time notifications for invites and responses. Keep reads fast (denormalized contacts), writes safe (validations), and UX responsive (Redis + WebSocket fanout).

## Scope Implemented
- Send invite via `connect_pin`.
- Accept/reject invites.
- Prevent self-invite and inviting existing contacts.
- No re-invite when a pending invite already exists; rejection stops re-invite for now.
- Real-time notifications for:
  - `invite_received` (to invitee)
  - `invite_accepted` / `invite_rejected` (to invitor)
- Contacts list retrieval and contact checks (by IDs and by username for chat-service).
- Chat participant add guarded by contact check.
- Frontend UI for add-by-pin, pending invites, real-time toasts, accept/reject.
- User display enrichment on messages (name/username carried through WS and stored).

## Key Design Decisions & Rationale
1) **Unidirectional contacts table (contact_one_id, contact_two_id with min/max)**  
   - Ensures uniqueness with a single row per pair; simplifies writes and lookups.
   - Avoids dual-row or join-table symmetry complexity.

2) **User-service owns invites (PostgreSQL)**  
   - Strong consistency for invite + contact rules; relational fits the constraints/validation logic.

3) **Real-time via Redis Pub/Sub + chat-service WebSocket**  
   - Reuse existing WS path; no extra WS infra.  
   - Personal channels `user:{user_id}` for direct notifications; chat channels unchanged.

4) **No invite expiration initially (extensible later)**  
   - Keep MVP simple; schema and service logic can add TTL/expiry when needed.

5) **No re-invite after rejection (current stance)**  
   - Reduces spam; can loosen later with a rule/ttl if desired.

6) **Backend enrichment for display data**  
   - Messages and invites carry `sender_username`/`sender_name` to avoid extra lookups on the client; prevents spoofing from the client.

7) **Channel identity = numeric user ID (string)**  
   - Aligns Redis channels with WS subscription (`user:{id}`) to guarantee delivery.

## Data Model (PostgreSQL, user-service)
- `invites`  
  - `id`, `invitor_id`, `invitee_id`, `status` (`pending|accepted|rejected` as string), `created_at`, `updated_at`
- `contacts` (unidirectional)  
  - `id`, `contact_one_id` (min), `contact_two_id` (max), `created_at`; unique constraint on (contact_one_id, contact_two_id)
- `users` (existing)  
  - includes `connect_pin` (unique)

## Validations
- `connect_pin` must exist.
- No self-invite.
- Cannot invite if already contacts.
- Cannot create duplicate pending invites.
- Respond: only invitee may accept/reject; must be pending.

## Real-Time Flow
1. Send invite → Redis publish to `user:{invitee_id}` → chat-service WS delivers `invite_received`.
2. Accept/Reject → Redis publish to `user:{invitor_id}` → WS delivers `invite_accepted` / `invite_rejected`.
3. WebSocket manager subscribes on connect to:
   - `user:{user_id}` (personal)
   - `chat:{chat_id}` for each chat

## Frontend UX
- Add Contact dialog: enter `connect_pin`, send invite.
- Pending Invites list: accept/reject.
- Toast/notification on real-time invite receipt.
- Message bubbles show sender name/username.
- Zustand stores: `invite-store`, `chat-store` (stores `userId`, `username`, `name`).

## API Surfaces (user-service)
- `POST /api/invites` (send by `connect_pin`)
- `GET /api/invites` (pending received)
- `GET /api/invites/sent`
- `PUT /api/invites/{id}` (accept/reject)
- `GET /api/contacts`
- `GET /api/contacts/check`
- `GET /api/contacts/check-by-username`
- `POST /api/users/login` (get-or-create by username; returns `connect_pin`)

## Chat-Service Integration
- Adds participants only if contacts (via user-service check-by-username).
- Subscribes WS to personal `user:{id}` channel to deliver invite events.

## Known Extensibility Hooks
- Add invite expiration (TTL, cron cleanup, status transition).
- Allow re-invite after rejection with cooldown/flag.
- Enrich inbox sync responses with display info (already supported for live messages).
- Caching user lookups in chat-service if needed for scale.

## Non-Goals (current)
- Strong auth; current login is username-based convenience.
- Invite batching or bulk contact imports.
- Delivery receipts beyond basic WS fanout (no ACK persistence).


