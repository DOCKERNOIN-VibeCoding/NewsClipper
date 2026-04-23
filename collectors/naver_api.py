"""Naver News Search API를 이용한 뉴스 수집"""

import requests
import time
import re
from datetime import datetime, timedelta
from typing import List, Dict, Callable, Optional

class NaverNewsCollector:
    """Naver News Search API 수집기"""

    API_URL = "https://openapi.naver.com/v1/search/news.json"
    MAX_DISPLAY = 100   # 한 번에 최대 100건
    MAX_START = 1000    # start 최대값

    def __init__(self, client_id: str, client_secret: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.headers = {
            "X-Naver-Client-Id": client_id,
            "X-Naver-Client-Secret": client_secret
        }

    def search(
        self,
        query: str,
        max_results: int = 100,
        sort: str = "date",
        progress_callback: Optional[Callable] = None
    ) -> List[Dict]:
        """
        키워드로 뉴스 검색.
        
        Args:
            query: 검색 키워드
            max_results: 최대 수집 건수 (최대 1000)
            sort: 정렬 방식 ("date": 최신순, "sim": 관련도순)
            progress_callback: 진행 상태 콜백 함수
            
        Returns:
            기사 리스트 [{title, link, originallink, description, pubDate, source, query}, ...]
        """
        articles = []
        start = 1
        remaining = min(max_results, self.MAX_START)

        while remaining > 0 and start <= self.MAX_START:
            display = min(remaining, self.MAX_DISPLAY)

            params = {
                "query": query,
                "display": display,
                "start": start,
                "sort": sort
            }

            try:
                resp = requests.get(
                    self.API_URL,
                    headers=self.headers,
                    params=params,
                    timeout=10
                )

                if resp.status_code != 200:
                    if progress_callback:
                        progress_callback(f"⚠️ API 오류 (HTTP {resp.status_code}): {query}")
                    break

                data = resp.json()
                items = data.get("items", [])

                if not items:
                    break

                for item in items:
                    article = {
                        "title": self._clean_html(item.get("title", "")),
                        "link": item.get("link", ""),
                        "originallink": item.get("originallink", ""),
                        "description": self._clean_html(item.get("description", "")),
                        "pubDate": self._parse_date(item.get("pubDate", "")),
                        "pubDate_raw": item.get("pubDate", ""),
                        "source": self._extract_source(item.get("originallink", "")),
                        "query": query
                    }
                    articles.append(article)

                start += display
                remaining -= len(items)

                # API 속도 제한 준수 (초당 10회 이내)
                time.sleep(0.15)

            except requests.exceptions.Timeout:
                if progress_callback:
                    progress_callback(f"⚠️ 타임아웃: {query}")
                break
            except Exception as e:
                if progress_callback:
                    progress_callback(f"⚠️ 오류: {str(e)[:50]}")
                break

        return articles

    def collect_by_keywords(
        self,
        keywords: List[str],
        max_per_keyword: int = 100,
        progress_callback: Optional[Callable] = None
    ) -> List[Dict]:
        """
        여러 키워드로 검색하여 기사를 모두 수집.
        
        Args:
            keywords: 검색 키워드 리스트
            max_per_keyword: 키워드당 최대 수집 건수
            progress_callback: 진행 상태 콜백
            
        Returns:
            전체 기사 리스트 (중복 URL 제거됨)
        """
        all_articles = []
        seen_urls = set()

        for i, keyword in enumerate(keywords):
            if progress_callback:
                progress_callback(
                    f"🔍 [{i+1}/{len(keywords)}] '{keyword}' 검색 중..."
                )

            results = self.search(
                query=keyword,
                max_results=max_per_keyword,
                progress_callback=progress_callback
            )

            for article in results:
                url = article.get("originallink") or article.get("link", "")
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    all_articles.append(article)

            if progress_callback:
                progress_callback(
                    f"  ✅ '{keyword}': {len(results)}건 수집 (신규 {len([r for r in results if (r.get('originallink') or r.get('link', '')) in seen_urls])}건)"
                )

            # 키워드 간 간격
            time.sleep(0.3)

        return all_articles

    def _clean_html(self, text: str) -> str:
        """HTML 태그 및 특수문자 제거"""
        text = re.sub(r'<[^>]+>', '', text)
        text = text.replace("&quot;", '"').replace("&amp;", "&")
        text = text.replace("&lt;", "<").replace("&gt;", ">")
        text = text.replace("&apos;", "'")
        return text.strip()

    def _parse_date(self, date_str: str) -> str:
        """날짜 문자열을 YYYY-MM-DD 형식으로 변환"""
        try:
            dt = datetime.strptime(date_str, "%a, %d %b %Y %H:%M:%S %z")
            return dt.strftime("%Y-%m-%d")
        except:
            return date_str

    def _extract_source(self, url: str) -> str:
        """URL에서 도메인(매체명) 추출"""
        try:
            from urllib.parse import urlparse
            domain = urlparse(url).netloc
            domain = domain.replace("www.", "")
            return domain
        except:
            return ""
