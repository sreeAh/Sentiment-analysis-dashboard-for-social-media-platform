# Social Pulse — Sentiment Analysis Dashboard

A small Flask dashboard for exploring social media sentiment. It starts with sample posts from X, Instagram, Reddit, and TikTok. You can filter the feed, analyze a post with the built-in word-list classifier, and export the visible posts as CSV.

## Run locally

### Windows PowerShell

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python app.py
```

Then open <http://127.0.0.1:5000>.

### macOS / Linux

```bash
source .venv/bin/activate
python -m pip install -r requirements.txt
python app.py
```

## Notes

- The classifier is a lightweight demo based on positive and negative keywords. It is not a machine-learning model and may miss context, sarcasm, and language nuance.
- Posts are held in memory and reset when the Flask server restarts.
- Sample posts are fictional. Connect an approved platform API and a persistent database before using real social data.
