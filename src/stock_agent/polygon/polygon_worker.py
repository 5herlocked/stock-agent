import datetime
from polygon import RESTClient
import os
from typing import List, Dict, Optional


class PolygonWorker:
    def __init__(self):
        api_key = os.getenv('POLYGON_API_KEY')
        if not api_key:
            raise Exception("Polygon API not available - check POLYGON_API_KEY")
        self.client = RESTClient(api_key)

    def get_market_aggregates(self, date=datetime.date.today().isoformat()):
        """
            Date has to be in ISO format - YYYY-MM-DD
        """
        grouped_aggs = self.client.get_grouped_daily_aggs(
            date,
            adjusted=True,
        )
        return grouped_aggs

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
                limit=min(limit, 10),  # Respect API limits
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

    def get_ticker_details(self, ticker: str) -> Optional[Dict]:
        """
        Get detailed information about a specific ticker
        
        Args:
            ticker: The ticker symbol to get details for
            
        Returns:
            Dictionary with ticker details or None if not found
        """
        try:
            details = self.client.get_ticker_details(ticker)
            return {
                'ticker': details.ticker,
                'company_name': details.name,
                'market_cap': getattr(details, 'market_cap', None),
                'description': getattr(details, 'description', None),
                'homepage_url': getattr(details, 'homepage_url', None),
                'total_employees': getattr(details, 'total_employees', None),
                'list_date': getattr(details, 'list_date', None),
                'locale': getattr(details, 'locale', None),
                'primary_exchange': getattr(details, 'primary_exchange', None),
                'type': getattr(details, 'type', None),
                'currency_name': getattr(details, 'currency_name', None),
                'cik': getattr(details, 'cik', None),
                'composite_figi': getattr(details, 'composite_figi', None),
                'share_class_figi': getattr(details, 'share_class_figi', None),
                'phone_number': getattr(details, 'phone_number', None),
                'address': getattr(details, 'address', None),
                'sic_code': getattr(details, 'sic_code', None),
                'sic_description': getattr(details, 'sic_description', None),
                'ticker_root': getattr(details, 'ticker_root', None),
                'active': getattr(details, 'active', True),
            }
        except Exception as e:
            print(f"Error getting ticker details for {ticker}: {e}")
            return None

    def get_previous_close(self, ticker: str) -> Optional[Dict]:
        """
        Get the previous trading day's close price for a ticker
        
        Args:
            ticker: The ticker symbol to get data for
            
        Returns:
            Dictionary with price data or None if not found
        """
        try:
            prev_close = self.client.get_previous_close_agg(ticker)
            if prev_close and len(prev_close) > 0:
                data = prev_close[0]
                return {
                    'ticker': data.ticker,
                    'close': data.close,
                    'high': data.high,
                    'low': data.low,
                    'open': data.open,
                    'volume': data.volume,
                    'vwap': getattr(data, 'vwap', None),
                    'timestamp': data.timestamp,
                    'transactions': getattr(data, 'transactions', None)
                }
            return None
        except Exception as e:
            print(f"Error getting previous close for {ticker}: {e}")
            return None

    def get_daily_open_close(self, ticker: str, date: str = None) -> Optional[Dict]:
        """
        Get daily open/close data for a ticker
        
        Args:
            ticker: The ticker symbol
            date: Date in YYYY-MM-DD format (defaults to previous trading day)
            
        Returns:
            Dictionary with daily data or None if not found
        """
        try:
            if not date:
                # Use previous trading day
                from datetime import datetime, timedelta
                yesterday = datetime.now() - timedelta(days=1)
                date = yesterday.strftime('%Y-%m-%d')
            
            daily_data = self.client.get_daily_open_close_agg(ticker, date)
            if daily_data:
                return {
                    'ticker': ticker,
                    'date': date,
                    'open': daily_data.open,
                    'close': daily_data.close,
                    'high': daily_data.high,
                    'low': daily_data.low,
                    'volume': daily_data.volume,
                    'after_hours': getattr(daily_data, 'after_hours', None),
                    'pre_market': getattr(daily_data, 'pre_market', None)
                }
            return None
        except Exception as e:
            print(f"Error getting daily data for {ticker} on {date}: {e}")
            return None

    def get_last_trade(self, ticker: str) -> Optional[Dict]:
        """
        Get the last trade for a ticker
        
        Args:
            ticker: The ticker symbol
            
        Returns:
            Dictionary with last trade data or None if not found
        """
        try:
            last_trade = self.client.get_last_trade(ticker)
            if last_trade:
                return {
                    'ticker': ticker,
                    'price': last_trade.price,
                    'size': last_trade.size,
                    'exchange': getattr(last_trade, 'exchange', None),
                    'timestamp': last_trade.participant_timestamp,
                    'conditions': getattr(last_trade, 'conditions', None),
                    'sequence_number': getattr(last_trade, 'sequence_number', None)
                }
            return None
        except Exception as e:
            print(f"Error getting last trade for {ticker}: {e}")
            return None

    def get_snapshot(self, ticker: str) -> Optional[Dict]:
        """
        Get current snapshot data for a ticker (most comprehensive current data)
        
        Args:
            ticker: The ticker symbol
            
        Returns:
            Dictionary with snapshot data or None if not found
        """
        try:
            snapshot = self.client.get_snapshot_ticker("stocks", ticker)
            if snapshot:
                # Extract data from snapshot
                day_data = getattr(snapshot, 'day', None)
                prev_day_data = getattr(snapshot, 'prev_day', None)
                last_quote = getattr(snapshot, 'last_quote', None)
                last_trade = getattr(snapshot, 'last_trade', None)
                
                result = {
                    'ticker': snapshot.ticker,
                    'updated': getattr(snapshot, 'updated', None),
                    'market_status': getattr(snapshot, 'market_status', None),
                    'fmv': getattr(snapshot, 'fmv', None)
                }
                
                # Add day data if available
                if day_data:
                    result.update({
                        'open': getattr(day_data, 'open', None),
                        'high': getattr(day_data, 'high', None),
                        'low': getattr(day_data, 'low', None),
                        'close': getattr(day_data, 'close', None),
                        'volume': getattr(day_data, 'volume', None),
                        'vwap': getattr(day_data, 'vwap', None)
                    })
                
                # Add previous day data for change calculation
                if prev_day_data:
                    prev_close = getattr(prev_day_data, 'close', None)
                    current_close = result.get('close')
                    if prev_close and current_close:
                        change = current_close - prev_close
                        change_percent = (change / prev_close) * 100
                        result.update({
                            'prev_close': prev_close,
                            'change': round(change, 2),
                            'change_percent': round(change_percent, 2)
                        })
                
                # Add last trade price if no close price
                if not result.get('close') and last_trade:
                    result['close'] = getattr(last_trade, 'price', None)
                
                return result
            return None
        except Exception as e:
            print(f"Error getting snapshot for {ticker}: {e}")
            return None
