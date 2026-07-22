# EKAM — One Customer Graph Prototype

A working prototype for the "One Customer Graph" pitch:

- **Steward Dashboard** — the banker/admin-facing view of a household managed under the new operating model.
- **Backend / P&L Engine** — how the household P&L, transfer pricing, and impact numbers work underneath it.

## Files

```
ekam-prototype/
├── app.py                     # the Streamlit app
├── requirements.txt           # Python dependencies
├── .streamlit/config.toml     # app theme
└── .gitignore
```

## Option A — Run locally (fastest way to check it works)

```bash
pip install -r requirements.txt
streamlit run app.py
```

It opens automatically at `http://localhost:8501`.

## Option B — Host it for free on Streamlit Community Cloud

**Step 1 — Push this folder to GitHub**

```bash
cd ekam-prototype
git init
git add .
git commit -m "EKAM prototype"
```

Then create a new empty repo on GitHub (no README/license, so it stays empty), and push:

```bash
git remote add origin https://github.com/<your-username>/<repo-name>.git
git branch -M main
git push -u origin main
```

(Or just create the repo on github.com, then drag-and-drop all these files/folders into it through the web UI — no git command line needed. Make sure `.streamlit/config.toml` keeps its folder structure when uploading.)

**Step 2 — Deploy on Streamlit Cloud**

1. Go to **share.streamlit.io** and sign in with your GitHub account.
2. Click **"New app"**.
3. Select your repository, branch (`main`), and main file path (`app.py`).
4. Click **Deploy**.

Streamlit Cloud will install `requirements.txt` automatically and give you a public URL (e.g. `https://your-app-name.streamlit.app`) within a minute or two. That's the link you can drop straight into your submission or open live during the pitch.

**Step 3 — Redeploying after changes**

Any time you push a new commit to the `main` branch, Streamlit Cloud auto-redeploys — no extra steps needed.

## Notes for the demo

- All data (households, feed items, P&L figures) is mock/illustrative — swap the numbers in `app.py` for your deck's real figures before presenting, especially the impact calculator's baseline assumptions near the bottom of the "Backend" tab.
- The three sample households map to your deck's Mass / Complex / Private coverage tiers, so you can walk judges through the same continuum live.
