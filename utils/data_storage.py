import json
from datetime import datetime
from typing import Dict
import pandas as pd

def store_analysis_results(analysis_data: Dict):
    """
    Store analysis results for historical reference
    """
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    
    # Convert DataFrame objects to lists for JSON serialization
    if 'social_data' in analysis_data:
        if isinstance(analysis_data['social_data']['reddit'], pd.DataFrame):
            analysis_data['social_data']['reddit'] = analysis_data['social_data']['reddit'].to_dict('records')
        if isinstance(analysis_data['social_data']['twitter'], pd.DataFrame):
            analysis_data['social_data']['twitter'] = analysis_data['social_data']['twitter'].to_dict('records')

    # Store as JSON file
    try:
        with open(f'analysis_history_{timestamp}.json', 'w') as f:
            json.dump(analysis_data, f, indent=4)
    except Exception as e:
        print(f"Error storing analysis results: {e}")

def load_historical_analysis(start_date: str, end_date: str) -> list:
    """
    Load historical analysis results for a given date range
    """
    # Implementation for loading historical data
    # This would be expanded based on specific needs
    return []
