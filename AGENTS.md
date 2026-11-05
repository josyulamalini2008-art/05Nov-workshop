# Project Guidance

## Project shape
- The application currently lives in `backend/app.py` and is a small Flask service backed by Supabase.
- `backend/.agents/skills/` contains the installed Supabase and Supabase Postgres best-practices skills. Consult them when changing database schema, queries, access policies, or Supabase integration.
- Keep changes focused on the existing backend unless the task calls for a broader structure.

## Configuration and security
- Local configuration is loaded with `python-dotenv`; required Supabase settings are `SUPABASE_URL` and `SUPABASE_PUBLISHABLE_KEY`.
- Never commit `.env` values or print credentials. Do not replace a publishable key with a service-role key in browser-facing code; keep privileged credentials server-side and use the minimum required access.
- Validate required configuration clearly when changing startup behavior.

## Development and verification
- Run the app from `backend/` with `python app.py` when local dependencies and environment variables are configured.
- No dependency manifest or test suite is currently present. Before adding one, follow the task's scope and the project's existing setup rather than assuming a framework or deployment target.
- For behavior changes, add or update focused tests when a test setup exists; otherwise run the narrowest available check and state what remains unverified.