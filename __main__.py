"""stocksight v2 CLI。

子命令：
    news <symbol>         拉真实新闻清单（akshare A 股 / yfinance 美股）
    analyze <symbol>      拉新闻 + 多 backend 情感分析 → 聚合信号
    sentiment <text>      单段文本情感分析（任意输入）
    list-backends         列支持的情感分析 backend

示例：

    python -m stocksight news 600519                  # 茅台 A 股新闻
    python -m stocksight news AAPL                    # 苹果美股新闻
    python -m stocksight analyze TSLA --backend vader
    python -m stocksight analyze 000001 --backend snownlp
    python -m stocksight sentiment "苹果发布新品大获成功" --backend snownlp
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# 让 scripts/ 内的模块可 import
sys.path.insert(0, str(Path(__file__).resolve().parent / "scripts"))

from news_sources import NewsSourceError, fetch_news  # noqa: E402
from sentiment import aggregate, analyze, analyze_batch  # noqa: E402


def cmd_news(args) -> int:
    try:
        items = fetch_news(args.symbol, limit=args.limit, source=args.source)
    except NewsSourceError as e:
        sys.stderr.write(f"[error] {e}\n")
        return 1
    if not items:
        sys.stderr.write(f"[warn] 没拿到 {args.symbol} 的新闻\n")
    payload = [it.to_dict() for it in items]
    text = json.dumps(payload, ensure_ascii=False, indent=2)
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
        sys.stderr.write(f"[ok] {len(items)} 条已写入 {args.output}\n")
    else:
        print(text)
    return 0


def cmd_analyze(args) -> int:
    try:
        items = fetch_news(args.symbol, limit=args.limit, source=args.source)
    except NewsSourceError as e:
        sys.stderr.write(f"[error] {e}\n")
        return 1
    if not items:
        sys.stderr.write(f"[warn] 没新闻可分析\n")
        return 0

    # 用标题 + 摘要拼起来做情感分析
    texts = [(it.title + "。" + it.summary).strip() for it in items]
    scores = analyze_batch(texts, backend=args.backend)
    agg = aggregate(scores)

    payload = {
        "symbol": args.symbol,
        "n_items": len(items),
        "backend": args.backend,
        "aggregate": agg,
        "items": [
            {
                "news": items[i].to_dict(),
                "sentiment": scores[i].to_dict(),
            }
            for i in range(len(items))
        ],
    }
    text = json.dumps(payload, ensure_ascii=False, indent=2)
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
        sys.stderr.write(
            f"[ok] {len(items)} 条新闻已分析，aggregate signal={agg['signal']} "
            f"(mean_polarity={agg['mean_polarity']}) 写入 {args.output}\n"
        )
    else:
        print(text)
    return 0


def cmd_sentiment(args) -> int:
    score = analyze(args.text, backend=args.backend)
    print(json.dumps(score.to_dict(), ensure_ascii=False, indent=2))
    return 0


def cmd_list_backends(args) -> int:
    rows = [
        ("vader",    "英文规则+词典，速度快",          "vaderSentiment"),
        ("textblob", "英文简单 polarity/subjectivity", "textblob"),
        ("snownlp",  "中文情感分析（默认中文路由）",   "snownlp"),
        ("finbert",  "ProsusAI/finbert 英文金融预训练", "transformers + torch（~400MB）"),
        ("auto",     "按语言自动路由（默认）",          "—"),
    ]
    print(f"{'backend':<12} {'描述':<35} {'依赖'}")
    print("-" * 90)
    for b, d, dep in rows:
        print(f"{b:<12} {d:<35} {dep}")
    return 0


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="stocksight", description="股市情感分析 CLI")
    sub = p.add_subparsers(dest="cmd", required=True)

    common_source = ["auto", "akshare", "yfinance", "newsapi"]
    common_backend = ["auto", "vader", "textblob", "snownlp", "finbert"]

    sp = sub.add_parser("news", help="拉真实新闻清单")
    sp.add_argument("symbol", help="A 股代码（如 600519）或美股代码（如 AAPL）")
    sp.add_argument("--limit", type=int, default=20)
    sp.add_argument("--source", default="auto", choices=common_source)
    sp.add_argument("-o", "--output")
    sp.set_defaults(func=cmd_news)

    sp = sub.add_parser("analyze", help="新闻 + 情感分析 → 聚合信号")
    sp.add_argument("symbol")
    sp.add_argument("--limit", type=int, default=20)
    sp.add_argument("--source", default="auto", choices=common_source)
    sp.add_argument("--backend", default="auto", choices=common_backend)
    sp.add_argument("-o", "--output")
    sp.set_defaults(func=cmd_analyze)

    sp = sub.add_parser("sentiment", help="单段文本情感分析")
    sp.add_argument("text")
    sp.add_argument("--backend", default="auto", choices=common_backend)
    sp.set_defaults(func=cmd_sentiment)

    sp = sub.add_parser("list-backends", help="列支持的 backend")
    sp.set_defaults(func=cmd_list_backends)

    return p


def main(argv=None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
