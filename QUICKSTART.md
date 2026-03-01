# 🚀 stocksight 快速开始指南

## 1 分钟上手

### 步骤 1: 安装依赖

```bash
cd stocksight-skill
pip install -r requirements.txt
```

### 步骤 2: 下载 NLTK 数据

```bash
python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords')"
```

### 步骤 3: 运行分析

```bash
# 分析股票情感
python scripts/stocksight.py --symbol TSLA --analyze

# 生成价格预测
python scripts/stocksight.py --symbol AAPL --predict

# 查看历史记录
python scripts/stocksight.py --symbol NVDA --history
```

## OpenClaw 集成

### 作为 Skill 使用

在 OpenClaw 中调用：

```bash
# Markdown 格式输出
python openclaw_integration.py --action analyze --symbol TSLA --format markdown

# JSON 格式输出（程序化使用）
python openclaw_integration.py --action predict --symbol AAPL --format json
```

### 输出示例

```markdown
## 📊 Stocksight 分析：TSLA

### 💭 情感分析

- **总体情感**: POSITIVE
- **极性值**: 0.209
- **分析文章数**: 5

### 📈 情感分布

- ✅ 正面：4
- ➖ 中性：1
- ❌ 负面：0

### 🔮 价格预测

- **方向**: 📈 UP
- **置信度**: 72.5%
```

## 常用命令速查

| 命令 | 说明 |
|------|------|
| `python scripts/stocksight.py -s TSLA -a` | 分析 TSLA 情感 |
| `python scripts/stocksight.py -s AAPL -n` | 获取 AAPL 新闻并分析 |
| `python scripts/stocksight.py -s NVDA -p` | 预测 NVDA 价格走势 |
| `python scripts/stocksight.py -s TSLA --history` | 查看 TSLA 历史 |
| `python scripts/stocksight.py -s TSLA -a -v` | 详细模式分析 |

## 配置 API（可选）

编辑 `config.json`：

```json
{
  "news_api_key": "YOUR_NEWSAPI_KEY"
}
```

获取 NewsAPI 密钥：https://newsapi.org/

**注意**：即使没有 API 密钥，工具也会使用模拟数据运行。

## 下一步

- 📖 查看完整文档：`README.md`
- 🔧 查看 API 文档：`references/api-docs.md`
- 💬 查看 Skill 定义：`SKILL.md`

---

**有问题？** 查看 `README.md` 的故障排除部分。
