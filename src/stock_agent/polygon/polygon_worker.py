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
        
        # Caching to minimize API calls
        self.cache = {
            'market_aggregates': {},  # date -> aggregates data
            'search_results': {},     # query -> search results
            'ticker_info': {},        # ticker -> ticker info
        }
        self.cache_ttl = {
            'market_aggregates': 3600,  # 1 hour (daily data doesn't change much)
            'search_results': 1800,     # 30 minutes (ticker lists are fairly stable)
            'ticker_info': 3600,        # 1 hour (company info is stable)
        }
        self.cache_timestamps = {
            'market_aggregates': {},
            'search_results': {},
            'ticker_info': {},
        }

    def _check_rate_limit(self):
        """Check if we can make a call without blocking. Raises exception if rate limited."""
        now = time.time()
        
        # Remove calls older than the rate window
        while self.call_times and now - self.call_times[0] >= self.rate_window:
            self.call_times.popleft()
        
        # If we're at the rate limit, raise an exception instead of blocking
        if len(self.call_times) >= self.rate_limit:
            sleep_time = self.rate_window - (now - self.call_times[0]) + 0.1
            if sleep_time > 0:
                print(f"Rate limit reached, would need to wait {sleep_time:.1f} seconds. Failing fast.")
                raise Exception(f"Polygon API rate limit exceeded. Try again in {sleep_time:.0f} seconds.")
        
        # Record this call
        self.call_times.append(now)
    
    def _is_cache_valid(self, cache_type: str, key: str) -> bool:
        """Check if cached data is still valid"""
        if key not in self.cache[cache_type]:
            return False
        
        timestamp = self.cache_timestamps[cache_type].get(key, 0)
        ttl = self.cache_ttl[cache_type]
        return time.time() - timestamp < ttl
    
    def _set_cache(self, cache_type: str, key: str, data):
        """Store data in cache with timestamp"""
        self.cache[cache_type][key] = data
        self.cache_timestamps[cache_type][key] = time.time()
    
    def _get_cache(self, cache_type: str, key: str):
        """Get data from cache if valid"""
        if self._is_cache_valid(cache_type, key):
            return self.cache[cache_type][key]
        return None

    def get_market_aggregates(self, date=datetime.date.today().isoformat()):
        """
        Get grouped daily aggregates for all tickers on a given date
        Date has to be in ISO format - YYYY-MM-DD
        """
        # Check cache first
        cached_data = self._get_cache('market_aggregates', date)
        if cached_data is not None:
            print(f"Using cached market aggregates for {date}")
            return cached_data
        
        self._check_rate_limit()
        try:
            grouped_aggs = self.client.get_grouped_daily_aggs(
                date,
                adjusted=True,
            )
            # Cache the result
            self._set_cache('market_aggregates', date, grouped_aggs)
            print(f"Fetched and cached market aggregates for {date}")
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
        # Create cache key that includes query and limit
        cache_key = f"{query.lower()}:{limit}"
        
        # Check cache first
        cached_data = self._get_cache('search_results', cache_key)
        if cached_data is not None:
            print(f"Using cached search results for '{query}'")
            return cached_data
        
        self._check_rate_limit()
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
                ticker_data = {
                    'ticker': ticker.ticker,
                    'company_name': ticker.name or f"{ticker.ticker} Corporation"
                }
                results.append(ticker_data)
                
                # Also cache individual ticker info while we have it
                self._set_cache('ticker_info', ticker.ticker, {
                    'ticker': ticker.ticker,
                    'company_name': ticker.name or f"{ticker.ticker} Corporation",
                    'market': getattr(ticker, 'market', 'stocks'),
                    'locale': getattr(ticker, 'locale', 'us'),
                    'primary_exchange': getattr(ticker, 'primary_exchange', None),
                    'type': getattr(ticker, 'type', None),
                    'active': getattr(ticker, 'active', True),
                    'currency_name': getattr(ticker, 'currency_name', 'USD'),
                    'cik': getattr(ticker, 'cik', None),
                    'composite_figi': getattr(ticker, 'composite_figi', None),
                    'share_class_figi': getattr(ticker, 'share_class_figi', None),
                    'last_updated_utc': getattr(ticker, 'last_updated_utc', None)
                })
            
            # Cache the search results
            self._set_cache('search_results', cache_key, results)
            print(f"Fetched and cached search results for '{query}' ({len(results)} results)")
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
        # Check cache first
        cached_data = self._get_cache('ticker_info', ticker)
        if cached_data is not None:
            return cached_data
        
        self._check_rate_limit()
        try:
            # Use reference tickers API to get ticker info
            tickers = self.client.list_tickers(
                ticker=ticker,
                active=True,
                market='stocks',
                limit=1
            )
            
            for ticker_info in tickers:
                result = {
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
                # Cache the result
                self._set_cache('ticker_info', ticker, result)
                return result
            
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
    
    def get_cache_stats(self) -> Dict[str, Dict]:
        """Get cache statistics for monitoring"""
        stats = {}
        for cache_type in self.cache:
            valid_count = 0
            total_count = len(self.cache[cache_type])
            
            for key in self.cache[cache_type]:
                if self._is_cache_valid(cache_type, key):
                    valid_count += 1
            
            stats[cache_type] = {
                'total_entries': total_count,
                'valid_entries': valid_count,
                'expired_entries': total_count - valid_count,
                'ttl_seconds': self.cache_ttl[cache_type]
            }
        
        return stats
    
    def clear_expired_cache(self):
        """Clear expired cache entries to free memory"""
        for cache_type in self.cache:
            expired_keys = []
            for key in self.cache[cache_type]:
                if not self._is_cache_valid(cache_type, key):
                    expired_keys.append(key)
            
            for key in expired_keys:
                del self.cache[cache_type][key]
                del self.cache_timestamps[cache_type][key]
            
            if expired_keys:
                print(f"Cleared {len(expired_keys)} expired {cache_type} entries")
