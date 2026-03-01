# 📊 stocksight - 股市情感分析工具

**简化版 stocksight for OpenClaw** - 基于新闻情感分析的股市预测工具

![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.8+-blue.svg)

## 🌟 功能特性

- 📰 **新闻情感分析**：自动抓取财经新闻并分析情感倾向
- 📈 **价格预测**：基于情感数据预测短期股价走势
- 💾 **本地存储**：无需 Elasticsearch，使用 JSON 本地存储
- 🔧 **简化配置**：最小化 API 依赖，开箱即用
- 🎯 **OpenClaw 集成**：作为 Skill 无缝集成到 OpenClaw

## 🚀 快速开始

### 1. 安装依赖

```bash
cd stocksight-skill
pip install -r requirements.txt
```

### 2. 下载 NLTK 数据

```bash
python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords')"
```

### 3. 运行分析

```bash
# 分析股票情感
python scripts/stocksight.py --symbol TSLA --analyze

# 获取新闻并分析
python scripts/stocksight.py --symbol AAPL --news

# 生成价格预测
python scripts/stocksight.py --symbol NVDA --predict

# 查看历史数据
python scripts/stocksight.py --symbol TSLA --history
```

## 📖 详细用法

### 基本命令

| 命令 | 说明 |
|------|------|
| `--symbol TSLA` | 指定股票代号（必需） |
| `--analyze` | 分析当前情感 |
| `--news` | 抓取新闻并分析 |
| `--predict` | 生成价格预测 |
| `--history` | 查看历史记录 |
| `--verbose` | 详细输出模式 |

### 示例输出

```
============================================================
📊 STOCKSIGHT ANALYSIS: TSLA
============================================================

📰 Articles Analyzed: 15

💭 Overall Sentiment:
   Label: POSITIVE
   Polarity: 0.42
   Subjectivity: 0.65

📈 Label Distribution:
   Positive: 9
   Neutral: 4
   Negative: 2

📝 Recent Headlines:
   1. ✅ [POSITIVE] Tesla Stock Rises on Strong Earnings...
   2. ✅ [POSITIVE] Analysts Upgrade TSLA Price Target...
   3. ➖ [NEUTRAL] Market Volatility Affects Tesla Shares...
   4. ✅ [POSITIVE] Tesla Announces New Product Launch...
   5. ❌ [NEGATIVE] Production Delays Reported...

🔮 Price Prediction (1 day):
   Direction: 📈 UP
   Confidence: 72.5%

============================================================
```

## ⚙️ 配置说明

### config.json 配置项

```json
{
  "news_api_key": "",           // NewsAPI 密钥（可选）
  "twitter_api_key": "",        // Twitter API 密钥（可选）
  "default_frequency": 300,     // 数据刷新频率（秒）
  "sentiment_threshold": 0.3,   // 情感阈值
  "storage_path": "./data",     // 数据存储路径
  "news_sources": ["yahoo", "google", "reuters"],  // 新闻源
  "max_articles": 20,           // 最大文章数
  "cache_hours": 1              // 缓存时间（小时）
}
```

### 获取 NewsAPI 密钥（可选）

1. 访问 https://newsapi.org/
2. 注册免费账户
3. 获取 API Key
4. 填入 `config.json` 的 `news_api_key` 字段

**注意**：即使没有 API Key，工具也会使用模拟数据进行演示。

## 📁 项目结构

```
stocksight-skill/
├── SKILL.md              # OpenClaw Skill 定义
├── README.md             # 使用说明（本文件）
├── requirements.txt      # Python 依赖
├── config.json           # 配置文件
├── scripts/
│   └── stocksight.py     # 主脚本
├── data/
│   ├── {symbol}_sentiment.json    # 情感历史数据
│   └── {symbol}_predictions.json  # 预测历史数据
└── references/
    └── api-docs.md       # API 文档
```

## 🔬 技术原理

### 情感分析算法

stocksight 使用两种 NLP 工具进行情感分析：

1. **TextBlob**: 计算极性 (polarity) 和主观性 (subjectivity)
   - 极性范围：-1.0 (负面) 到 1.0 (正面)
   - 主观性范围：0.0 (客观) 到 1.0 (主观)

2. **VADER Sentiment**: 专门针对社交媒体优化的情感分析
   - 输出 compound 分数：-1.0 到 1.0
   - 分别计算正面、中性、负面比例

3. **综合算法**:
   ```python
   combined_polarity = (textblob_polarity + vader_compound) / 2
   
   if combined_polarity >= 0.05:
       label = "positive"
   elif combined_polarity <= -0.05:
       label = "negative"
   else:
       label = "neutral"
   ```

### 价格预测逻辑

基于情感数据的简单预测模型：

```python
if sentiment == "positive" and polarity > 0.3:
    direction = "up"
    confidence = 0.5 + polarity * 0.4
elif sentiment == "negative" and polarity < -0.3:
    direction = "down"
    confidence = 0.5 + abs(polarity) * 0.4
else:
    direction = "sideways"
    confidence = 0.5
```

**注意**：这是简化版预测，实际交易请使用更复杂的量化模型。

## 📊 数据存储

### 情感数据格式

```json
{
  "symbol": "TSLA",
  "timestamp": "2026-03-01T12:00:00Z",
  "articles_analyzed": 15,
  "overall_sentiment": {
    "polarity": 0.42,
    "subjectivity": 0.65,
    "label": "positive"
  },
  "label_distribution": {
    "positive": 9,
    "neutral": 4,
    "negative": 2
  },
  "articles": [...]
}
```

### 预测数据格式

```json
{
  "symbol": "TSLA",
  "timestamp": "2026-03-01T12:00:00Z",
  "prediction": {
    "direction": "up",
    "confidence": 0.725,
    "timeframe": "1d"
  },
  "based_on": {
    "sentiment_label": "positive",
    "polarity": 0.42,
    "articles": 15
  }
}
```

## ⚠️ 免责声明

**重要提示**：

1. **本工具仅供学习和研究使用**
2. **不构成任何投资建议**
3. **股市有风险，投资需谨慎**
4. **情感分析存在误差，请结合其他指标**
5. **作者不对任何交易损失负责**

## 🔧 故障排除

### 常见问题

**Q: 安装时出现编码错误**
```bash
# Windows PowerShell 解决方案
$env:PYTHONIOENCODING="utf-8"
pip install -r requirements.txt
```

**Q: NLTK 数据下载失败**
```bash
# 手动下载
python -m nltk.downloader punkt
python -m nltk.downloader stopwords
```

**Q: 没有真实新闻数据**
- 检查 `config.json` 中的 `news_api_key`
- 或使用模拟数据模式（默认）

**Q: 情感分析结果不准确**
- 增加新闻数量（修改 `max_articles`）
- 调整情感阈值（修改 `sentiment_threshold`）

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

Apache License 2.0

基于原 stocksight 项目简化：https://github.com/shirosaidev/stocksight

## 🙏 致谢

- 原 stocksight 项目作者：Chris Park
- TextBlob: https://textblob.readthedocs.io/
- VADER Sentiment: https://github.com/cjhutto/vaderSentiment
- NewsAPI: https://newsapi.org/

---

**Made with ⭐ for OpenClaw**
