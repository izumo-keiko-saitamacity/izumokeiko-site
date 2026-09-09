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
    "対応予定": "対応予定",
    "検討へ": "検討へ",
    "研究段階": "研究段階",
    "提案のみ": "提案のみ",
    "適正確認": "適正確認",
    # 旧・3段階運用からの互換用（古いデータが残っていた場合のフォールバック）
    "改善・対応予定": "対応予定",
    "検討を引き出した": "検討へ",
}


def level_label(raw):
    if not raw:
        return "確認中"
    return LEVEL_LABELS.get(raw, raw)


def esc(s):
    return html.escape(s or "", quote=True)


def evidence_html(ev):
    """follow_up_evidence を根拠ラベル＋リンクとして描画する。

    表示ラベルはデータに保存せず、council_ref / evidence_url の
    有無からその都度計算する（follow_up_定義.md の対応表のとおり）。
    council_ref（kaigiroku.net の会議録URL）は文字列として
    リンクにするだけで、Claude 側から取得・閲覧は行わない。
    """
    if not ev:
        return ""

    council_ref = ev.get("council_ref") or ""
    evidence_url = ev.get("evidence_url") or ""
    evidence_title = ev.get("evidence_title") or ""
    verified_date = ev.get("verified_date") or ""

    if council_ref and evidence_url:
        label = "議会・行政資料で確認"
    elif council_ref:
        label = "議会で確認"
    elif evidence_url:
        label = "行政資料で確認"
    else:
        return ""

    links = []
    if evidence_url:
        title = evidence_title or "行政資料"
        date_note = f"／{esc(verified_date)}確認" if verified_date else ""
        links.append(
            f'<a href="{esc(evidence_url)}" target="_blank" rel="noopener">'
            f"{esc(title)}（外部リンク{date_note}）</a>"
        )
    if council_ref:
        links.append(
            f'<a href="{esc(council_ref)}" target="_blank" rel="noopener">'
            "会議録で確認（外部リンク）</a>"
        )
    links_html = "　".join(links)

    return f'<p><strong>根拠：</strong>{label}　{links_html}</p>'


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
    evidence_line = evidence_html(r.get("follow_up_evidence"))
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
  {evidence_line}
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
