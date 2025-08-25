from polygon.rest.models.aggs import GroupedDailyAgg
from stock_agent.polygon.polygon_worker import PolygonWorker
from ..notification_service import NotificationService
from ..auth.models import StockData
import pandas as pd
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class StockMetrics:
    """Represents daily market metrics for a stock.
    """
    ticker: str          # T: The exchange symbol
    close: float        # c: Close price
    high: float         # h: Highest price
    low: float          # l: Lowest price
    open: float         # o: Open price
    volume: float       # v: Trading volume
    vwap: float        # vw: Volume weighted average price
    transactions: int   # n: Number of transactions
    timestamp: int      # t: Unix millisecond timestamp

    @staticmethod
    def from_polygon(polygon_metrics: GroupedDailyAgg):
        """Update metrics from Polygon API response"""
        return StockMetrics(
            close=polygon_metrics.close if polygon_metrics.close is not None else 0.0,
            high=polygon_metrics.high if polygon_metrics.high is not None else 0.0,
            low=polygon_metrics.low if polygon_metrics.low is not None else 0.0,
            open=polygon_metrics.open if polygon_metrics.open is not None else 0.0,
            volume=polygon_metrics.volume if polygon_metrics.volume is not None else 0.0,
            vwap=polygon_metrics.vwap if polygon_metrics.vwap else 0.0,
            transactions=polygon_metrics.transactions if polygon_metrics.transactions else 0,
            timestamp=polygon_metrics.timestamp if polygon_metrics.timestamp is not None else 0,
            ticker=polygon_metrics.ticker if polygon_metrics.ticker else ""
        )

class StockService:
    """Service for retrieving and analyzing stock market data.

    Example:
        service = StockService()
        df = service.generate_market_summary()

        # Access data for a specific stock and date
        aapl_metrics = df.loc['AAPL']['2023-11-20']
        print(f"AAPL close: ${aapl_metrics.close:.2f}")
        print(f"AAPL volume: {aapl_metrics.volume:,.0f}")

        # Calculate daily returns for AAPL
        aapl_closes = [df.loc['AAPL'][date].close for date in df.columns]
        print(f"AAPL prices over last 5 days: {aapl_closes}")

        # Find stocks with highest volume
        for ticker in df.index:
            latest_metrics = df.iloc[0][ticker]  # Most recent day
            if latest_metrics.volume > 1000000:
                print(f"{ticker}: {latest_metrics.volume:,.0f} shares")
    """
    def __init__(self):
        try:
            self.stock_worker = PolygonWorker()
        except Exception:
            # Fallback if no API key or polygon service unavailable
            self.stock_worker = None
        
        try:
            self.notification_service = NotificationService()
        except Exception:
            # Fallback if Firebase not configured
            self.notification_service = None
        
        self.current_summary = None

    def generate_market_summary(self):
        """
        Get market summary for the last five days, organized by ticker and date.
        Returns a DataFrame with tickers as index and dates as columns.
        Each cell contains a dataclass of metrics (close, volume, etc.) for that ticker/date.
        """
        # Calculate dates for the last 5 trading days
        dates = []
        current_date = datetime.now().date() - timedelta(days=1)  # Start from yesterday
        days_back = 0

        # Get 5 days worth of dates, skipping weekends
        while len(dates) < 5:
            check_date = current_date - timedelta(days=days_back)
            if check_date.weekday() < 5:  # Monday = 0, Friday = 4
                dates.append(check_date.isoformat())
            days_back += 1

        # Dictionary to store data by ticker and date
        data_by_ticker: Dict[str, Dict[str, StockMetrics]] = {}

        # Collect market data for each date
        for date in dates:
            aggs = self.stock_worker.get_market_aggregates(date)
            for agg in aggs:
                metrics = StockMetrics.from_polygon(agg)

                if metrics.ticker not in data_by_ticker:
                    data_by_ticker[metrics.ticker] = {}

                # Store StockMetrics object
                data_by_ticker[metrics.ticker][date] = metrics

        # Convert nested dict to DataFrame
        df = pd.DataFrame.from_dict(data_by_ticker, orient='index')

        # Sort columns by date (most recent first)
        df = df[sorted(dates, reverse=True)]

        self.current_summary = df

        return df

    def send_notification(self, message, topic=""):
        """Send stock-related notifications"""
        if self.notification_service:
            return self.notification_service.send_notification_to_topic(topic, message)
        return False

    def search_stocks(self, query: str) -> List[Dict]:
        """Search for stocks by ticker or company name using Polygon API"""
        if not self.stock_worker:
            raise Exception("Polygon API not available - check POLYGON_API_KEY")
        
        # Use Polygon API to search for stocks
        try:
            results = self.stock_worker.search_tickers(query.strip(), limit=10)
            return results
        except Exception as e:
            print(f"Error searching stocks: {e}")
            return []

    def get_stock_data(self, tickers: List[str]) -> List[StockData]:
        """Get stock data for given tickers using Polygon API grouped aggregates"""
        if not self.stock_worker:
            raise Exception("Polygon API not available - check POLYGON_API_KEY")
        
        stock_data = []
        
        try:
            # Get stock data from grouped aggregates using previous trading day
            # (free tier doesn't allow current day data)
            from datetime import datetime, timedelta
            
            # Try the last few days to find a trading day
            for days_back in range(1, 6):  # Try up to 5 days back
                test_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
                ticker_data = self.stock_worker.get_stock_data_from_aggregates(tickers, test_date)
                if ticker_data:  # Found data for this date
                    break
            else:
                ticker_data = {}  # No data found in the last 5 days

            # Process each ticker (caching in PolygonWorker handles efficiency)
            for ticker in tickers:
                try:
                    # Get ticker info (will use cache if available)
                    ticker_info = self.stock_worker.get_ticker_info(ticker)
                    company_name = ticker_info.get('company_name', f"{ticker} Corporation") if ticker_info else f"{ticker} Corporation"

                    # Get price data from aggregates
                    price_data = ticker_data.get(ticker)
                    
                    if price_data:
                        # Calculate change from open to close
                        open_price = price_data.get('open', 0.0)
                        close_price = price_data.get('close', 0.0)
                        change = close_price - open_price if open_price and close_price else 0.0
                        change_percent = (change / open_price * 100) if open_price else 0.0
                        
                        stock_data.append(StockData(
                            ticker=ticker,
                            company_name=company_name,
                            price=close_price,
                            change=round(change, 2),
                            change_percent=round(change_percent, 2),
                            volume=price_data.get('volume', 0),
                            market_cap="N/A"  # Not available in free tier
                        ))
                    else:
                        # No price data available, create placeholder
                        stock_data.append(StockData(
                            ticker=ticker,
                            company_name=company_name,
                            price=0.0,
                            change=0.0,
                            change_percent=0.0,
                            volume=0,
                            market_cap="N/A"
                        ))
                        
                except Exception as e:
                    print(f"Failed to process data for {ticker}: {e}")
                    continue

        except Exception as e:
            print(f"Failed to get stock data: {e}")
        
        return stock_data

    def get_major_indexes(self) -> List[StockData]:
        """Get data for major stock indexes using Polygon API grouped aggregates"""
        if not self.stock_worker:
            raise Exception("Polygon API not available - check POLYGON_API_KEY")
        
        # Major market indexes - try common ticker symbols
        major_tickers = [
            'DJI',      # Dow Jones Industrial Average
            'SPX',      # S&P 500  
            'IXIC',     # NASDAQ Composite
            'VTI'       # Vanguard Total Stock Market (alternative to SWTSX)
        ]
        
        stock_data = []
        
        try:
            # Get stock data from grouped aggregates using previous trading day
            from datetime import datetime, timedelta
            
            # Try the last few days to find a trading day
            for days_back in range(1, 6):  # Try up to 5 days back
                test_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
                ticker_data = self.stock_worker.get_stock_data_from_aggregates(major_tickers, test_date)
                if ticker_data:  # Found data for this date
                    break
            else:
                ticker_data = {}  # No data found in the last 5 days

            # Process each major index ticker
            for ticker in major_tickers:
                try:
                    # Get price data from aggregates
                    price_data = ticker_data.get(ticker)
                    
                    # Use simple display names for major indexes (no API call needed)
                    index_names = {
                        'DJI': 'Dow Jones Industrial Average',
                        'SPX': 'S&P 500',
                        'IXIC': 'NASDAQ Composite',
                        'VTI': 'Vanguard Total Stock Market ETF'
                    }
                    company_name = index_names.get(ticker, f"{ticker} Index")
                    
                    if price_data:
                        # Calculate change from open to close
                        open_price = price_data.get('open', 0.0)
                        close_price = price_data.get('close', 0.0)
                        change = close_price - open_price if open_price and close_price else 0.0
                        change_percent = (change / open_price * 100) if open_price else 0.0
                        
                        stock_data.append(StockData(
                            ticker=ticker,
                            company_name=company_name,
                            price=close_price,
                            change=round(change, 2),
                            change_percent=round(change_percent, 2),
                            volume=price_data.get('volume', 0),
                            market_cap="N/A"  # Not applicable for indexes
                        ))
                    else:
                        # No price data available, create placeholder
                        stock_data.append(StockData(
                            ticker=ticker,
                            company_name=company_name,
                            price=0.0,
                            change=0.0,
                            change_percent=0.0,
                            volume=0,
                            market_cap="N/A"
                        ))
                        
                except Exception as e:
                    print(f"Failed to process major index {ticker}: {e}")
                    continue
                    
        except Exception as e:
            print(f"Failed to get major indexes data: {e}")
        
        return stock_data

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=".dev.env")
    service = StockService()
    df = service.generate_market_summary()
    print(df.head())
