import random
from typing import List, Dict, Optional
from ..auth.models import StockData

class StockService:
    """Simple stock service with mock data for favorites and dashboard functionality"""
    
    def __init__(self):
        # Major indexes with realistic base prices
        self.major_indexes = {
            'DJI': {'name': 'Dow Jones Industrial Average', 'base_price': 34000},
            'SPX': {'name': 'S&P 500', 'base_price': 4200},
            'IXIC': {'name': 'NASDAQ Composite', 'base_price': 13000}
        }
        
        # Common stock base prices for more realistic mock data
        self.stock_prices = {
            'AAPL': 175, 'MSFT': 350, 'GOOGL': 125, 'AMZN': 140, 'TSLA': 200,
            'META': 300, 'NVDA': 450, 'NFLX': 400, 'AMD': 100, 'INTC': 45,
            'JPM': 150, 'JNJ': 160, 'V': 250, 'PG': 150, 'UNH': 500
        }
        
        # Mock company database
        self.companies = [
            {'ticker': 'AAPL', 'company_name': 'Apple Inc.'},
            {'ticker': 'MSFT', 'company_name': 'Microsoft Corporation'},
            {'ticker': 'GOOGL', 'company_name': 'Alphabet Inc.'},
            {'ticker': 'AMZN', 'company_name': 'Amazon.com Inc.'},
            {'ticker': 'TSLA', 'company_name': 'Tesla Inc.'},
            {'ticker': 'META', 'company_name': 'Meta Platforms Inc.'},
            {'ticker': 'NVDA', 'company_name': 'NVIDIA Corporation'},
            {'ticker': 'NFLX', 'company_name': 'Netflix Inc.'},
            {'ticker': 'AMD', 'company_name': 'Advanced Micro Devices Inc.'},
            {'ticker': 'INTC', 'company_name': 'Intel Corporation'},
            {'ticker': 'JPM', 'company_name': 'JPMorgan Chase & Co.'},
            {'ticker': 'JNJ', 'company_name': 'Johnson & Johnson'},
            {'ticker': 'V', 'company_name': 'Visa Inc.'},
            {'ticker': 'PG', 'company_name': 'Procter & Gamble Co.'},
            {'ticker': 'UNH', 'company_name': 'UnitedHealth Group Inc.'},
            {'ticker': 'HD', 'company_name': 'The Home Depot Inc.'},
            {'ticker': 'MA', 'company_name': 'Mastercard Inc.'},
            {'ticker': 'BAC', 'company_name': 'Bank of America Corp.'},
            {'ticker': 'XOM', 'company_name': 'Exxon Mobil Corporation'},
            {'ticker': 'CVX', 'company_name': 'Chevron Corporation'},
        ]
    
    def search_stocks(self, query: str) -> List[Dict]:
        """Search for stocks by ticker or company name"""
        query = query.upper()
        results = []
        
        for stock in self.companies:
            if query in stock['ticker'] or query.lower() in stock['company_name'].lower():
                results.append(stock)
        
        # If exact ticker match, add it even if not in mock list
        if len(query) <= 5 and query.isalpha() and not any(s['ticker'] == query for s in results):
            results.insert(0, {'ticker': query, 'company_name': f'{query} Corporation'})
        
        return results[:10]  # Limit to 10 results
    
    def get_stock_data(self, tickers: List[str]) -> List[StockData]:
        """Get current stock data for given tickers"""
        stock_data = []
        
        for ticker in tickers:
            # Check if it's a major index
            if ticker in self.major_indexes:
                index_info = self.major_indexes[ticker]
                base_price = index_info['base_price']
                # Generate realistic mock data
                change_percent = random.uniform(-2.0, 2.0)
                change = base_price * (change_percent / 100)
                current_price = base_price + change
                
                stock_data.append(StockData(
                    ticker=ticker,
                    company_name=index_info['name'],
                    price=round(current_price, 2),
                    change=round(change, 2),
                    change_percent=round(change_percent, 2),
                    volume=random.randint(50000000, 200000000),
                    market_cap="N/A"
                ))
            else:
                # Use known stock price or generate random one
                base_price = self.stock_prices.get(ticker, random.uniform(20, 300))
                change_percent = random.uniform(-5.0, 5.0)
                change = base_price * (change_percent / 100)
                current_price = base_price + change
                
                # Get company name from search results
                search_results = self.search_stocks(ticker)
                company_name = next((s['company_name'] for s in search_results if s['ticker'] == ticker), f"{ticker} Corporation")
                
                stock_data.append(StockData(
                    ticker=ticker,
                    company_name=company_name,
                    price=round(current_price, 2),
                    change=round(change, 2),
                    change_percent=round(change_percent, 2),
                    volume=random.randint(1000000, 50000000),
                    market_cap=f"${random.randint(10, 500)}B"
                ))
        
        return stock_data
    
    def get_major_indexes(self) -> List[StockData]:
        """Get data for major stock indexes"""
        return self.get_stock_data(list(self.major_indexes.keys()))
