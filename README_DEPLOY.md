### Deploying to Railway

1) Create a Web service for the Next.js frontend
- Root directory: `frontend`
- Build command: `npm ci && npm run build`
- Start command: `npm run start -p $PORT`
- Set `NIXPACKS_NODE_VERSION=20` (or engines.node ^20 in package.json)

2) Environment variables (Web service)
- `FANTASY_DATABASE_URL` → Railway Postgres (RW)
- `NHL_DATABASE_URL` → GCP Postgres (RO)
- `KINDE_ISSUER`, `KINDE_AUDIENCE`, `KINDE_CLIENT_ID`, `KINDE_CLIENT_SECRET`
- Any `NEXT_PUBLIC_*` used for Kinde and public URLs

3) Database schema (Railway Postgres)
- Run once: `backend/sql/001_init_fantasy.sql`
  - You can use the Node runner:
    ```bash
    node -e "require('dotenv').config();const fs=require('fs');const {Pool}=require('pg');(async()=>{const sql=fs.readFileSync('backend/sql/001_init_fantasy.sql','utf8');const pool=new Pool({connectionString:process.env.FANTASY_DATABASE_URL});const c=await pool.connect();try{await c.query(sql);console.log('Migration applied');}finally{c.release();await pool.end();}})()"
    ```

4) Routes exposed
- `/api/pools/:poolId/state`
- `/api/pools/:poolId/order` (GET/PUT)
- `/api/pools/:poolId/pick` (POST)
- `/api/pools/:poolId/bid` (POST)
- `/api/pools/:poolId/teams/:teamId/targets` (GET)
- `/api/pools/:poolId/teams/:teamId/targets/:slotId` (PUT)

5) Kinde configuration
- Add the Railway domain as an allowed callback, logout, and post-login URL in Kinde.


