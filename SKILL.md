# stocksight - 股市情感分析 Skill

**简化版 stocksight for OpenClaw** - 基于 Twitter/新闻情感分析的股市预测工具

## 功能特性

- 📊 **情感分析**：分析新闻/社交媒体对股票的情感倾向
- 📈 **价格预测**：基于情感数据预测短期股价走势
- 📰 **新闻聚合**：自动抓取财经新闻头条
- 💾 **本地存储**：无需 Elasticsearch，使用 JSON 本地存储
- 🔧 **简化配置**：最小化 API 依赖

## 使用方法

### 基本用法

```bash
# 分析单只股票的情感
python scripts/stocksight.py --symbol TSLA --analyze

# 获取新闻情感分析
python scripts/stocksight.py --symbol AAPL --news

# 查看历史情感数据
python scripts/stocksight.py --symbol TSLA --history

# 生成预测报告
python scripts/stocksight.py --symbol NVDA --predict
```

### 高级用法

```bash
# 自定义新闻源
python scripts/stocksight.py --symbol TSLA --news --sources yahoo,google

# 情感阈值过滤
python scripts/stocksight.py --symbol AAPL --analyze --min-polarity 0.3

# 导出分析报告
python scripts/stocksight.py --symbol TSLA --report --format markdown
```

## 配置说明

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置文件

编辑 `config.json`：

```json
{
  "news_api_key": "YOUR_NEWS_API_KEY",
  "twitter_api_key": "",  // 可选
  "default_frequency": 300,
  "sentiment_threshold": 0.3,
  "storage_path": "./data"
}
```

### 3. 可选 API

- **NewsAPI** (推荐): https://newsapi.org/ - 免费财经新闻
- **Alpha Vantage**: https://www.alphavantage.co/ - 免费股票数据
- **Twitter API** (可选): 用于 Twitter 情感分析

## 输出示例

### 情感分析结果

```json
{
  "symbol": "TSLA",
  "timestamp": "2026-03-01T12:00:00Z",
  "sentiment": {
    "polarity": 0.65,
    "subjectivity": 0.72,
    "label": "positive"
  },
  "news_count": 15,
  "prediction": {
    "direction": "up",
    "confidence": 0.78,
    "timeframe": "1d"
  }
}
```

## 文件结构

```
stocksight-skill/
├── SKILL.md              # OpenClaw Skill 定义
├── README.md             # 使用说明
├── requirements.txt      # Python 依赖
├── config.json           # 配置文件
├── scripts/
│   ├── stocksight.py     # 主脚本
│   ├── sentiment.py      # 情感分析模块
│   ├── news_fetcher.py   # 新闻抓取模块
│   └── predictor.py      # 价格预测模块
├── data/
│   ├── sentiment_log.json
│   └── predictions.json
└── references/
    └── api-docs.md       # API 文档
```

## 注意事项

1. **API 限制**：免费 API 有请求限制，请合理使用
2. **数据延迟**：新闻数据可能有 15 分钟延迟
3. **投资风险**：本工具仅供学习参考，不构成投资建议
4. **情感准确性**：NLP 情感分析存在误差，需结合其他指标

## 许可证

Apache 2.0 (基于原 stocksight 项目简化)

## 致谢

原项目：https://github.com/shirosaidev/stocksight
