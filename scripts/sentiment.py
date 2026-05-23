"""多后端情感分析引擎。

支持 4 个 backend：

- ``vader``    — VADER（英文，规则+词典，速度极快）
- ``textblob`` — TextBlob（英文，简单）
- ``snownlp``  — SnowNLP（中文）
- ``finbert``  — ProsusAI/finbert（英文金融领域专门预训练，需 transformers）

unified API：``analyze(text, backend="auto")`` 自动按语言路由：

- 主要英文 → vader（默认）或 finbert（如已装）
- 主要中文 → snownlp（默认）

返回统一的 ``SentimentScore``。
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import List, Literal, Optional


log = logging.getLogger(__name__)


Label = Literal["positive", "neutral", "negative"]
Backend = Literal["vader", "textblob", "snownlp", "finbert", "auto"]


@dataclass(frozen=True)
class SentimentScore:
    text: str
    label: Label
    polarity: float           # [-1, 1]，正负反映方向，绝对值反映强度
    confidence: float         # [0, 1]
    backend: str

    def to_dict(self) -> dict:
        return {
            "text": self.text[:200],
            "label": self.label,
            "polarity": round(self.polarity, 4),
            "confidence": round(self.confidence, 4),
            "backend": self.backend,
        }


_CJK_PATTERN = re.compile(r"[一-鿿]")


def _is_chinese(text: str, threshold: float = 0.2) -> bool:
    """简易语言判断：CJK 字符占比超过 threshold 视为中文。"""
    if not text:
        return False
    cjk_count = len(_CJK_PATTERN.findall(text))
    return cjk_count / len(text) >= threshold


def _label_from_polarity(p: float, threshold: float = 0.05) -> Label:
    if p >= threshold:
        return "positive"
    if p <= -threshold:
        return "negative"
    return "neutral"


# ---------------------------------------------------------------------------
# Backend 实现
# ---------------------------------------------------------------------------


def _analyze_vader(text: str) -> SentimentScore:
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    scores = SentimentIntensityAnalyzer().polarity_scores(text)
    comp = scores["compound"]
    return SentimentScore(
        text=text,
        label=_label_from_polarity(comp),
        polarity=comp,
        confidence=abs(comp),
        backend="vader",
    )


def _analyze_textblob(text: str) -> SentimentScore:
    from textblob import TextBlob
    polarity = TextBlob(text).sentiment.polarity
    subjectivity = TextBlob(text).sentiment.subjectivity
    return SentimentScore(
        text=text,
        label=_label_from_polarity(polarity),
        polarity=polarity,
        confidence=1.0 - subjectivity,    # 越客观 confidence 越高（rough heuristic）
        backend="textblob",
    )


def _analyze_snownlp(text: str) -> SentimentScore:
    try:
        from snownlp import SnowNLP
    except ImportError as e:
        raise RuntimeError(
            "SnowNLP 未安装：pip install snownlp"
        ) from e
    s = SnowNLP(text)
    score = float(s.sentiments)           # [0, 1]，0=极负 1=极正
    polarity = (score - 0.5) * 2          # 映射到 [-1, 1]
    return SentimentScore(
        text=text,
        label=_label_from_polarity(polarity),
        polarity=polarity,
        confidence=abs(polarity),
        backend="snownlp",
    )


_FINBERT_PIPELINE = None


def _analyze_finbert(text: str) -> SentimentScore:
    """ProsusAI/finbert — 英文金融领域 BERT 模型。首次加载约 400MB。"""
    global _FINBERT_PIPELINE
    if _FINBERT_PIPELINE is None:
        try:
            from transformers import pipeline
        except ImportError as e:
            raise RuntimeError(
                "FinBERT 需要 transformers：pip install transformers torch"
            ) from e
        log.info("loading ProsusAI/finbert (first call may take ~30s)...")
        _FINBERT_PIPELINE = pipeline(
            "sentiment-analysis", model="ProsusAI/finbert",
        )
    result = _FINBERT_PIPELINE(text[:512])[0]  # FinBERT max 512 tokens
    label_lower = result["label"].lower()
    score = result["score"]
    polarity = score if label_lower == "positive" else \
               -score if label_lower == "negative" else 0.0
    return SentimentScore(
        text=text,
        label=label_lower,
        polarity=polarity,
        confidence=score,
        backend="finbert",
    )


# ---------------------------------------------------------------------------
# 统一入口
# ---------------------------------------------------------------------------


def analyze(text: str, backend: Backend = "auto") -> SentimentScore:
    """对一段文本做情感分析，自动按语言路由。"""
    if not text or not text.strip():
        return SentimentScore(text=text, label="neutral",
                              polarity=0.0, confidence=0.0,
                              backend=backend if backend != "auto" else "noop")

    if backend == "auto":
        backend = "snownlp" if _is_chinese(text) else "vader"

    dispatch = {
        "vader": _analyze_vader,
        "textblob": _analyze_textblob,
        "snownlp": _analyze_snownlp,
        "finbert": _analyze_finbert,
    }
    if backend not in dispatch:
        raise ValueError(f"unknown backend: {backend!r}")
    return dispatch[backend](text)


def analyze_batch(texts: List[str], backend: Backend = "auto") -> List[SentimentScore]:
    """批量分析，给每条返回 SentimentScore。"""
    return [analyze(t, backend=backend) for t in texts]


def aggregate(scores: List[SentimentScore]) -> dict:
    """聚合多条情感为投资信号：平均极性 + 各 label 占比。"""
    if not scores:
        return {"n": 0, "mean_polarity": 0.0, "label_dist": {},
                "signal": "neutral"}
    n = len(scores)
    mean_p = sum(s.polarity for s in scores) / n
    dist = {"positive": 0, "neutral": 0, "negative": 0}
    for s in scores:
        dist[s.label] = dist.get(s.label, 0) + 1
    dist_pct = {k: v / n for k, v in dist.items()}
    return {
        "n": n,
        "mean_polarity": round(mean_p, 4),
        "label_dist": dist,
        "label_pct": {k: round(v, 4) for k, v in dist_pct.items()},
        "signal": _label_from_polarity(mean_p),
    }
