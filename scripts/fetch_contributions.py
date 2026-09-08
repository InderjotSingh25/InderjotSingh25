#!/usr/bin/env python3
"""
fetch_contributions.py

GitHub serves your contribution calendar as a public HTML fragment at
https://github.com/users/<username>/contributions — the same fragment
the profile page itself uses. No GraphQL API, no personal access token.

Fetches it, parses the day cells with BeautifulSoup, and writes
data/contributions.json with raw days plus derived stats (current
streak, longest streak, best day, monthly totals).
"""
import json
import os
import sys
from datetime import datetime, date
from collections import defaultdict

import requests
from bs4 import BeautifulSoup

USERNAME = "InderjotSingh25"
URL = f"https://github.com/users/{USERNAME}/contributions"
OUT_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "contributions.json")


def fetch_html(username):
    url = f"https://github.com/users/{username}/contributions"
    resp = requests.get(url, headers={"User-Agent": "profile-art-bot"}, timeout=20)
    resp.raise_for_status()
    return resp.text


def parse_days(html):
    soup = BeautifulSoup(html, "html.parser")
    days = []

    # GitHub's markup has shifted between <td class="ContributionCalendar-day">
    # and <table>-less <div>/<tool-tip> layouts over time — handle both by
    # looking for any element with a data-date attribute and a contribution
    # count somewhere nearby.
    cells = soup.select("td[data-date], td.ContributionCalendar-day")
    if not cells:
        cells = soup.select("[data-date]")

    for cell in cells:
        d = cell.get("data-date")
        if not d:
            continue
        level = cell.get("data-level")
        count = 0
        if level is not None:
            level = int(level)
        else:
            level = 0

        # Try to recover an actual count from tooltip/aria text, e.g.
        # "5 contributions on January 1st."
        text = cell.get("aria-label") or cell.get("title") or ""
        import re
        m = re.search(r"(\d+)\s+contribution", text)
        if m:
            count = int(m.group(1))
        elif "No contributions" in text:
            count = 0

        days.append({"date": d, "count": count, "level": level})

    days.sort(key=lambda x: x["date"])
    return days


def derive_stats(days):
    if not days:
        return {}

    total = sum(d["count"] for d in days)
    best = max(days, key=lambda d: d["count"]) if days else None

    # current streak: consecutive days ending today/most recent with count>0
    current_streak = 0
    for d in reversed(days):
        if d["count"] > 0:
            current_streak += 1
        else:
            break

    longest_streak = 0
    running = 0
    for d in days:
        if d["count"] > 0:
            running += 1
            longest_streak = max(longest_streak, running)
        else:
            running = 0

    monthly = defaultdict(int)
    for d in days:
        month = d["date"][:7]  # YYYY-MM
        monthly[month] += d["count"]

    return {
        "total_last_year": total,
        "current_streak": current_streak,
        "longest_streak": longest_streak,
        "best_day": {"date": best["date"], "count": best["count"]} if best else None,
        "monthly_totals": dict(sorted(monthly.items())),
        "generated_at": datetime.utcnow().isoformat() + "Z",
    }


def main():
    username = sys.argv[1] if len(sys.argv) > 1 else USERNAME
    print(f"[fetch_contributions] fetching {username}...")
    html = fetch_html(username)
    days = parse_days(html)
    stats = derive_stats(days)

    out = {"username": username, "days": days, "stats": stats}
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w") as f:
        json.dump(out, f, indent=2)

    print(f"[fetch_contributions] wrote {OUT_PATH}  "
          f"({len(days)} days, {stats.get('total_last_year', 0)} contributions)")


if __name__ == "__main__":
    main()
