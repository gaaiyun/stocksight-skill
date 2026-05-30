# stocksight 快速开始指南

## 1 分钟上手

### 步骤 1: 安装依赖

```bash
pip install -r requirements.txt
# 用 A 股新闻
pip install akshare
# 用美股新闻
pip install yfinance
# 用 FinBERT（可选，模型较大）
pip install transformers torch
```

### 步骤 2: 下载 NLTK 数据（VADER / TextBlob 需要）

```bash
python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords')"
```

### 步骤 3: 运行分析

```bash
# 拉新闻清单
python __main__.py news 600519                # 茅台 A 股新闻
python __main__.py news AAPL                  # 苹果美股新闻

# 新闻 + 情感分析 → 聚合信号
python __main__.py analyze 600519 --backend snownlp
python __main__.py analyze TSLA --backend finbert

# 单段文本快速测
python __main__.py sentiment "苹果发布新品大获成功" --backend snownlp
python __main__.py sentiment "The company filed for bankruptcy" --backend vader

# 看支持的 backend
python __main__.py list-backends
```

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

## 常用命令速查

| 命令 | 说明 |
|------|------|
| `python __main__.py news 600519` | 拉茅台 A 股新闻 |
| `python __main__.py news AAPL` | 拉苹果美股新闻 |
| `python __main__.py analyze 600519 --backend snownlp` | 中文新闻情感聚合 |
| `python __main__.py analyze TSLA --backend finbert` | 用金融领域 BERT 分析美股 |
| `python __main__.py sentiment "<文本>" --backend vader` | 单段文本情感 |
| `python __main__.py list-backends` | 列出支持的 backend |

## 配置 API（可选）

A 股（akshare）和美股（yfinance）走公开渠道，不需要 key。若要用 NewsAPI 源，设置环境变量：

```bash
export NEWSAPI_KEY=YOUR_NEWSAPI_KEY
```

获取 NewsAPI 密钥：https://newsapi.org/

## 下一步

- 完整文档：`README.md`
- API 文档：`references/api-docs.md`
- Skill 定义：`SKILL.md`

---

有问题？查看 `README.md`。
