import datetime
from polygon import RESTClient
import os
from typing import List, Dict, Optional


class PolygonWorker:
    def __init__(self):
        # Try to get API key from environment or .dev.env
        api_key = os.getenv('POLYGON_API_KEY')
        
        # If not in environment, try to load from .dev.env
        if not api_key:
            try:
                from dotenv import load_dotenv
                load_dotenv('.dev.env')
                api_key = os.getenv('POLYGON_API_KEY')
            except ImportError:
                pass  # dotenv not available
        
        if not api_key:
            raise Exception("Polygon API not available - check POLYGON_API_KEY in environment or .dev.env")
        
        self.client = RESTClient(api_key)

    def get_market_aggregates(self, date=datetime.date.today().isoformat()):
        """
        Get grouped daily aggregates for all tickers on a given date
        Date has to be in ISO format - YYYY-MM-DD
        """
        try:
            grouped_aggs = self.client.get_grouped_daily_aggs(
                date,
                adjusted=True,
            )
            return grouped_aggs
        except Exception as e:
            print(f"Error getting market aggregates for {date}: {e}")
            return []

    def search_tickers(self, query: str, limit: int = 10) -> List[Dict]:
        """
        Search for tickers using Polygon's reference tickers API
        
        Args:
            query: Search term for ticker symbol or company name
            limit: Maximum number of results to return (default 10, max 1000)
            
        Returns:
            List of dictionaries containing ticker and company name
        """
        try:
            # Use the reference tickers API with search parameter
            tickers = self.client.list_tickers(
                search=query,
                active=True,  # Only active tickers
                market='stocks',  # Only stock market
                limit=min(limit, 1000),  # Respect API limits
                order='asc',
                sort='ticker'
            )
            
            results = []
            for ticker in tickers:
                results.append({
                    'ticker': ticker.ticker,
                    'company_name': ticker.name or f"{ticker.ticker} Corporation"
                })
            
            return results
            
        except Exception as e:
            print(f"Error searching tickers: {e}")
            return []

    def get_ticker_info(self, ticker: str) -> Optional[Dict]:
        """
        Get basic ticker information using reference tickers API
        
        Args:
            ticker: The ticker symbol to get info for
            
        Returns:
            Dictionary with ticker info or None if not found
        """
        try:
            # Use reference tickers API to get ticker info
            tickers = self.client.list_tickers(
                ticker=ticker,
                active=True,
                market='stocks',
                limit=1
            )
            
            for ticker_info in tickers:
                return {
                    'ticker': ticker_info.ticker,
                    'company_name': ticker_info.name or f"{ticker_info.ticker} Corporation",
                    'market': getattr(ticker_info, 'market', 'stocks'),
                    'locale': getattr(ticker_info, 'locale', 'us'),
                    'primary_exchange': getattr(ticker_info, 'primary_exchange', None),
                    'type': getattr(ticker_info, 'type', None),
                    'active': getattr(ticker_info, 'active', True),
                    'currency_name': getattr(ticker_info, 'currency_name', 'USD'),
                    'cik': getattr(ticker_info, 'cik', None),
                    'composite_figi': getattr(ticker_info, 'composite_figi', None),
                    'share_class_figi': getattr(ticker_info, 'share_class_figi', None),
                    'last_updated_utc': getattr(ticker_info, 'last_updated_utc', None)
                }
            
            return None
            
        except Exception as e:
            print(f"Error getting ticker info for {ticker}: {e}")
            return None

    def get_stock_data_from_aggregates(self, tickers: List[str], date: str = None) -> Dict[str, Dict]:
        """
        Get stock data for multiple tickers from grouped aggregates
        
        Args:
            tickers: List of ticker symbols
            date: Date in YYYY-MM-DD format (defaults to today)
            
        Returns:
            Dictionary mapping ticker to stock data
        """
        if not date:
            date = datetime.date.today().isoformat()
            
        try:
            # Get all market data for the date
            aggregates = self.get_market_aggregates(date)
            
            # Create lookup dictionary
            ticker_data = {}
            for agg in aggregates:
                if agg.ticker in tickers:
                    ticker_data[agg.ticker] = {
                        'ticker': agg.ticker,
                        'open': agg.open,
                        'high': agg.high,
                        'low': agg.low,
                        'close': agg.close,
                        'volume': agg.volume,
                        'vwap': getattr(agg, 'vwap', None),
                        'timestamp': agg.timestamp,
                        'transactions': getattr(agg, 'transactions', None),
                        'date': date
                    }
            
            return ticker_data
            
        except Exception as e:
            print(f"Error getting stock data from aggregates: {e}")
            return {}
