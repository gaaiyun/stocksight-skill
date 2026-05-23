"""news_sources.py 测试（不打真实网络，monkeypatch akshare / yfinance）。"""
from __future__ import annotations

import sys
import types
from pathlib import Path
from unittest.mock import MagicMock

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from news_sources import (
    NewsItem,
    NewsSourceError,
    fetch_akshare_cn_news,
    fetch_news,
    fetch_yfinance_us_news,
)


def test_news_item_to_dict():
    n = NewsItem(title="t", url="u", published_at="2024-01-01",
                 source="x", summary="s", symbol="AAPL")
    d = n.to_dict()
    assert d["title"] == "t"
    assert d["symbol"] == "AAPL"


# ---------------------------------------------------------------------------
# akshare A 股
# ---------------------------------------------------------------------------


def test_fetch_akshare_raises_when_missing(monkeypatch):
    monkeypatch.setitem(sys.modules, "akshare", None)
    with pytest.raises(NewsSourceError, match="akshare"):
        fetch_akshare_cn_news("600519")


def test_fetch_akshare_parses_chinese_columns(monkeypatch):
    fake_df = pd.DataFrame([
        {
            "新闻标题": "茅台业绩超预期",
            "新闻链接": "https://example.com/1",
            "发布时间": "2024-09-01 10:00",
            "新闻来源": "财联社",
            "新闻内容": "公司 2024Q3 营业收入同比增长 18%",
        },
        {
            "新闻标题": "白酒板块走强",
            "新闻链接": "https://example.com/2",
            "发布时间": "2024-09-02 09:30",
            "新闻来源": "证券时报",
            "新闻内容": "...",
        },
    ])
    fake_ak = types.ModuleType("akshare")
    fake_ak.stock_news_em = lambda symbol: fake_df
    monkeypatch.setitem(sys.modules, "akshare", fake_ak)

    items = fetch_akshare_cn_news("600519", limit=10)
    assert len(items) == 2
    assert items[0].title == "茅台业绩超预期"
    assert items[0].source == "财联社"
    assert items[0].symbol == "600519"


def test_fetch_akshare_strips_suffix(monkeypatch):
    """传入 600519.SS / 600519.XSHG 都应只用 600519 调 akshare。"""
    captured = {}
    fake_ak = types.ModuleType("akshare")
    def _capture(symbol):
        captured["symbol"] = symbol
        return pd.DataFrame()
    fake_ak.stock_news_em = _capture
    monkeypatch.setitem(sys.modules, "akshare", fake_ak)

    fetch_akshare_cn_news("600519.SS")
    assert captured["symbol"] == "600519"


def test_fetch_akshare_empty_df(monkeypatch):
    fake_ak = types.ModuleType("akshare")
    fake_ak.stock_news_em = lambda symbol: pd.DataFrame()
    monkeypatch.setitem(sys.modules, "akshare", fake_ak)
    assert fetch_akshare_cn_news("600519") == []


def test_fetch_akshare_wraps_exception(monkeypatch):
    fake_ak = types.ModuleType("akshare")
    def _boom(symbol):
        raise ValueError("api changed")
    fake_ak.stock_news_em = _boom
    monkeypatch.setitem(sys.modules, "akshare", fake_ak)

    with pytest.raises(NewsSourceError, match="api changed|akshare"):
        fetch_akshare_cn_news("600519")


# ---------------------------------------------------------------------------
# yfinance 美股
# ---------------------------------------------------------------------------


def test_fetch_yfinance_raises_when_missing(monkeypatch):
    monkeypatch.setitem(sys.modules, "yfinance", None)
    with pytest.raises(NewsSourceError, match="yfinance"):
        fetch_yfinance_us_news("AAPL")


def test_fetch_yfinance_parses_news(monkeypatch):
    fake_yf = types.ModuleType("yfinance")
    fake_ticker = MagicMock()
    fake_ticker.news = [
        {
            "title": "Apple announces new product",
            "link": "https://example.com/a1",
            "providerPublishTime": 1696000000,
            "publisher": "Reuters",
            "summary": "Apple unveiled...",
        },
        {
            "title": "Apple Q3 earnings beat",
            "link": "https://example.com/a2",
            "providerPublishTime": 1696100000,
            "publisher": "CNBC",
            "summary": "EPS came in...",
        },
    ]
    fake_yf.Ticker = lambda symbol: fake_ticker
    monkeypatch.setitem(sys.modules, "yfinance", fake_yf)

    items = fetch_yfinance_us_news("AAPL", limit=5)
    assert len(items) == 2
    assert items[0].title == "Apple announces new product"
    assert items[0].source == "Reuters"


# ---------------------------------------------------------------------------
# 自动路由
# ---------------------------------------------------------------------------


def test_fetch_news_auto_routes_6digit_to_akshare(monkeypatch):
    """全数字 6 位代码应路由到 akshare。"""
    captured = {"calls": []}

    fake_ak = types.ModuleType("akshare")
    def _ak_stock_news(symbol):
        captured["calls"].append(("akshare", symbol))
        return pd.DataFrame()
    fake_ak.stock_news_em = _ak_stock_news
    monkeypatch.setitem(sys.modules, "akshare", fake_ak)

    fetch_news("600519", source="auto")
    assert captured["calls"][0][0] == "akshare"


def test_fetch_news_auto_routes_letters_to_yfinance(monkeypatch):
    captured = {"calls": []}

    fake_yf = types.ModuleType("yfinance")
    fake_ticker = MagicMock()
    fake_ticker.news = []
    def _ticker(symbol):
        captured["calls"].append(("yfinance", symbol))
        return fake_ticker
    fake_yf.Ticker = _ticker
    monkeypatch.setitem(sys.modules, "yfinance", fake_yf)

    fetch_news("AAPL", source="auto")
    assert captured["calls"][0][0] == "yfinance"
