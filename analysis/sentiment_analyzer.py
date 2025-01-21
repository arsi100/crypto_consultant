from typing import Dict, List
import nltk
from nltk.sentiment import SentimentIntensityAnalyzer
from statistics import mean

# Download required NLTK data
nltk.download('vader_lexicon')

def analyze_sentiment(news_items: List[Dict]) -> Dict:
    """
    Analyze sentiment of news articles using NLTK's VADER
    """
    sia = SentimentIntensityAnalyzer()
    
    sentiments = []
    for item in news_items:
        # Analyze both title and content
        title_sentiment = sia.polarity_scores(item['title'])
        content_sentiment = sia.polarity_scores(item['content']) if item['content'] else {'compound': 0}
        
        # Calculate weighted average (title has more weight)
        combined_sentiment = (title_sentiment['compound'] * 0.4 + 
                            content_sentiment['compound'] * 0.6)
        
        sentiments.append(combined_sentiment)
        
        # Add sentiment to news item
        item['sentiment'] = 'positive' if combined_sentiment > 0.05 else 'negative' if combined_sentiment < -0.05 else 'neutral'

    # Calculate overall sentiment
    avg_sentiment = mean(sentiments)
    
    return {
        'overall': 'positive' if avg_sentiment > 0.05 else 'negative' if avg_sentiment < -0.05 else 'neutral',
        'score': round(avg_sentiment, 2),
        'distribution': {
            'positive': len([s for s in sentiments if s > 0.05]),
            'neutral': len([s for s in sentiments if -0.05 <= s <= 0.05]),
            'negative': len([s for s in sentiments if s < -0.05])
        }
    }
