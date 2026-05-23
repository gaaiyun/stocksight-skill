"""sentiment.py 测试（不依赖网络 / FinBERT 模型）。"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from sentiment import (
    SentimentScore,
    aggregate,
    analyze,
    analyze_batch,
    _is_chinese,
    _label_from_polarity,
)


def test_label_from_polarity_thresholds():
    assert _label_from_polarity(0.5) == "positive"
    assert _label_from_polarity(-0.5) == "negative"
    assert _label_from_polarity(0.01) == "neutral"
    assert _label_from_polarity(0.0) == "neutral"


def test_is_chinese_detection():
    assert _is_chinese("这是一段比较长的中文文本") is True
    assert _is_chinese("This is purely English text content") is False
    assert _is_chinese("") is False
    # 中文为主：判为中文
    assert _is_chinese("公司 Q3 业绩超预期增长稳健") is True
    # 英文为主：判为非中文
    assert _is_chinese("Apple reports record Q3 earnings with strong margins") is False


def test_analyze_empty_returns_neutral():
    s = analyze("")
    assert s.label == "neutral"
    assert s.polarity == 0.0


def test_analyze_english_positive_via_vader():
    s = analyze("The company reported excellent earnings and strong growth.",
                backend="vader")
    assert s.backend == "vader"
    assert s.label == "positive"
    assert s.polarity > 0


def test_analyze_english_negative_via_vader():
    s = analyze("Disaster: company faces bankruptcy and massive layoffs.",
                backend="vader")
    assert s.label == "negative"
    assert s.polarity < 0


def test_analyze_textblob_returns_valid_score():
    s = analyze("This is amazing news!", backend="textblob")
    assert s.backend == "textblob"
    assert s.label in ("positive", "neutral", "negative")
    assert -1 <= s.polarity <= 1
    assert 0 <= s.confidence <= 1


def test_analyze_auto_routes_chinese_to_snownlp():
    # snownlp 装了就用，没装就 raise — 用 try 兼容两种情况
    try:
        s = analyze("公司业绩超预期，前景乐观", backend="auto")
        assert s.backend == "snownlp"
    except RuntimeError as e:
        assert "SnowNLP" in str(e)


def test_analyze_auto_routes_english_to_vader():
    s = analyze("Sales hit record high in Q3", backend="auto")
    assert s.backend == "vader"


def test_analyze_unknown_backend_raises():
    with pytest.raises(ValueError, match="unknown backend"):
        analyze("text", backend="not-a-backend")  # type: ignore


def test_analyze_batch_preserves_order():
    texts = ["good news here", "terrible disaster", "neutral statement"]
    scores = analyze_batch(texts, backend="vader")
    assert len(scores) == 3
    assert scores[0].polarity > scores[1].polarity


def test_aggregate_empty():
    a = aggregate([])
    assert a["n"] == 0
    assert a["signal"] == "neutral"


def test_aggregate_three_positive():
    scores = [
        SentimentScore(text="a", label="positive", polarity=0.6, confidence=0.6, backend="vader"),
        SentimentScore(text="b", label="positive", polarity=0.4, confidence=0.4, backend="vader"),
        SentimentScore(text="c", label="neutral",  polarity=0.0, confidence=0.0, backend="vader"),
    ]
    a = aggregate(scores)
    assert a["n"] == 3
    assert a["mean_polarity"] == pytest.approx((0.6 + 0.4 + 0) / 3, rel=1e-3)
    assert a["signal"] == "positive"
    assert a["label_dist"]["positive"] == 2
    assert a["label_dist"]["neutral"] == 1


def test_aggregate_signal_neutral_when_balanced():
    scores = [
        SentimentScore(text="a", label="positive", polarity=0.5, confidence=0.5, backend="vader"),
        SentimentScore(text="b", label="negative", polarity=-0.5, confidence=0.5, backend="vader"),
    ]
    a = aggregate(scores)
    assert a["mean_polarity"] == pytest.approx(0.0)
    assert a["signal"] == "neutral"


def test_sentiment_score_to_dict_truncates_long_text():
    long_text = "x" * 500
    s = SentimentScore(text=long_text, label="neutral", polarity=0.0,
                       confidence=0.0, backend="vader")
    d = s.to_dict()
    assert len(d["text"]) <= 200
