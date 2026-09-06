#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_text.py

activity_archive.json から、検索エンジンやAIクローラー向けの
テキスト中心の静的ページ (record-text.html) を生成するスクリプト。

record.html は JavaScript でカードを描画しているため、
JS を実行しないクローラーには中身が空に見える。
このスクリプトが作る record-text.html は、同じデータを
最初からプレーンなHTMLとして書き出したもので、JSなしで全文が読める。

使い方:
    python3 build_text.py
    (activity_archive.json を更新するたびに実行し直してください)

出力:
    public/record-text.html
    ※ Cloudflare Workers Static Assets のデフォルト設定では
      /record-text でこのファイルがそのまま表示されます。
"""
import json
import html
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(BASE_DIR, "activity_archive.json")
OUT = os.path.join(BASE_DIR, "record-text.html")

LEVEL_LABELS = {
    "実施済": "実施済",
    "改善・対応予定": "検討・対応予定",
    "検討を引き出した": "検討・対応予定",
    "研究段階": "研究段階",
}


def level_label(raw):
    if not raw:
        return "確認中"
    return LEVEL_LABELS.get(raw, raw)


def esc(s):
    return html.escape(s or "", quote=True)


def record_html(r):
    meeting = r.get("meeting_type") or ""
    committee = r.get("committee") or ""
    meeting_label = f"{meeting}（{committee}）" if committee else meeting
    tags = "、".join(r.get("tags") or [])
    category = r.get("category") or ""
    q_text = r.get("proposal") or r.get("issue") or ""
    source_url = r.get("source_url") or ""
    source_line = (
        f'<p><a href="{esc(source_url)}" rel="noopener">会議録を見る（外部リンク）</a></p>'
        if source_url
        else ""
    )
    follow_up = r.get("follow_up") or ""
    follow_up_line = f"<p><strong>その後：</strong>{esc(follow_up)}</p>" if follow_up else ""
    category_line = f"<p><strong>分類：</strong>{esc(category)}</p>" if category else ""

    return f"""
<article>
  <h2>{esc(r.get('question_topic'))}</h2>
  <p><strong>日付：</strong>{esc(r.get('date'))}
     <strong>会議：</strong>{esc(r.get('session_name'))}　{esc(meeting_label)}
     <strong>対応状況：</strong>{esc(level_label(r.get('result_level')))}</p>
  {category_line}
  <p><strong>テーマ：</strong>{esc(tags)}</p>
  <p><strong>Q：</strong>{esc(q_text)}</p>
  <p><strong>A：</strong>{esc(r.get('answer_summary'))}</p>
  {follow_up_line}
  {source_line}
</article>
""".strip()


def main():
    with open(SRC, encoding="utf-8") as f:
        records = json.load(f)

    # 新しい日付が先に来るよう並び替え
    records = sorted(records, key=lambda r: r.get("date") or "", reverse=True)

    body = "\n<hr>\n".join(record_html(r) for r in records)

    page = f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>議会活動の記録（テキスト版）｜出雲けいこ</title>
<meta name="description" content="出雲けいこ（さいたま市議会議員）の議会活動の記録を、検索エンジン・AI向けにテキストのみで一覧にしたページです。通常の閲覧には record.html をご利用ください。">
<link rel="canonical" href="record.html">
<style>
  body {{ font-family: "Noto Sans JP", "Hiragino Sans", "Yu Gothic", sans-serif; line-height: 1.8; max-width: 760px; margin: 0 auto; padding: 32px 20px 80px; color: #22302A; }}
  h1 {{ font-size: 22px; }}
  h2 {{ font-size: 17px; margin: 0 0 8px; }}
  article {{ margin: 0 0 28px; }}
  hr {{ border: none; border-top: 1px solid #E1E9E2; margin: 0 0 28px; }}
  a {{ color: #2C6B4E; }}
</style>
</head>
<body>
<h1>議会活動の記録（テキスト版・全{len(records)}件）</h1>
<p>これは <a href="record.html">議会活動の記録</a> と同じ内容を、検索エンジンやAIが読み取りやすいよう、プレーンなテキストとして書き出したページです。絞り込みや検索をしたい場合は、通常のページをご利用ください。</p>
<hr>
{body}
</body>
</html>
"""
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(page)

    print(f"generated: {OUT} ({len(records)} records)")


if __name__ == "__main__":
    main()
