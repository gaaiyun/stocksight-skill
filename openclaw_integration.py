#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
stocksight OpenClaw Integration
股市情感分析 OpenClaw 集成接口

Usage in OpenClaw:
    python openclaw_integration.py --action analyze --symbol TSLA
    python openclaw_integration.py --action predict --symbol AAPL
"""

import sys
import json
import argparse
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from scripts.stocksight import (
    analyze_stock_sentiment,
    predict_price_movement,
    load_sentiment_history,
    load_config
)


def format_markdown_report(symbol, sentiment_data, prediction_data=None):
    """Format results as markdown for OpenClaw"""
    md = []
    md.append(f"## 📊 Stocksight 分析：{symbol}\n")
    
    if sentiment_data:
        sentiment = sentiment_data['overall_sentiment']
        md.append("### 💭 情感分析\n")
        md.append(f"- **总体情感**: {sentiment['label'].upper()}")
        md.append(f"- **极性值**: {sentiment['polarity']}")
        md.append(f"- **主观性**: {sentiment['subjectivity']}")
        md.append(f"- **分析文章数**: {sentiment_data['articles_analyzed']}\n")
        
        dist = sentiment_data['label_distribution']
        md.append("### 📈 情感分布\n")
        md.append(f"- ✅ 正面：{dist['positive']}")
        md.append(f"- ➖ 中性：{dist['neutral']}")
        md.append(f"- ❌ 负面：{dist['negative']}\n")
        
        md.append("### 📝 关键新闻\n")
        for i, article in enumerate(sentiment_data['articles'][:3], 1):
            emoji = "✅" if article['label'] == 'positive' else "❌" if article['label'] == 'negative' else "➖"
            md.append(f"{i}. {emoji} **{article['label'].upper()}** - {article['title']}")
    
    if prediction_data:
        pred = prediction_data['prediction']
        arrow = "📈" if pred['direction'] == 'up' else "📉" if pred['direction'] == 'down' else "➡️"
        md.append(f"\n### 🔮 价格预测\n")
        md.append(f"- **方向**: {arrow} {pred['direction'].upper()}")
        md.append(f"- **置信度**: {pred['confidence']*100:.1f}%")
        md.append(f"- **时间范围**: {pred['timeframe']}")
    
    md.append("\n---\n*免责声明：本分析仅供参考，不构成投资建议。*")
    
    return "\n".join(md)


def format_json_response(symbol, sentiment_data, prediction_data=None):
    """Format results as JSON for programmatic use"""
    response = {
        "symbol": symbol,
        "sentiment": sentiment_data,
        "prediction": prediction_data
    }
    return json.dumps(response, indent=2, ensure_ascii=False)


def main():
    parser = argparse.ArgumentParser(description="Stocksight OpenClaw Integration")
    parser.add_argument("--action", "-a", required=True, 
                       choices=['analyze', 'predict', 'news', 'history'],
                       help="Action to perform")
    parser.add_argument("--symbol", "-s", required=True, help="Stock symbol")
    parser.add_argument("--format", "-f", choices=['markdown', 'json'], default='markdown',
                       help="Output format")
    parser.add_argument("--config", "-c", type=str, help="Config file path")
    
    args = parser.parse_args()
    
    # Load config
    config = load_config()
    
    symbol = args.symbol.upper()
    
    try:
        if args.action == 'analyze' or args.action == 'news':
            sentiment_data = analyze_stock_sentiment(symbol, config)
            if not sentiment_data:
                print(f"❌ 无法获取 {symbol} 的情感数据")
                sys.exit(1)
            
            if args.format == 'markdown':
                print(format_markdown_report(symbol, sentiment_data))
            else:
                print(format_json_response(symbol, sentiment_data))
        
        elif args.action == 'predict':
            # Load latest sentiment
            history = load_sentiment_history(symbol)
            if not history:
                # Analyze first if no history
                sentiment_data = analyze_stock_sentiment(symbol, config)
                if not sentiment_data:
                    print(f"❌ 无法获取 {symbol} 的情感数据")
                    sys.exit(1)
            else:
                sentiment_data = history[-1]
            
            prediction = predict_price_movement(symbol, sentiment_data)
            
            if args.format == 'markdown':
                print(format_markdown_report(symbol, sentiment_data, prediction))
            else:
                print(format_json_response(symbol, sentiment_data, prediction))
        
        elif args.action == 'history':
            history = load_sentiment_history(symbol)
            if not history:
                print(f"📭 {symbol} 暂无历史数据")
                sys.exit(0)
            
            if args.format == 'markdown':
                print(f"## 📜 {symbol} 情感历史\n")
                print(f"总记录数：{len(history)}\n")
                print("| 时间 | 情感 | 极性 | 文章数 |")
                print("|------|------|------|--------|")
                for entry in history[-5:]:
                    ts = entry['timestamp'][:16]
                    label = entry['overall_sentiment']['label']
                    polarity = entry['overall_sentiment']['polarity']
                    articles = entry['articles_analyzed']
                    print(f"| {ts} | {label} | {polarity} | {articles} |")
            else:
                print(json.dumps({"symbol": symbol, "history": history}, indent=2, ensure_ascii=False))
    
    except Exception as e:
        print(f"❌ 错误：{e}")
        if args.format == 'json':
            print(json.dumps({"error": str(e)}, ensure_ascii=False))
        sys.exit(1)


if __name__ == "__main__":
    main()
