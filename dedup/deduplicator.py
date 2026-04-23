"""TF-IDF 코사인 유사도 + 키워드 겹침 기반 중복 기사 병합"""

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import re
from typing import List, Dict, Set


class ArticleDeduplicator:
    """동일 이슈 기사를 묶고 최고 티어 대표 기사만 남김"""

    def __init__(self, similarity_threshold: float = 0.35, noun_overlap_threshold: float = 0.60):
        self.threshold = similarity_threshold
        self.noun_overlap_threshold = noun_overlap_threshold

    def deduplicate(self, articles: List[Dict]) -> List[Dict]:
        if len(articles) <= 1:
            for a in articles:
                a["similar_count"] = 0
                a["similar_sources"] = []
            return articles

        # 텍스트 준비
        texts = []
        for a in articles:
            text = (a.get("title", "") + " " + a.get("description", "")).strip()
            texts.append(text if text else "empty")

        # TF-IDF 유사도
        vectorizer = TfidfVectorizer(max_features=5000)
        tfidf_matrix = vectorizer.fit_transform(texts)
        sim_matrix = cosine_similarity(tfidf_matrix)

        # 핵심 명사 추출 (제목에서)
        title_nouns = []
        for a in articles:
            nouns = self._extract_key_nouns(a.get("title", ""))
            title_nouns.append(nouns)

        # 유사도 판정: TF-IDF 유사도 OR 핵심 명사 겹침
        n = len(articles)
        is_similar = [[False] * n for _ in range(n)]

        for i in range(n):
            for j in range(i + 1, n):
                tfidf_sim = sim_matrix[i][j]
                noun_overlap = self._noun_overlap_ratio(title_nouns[i], title_nouns[j])

                # 조건: TF-IDF 0.35 이상 OR 핵심명사 60% 이상 겹침
                if tfidf_sim >= self.threshold or noun_overlap >= self.noun_overlap_threshold:
                    is_similar[i][j] = True
                    is_similar[j][i] = True

        # 클러스터링: Union-Find 방식으로 연결된 기사 모두 하나의 그룹으로
        parent = list(range(n))

        def find(x):
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        def union(x, y):
            px, py = find(x), find(y)
            if px != py:
                parent[px] = py

        for i in range(n):
            for j in range(i + 1, n):
                if is_similar[i][j]:
                    union(i, j)

        # 클러스터 수집
        clusters = {}
        for i in range(n):
            root = find(i)
            if root not in clusters:
                clusters[root] = []
            clusters[root].append(i)

        # 대표 기사 선정
        result = []
        for cluster_indices in clusters.values():
            if len(cluster_indices) == 1:
                idx = cluster_indices[0]
                articles[idx]["similar_count"] = 0
                articles[idx]["similar_sources"] = []
                result.append(articles[idx])
            else:
                cluster_articles = [(idx, articles[idx]) for idx in cluster_indices]
                cluster_articles.sort(key=lambda x: (
                    x[1].get("tier", 99),
                    -x[1].get("relevance_score", 0),
                    -len(x[1].get("title", ""))
                ))

                _, representative = cluster_articles[0]

                similar_sources = []
                for _, art in cluster_articles[1:]:
                    source_name = art.get("media_name", art.get("source", "알 수 없음"))
                    similar_sources.append(source_name)

                representative["similar_count"] = len(cluster_indices) - 1
                representative["similar_sources"] = similar_sources

                # 유사 기사 상세 정보 보존 (펼침 기능용)
                similar_details = []
                for _, art in cluster_articles[1:]:
                    similar_details.append({
                        "title": art.get("title", ""),
                        "link": art.get("link", ""),
                        "originallink": art.get("originallink", ""),
                        "media_name": art.get("media_name", art.get("source", "")),
                        "tier": art.get("tier", 0),
                        "pubDate": art.get("pubDate", ""),
                        "source": art.get("source", ""),
                    })
                representative["similar_articles"] = similar_details

                result.append(representative)


        return result

    def _extract_key_nouns(self, title: str) -> Set[str]:
        """제목에서 핵심 명사를 추출 (2글자 이상 한글 단어 + 영문 단어 + 숫자포함 단어)"""
        # 불용어
        stopwords = {
            "기자", "뉴스", "속보", "단독", "종합", "업데이트", "포토",
            "오늘", "내일", "어제", "올해", "지난", "최근", "이번",
            "대한", "관련", "통해", "위해", "대해", "있는", "하는", "되는",
            "것으로", "에서", "으로", "까지", "부터", "에게", "라고",
        }

        # 한글 2글자 이상 단어
        korean_words = set(re.findall(r'[가-힣]{2,}', title))

        # 영문 단어 (2글자 이상)
        english_words = set(w.upper() for w in re.findall(r'[a-zA-Z]{2,}', title))

        # 숫자+단위 (예: 3조원, 10억)
        number_words = set(re.findall(r'\d+[조억만원%]+', title))

        all_words = korean_words | english_words | number_words
        filtered = {w for w in all_words if w not in stopwords and len(w) >= 2}

        return filtered

    def _noun_overlap_ratio(self, nouns_a: Set[str], nouns_b: Set[str]) -> float:
        """두 명사 집합의 겹침 비율 (작은 쪽 기준)"""
        if not nouns_a or not nouns_b:
            return 0.0

        overlap = len(nouns_a & nouns_b)
        min_size = min(len(nouns_a), len(nouns_b))

        return overlap / min_size if min_size > 0 else 0.0
