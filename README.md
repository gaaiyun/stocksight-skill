# stocksight-skill

把一只股票的真实新闻聚合起来，跑多种情感分析，给出可读的多空信号。

支持 A 股（akshare）+ 美股（yfinance）两套数据源，以及 4 个情感分析 backend（VADER、TextBlob、SnowNLP、FinBERT），按语言自动路由。

## 一、它解决什么问题

写量化或基本面研究时，"市场对这只股票的近期情绪"是常用但难量化的输入。手动看新闻不可扩展，单一情感模型在金融领域准确率差（VADER 连"beat earnings"这种积极信号都识别不出来），中英文混合场景下尤其混乱。

本项目把"拉新闻"和"算情感"两件事都做到可用：

- 拉新闻：akshare 拿 A 股个股新闻、yfinance 拿美股个股新闻，公开渠道不需要 key
- 算情感：4 个 backend 可选，按语言自动路由，FinBERT 专门处理英文金融文本
- 聚合：把多条情感汇总成一个统计信号（均值极性 + 标签分布 + 多空判断）

## 二、架构

```
   股票代码 (600519 / AAPL / ...)
        │
        ▼
   news_sources.fetch_news()  根据代码格式自动路由
   ├── 6 位数字 → akshare.stock_news_em (A 股)
   ├── 含字母   → yfinance.Ticker.news  (美股)
   └── 显式     → NewsAPI.org           (需 NEWSAPI_KEY)
        │
        ▼
   List[NewsItem]
        │
        ▼
   sentiment.analyze_batch()  按文本语言自动路由
   ├── 中文为主 → SnowNLP
   ├── 英文为主 → VADER (默认) 或 FinBERT (--backend finbert)
   └── 显式     → TextBlob
        │
        ▼
   sentiment.aggregate()  统计聚合
        │
        ▼
   {n, mean_polarity, label_dist, signal: positive/neutral/negative}
```

4 个情感 backend 的特点：

| Backend | 适用 | 速度 | 依赖体积 | 备注 |
|---|---|---|---|---|
| vader | 英文通用 | 极快 | 小 | 规则+词典，金融术语理解差 |
| textblob | 英文通用 | 快 | 小 | polarity + subjectivity |
| snownlp | 中文 | 快 | 小 | 默认中文路由 |
| finbert | 英文金融领域 | 慢（首次加载约 30s） | ~400MB | ProsusAI/finbert，对 beat / record 等金融积极词识别准 |

## 三、快速开始

### 安装

```bash
pip install -r requirements.txt
# 用 A 股新闻
pip install akshare
# 用美股新闻
pip install yfinance
# 用 FinBERT（可选，模型较大）
pip install transformers torch
```

### CLI

```bash
# 拉新闻清单
python __main__.py news 600519                # 茅台 A 股新闻
python __main__.py news AAPL                  # 苹果美股新闻
python __main__.py news AAPL --limit 30 -o news.json

# 新闻 + 情感分析 → 聚合信号
python __main__.py analyze 600519 --backend snownlp -o report.json
python __main__.py analyze TSLA --backend finbert     # 用金融领域 BERT
python __main__.py analyze NVDA --backend vader       # 默认快但金融词差

# 单段文本快速测
python __main__.py sentiment "苹果发布新品大获成功" --backend snownlp
python __main__.py sentiment "The company filed for bankruptcy" --backend vader
python __main__.py sentiment "Q3 EPS beat expectations" --backend finbert

# 看支持的 backend
python __main__.py list-backends
```

### 库调用

```python
from scripts.news_sources import fetch_news
from scripts.sentiment import analyze_batch, aggregate

items = fetch_news("600519", limit=20)        # 自动路由到 akshare
texts = [(it.title + "。" + it.summary).strip() for it in items]
scores = analyze_batch(texts, backend="auto") # 自动选 snownlp（中文）
signal = aggregate(scores)
print(signal["signal"], signal["mean_polarity"])
```

## 四、设计取舍

**为什么不只用 VADER？**

VADER 词典里没有 beat / record / miss / guidance 这种金融语境下情绪很强的词。对纯财经新闻准确率明显低于 FinBERT。VADER 留作"快速无依赖"兜底。

**为什么不只用 FinBERT？**

模型 400MB，加载约 30 秒，每次推理也慢。日常快速看一眼用 VADER 就够了，做严肃因子时切到 FinBERT。

**为什么 A 股用 akshare 而不是自己爬？**

akshare 已经包装了东方财富的公开接口，处理了反爬限速，不需要自己维护爬虫。代价是接口字段名可能随东方财富升级变动，所以用 ``_pick(row, aliases)`` 兼容多个候选列名做了缓冲。

**为什么不内置 LLM 综合判断？**

"算每条新闻的情感"是统计任务，FinBERT 已经够好。LLM 适合做的是"这堆情感信号说明什么投资逻辑"——那是上游策略层的事，不在本工具范围。

## 五、目录结构

```
.
├── __main__.py                   CLI (news / analyze / sentiment / list-backends)
├── scripts/
│   ├── news_sources.py           akshare / yfinance / NewsAPI 三源 + 自动路由
│   ├── sentiment.py              4 backend 情感分析 + 语言自动路由 + 聚合
│   └── stocksight.py             v1 留存的 CLI（兼容）
├── tests/
│   ├── test_news_sources.py      monkeypatch 不打真实网络
│   └── test_sentiment.py         polarity / label / aggregate 数学性质
├── references/
├── data/
├── requirements.txt
└── README.md
```

## 六、测试

```bash
pytest tests/
```

24 个测试覆盖：
- 语言判断（中文 / 英文 / 混合）
- 4 个 backend 的 polarity 范围与 label 一致性
- 多源新闻 fetcher 字段映射（akshare 中文列名 / yfinance）
- 自动路由（6 位数字 → akshare、含字母 → yfinance）
- aggregate 统计聚合

不打真实 akshare / yfinance / FinBERT 模型；CI 不需要任何 API key 或 GPU。

## 七、合规边界

- akshare 抓的是东方财富等公开渠道的免费新闻摘要
- 本工具不绕过付费墙、不爬限制访问内容
- 情感分析结果**不构成投资建议**，仅作为定量信号供策略参考

## License

MIT
