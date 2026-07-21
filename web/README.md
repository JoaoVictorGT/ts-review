# TrueStay — Web App

**Live site:** https://truestayco.com

React + Vite front-end for the TrueStay hotel-intelligence platform.

## Prerequisites

- Node.js 20+ (tested with v24)

## Run it locally

1. Open a terminal (PowerShell, or your editor's integrated terminal).
2. Go to this folder. On Windows, the repo path has spaces — keep the quotes:
   ```powershell
   cd "C:\path\to\hotelReviews\web"
   ```
3. Install dependencies (first time only, or whenever `package.json` changes):
   ```bash
   npm install
   ```
4. Start the dev server:
   ```bash
   npm run dev
   ```
5. You should see something like:
   ```
   VITE vX.X.X  ready in XXX ms
   ➜  Local:   http://localhost:5173/
   ```
6. Open **http://localhost:5173** in your browser.

Other notes:

- The dev server has hot-reload — edits to any file under `src/` show up immediately, no restart needed.
- To stop it: click the terminal running `npm run dev` and press `Ctrl+C`.
- If port 5173 is already in use, Vite automatically picks the next free port (5174, 5175, …) — check the terminal output for the actual URL.
- If a step fails, the exact error text in the terminal is what matters — copy it verbatim when asking for help.

## Other commands

```bash
npm run build      # production build -> web/dist/ (also catches type/import errors)
npm run lint        # oxlint — checks code style issues
npm run preview     # serves the production build locally, to sanity-check it before deploying
```

## Project structure

```
src/
  main.jsx              # entry point, wraps the app in BrowserRouter
  App.jsx                # route definitions
  components/            # Layout, Header, Logo — shared across every page
  data/mockData.js        # all mock data lives here; swap for a real API once the backend exists
  pages/
    Home.jsx               # "/" — marketing/methodology page
    Pricing.jsx             # "/pricing"
    Login.jsx               # "/login" — form only, no real auth yet
    Dashboard/               # "/dashboard" — the core analytics screen (insight card, health cards,
                              #   gap matrix, monthly trend, leaderboard, comments, vulnerabilities)
    Chat/                    # "/chat" — conversational agent (keyword-matched canned replies for now)
    Quadrant/                 # "/quadrant" — price vs. quality scatter plot + hotel detail drawer
```

## Notes

- Every number shown (scores, rankings, regional average, chat replies) is derived from
  `src/data/mockData.js` — nothing is hardcoded twice, so changing a value there updates every
  component that uses it.
- No backend yet. See the project root's `README.md` for the Python data pipeline this app will
  eventually consume.
