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
        # For now, return the query as a ticker if it looks valid
        query = query.upper().strip()
        
        if len(query) <= 5 and query.isalpha():
            # Return the ticker - Polygon API will validate it when we get price data
            return [{'ticker': query, 'company_name': f'{query}'}]
        
        return []

    def get_stock_data(self, tickers: List[str]) -> List[StockData]:
        """Get current stock data for given tickers using Polygon API"""
        if not self.stock_worker:
            raise Exception("Polygon API not available - check POLYGON_API_KEY")
        
        stock_data = []
        
        for ticker in tickers:
            try:
                # Use Polygon API to get real stock data
                # This would need to be implemented in polygon_worker.py
                # For now, raise an exception to indicate real API is needed
                raise NotImplementedError(f"Real Polygon API integration needed for ticker: {ticker}")
                
            except Exception as e:
                # If we can't get real data, skip this ticker
                print(f"Failed to get data for {ticker}: {e}")
                continue
        
        return stock_data

    def get_major_indexes(self) -> List[StockData]:
        """Get data for major stock indexes using Polygon API"""
        # Major market indexes - these would need real Polygon API implementation
        major_tickers = ['DJI', 'SPX', 'IXIC', 'SWTSX']
        return self.get_stock_data(major_tickers)

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=".dev.env")
    service = StockService()
    df = service.generate_market_summary()
    print(df.head())
