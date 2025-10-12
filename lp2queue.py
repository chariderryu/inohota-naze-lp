# -*- coding: utf-8 -*-
"""
lp2queue.py
- index.html (.topics-grid .topic-card) から「本日の注目章」を LP と同じローテ（UTC基準, 2025-01-01 起点）で選択
- Tweet テキストを生成し、post_queue.py（TSVキュー）形式で 1 行 PENDING を追記
- 予約時刻は **日本時間（JST）** で指定
- 画像は該当カードの QR を優先、なければ書影 ../lib/inohotanaze_front_cover_small.jpg を使用
"""

from __future__ import annotations
from pathlib import Path
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
import argparse, re, random, csv, os

JST = ZoneInfo("Asia/Tokyo")
DEFAULT_HASHTAGS = ["いのほたなぜ", "英語学", "英語史"]

def load_cards(index_path: Path):
    html = index_path.read_text(encoding="utf-8", errors="ignore")
    cards = []
    for block in re.findall(r'<article[^>]*class="[^"]*topic-card[^"]*"[^>]*>(.*?)</article>', html, flags=re.S|re.I):
        m_title = re.search(r'<h3[^>]*>(.*?)</h3>', block, flags=re.S|re.I)
        m_href  = re.search(r'<a[^>]*href="([^"]+)"', block, flags=re.S|re.I)
        m_qr    = re.search(r'<div[^>]*class="[^"]*topic-qr[^"]*"[^>]*>.*?<img[^>]*src="([^"]+)"', block, flags=re.S|re.I)
        if not (m_title and m_href):
            continue
        title = re.sub(r"\s+", " ", re.sub(r"<.*?>", "", m_title.group(1))).strip()
        url   = m_href.group(1)
        qr_src = m_qr.group(1) if m_qr else None
        cards.append({"title": title, "url": url, "qr": qr_src})
    if not cards:
        raise RuntimeError("No .topic-card found in index.html")
    return cards

def pick_index(count: int) -> int:
    epoch = datetime(2025,1,1, tzinfo=timezone.utc).date()
    today = datetime.now(timezone.utc).date()
    return (today - epoch).days % count

def build_text(title: str, url: str, lp_url: str|None, style: str|None, hashtags):
    h = " ".join(f"#{x}" for x in hashtags if x)
    lp = f"\nLP: {lp_url}" if lp_url else ""
    T = {
        "short": f"今日の #いのほたなぜ 📖「{title}」→ {url} {h}",
        "mid":   f"【今日の注目章】「{title}」\n英語の『なぜ？』を言語学でスッキリ！\n→ {url}\n{h}{lp}",
        "long":  f"『今日の #いのほたなぜ 📖】\n\n英語の『なぜ？』を言語学でスッキリ！\n\n本日のおすすめ：「{title}」\n\n解説と関連動画はこちら→ {url}\n\n{h}\n@ippeiinoue @natsumepub @khelf_keio @helvillian\n{lp}",
    }
    if style in T:
        return T[style]
    import random
    return random.choice([T["short"], T["mid"], T["long"]])

def ensure_dir(p: Path):
    p.parent.mkdir(parents=True, exist_ok=True)

def append_queue(queue_tsv: Path, row: dict):
    rows = []
    if queue_tsv.exists():
        import csv
        with queue_tsv.open("r", encoding="utf-8", newline="") as f:
            r = csv.DictReader(f, delimiter="\t")
            rows.extend(r)
    headers = ["id","scheduled_at_jst","text_path","media_paths","status","tweet_id","posted_at"]
    rows.append({k: row.get(k,"") for k in headers})
    with queue_tsv.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, delimiter="\t", fieldnames=headers)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k,"") for k in headers})

def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--index", default="index.html", help="LP index.html のパス")
    ap.add_argument("--queue", default="queue.tsv", help="post_queue.py が参照する TSV")
    ap.add_argument("--lp-url", help="LP の公開URL（任意）")
    ap.add_argument("--style", choices=["short","mid","long"], help="固定テンプレ")
    ap.add_argument("--hashtags", nargs="*", help="追加ハッシュタグ（#不要）")
    ap.add_argument("--schedule", help="JST 予約: 'now' | 'YYYY-MM-DD HH:MM'（例: 2025-10-13 08:10）", default="now")
    ap.add_argument("--text-dir", default="posts", help="ツイート本文 .txt を保存するディレクトリ")
    ap.add_argument("--id-prefix", default="naze", help="id の接頭辞")
    ap.add_argument("--cover-fallback", default="../lib/inohotanaze_front_cover_small.jpg", help="QRがない場合の代替画像パス")
    args = ap.parse_args()

    index_path = Path(args.index).resolve()
    queue_path = Path(args.queue).resolve()

    cards = load_cards(index_path)
    idx = pick_index(len(cards))
    pick = cards[idx]

    hashtags = DEFAULT_HASHTAGS + (args.hashtags or [])
    text = build_text(pick["title"], pick["url"], args.lp_url, args.style, hashtags)

    text_dir = Path(args.text_dir).resolve()
    ensure_dir(text_dir / "dummy")
    now_jst = datetime.now(JST)
    text_file = text_dir / f"{args.id_prefix}_{now_jst.strftime('%Y%m%d_%H%M')}.txt"
    text_file.write_text(text, encoding="utf-8")

    media_paths = ""
    if pick.get("qr"):
        qr_path = (index_path.parent / pick["qr"]).resolve()
        if qr_path.exists():
            media_paths = str(qr_path)
    if not media_paths:
        cover = (index_path.parent / args.cover_fallback).resolve()
        if cover.exists():
            media_paths = str(cover)

    if args.schedule.strip().lower() == "now":
        sched = now_jst.strftime("%Y-%m-%d %H:%M")
    else:
        try:
            dt = datetime.strptime(args.schedule.strip(), "%Y-%m-%d %H:%M")
            sched = dt.strftime("%Y-%m-%d %H:%M")
        except Exception:
            raise SystemExit("schedule は 'now' か 'YYYY-MM-DD HH:MM'（JST）で指定してください。")

    row = {
        "id": f"{args.id_prefix}-{now_jst.strftime('%Y%m%d-%H%M%S')}-idx{idx}",
        "scheduled_at_jst": sched,
        "text_path": str(text_file),
        "media_paths": media_paths,
        "status": "PENDING",
        "tweet_id": "",
        "posted_at": "",
    }

    append_queue(queue_path, row)
    print("Appended:", row)

if __name__ == "__main__":
    main()
