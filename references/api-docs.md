# API 文档

## NewsAPI

### 免费计划
- 请求限制：100 次/天
- 延迟：1 小时
- 来源：部分可用

### 获取密钥
1. 访问 https://newsapi.org/
2. 点击 "Get API Key"
3. 选择 Developer 计划（免费）
4. 填写邮箱，获取密钥

### API 端点

#### Everything Endpoint
```
GET https://newsapi.org/v2/everything
```

**参数**:
- `q`: 搜索关键词（如股票代号）
- `language`: 语言（en, zh 等）
- `sortBy`: 排序方式（publishedAt, relevance, popularity）
- `pageSize`: 每页数量（最大 100）
- `apiKey`: API 密钥

**示例**:
```bash
curl "https://newsapi.org/v2/everything?q=TSLA&language=en&sortBy=publishedAt&pageSize=20&apiKey=YOUR_API_KEY"
```

**响应**:
```json
{
  "status": "ok",
  "totalResults": 1234,
  "articles": [
    {
      "title": "Tesla Stock Rises",
      "description": "...",
      "url": "https://...",
      "publishedAt": "2026-03-01T12:00:00Z",
      "source": {
        "name": "Bloomberg"
      }
    }
  ]
}
```

---

## Alpha Vantage (股票价格)

### 免费计划
- 请求限制：5 次/分钟，500 次/天
- 无需信用卡

### 获取密钥
1. 访问 https://www.alphavantage.co/support/#api-key
2. 填写表单
3. 立即获取密钥

### API 端点

#### Daily Time Series
```
GET https://www.alphavantage.co/query
```

**参数**:
- `function`: TIME_SERIES_DAILY
- `symbol`: 股票代号
- `apikey`: API 密钥

**示例**:
```bash
curl "https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol=TSLA&apikey=YOUR_API_KEY"
```

---

## Twitter API v2 (可选)

### 免费计划
- 发帖限制：1500 条/月
- 读取限制：有限

### 获取密钥
1. 访问 https://developer.twitter.com/
2. 申请开发者账户
3. 创建项目和应用
4. 获取 API Key 和 Secret

---

## 替代方案（无需 API Key）

### 1. Yahoo Finance
- URL: https://finance.yahoo.com/
- 可抓取新闻和股票数据
- 无官方 API，需网页爬虫

### 2. Google Finance
- URL: https://www.google.com/finance
- 提供股票数据和新闻
- 无官方 API

### 3. 财经新闻 RSS
- Reuters: https://www.reuters.com/tools/rss
- Bloomberg: https://www.bloomberg.com/feed
- CNBC: https://www.cnbc.com/id/100003114/device/rss/rss.html

### 4. 模拟数据模式
stocksight 内置模拟数据生成器，用于测试和演示：
- 自动生成假新闻标题
- 模拟情感分析结果
- 无需任何 API 密钥

---

## 最佳实践

### 1. API 密钥管理
```json
// config.json
{
  "news_api_key": "YOUR_KEY_HERE",
  "twitter_api_key": ""  // 留空使用模拟数据
}
```

**不要**将 API 密钥提交到 Git！

### 2. 请求频率控制
```python
import time
time.sleep(1)  # 请求间延迟 1 秒
```

### 3. 错误处理
```python
try:
    response = requests.get(url, timeout=10)
    response.raise_for_status()
except requests.exceptions.RequestException as e:
    logger.error(f"API request failed: {e}")
```

### 4. 数据缓存
```python
# 缓存结果，避免重复请求
cache = {
    "data": response_data,
    "timestamp": datetime.now()
}
```

---

## 资源链接

- NewsAPI 文档：https://newsapi.org/docs
- Alpha Vantage 文档：https://www.alphavantage.co/documentation/
- Twitter API 文档：https://developer.twitter.com/en/docs
- TextBlob 文档：https://textblob.readthedocs.io/
- VADER Sentiment: https://github.com/cjhutto/vaderSentiment

---

**提示**: 对于学习和演示目的，使用模拟数据模式即可。生产环境建议购买付费 API 计划以获得更稳定的数据源。
