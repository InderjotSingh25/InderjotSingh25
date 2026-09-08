#!/usr/bin/env python3
"""
render_heatmap_svg.py

Renders data/contributions.json as the classic 53-week x 7-day
contribution calendar: rounded, colored boxes on a GitHub-ish green
ramp. Reveals once with a diagonal, line-after-line slide-down (CSS
keyframes that play on load, then freeze — no looping), plus a
Less->More legend and a stats footer.

Output: contrib-heatmap.svg
"""
import json
import os
from datetime import datetime, timedelta

PALETTE = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353", "#69f0a0"]
#          none    -> ...................................... -> brightest (level 5 is a neon top end)

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "contributions.json")
OUT_PATH = "contrib-heatmap.svg"

CELL = 11
GAP = 3
RADIUS = 2
LEFT_PAD = 28   # room for day labels
TOP_PAD = 20    # room for month labels
LEGEND_H = 26
FOOTER_H = 22

MONTH_LABELS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def level_from_count(count, thresholds=(0, 2, 5, 10, 20)):
    if count <= thresholds[0]:
        return 0
    for i, t in enumerate(thresholds[1:], start=1):
        if count < t:
            return i
    return 5


def build_weeks(days):
    """Arrange days into 53 columns x 7 rows (Sun-Sat), most recent last."""
    by_date = {d["date"]: d for d in days}
    if not days:
        return [], None, None

    end = datetime.strptime(days[-1]["date"], "%Y-%m-%d").date()
    start = end - timedelta(days=53 * 7 - 1)
    # snap start back to a Sunday
    start -= timedelta(days=(start.weekday() + 1) % 7)

    weeks = []
    cur = start
    week = []
    while cur <= end:
        rec = by_date.get(cur.isoformat())
        count = rec["count"] if rec else 0
        level = rec["level"] if rec and "level" in rec else level_from_count(count)
        week.append({"date": cur.isoformat(), "count": count, "level": level})
        if cur.weekday() == 5:  # Saturday -> close out the week column
            weeks.append(week)
            week = []
        cur += timedelta(days=1)
    if week:
        weeks.append(week)

    return weeks, start, end


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def build_svg(weeks, stats, username):
    cols = len(weeks)
    width = LEFT_PAD + cols * (CELL + GAP)
    height = TOP_PAD + 7 * (CELL + GAP) + LEGEND_H + FOOTER_H

    parts = []
    parts.append(f'<svg xmlns="http://www.w3.org/2000/svg" '
                  f'viewBox="0 0 {width} {height}" width="{width}" height="{height}">')
    parts.append('<rect width="100%" height="100%" fill="transparent"/>')
    parts.append('<style>'
                  'text{font-family:"SFMono-Regular",Consolas,"Liberation Mono",Menlo,monospace;'
                  'font-size:10px;fill:#8b949e;}'
                  '.cell{opacity:0;transform:translate(-6px,-6px);'
                  'animation:slideIn 0.5s cubic-bezier(.2,0,.1,1) forwards;}'
                  '@keyframes slideIn{to{opacity:1;transform:translate(0,0);}}'
                  '</style>')

    # month labels: mark the first week column of each new month
    last_month = None
    for wi, week in enumerate(weeks):
        first_day = week[0]["date"]
        month = int(first_day[5:7])
        if month != last_month:
            x = LEFT_PAD + wi * (CELL + GAP)
            parts.append(f'<text x="{x}" y="{TOP_PAD - 6}">{MONTH_LABELS[month - 1]}</text>')
            last_month = month

    # day-of-week labels (Mon/Wed/Fri, GitHub-style)
    dow_labels = {1: "Mon", 3: "Wed", 5: "Fri"}
    for row, label in dow_labels.items():
        y = TOP_PAD + row * (CELL + GAP) + CELL - 2
        parts.append(f'<text x="0" y="{y}">{label}</text>')

    # cells, staggered diagonally: delay grows with column + row
    for wi, week in enumerate(weeks):
        for di, day in enumerate(week):
            x = LEFT_PAD + wi * (CELL + GAP)
            y = TOP_PAD + di * (CELL + GAP)
            color = PALETTE[day["level"]]
            delay = (wi * 0.012) + (di * 0.02)
            title = f'{day["count"]} contributions on {day["date"]}'
            parts.append(
                f'<rect class="cell" x="{x}" y="{y}" width="{CELL}" height="{CELL}" '
                f'rx="{RADIUS}" ry="{RADIUS}" fill="{color}" '
                f'style="animation-delay:{delay:.3f}s"><title>{esc(title)}</title></rect>'
            )

    # legend: Less -> More
    legend_y = TOP_PAD + 7 * (CELL + GAP) + 16
    lx = LEFT_PAD
    parts.append(f'<text x="{lx}" y="{legend_y + 9}">Less</text>')
    lx += 32
    for level, color in enumerate(PALETTE):
        parts.append(f'<rect x="{lx}" y="{legend_y}" width="{CELL}" height="{CELL}" '
                      f'rx="{RADIUS}" ry="{RADIUS}" fill="{color}"/>')
        lx += CELL + GAP
    parts.append(f'<text x="{lx + 4}" y="{legend_y + 9}">More</text>')

    # stats footer
    total = stats.get("total_last_year", 0)
    streak = stats.get("current_streak", 0)
    longest = stats.get("longest_streak", 0)
    footer = f"{total:,} contributions in the last year  ·  current streak {streak}  ·  longest streak {longest}"
    parts.append(f'<text x="{LEFT_PAD}" y="{height - 6}" fill="#c9d1d9">{esc(footer)}</text>')

    parts.append('</svg>')
    return "\n".join(parts)


def main():
    if not os.path.exists(DATA_PATH):
        print(f"error: {DATA_PATH} not found — run fetch_contributions.py first")
        return

    with open(DATA_PATH) as f:
        data = json.load(f)

    weeks, start, end = build_weeks(data.get("days", []))
    svg = build_svg(weeks, data.get("stats", {}), data.get("username", ""))

    with open(OUT_PATH, "w") as f:
        f.write(svg)
    print(f"[render_heatmap_svg] wrote {OUT_PATH}  ({len(weeks)} weeks)")


if __name__ == "__main__":
    main()
