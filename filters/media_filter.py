"""매체 티어 기반 화이트리스트 필터"""

import yaml
import os
from typing import List, Dict, Optional

class MediaFilter:
    """매체 도메인을 기반으로 티어를 판별하고 필터링"""

    def __init__(self, tiers_path: str = None):
        if tiers_path is None:
            tiers_path = os.path.join("config", "media_tiers.yaml")
        
        self.tiers = {}       # {domain: {"name": ..., "tier": ...}}
        self._load_tiers(tiers_path)

    def _load_tiers(self, path: str):
        """media_tiers.yaml을 읽어 도메인→티어 매핑 구축"""
        if not os.path.exists(path):
            return

        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}

        for tier_key in ["tier_1", "tier_2", "tier_3"]:
            tier_num = int(tier_key.split("_")[1])
            for media in data.get(tier_key, []):
                domain = media.get("domain", "").lower()
                if domain:
                    self.tiers[domain] = {
                        "name": media.get("name", domain),
                        "tier": tier_num
                    }

    def get_tier(self, url: str) -> Optional[int]:
        """URL에서 매체 티어 반환. 미등록 매체는 None."""
        domain = self._extract_domain(url)
        for registered_domain, info in self.tiers.items():
            if registered_domain in domain:
                return info["tier"]
        return None

    def get_media_name(self, url: str) -> str:
        """URL에서 매체명 반환. 미등록이면 도메인 반환."""
        domain = self._extract_domain(url)
        for registered_domain, info in self.tiers.items():
            if registered_domain in domain:
                return info["name"]
        return domain

    def filter_articles(
        self,
        articles: List[Dict],
        allowed_tiers: List[int]
    ) -> List[Dict]:
        """
        허용된 티어에 해당하는 기사만 반환.
        각 기사에 tier, media_name 필드를 추가.
        """
        filtered = []
        for article in articles:
            url = article.get("originallink") or article.get("link", "")
            tier = self.get_tier(url)

            if tier is not None and tier in allowed_tiers:
                article["tier"] = tier
                article["media_name"] = self.get_media_name(url)
                filtered.append(article)

        return filtered

    def _extract_domain(self, url: str) -> str:
        """URL에서 도메인 추출"""
        try:
            from urllib.parse import urlparse
            domain = urlparse(url).netloc.lower()
            domain = domain.replace("www.", "")
            return domain
        except:
            return ""
