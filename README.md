# AdaptCode — Web Version

Browser-playable version of AdaptCode. One shared URL — nobody installs
anything. The game itself runs on your server; questionnaire responses go
straight from each student's browser into your Supabase project.

## Local run

```bash
pip install -r requirements.txt
export GROQ_API_KEY=your_key_here          # optional — game falls back to templated hints/no generation without it
export SUPABASE_URL=https://xxxx.supabase.co
export SUPABASE_KEY=your_anon_public_key
uvicorn server:app --reload
```
Open http://localhost:8000

## Deploy to Render (free tier works)

1. Push this folder to a GitHub repo (see steps below).
2. On Render: **New → Web Service** → connect the repo.
3. Settings:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn server:app --host 0.0.0.0 --port $PORT`
4. **Environment** tab → add:
   - `GROQ_API_KEY` (optional, enables live hint text + problem generation)
   - `SUPABASE_URL`
   - `SUPABASE_KEY`
5. Deploy. Render gives you a URL like `https://adaptcode.onrender.com` —
   that's what you share with everyone.

**Note on free tier**: Render's free web services spin down after ~15 min
of inactivity and take ~30–60s to wake back up on the next request. Game
sessions live in server memory, so a spin-down clears in-progress games —
the frontend detects this and silently starts a fresh session. Questionnaire
responses are unaffected since they go directly to Supabase, not through
the game session.

## Supabase setup

Run in the Supabase SQL Editor:
```sql
create table pre_questionnaire_responses (
  id bigint generated always as identity primary key,
  timestamp text, student_id text, q1 text, q2 text, q3 text
);

create table post_questionnaire_responses (
  id bigint generated always as identity primary key,
  timestamp text, student_id text,
  q1 text, q2 text, q3 text, r5 text, q4 text, overall_rating text
);

alter table pre_questionnaire_responses enable row level security;
alter table post_questionnaire_responses enable row level security;

create policy "allow anon insert" on pre_questionnaire_responses
  for insert to anon with check (true);
create policy "allow anon insert" on post_questionnaire_responses
  for insert to anon with check (true);
```
Get **Project URL** and **anon public key** from Project Settings → API.
The anon key is meant to be public in client-side code — access is
controlled by the insert-only RLS policies above, not by secrecy.

## Push to GitHub

```bash
cd AdaptCode_Web
git init
git add .
git commit -m "AdaptCode web version"
git branch -M main
git remote add origin https://github.com/<your-username>/<repo-name>.git
git push -u origin main
```

## Files
- `server.py` — FastAPI backend: session-based game state, hint requests, problem generation, `/api/config` for the frontend to fetch Supabase credentials
- `static/` — frontend (`index.html`, `style.css`, `app.js`)
- `game.py`, `snippets.py`, `hint_policy.py`, `dqn_agent.py`, `problem_generator.py`, `config.py` — unchanged game logic, reused as-is
- `hint_policy.pt` — trained hint-policy weights
