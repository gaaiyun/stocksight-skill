---
name: stocksight
description: 基于真实财经新闻的股市情感分析工具。抓取 A 股（akshare）/ 美股（yfinance）新闻，用 VADER / TextBlob / SnowNLP / FinBERT 多 backend 做情感分析并聚合成方向信号。当用户要分析某只股票的新闻情绪、给一段财经文本打情感分、或想拿到基于新闻的多空信号时使用。
---

# stocksight - 股市情感分析 Skill

基于新闻情感分析的股市信号工具。抓取真实财经新闻，逐条做情感分析，再聚合成方向信号。

## 功能

- 真实新闻源：A 股走 akshare，美股走 yfinance，可选 NewsAPI，按代码自动路由。
- 多 backend 情感分析：VADER、TextBlob、SnowNLP、FinBERT，按文本语言自动选择。
- 信号聚合：把逐条情感汇总成 mean_polarity + label 分布 + 方向信号（positive / neutral / negative）。

## 使用方法

入口是 `python __main__.py`（在仓库目录内运行），四个子命令：

```bash
# 拉真实新闻清单
python __main__.py news 600519                 # 茅台 A 股新闻
python __main__.py news AAPL                    # 苹果美股新闻

# 新闻 + 情感分析 → 聚合信号
python __main__.py analyze 600519 --backend snownlp
python __main__.py analyze TSLA --backend finbert

# 单段文本情感分析
python __main__.py sentiment "苹果发布新品大获成功" --backend snownlp

# 列出支持的情感分析 backend
python __main__.py list-backends
```

`--backend` 默认 `auto`，按文本语言路由（中文→SnowNLP，英文→VADER）。`--source` 默认 `auto`，按代码格式路由（数字代码→akshare，字母代码→yfinance）。`analyze`/`news` 支持 `-o` 把结果写入 JSON 文件。

## 配置

A 股（akshare）和美股（yfinance）走公开渠道，不需要 API key。若要用 NewsAPI 源，设置环境变量：

```bash
export NEWSAPI_KEY=YOUR_NEWSAPI_KEY
```

依赖安装见 `requirements.txt`；FinBERT 需要额外的 `transformers` + `torch`（模型较大，可选）。

## 输出示例

```json
{
  "symbol": "600519",
  "n_items": 20,
  "backend": "snownlp",
  "aggregate": {
    "n": 20,
    "mean_polarity": 0.21,
    "label_dist": { "positive": 14, "neutral": 4, "negative": 2 },
    "signal": "positive"
  }
}
```

## 文件结构

```
stocksight-skill/
├── SKILL.md                  # Skill 定义
├── README.md                 # 使用说明
├── QUICKSTART.md             # 快速上手
├── requirements.txt          # Python 依赖
├── __main__.py               # CLI 入口（news / analyze / sentiment / list-backends）
├── scripts/
│   ├── news_sources.py       # akshare / yfinance / NewsAPI 三源 + 自动路由
│   └── sentiment.py          # 4 backend 情感分析 + 语言自动路由 + 聚合
├── tests/
│   ├── test_news_sources.py
│   └── test_sentiment.py
├── data/
└── references/
    └── api-docs.md           # API 文档
```

## 注意事项

1. 数据延迟：新闻数据可能有延迟，上游源的 schema 偶有变动。
2. 投资风险：本工具仅供学习参考，不构成投资建议。
3. 情感准确性：NLP 情感分析存在误差，需结合其他指标。

## 许可证

Apache 2.0（基于原 stocksight 项目简化）。原项目：https://github.com/shirosaidev/stocksight
