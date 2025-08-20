from pathlib import Path
import pandas as pd
from typing import Dict, List, Optional, Union
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class PolygonDataProcessor:
    """Processes Polygon.io flat files for market analysis"""

    def __init__(self, data_dir: Union[str, Path]):
        """
        Initialize the data processor

        Args:
            data_dir: Directory containing Polygon.io flat files
        """
        self.data_dir = Path(data_dir)
        if not self.data_dir.exists():
            raise ValueError(f"Data directory does not exist: {self.data_dir}")

    def _load_file(self, file_path: Path) -> pd.DataFrame:
        """
        Load a Polygon flat file into a pandas DataFrame

        Args:
            file_path: Path to the flat file

        Returns:
            DataFrame containing the file data
        """
        try:
            # Polygon files are typically pipe-delimited
            df = pd.read_csv(file_path, delimiter='|')
            return df
        except Exception as e:
            logger.error(f"Failed to load file {file_path}: {str(e)}")
            raise

    def get_stock_data(self, ticker: str, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """
        Get stock data for a specific ticker within a date range

        Args:
            ticker: Stock ticker symbol
            start_date: Start date for data
            end_date: End date for data

        Returns:
            DataFrame containing the stock data
        """
        dfs = []
        current_date = start_date

        while current_date <= end_date:
            date_str = current_date.strftime('%Y-%m-%d')
            file_path = self.data_dir / f"{date_str}" / f"{ticker}.txt"

            if file_path.exists():
                try:
                    df = self._load_file(file_path)
                    dfs.append(df)
                except Exception as e:
                    logger.warning(f"Could not load data for {ticker} on {date_str}: {str(e)}")

            current_date += timedelta(days=1)

        if not dfs:
            logger.warning(f"No data found for {ticker} between {start_date} and {end_date}")
            return pd.DataFrame()

        return pd.concat(dfs, ignore_index=True)

    def get_market_movers(self, date: datetime, threshold: float = 5.0) -> Dict[str, List[Dict]]:
        """
        Get market movers (gainers and losers) for a specific date

        Args:
            date: Date to analyze
            threshold: Minimum percentage change to consider (default: 5.0%)

        Returns:
            Dictionary containing 'gainers' and 'losers' lists
        """
        date_str = date.strftime('%Y-%m-%d')
        daily_dir = self.data_dir / date_str

        if not daily_dir.exists():
            raise ValueError(f"No data directory found for date: {date_str}")

        results = {
            'gainers': [],
            'losers': []
        }

        # Process all stock files in the directory
        for file_path in daily_dir.glob('*.txt'):
            ticker = file_path.stem
            try:
                df = self._load_file(file_path)

                # Calculate daily stats
                if not df.empty:
                    open_price = df.iloc[0]['open']  # Assuming 'open' column exists
                    close_price = df.iloc[-1]['close']  # Assuming 'close' column exists
                    percent_change = ((close_price - open_price) / open_price) * 100

                    result = {
                        'ticker': ticker,
                        'open': open_price,
                        'close': close_price,
                        'percent_change': percent_change
                    }

                    if abs(percent_change) >= threshold:
                        if percent_change > 0:
                            results['gainers'].append(result)
                        else:
                            results['losers'].append(result)

            except Exception as e:
                logger.error(f"Error processing {ticker}: {str(e)}")
                continue

        # Sort results by absolute percentage change
        results['gainers'] = sorted(results['gainers'],
                                  key=lambda x: x['percent_change'],
                                  reverse=True)
        results['losers'] = sorted(results['losers'],
                                 key=lambda x: x['percent_change'])

        return results

    def get_index_constituents(self, index_file: str) -> List[str]:
        """
        Get list of constituents for a market index

        Args:
            index_file: Name of the index constituents file (e.g., 'sp500.txt')

        Returns:
            List of ticker symbols
        """
        file_path = self.data_dir / index_file
        if not file_path.exists():
            raise ValueError(f"Index file not found: {file_path}")

        try:
            with open(file_path, 'r') as f:
                # Assuming one ticker per line
                return [line.strip() for line in f if line.strip()]
        except Exception as e:
            logger.error(f"Failed to load index constituents from {file_path}: {str(e)}")
            raise

    def get_volume_leaders(self, date: datetime, top_n: int = 10) -> List[Dict]:
        """
        Get top volume leaders for a specific date

        Args:
            date: Date to analyze
            top_n: Number of top volume leaders to return

        Returns:
            List of dictionaries containing volume leader data
        """
        date_str = date.strftime('%Y-%m-%d')
        daily_dir = self.data_dir / date_str

        if not daily_dir.exists():
            raise ValueError(f"No data directory found for date: {date_str}")

        volume_data = []

        for file_path in daily_dir.glob('*.txt'):
            ticker = file_path.stem
            try:
                df = self._load_file(file_path)
                if not df.empty:
                    total_volume = df['volume'].sum()  # Assuming 'volume' column exists
                    volume_data.append({
                        'ticker': ticker,
                        'volume': total_volume,
                        'close': df.iloc[-1]['close']
                    })
            except Exception as e:
                logger.error(f"Error processing {ticker}: {str(e)}")
                continue

        # Sort by volume and return top N
        return sorted(volume_data, key=lambda x: x['volume'], reverse=True)[:top_n]
