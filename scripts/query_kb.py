#!/usr/bin/env python3
"""千星奇域综合指南知识库检索器。

从官方 textMap.json 中检索与查询词相关的文档片段，输出带文档 ID 的原文证据。
依赖：仅 Python 标准库。

用法:
    python query_kb.py "是否支持2d游戏"
    python query_kb.py "lua 脚本 2D" --limit 5 --context 200
    python query_kb.py "可调色方块" --doc-id mhbgxf0nynww
"""

import argparse
import json
import os
import re
import sys

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEXTMAP_PATH = os.path.join(SKILL_DIR, "references", "textMap.json")
CATALOG_PATH = os.path.join(SKILL_DIR, "references", "catalog.json")


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def build_title_map(catalog):
    """构建 doc_id -> 标题路径 的映射。"""
    titles = {}

    def walk(nodes, parents):
        for node in nodes or []:
            name = node.get("title", "")
            path = parents + [name]
            doc_id = node.get("real_id") or node.get("path_id")
            if doc_id:
                titles[doc_id] = " > ".join(path)
            walk(node.get("children"), path)

    walk(catalog, [])
    return titles


def tokenize(query):
    """中文按 2-4 字滑窗切分，英文/数字按词切分，用于模糊匹配。"""
    parts = re.findall(r"[A-Za-z][A-Za-z0-9_.+-]*|\d+", query.lower())
    chinese = re.findall(r"[\u4e00-\u9fff]+", query)
    for seg in chinese:
        if len(seg) <= 4:
            parts.append(seg)
        else:
            for n in (4, 3, 2):
                for i in range(len(seg) - n + 1):
                    parts.append(seg[i:i + n])
    return sorted(set(p for p in parts if len(p) >= 2), key=len, reverse=True)


def search(textmap, titles, query, limit, context, doc_id=None, doc_title=None):
    tokens = tokenize(query)
    if not tokens:
        return []

    results = []
    for key, text in textmap.items():
        if doc_id and key != doc_id:
            continue
        if doc_title and doc_title not in titles.get(key, ""):
            continue
        lower = text.lower()
        hits = []
        for tok in tokens:
            start = 0
            count = 0
            while True:
                pos = lower.find(tok.lower(), start)
                if pos < 0 or count >= 8:
                    break
                hits.append((pos, tok))
                start = pos + len(tok)
                count += 1
        if not hits:
            continue

        # 按位置聚类，合并重叠窗口
        hits.sort()
        windows = []
        for pos, tok in hits:
            lo, hi = max(0, pos - context), min(len(text), pos + context + len(tok))
            if windows and lo <= windows[-1][1]:
                windows[-1][1] = max(windows[-1][1], hi)
                windows[-1][2] += 1
            else:
                windows.append([lo, hi, 1])
        windows.sort(key=lambda w: -w[2])
        score = sum(w[2] * w[2] for w in windows[:5])

        snippets = []
        for lo, hi, _ in windows[:4]:
            snippet = text[lo:hi].replace("\n", " ")
            snippets.append(("…" if lo > 0 else "") + snippet + ("…" if hi < len(text) else ""))

        results.append({
            "doc_id": key,
            "title": titles.get(key, "(未命名文档)"),
            "score": score,
            "match_count": len(hits),
            "snippets": snippets,
        })

    results.sort(key=lambda r: -r["score"])
    return results[:limit]


def main():
    parser = argparse.ArgumentParser(description="检索千星奇域官方综合指南知识库")
    parser.add_argument("query", help="自然语言查询词")
    parser.add_argument("--limit", type=int, default=5, help="返回文档数，默认 5")
    parser.add_argument("--context", type=int, default=180, help="片段上下文字符数，默认 180")
    parser.add_argument("--doc-id", help="限定在指定 doc_id 内检索")
    parser.add_argument("--doc-title", help="按标题关键字限定文档范围")
    parser.add_argument("--list-docs", action="store_true", help="列出所有文档 ID 与标题")
    parser.add_argument("--raw-doc", help="输出指定 doc_id 的完整正文")
    args = parser.parse_args()

    textmap = load_json(TEXTMAP_PATH)
    catalog = load_json(CATALOG_PATH)
    titles = build_title_map(catalog)

    if args.list_docs:
        for doc_id, title in sorted(titles.items(), key=lambda x: x[1]):
            print(f"{doc_id}\t{title}")
        return

    if args.raw_doc:
        text = textmap.get(args.raw_doc)
        if text is None:
            print(f"未找到文档: {args.raw_doc}", file=sys.stderr)
            sys.exit(1)
        print(f"# {titles.get(args.raw_doc, '')} [{args.raw_doc}]\n")
        print(text)
        return

    results = search(textmap, titles, args.query, args.limit, args.context,
                     args.doc_id, args.doc_title)
    if not results:
        print("知识库中未检索到相关内容。请尝试更换关键词，或确认该能力是否在官方文档覆盖范围内。")
        return

    print(f"检索词: {args.query}\n命中文档: {len(results)}\n")
    for i, r in enumerate(results, 1):
        print(f"--- [{i}] {r['title']} (doc_id: {r['doc_id']}, 匹配分: {r['score']}) ---")
        for snippet in r["snippets"]:
            print(snippet)
        print()


if __name__ == "__main__":
    main()
