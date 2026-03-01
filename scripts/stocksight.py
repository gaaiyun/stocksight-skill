#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
stocksight.py - Simplified stock market sentiment analyzer for OpenClaw
基于新闻情感分析的股市预测工具

Usage:
    python stocksight.py --symbol TSLA --analyze
    python stocksight.py --symbol AAPL --news
    python stocksight.py --symbol NVDA --predict
"""

import sys
import json
import argparse
import logging
from datetime import datetime, timedelta
from pathlib import Path
import requests
from textblob import TextBlob
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import numpy as np

# Fix Windows console encoding for emoji
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Configuration
CONFIG_FILE = Path(__file__).parent / "config.json"
DATA_DIR = Path(__file__).parent / "data"

# Ensure data directory exists
DATA_DIR.mkdir(exist_ok=True)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_config():
    """Load configuration from config.json"""
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    else:
        # Create default config
        default_config = {
            "news_api_key": "",
            "twitter_api_key": "",
            "default_frequency": 300,
            "sentiment_threshold": 0.3,
            "storage_path": "./data"
        }
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(default_config, f, indent=2)
        return default_config


def fetch_news_headlines(symbol, api_key=None):
    """
    Fetch news headlines for a stock symbol
    
    Args:
        symbol: Stock symbol (e.g., TSLA, AAPL)
        api_key: NewsAPI key (optional, will use demo endpoint if not provided)
    
    Returns:
        list: List of news articles with title, url, published_at
    """
    articles = []
    
    # Try NewsAPI first
    if api_key:
        try:
            url = f"https://newsapi.org/v2/everything"
            params = {
                "q": symbol,
                "language": "en",
                "sortBy": "publishedAt",
                "pageSize": 20,
                "apiKey": api_key
            }
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                articles = data.get("articles", [])
                logger.info(f"Fetched {len(articles)} articles from NewsAPI")
        except Exception as e:
            logger.warning(f"NewsAPI failed: {e}")
    
    # Fallback: Use free financial news sources
    if not articles:
        logger.info("Using fallback news sources...")
        # Simulate news data for demo purposes
        # In production, you would scrape Yahoo Finance, Google Finance, etc.
        articles = simulate_news_data(symbol)
    
    return articles


def simulate_news_data(symbol):
    """
    Simulate news data for testing/demo purposes
    
    Args:
        symbol: Stock symbol
    
    Returns:
        list: Simulated news articles
    """
    # This is a demo - in production, you would use real news APIs
    demo_articles = [
        {
            "title": f"{symbol} Stock Rises on Strong Earnings Report",
            "url": "https://example.com/news1",
            "publishedAt": datetime.now().isoformat(),
            "source": {"name": "Financial Times"}
        },
        {
            "title": f"Analysts Upgrade {symbol} Price Target",
            "url": "https://example.com/news2",
            "publishedAt": (datetime.now() - timedelta(hours=2)).isoformat(),
            "source": {"name": "Bloomberg"}
        },
        {
            "title": f"{symbol} Announces New Product Launch",
            "url": "https://example.com/news3",
            "publishedAt": (datetime.now() - timedelta(hours=5)).isoformat(),
            "source": {"name": "Reuters"}
        },
        {
            "title": f"Market Volatility Affects {symbol} Shares",
            "url": "https://example.com/news4",
            "publishedAt": (datetime.now() - timedelta(hours=8)).isoformat(),
            "source": {"name": "CNBC"}
        },
        {
            "title": f"{symbol} CEO Makes Bold Statement at Conference",
            "url": "https://example.com/news5",
            "publishedAt": (datetime.now() - timedelta(hours=12)).isoformat(),
            "source": {"name": "Wall Street Journal"}
        }
    ]
    return demo_articles


def analyze_sentiment(text):
    """
    Analyze sentiment of text using TextBlob and VADER
    
    Args:
        text: Text to analyze
    
    Returns:
        dict: Sentiment analysis results
    """
    # TextBlob analysis
    blob = TextBlob(text)
    polarity_tb = blob.sentiment.polarity
    subjectivity_tb = blob.sentiment.subjectivity
    
    # VADER analysis
    analyzer = SentimentIntensityAnalyzer()
    vader_scores = analyzer.polarity_scores(text)
    compound = vader_scores['compound']
    
    # Combined sentiment
    combined_polarity = (polarity_tb + compound) / 2
    
    # Determine sentiment label
    if combined_polarity >= 0.05:
        label = "positive"
    elif combined_polarity <= -0.05:
        label = "negative"
    else:
        label = "neutral"
    
    return {
        "polarity": round(combined_polarity, 3),
        "subjectivity": round(subjectivity_tb, 3),
        "label": label,
        "textblob": {
            "polarity": round(polarity_tb, 3),
            "subjectivity": round(subjectivity_tb, 3)
        },
        "vader": {
            "compound": round(compound, 3),
            "positive": round(vader_scores['pos'], 3),
            "neutral": round(vader_scores['neu'], 3),
            "negative": round(vader_scores['neg'], 3)
        }
    }


def analyze_stock_sentiment(symbol, config):
    """
    Analyze overall sentiment for a stock
    
    Args:
        symbol: Stock symbol
        config: Configuration dict
    
    Returns:
        dict: Sentiment analysis results
    """
    logger.info(f"Analyzing sentiment for {symbol}...")
    
    # Fetch news
    articles = fetch_news_headlines(symbol, config.get("news_api_key"))
    
    if not articles:
        logger.warning(f"No news found for {symbol}")
        return None
    
    # Analyze each article
    sentiments = []
    for article in articles:
        title = article.get("title", "")
        if title:
            sentiment = analyze_sentiment(title)
            sentiment["title"] = title
            sentiment["source"] = article.get("source", {}).get("name", "Unknown")
            sentiment["url"] = article.get("url", "")
            sentiment["published_at"] = article.get("publishedAt", "")
            sentiments.append(sentiment)
            logger.info(f"  [{sentiment['label'].upper()}] {title[:60]}...")
    
    # Calculate aggregate sentiment
    if sentiments:
        avg_polarity = np.mean([s["polarity"] for s in sentiments])
        avg_subjectivity = np.mean([s["subjectivity"] for s in sentiments])
        
        # Determine overall label
        if avg_polarity >= 0.05:
            overall_label = "positive"
        elif avg_polarity <= -0.05:
            overall_label = "negative"
        else:
            overall_label = "neutral"
        
        # Count by label
        label_counts = {
            "positive": sum(1 for s in sentiments if s["label"] == "positive"),
            "neutral": sum(1 for s in sentiments if s["label"] == "neutral"),
            "negative": sum(1 for s in sentiments if s["label"] == "negative")
        }
        
        result = {
            "symbol": symbol,
            "timestamp": datetime.now().isoformat(),
            "articles_analyzed": len(sentiments),
            "overall_sentiment": {
                "polarity": round(avg_polarity, 3),
                "subjectivity": round(avg_subjectivity, 3),
                "label": overall_label
            },
            "label_distribution": label_counts,
            "articles": sentiments
        }
        
        # Save to file
        save_sentiment_data(symbol, result)
        
        return result
    else:
        return None


def save_sentiment_data(symbol, data):
    """Save sentiment data to JSON file"""
    filename = DATA_DIR / f"{symbol.lower()}_sentiment.json"
    
    # Load existing data
    if filename.exists():
        with open(filename, 'r', encoding='utf-8') as f:
            history = json.load(f)
    else:
        history = []
    
    # Append new data
    history.append(data)
    
    # Keep only last 100 entries
    history = history[-100:]
    
    # Save
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(history, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Saved sentiment data to {filename}")


def load_sentiment_history(symbol):
    """Load historical sentiment data"""
    filename = DATA_DIR / f"{symbol.lower()}_sentiment.json"
    if filename.exists():
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []


def predict_price_movement(symbol, sentiment_data):
    """
    Predict short-term price movement based on sentiment
    
    Args:
        symbol: Stock symbol
        sentiment_data: Sentiment analysis results
    
    Returns:
        dict: Prediction results
    """
    if not sentiment_data:
        return None
    
    polarity = sentiment_data["overall_sentiment"]["polarity"]
    label = sentiment_data["overall_sentiment"]["label"]
    article_count = sentiment_data["articles_analyzed"]
    
    # Simple prediction logic (can be enhanced with ML)
    if label == "positive" and polarity > 0.3:
        direction = "up"
        confidence = min(0.9, 0.5 + polarity * 0.4)
    elif label == "negative" and polarity < -0.3:
        direction = "down"
        confidence = min(0.9, 0.5 + abs(polarity) * 0.4)
    else:
        direction = "sideways"
        confidence = 0.5
    
    # Adjust confidence based on article count
    if article_count < 5:
        confidence *= 0.8
    elif article_count > 20:
        confidence = min(0.95, confidence * 1.1)
    
    prediction = {
        "symbol": symbol,
        "timestamp": datetime.now().isoformat(),
        "prediction": {
            "direction": direction,
            "confidence": round(confidence, 3),
            "timeframe": "1d"
        },
        "based_on": {
            "sentiment_label": label,
            "polarity": polarity,
            "articles": article_count
        }
    }
    
    # Save prediction
    save_prediction(symbol, prediction)
    
    return prediction


def save_prediction(symbol, data):
    """Save prediction to JSON file"""
    filename = DATA_DIR / f"{symbol.lower()}_predictions.json"
    
    # Load existing data
    if filename.exists():
        with open(filename, 'r', encoding='utf-8') as f:
            history = json.load(f)
    else:
        history = []
    
    # Append new data
    history.append(data)
    
    # Keep only last 50 entries
    history = history[-50:]
    
    # Save
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(history, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Saved prediction to {filename}")


def print_results(symbol, sentiment_data, prediction_data=None):
    """Print formatted results to console"""
    print("\n" + "="*60)
    print(f"📊 STOCKSIGHT ANALYSIS: {symbol}")
    print("="*60)
    
    if sentiment_data:
        print(f"\n📰 Articles Analyzed: {sentiment_data['articles_analyzed']}")
        print(f"\n💭 Overall Sentiment:")
        print(f"   Label: {sentiment_data['overall_sentiment']['label'].upper()}")
        print(f"   Polarity: {sentiment_data['overall_sentiment']['polarity']}")
        print(f"   Subjectivity: {sentiment_data['overall_sentiment']['subjectivity']}")
        
        print(f"\n📈 Label Distribution:")
        dist = sentiment_data['label_distribution']
        print(f"   Positive: {dist['positive']}")
        print(f"   Neutral: {dist['neutral']}")
        print(f"   Negative: {dist['negative']}")
        
        print(f"\n📝 Recent Headlines:")
        for i, article in enumerate(sentiment_data['articles'][:5], 1):
            emoji = "✅" if article['label'] == 'positive' else "❌" if article['label'] == 'negative' else "➖"
            print(f"   {i}. {emoji} [{article['label'].upper()}] {article['title'][:50]}...")
    
    if prediction_data:
        print(f"\n🔮 Price Prediction (1 day):")
        pred = prediction_data['prediction']
        arrow = "📈" if pred['direction'] == 'up' else "📉" if pred['direction'] == 'down' else "➡️"
        print(f"   Direction: {arrow} {pred['direction'].upper()}")
        print(f"   Confidence: {pred['confidence']*100:.1f}%")
    
    print("\n" + "="*60)


def main():
    parser = argparse.ArgumentParser(
        description="stocksight - Stock Market Sentiment Analyzer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python stocksight.py --symbol TSLA --analyze
  python stocksight.py --symbol AAPL --news
  python stocksight.py --symbol NVDA --predict
  python stocksight.py --symbol TSLA --history
        """
    )
    
    parser.add_argument("--symbol", "-s", required=True, help="Stock symbol (e.g., TSLA, AAPL)")
    parser.add_argument("--analyze", "-a", action="store_true", help="Analyze sentiment")
    parser.add_argument("--news", "-n", action="store_true", help="Fetch and analyze news")
    parser.add_argument("--predict", "-p", action="store_true", help="Generate price prediction")
    parser.add_argument("--history", action="store_true", help="Show sentiment history")
    parser.add_argument("--config", "-c", type=str, help="Path to config file")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    # Load config
    config = load_config()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Analyze sentiment
    if args.analyze or args.news:
        sentiment_data = analyze_stock_sentiment(args.symbol.upper(), config)
        if sentiment_data:
            print_results(args.symbol.upper(), sentiment_data)
    
    # Generate prediction
    if args.predict:
        # Load latest sentiment
        history = load_sentiment_history(args.symbol.upper())
        if history:
            latest_sentiment = history[-1]
            prediction = predict_price_movement(args.symbol.upper(), latest_sentiment)
            if prediction:
                print_results(args.symbol.upper(), latest_sentiment, prediction)
        else:
            logger.warning(f"No sentiment history found for {args.symbol}. Run --analyze first.")
    
    # Show history
    if args.history:
        history = load_sentiment_history(args.symbol.upper())
        if history:
            print(f"\n📜 Sentiment History for {args.symbol.upper()}:")
            print(f"Total records: {len(history)}")
            print("\nLast 5 entries:")
            for entry in history[-5:]:
                print(f"  {entry['timestamp'][:16]} - {entry['overall_sentiment']['label']:10} (polarity: {entry['overall_sentiment']['polarity']})")
        else:
            print(f"No history found for {args.symbol.upper()}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Error: {e}")
        if "--debug" in sys.argv:
            raise
        sys.exit(1)
