"""真实新闻数据源 —— 替代原 stocksight.py 里的 simulate_news_data。

支持三种源：

- ``akshare`` 抓 A 股个股新闻（东方财富等公开渠道）
- ``yfinance`` 拿美股个股新闻（Yahoo Finance）
- ``newsapi`` 调用 NewsAPI.org（需要 key）

所有源在依赖未安装时优雅降级（raise 带 actionable 提示）。
"""
from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional


log = logging.getLogger(__name__)


@dataclass(frozen=True)
class NewsItem:
    """统一的新闻条目。"""

    title: str
    url: Optional[str]
    published_at: str        # ISO 8601
    source: str
    summary: str = ""
    symbol: str = ""

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "url": self.url,
            "published_at": self.published_at,
            "source": self.source,
            "summary": self.summary,
            "symbol": self.symbol,
        }


class NewsSourceError(RuntimeError):
    """新闻源调用失败。"""


# ---------------------------------------------------------------------------
# akshare A 股个股新闻
# ---------------------------------------------------------------------------


def fetch_akshare_cn_news(symbol: str, limit: int = 20) -> List[NewsItem]:
    """抓某 A 股个股的最新新闻。

    Parameters
    ----------
    symbol : 6 位股票代码（如 ``"600519"``、``"000001"``）；带交易所后缀也会自动去掉。
    """
    try:
        import akshare as ak
    except ImportError as e:
        raise NewsSourceError(
            "未安装 akshare。pip install akshare 后重试。"
        ) from e

    code = symbol.split(".")[0]   # 去掉 .SS / .SZ / .XSHG 后缀

    try:
        df = ak.stock_news_em(symbol=code)
    except Exception as e:
        raise NewsSourceError(
            f"akshare.stock_news_em({code}) 失败：{e}。检查股票代码或升级 akshare"
        ) from e

    if df is None or len(df) == 0:
        return []

    out: List[NewsItem] = []
    for _, row in df.head(limit).iterrows():
        try:
            out.append(NewsItem(
                title=_pick(row, ["新闻标题", "标题"]) or "",
                url=_pick(row, ["新闻链接", "链接", "url"]),
                published_at=_pick(row, ["发布时间", "时间", "日期"]) or "",
                source=_pick(row, ["新闻来源", "来源"]) or "akshare",
                summary=_pick(row, ["新闻内容", "摘要"]) or "",
                symbol=code,
            ))
        except Exception as e:
            log.warning("跳过一行解析失败的新闻: %s", e)
    return out


# ---------------------------------------------------------------------------
# yfinance 美股新闻
# ---------------------------------------------------------------------------


def fetch_yfinance_us_news(symbol: str, limit: int = 20) -> List[NewsItem]:
    """抓某美股个股的最新新闻（Yahoo Finance）。"""
    try:
        import yfinance as yf
    except ImportError as e:
        raise NewsSourceError(
            "未安装 yfinance。pip install yfinance 后重试。"
        ) from e

    try:
        ticker = yf.Ticker(symbol)
        news = ticker.news or []
    except Exception as e:
        raise NewsSourceError(
            f"yfinance.Ticker({symbol}).news 失败：{e}"
        ) from e

    out: List[NewsItem] = []
    for item in news[:limit]:
        try:
            ts = item.get("providerPublishTime") or item.get("pubDate")
            if isinstance(ts, (int, float)):
                published = datetime.fromtimestamp(ts).isoformat()
            elif isinstance(ts, str):
                published = ts
            else:
                published = ""
            out.append(NewsItem(
                title=item.get("title", ""),
                url=item.get("link") or item.get("url"),
                published_at=published,
                source=item.get("publisher", "Yahoo Finance"),
                summary=item.get("summary", ""),
                symbol=symbol,
            ))
        except Exception as e:
            log.warning("跳过一行 yfinance 新闻: %s", e)
    return out


# ---------------------------------------------------------------------------
# NewsAPI.org（需 key）
# ---------------------------------------------------------------------------


def fetch_newsapi(symbol: str, limit: int = 20,
                  api_key: Optional[str] = None,
                  language: str = "en") -> List[NewsItem]:
    """调 NewsAPI.org 拿一般新闻（需要 key）。"""
    import requests
    api_key = api_key or os.getenv("NEWSAPI_KEY")
    if not api_key:
        raise NewsSourceError(
            "NewsAPI 需要 key。把 key 写到 NEWSAPI_KEY 环境变量，或显式传 api_key 参数。"
        )

    try:
        resp = requests.get(
            "https://newsapi.org/v2/everything",
            params={
                "q": symbol,
                "language": language,
                "sortBy": "publishedAt",
                "pageSize": limit,
                "apiKey": api_key,
            },
            timeout=15,
        )
        resp.raise_for_status()
    except Exception as e:
        raise NewsSourceError(f"NewsAPI 请求失败：{e}") from e

    out: List[NewsItem] = []
    for item in resp.json().get("articles", []):
        out.append(NewsItem(
            title=item.get("title", ""),
            url=item.get("url"),
            published_at=item.get("publishedAt", ""),
            source=(item.get("source") or {}).get("name", "NewsAPI"),
            summary=item.get("description", "") or "",
            symbol=symbol,
        ))
    return out


# ---------------------------------------------------------------------------
# 统一入口：根据 symbol 自动路由
# ---------------------------------------------------------------------------


def fetch_news(symbol: str, limit: int = 20,
               source: str = "auto") -> List[NewsItem]:
    """根据股票代码自动路由到合适的数据源。

    Parameters
    ----------
    symbol : 股票代码。
        - 全数字 6 位（如 ``"600519"``）→ A 股，走 akshare
        - 含字母（如 ``"AAPL"``、``"TSLA"``）→ 美股，走 yfinance
    source : 可强制指定 ``"akshare" / "yfinance" / "newsapi" / "auto"``。
    """
    if source == "akshare":
        return fetch_akshare_cn_news(symbol, limit=limit)
    if source == "yfinance":
        return fetch_yfinance_us_news(symbol, limit=limit)
    if source == "newsapi":
        return fetch_newsapi(symbol, limit=limit)

    # auto
    code = symbol.split(".")[0]
    if code.isdigit() and len(code) == 6:
        return fetch_akshare_cn_news(symbol, limit=limit)
    return fetch_yfinance_us_news(symbol, limit=limit)


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def _pick(row, aliases) -> Optional[str]:
    for k in aliases:
        if k in row.index:
            v = row[k]
            if v is None:
                return None
            import math
            if isinstance(v, float) and math.isnan(v):
                return None
            return str(v).strip()
    return None
