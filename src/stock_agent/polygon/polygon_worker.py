import datetime
import time
from polygon import RESTClient
import os
from typing import List, Dict, Optional
from collections import deque


class PolygonWorker:
    def __init__(self):
        api_key = os.getenv('POLYGON_API_KEY')
        if not api_key:
            raise Exception("Polygon API not available - check POLYGON_API_KEY")
        self.client = RESTClient(api_key)
        
        # Rate limiting: 5 calls per minute for free tier
        self.rate_limit = 5
        self.rate_window = 60  # seconds
        self.call_times = deque()
    
    def _wait_for_rate_limit(self):
        """Ensure we don't exceed the rate limit of 5 calls per minute"""
        now = time.time()
        
        # Remove calls older than the rate window
        while self.call_times and now - self.call_times[0] >= self.rate_window:
            self.call_times.popleft()
        
        # If we're at the rate limit, wait until we can make another call
        if len(self.call_times) >= self.rate_limit:
            sleep_time = self.rate_window - (now - self.call_times[0]) + 0.1  # Add small buffer
            if sleep_time > 0:
                print(f"Rate limit reached, waiting {sleep_time:.1f} seconds...")
                time.sleep(sleep_time)
                # Clean up old calls after waiting
                now = time.time()
                while self.call_times and now - self.call_times[0] >= self.rate_window:
                    self.call_times.popleft()
        
        # Record this call
        self.call_times.append(now)

    def get_market_aggregates(self, date=datetime.date.today().isoformat()):
        """
        Get grouped daily aggregates for all tickers on a given date
        Date has to be in ISO format - YYYY-MM-DD
        """
        self._wait_for_rate_limit()
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
        self._wait_for_rate_limit()
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
        self._wait_for_rate_limit()
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
