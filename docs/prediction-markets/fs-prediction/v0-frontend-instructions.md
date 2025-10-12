## V0 Frontend Spec — Fantasy Forecasts (App Router, TS, Tailwind, shadcn)

### Project

- Name: Fantasy Forecasts Web
- Stack: Next.js 14 (App Router) + TypeScript + Tailwind + shadcn/ui + Lucide icons
- State: React Query for server state; `localStorage` for auth key/user
- Validation: Zod (optional at v0), clsx/tw-merge utilities

### Naming & Structure

- Routes (folders in `app/`): kebab-case (e.g., `my-playbook`, `snipe-podcast`)
- Components (`components/`): PascalCase (e.g., `Header.tsx`)
- Hooks (`hooks/`): `useXxx.ts` (e.g., `useAuth.ts`)
- Lib (`lib/`): `api.ts`, `formats.ts`
- Types (`types/`): `auth.ts`, `fantasy.ts`
- Each route: `page.tsx` (+ optional `layout.tsx`, `loading.tsx`, `error.tsx`)

### ENV & Auth

- Env var: `NEXT_PUBLIC_API_BASE` (FastAPI base URL with protocol)
- Local storage keys:
  - `fantasy_api_key`: API key string
  - `fantasy_user`: JSON string `{ id, email }`
- Always send `x-api-key` header when present

### Global Layout

- `app/layout.tsx` provides shell with `Header` and React Query provider
- Dark-friendly, responsive, mobile-first

### Header/Nav (must match exactly)

- Left: brand/title
- Nav items: My Playbook, Research, Snipe Podcast, Snipe Chat, Sync League
- No search bar
- CTA rules:
  - Not authenticated: “Get Started” → `/login`, “Sync League” → `/login`
  - Authenticated: user icon → `/account` (no email text)

### Pages to Create (v0 MVP)

- Public
  - `/` Home (hero + CTAs to Login/Sync League)
  - `/login` Login form (email/password → POST `/api/auth/login`)
  - `/signup` Signup form (→ POST `/api/auth/register`)

- Auth required (redirect to `/login` if not authed)
  - `/account` Minimal profile (shows presence of API key, logout)
  - `/sync` Provider sync entry (only CBS tile). “Connect” → `/sync/extension`
  - `/sync/extension` Extension instructions and buttons to open CBS pages
  - `/my-playbook` Hub landing (links to My Team)
  - `/my-playbook/my-team` User team view
  - `/research` Placeholder page
  - `/snipe-podcast` Placeholder page
  - `/snipe-chat` Placeholder or link-out

- Forecast twist (stubs for future wiring)
  - `/players` Player search/list
  - `/players/[id]` Player detail (consensus line, forecasts)
  - `/forecasts` Latest/community forecasts

### Components (must-have)

- `Header` (nav rules above)
- Auth: `LoginForm`, `SignupForm`
- Sync: `SyncLeague` (CBS-only tile)
- Playbook: `MyTeamContent` (fetches overview and renders roster)
- UI kit: `Button`, `Input`, `Select`, `Card`, `Table`, `Badge`, `Toast`

### Hooks & Lib

- `hooks/useAuth.ts`
  - `isAuthenticated(): boolean`
  - `getUser(): { id: number|string, email: string } | null`
  - `login(data): void` (sets localStorage keys)
  - `logout(): void`

- `hooks/useProtectedRoute.ts`
  - Redirects to `/login` if not authed

- `lib/api.ts`
  - Central fetch wrapper: prefixes `NEXT_PUBLIC_API_BASE`, applies `x-api-key`
  - JSON helpers, normalized error shape `{ status, code, message }`

### React Query Hooks (names & intent)

- `useLogin`, `useRegister`
- `useUserProfile`
- `useConnectCbsAccount`
- `useLeagueOverview(slugOrId)`
- `useWaivers(slugOrId)`
- `useSchedule(slugOrId)`
- `useTransactions(slugOrId)`

### Endpoint Wiring (backend alignment)

- Auth
  - POST `/api/auth/login` → store `fantasy_user`, `fantasy_api_key`; redirect
  - POST `/api/auth/register` → same storage; redirect
- Account
  - GET `/api/user/profile` (dev: may not require key)
- Sync
  - POST `/api/public/providers/cbs/connect_local` (on success → `/sync/extension`)
- League (My Team)
  - GET `/api/user/cbs/league/{slug}/overview` (accepts `?league_id=`)
  - Data contract expectations:
    - `league`: `{ id, name, slug }`
    - `user_team_id`: string
    - `teams[]`: `{ id, name, owner_id }`
    - `owners[]`: `{ id, display_name }`
    - `rosters[]`: `{ team_id, players: [{ provider_player_id, name, pos, nhl_team }] }`
    - `rules[]`: `{ key, value }`
- Public (optional views)
  - GET `/api/public/cbs/league/{slug}/waivers`
  - GET `/api/public/cbs/league/{slug}/schedule`
  - GET `/api/public/cbs/league/{slug}/transactions`

### UI/UX Rules

- Protected routes must not flash unauthenticated content; guard before render
- Errors → toast + friendly empty states
- Loading → skeletons for main panes
- No duplicate headers; header rendered only from root layout

### Acceptance Checklist (v0)

- Header nav and auth-aware CTAs match spec
- Login/Signup wire to backend and persist API key/user
- `/sync` shows only CBS tile; “Connect” routes to `/sync/extension`
- `/my-playbook/my-team` fetches overview, auto-selects `user_team_id`, renders roster and basic rules
- All protected routes redirect to `/login` when unauthenticated
- All API calls go through `lib/api.ts` and include `x-api-key` when present
- `NEXT_PUBLIC_API_BASE` includes protocol; CORS validated in browser


