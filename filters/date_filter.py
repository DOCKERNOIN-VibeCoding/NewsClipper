"""날짜 범위 기반 기사 필터"""

from datetime import datetime, timedelta
from typing import List, Dict

class DateFilter:
    """지정된 기간 내의 기사만 필터링"""

    def filter_articles(
        self,
        articles: List[Dict],
        range_days: int
    ) -> List[Dict]:
        """
        현재 시점에서 range_days일 이내의 기사만 반환.
        """
        cutoff = datetime.now() - timedelta(days=range_days)
        cutoff_str = cutoff.strftime("%Y-%m-%d")

        filtered = []
        for article in articles:
            pub_date = article.get("pubDate", "")
            if pub_date >= cutoff_str:
                filtered.append(article)

        return filtered
