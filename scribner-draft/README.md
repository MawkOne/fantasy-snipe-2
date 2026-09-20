# Scribner Draft

Responsive web app for a sealed, simultaneous fantasy hockey draft.

## Draft rule

Each team submits one private player selection per round. Duplicate selections are allowed in the same round. When the commissioner reveals the round, every submitting team receives its selected player. The unique set of selected players is then removed from the pool for future rounds.

## Local development

```bash
npm install
npm run dev
```

Local development uses `.data/rooms.json` when no database URL is configured.

## Production

Configure Railway (or another durable PostgreSQL service) with one of:

```bash
DATABASE_URL=postgresql://...
# or
FANTASY_DATABASE_URL=postgresql://...
```

The app initializes the required tables automatically. The reference schema is also available at `sql/001_scribner_draft.sql`.

Production intentionally refuses JSON-file storage unless `SCRIBNER_ALLOW_JSON_STORAGE=true` is explicitly set. JSON storage is not safe for serverless or multi-instance deployment.

## Optional email delivery

Configure Resend to enable `Send Invite`:

```bash
RESEND_API_KEY=...
RESEND_FROM_EMAIL="Scribner Draft <draft@yourdomain.com>"
```

Without Resend, every team still has a private copyable invite link.

## Validation

```bash
npx tsc --noEmit
npm run build
```
