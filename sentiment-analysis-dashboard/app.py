"""Flask app for a small, self-contained social sentiment dashboard."""

from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path
import csv
import io
import re

from flask import Flask, jsonify, render_template, request

app = Flask(__name__)

POSITIVE = {
    "amazing", "awesome", "best", "brilliant", "calm", "celebrate", "enjoy",
    "excellent", "excited", "fantastic", "good", "great", "happy", "helpful",
    "impressive", "love", "loved", "lovely", "perfect", "recommend", "smooth",
    "success", "thank", "thanks", "useful", "welcome", "wonderful", "wow",
}
NEGATIVE = {
    "angry", "awful", "bad", "broken", "confusing", "disappointed", "disappointing",
    "disaster", "hate", "hated", "horrible", "late", "lost", "missing", "poor",
    "problem", "slow", "terrible", "unhelpful", "unhappy", "wait", "worse", "worst",
}

SEED_POSTS = [
    ("X", "The new update is brilliant. Everything feels so much smoother!", "@mira_codes", 2),
    ("Instagram", "Finally found a café that gets the little things right ☕", "@weekendwanders", 8),
    ("Reddit", "Support was helpful and fixed my issue in minutes. Thank you!", "u/packetgarden", 16),
    ("X", "Been waiting all morning and the app is still broken. Disappointing.", "@jules_online", 22),
    ("TikTok", "This is the best tutorial I have seen all week ✨", "@learnwithlee", 30),
    ("Reddit", "The latest change is confusing and the page loads painfully slow.", "u/quietbrowser", 39),
    ("Instagram", "Love how easy this was to set up. Great work!", "@sana.makes", 48),
    ("X", "Order arrived late and support was unhelpful. Not happy.", "@rohanreviews", 61),
    ("TikTok", "Amazing results, honestly exceeded every expectation 🙌", "@dailyfinds", 73),
    ("Reddit", "It works fine, but the new layout takes some getting used to.", "u/slowread", 88),
    ("Instagram", "Wonderful experience from start to finish 💛", "@nina.notes", 103),
    ("X", "Another outage. This is getting worse every week.", "@bytebloom", 119),
    ("TikTok", "Such a useful feature! I have already recommended it to friends.", "@tinyreviews", 138),
    ("Reddit", "Pretty average so far. Nothing bad, nothing especially good.", "u/coppercloud", 161),
    ("Instagram", "The quality is awful compared with what was promised.", "@mondaymood", 187),
    ("X", "So excited about this launch. The team did an excellent job!", "@elliebuilds", 210),
    ("TikTok", "Waited ages for this? Not worth it, honestly.", "@clipcritic", 235),
    ("Reddit", "Great documentation and a smooth first run. Thanks!", "u/fernlogic", 263),
]

def analyze_text(text):
    words = re.findall(r"[a-z']+", text.lower())
    score = sum(word in POSITIVE for word in words) - sum(word in NEGATIVE for word in words)
    sentiment = "Positive" if score > 0 else "Negative" if score < 0 else "Neutral"
    return sentiment, score


POSTS = []
for index, (platform, text, author, minutes_ago) in enumerate(SEED_POSTS, start=1):
    sentiment, score = analyze_text(text)
    POSTS.append({
        "id": index,
        "platform": platform,
        "text": text,
        "author": author,
        "minutes_ago": minutes_ago,
        "created_at": (datetime.now() - timedelta(minutes=minutes_ago)).isoformat(timespec="minutes"),
        "sentiment": sentiment,
        "score": score,
    })


def filtered_posts():
    platform = request.args.get("platform", "All")
    sentiment = request.args.get("sentiment", "All")
    items = POSTS
    if platform != "All":
        items = [post for post in items if post["platform"] == platform]
    if sentiment != "All":
        items = [post for post in items if post["sentiment"] == sentiment]
    return items


@app.get("/")
def dashboard():
    return render_template("index.html")


@app.get("/api/summary")
def summary():
    posts = filtered_posts()
    counts = Counter(post["sentiment"] for post in posts)
    platforms = sorted({post["platform"] for post in POSTS})
    return jsonify({
        "total": len(posts),
        "positive": counts["Positive"],
        "neutral": counts["Neutral"],
        "negative": counts["Negative"],
        "platforms": platforms,
        "posts": posts,
        "all_posts": len(POSTS),
        "positive_rate": round(counts["Positive"] / len(posts) * 100) if posts else 0,
    })


@app.post("/api/analyze")
def add_post():
    payload = request.get_json(silent=True) or {}
    text = str(payload.get("text", "")).strip()
    platform = str(payload.get("platform", "X")).strip()
    author = str(payload.get("author", "@you")).strip()[:40]
    if not text:
        return jsonify({"error": "Write a post before analyzing it."}), 400
    if platform not in {"X", "Instagram", "Reddit", "TikTok"}:
        return jsonify({"error": "Choose a supported platform."}), 400
    sentiment, score = analyze_text(text)
    post = {
        "id": max((item["id"] for item in POSTS), default=0) + 1,
        "platform": platform,
        "text": text[:500],
        "author": author or "@you",
        "minutes_ago": 0,
        "created_at": datetime.now().isoformat(timespec="minutes"),
        "sentiment": sentiment,
        "score": score,
    }
    POSTS.insert(0, post)
    return jsonify({"post": post, "summary": summary().get_json()}), 201


@app.get("/api/export.csv")
def export_csv():
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=["created_at", "platform", "author", "sentiment", "score", "text"])
    writer.writeheader()
    writer.writerows({key: post[key] for key in writer.fieldnames} for post in filtered_posts())
    return app.response_class(
        output.getvalue(), mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=sentiment-posts.csv"},
    )


if __name__ == "__main__":
    app.run(debug=True)
