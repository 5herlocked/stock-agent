import datetime
from polygon import RESTClient
import os


class PolygonWorker:
    def __init__(self):
        self.client = RESTClient(os.getenv('POLYGON_API_KEY'))

    def get_market_aggregates(self, date=datetime.date.today().isoformat()):
        """
            Date has to be in ISO format - YYYY-MM-DD
        """
        grouped_aggs = self.client.get_grouped_daily_aggs(
            date,
            adjusted=True,
        )
        return grouped_aggs
