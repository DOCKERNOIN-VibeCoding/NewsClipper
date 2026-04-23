"""뉴스 클리핑 파이프라인 v2 — 수집 → 필터 → 중복 병합 → 관련도 분류 → 정렬"""

import os
import yaml
from typing import Dict, List, Callable, Optional
from collectors.naver_api import NaverNewsCollector
from filters.media_filter import MediaFilter
from filters.date_filter import DateFilter
from dedup.deduplicator import ArticleDeduplicator


class NewsPipeline:
    """뉴스 클리핑 전체 파이프라인 v2"""

    def __init__(self, settings: dict):
        self.settings = settings
        self.results = {
            "articles": [],
            "stats": {},
            "log": []
        }

    def run(self, progress_callback: Optional[Callable] = None, log_callback: Optional[Callable] = None):
        total_steps = 6

        def _progress(step, msg):
            if progress_callback:
                progress_callback(step, total_steps, msg)
            if log_callback:
                log_callback(msg)

        def _log(msg):
            self.results["log"].append(msg)
            if log_callback:
                log_callback(msg)

        # ═══════════════════════════════
        #  Step 1: 검색 키워드 준비
        # ═══════════════════════════════
        _progress(1, "📋 검색 키워드 준비 중...")
        keyword_groups = self._build_search_keywords()

        _log(f"  제품/브랜드: {keyword_groups['products']}")
        _log(f"  회사명: {keyword_groups['company']}")
        _log(f"  경쟁사: {keyword_groups['competitors']}")
        _log(f"  업계: {keyword_groups['industry']}")

        total_kw = sum(len(v) for v in keyword_groups.values())
        _log(f"  총 {total_kw}개 검색 키워드")

        # ═══════════════════════════════
        #  Step 2: Naver API로 기사 수집
        # ═══════════════════════════════
        _progress(2, "🔍 Naver API에서 기사 수집 중...")

        api = self.settings.get("api", {}).get("naver", {})
        collector = NaverNewsCollector(
            client_id=api.get("client_id", ""),
            client_secret=api.get("client_secret", "")
        )

        all_articles = []
        seen_urls = set()

        # 제품/브랜드명: 최우선, 각 최대 100건
        _log("\n── 🎯 제품/브랜드 키워드 검색 ──")
        for i, kw in enumerate(keyword_groups['products']):
            _log(f"  🔍 [{i+1}/{len(keyword_groups['products'])}] '{kw}' 검색 중...")
            results = collector.search(query=kw, max_results=100, progress_callback=_log)
            new_count = self._add_articles(all_articles, seen_urls, results, "product", kw)
            _log(f"    → {len(results)}건 중 {new_count}건 신규")

        # 회사명: 각 최대 50건
        _log("\n── 🏢 회사명 검색 ──")
        for i, kw in enumerate(keyword_groups['company']):
            _log(f"  🔍 [{i+1}/{len(keyword_groups['company'])}] '{kw}' 검색 중...")
            results = collector.search(query=kw, max_results=50, progress_callback=_log)
            new_count = self._add_articles(all_articles, seen_urls, results, "company", kw)
            _log(f"    → {len(results)}건 중 {new_count}건 신규")

        # 경쟁사: 각 최대 50건
        if keyword_groups['competitors']:
            _log("\n── ⚔️ 경쟁사 검색 ──")
            for i, kw in enumerate(keyword_groups['competitors']):
                _log(f"  🔍 [{i+1}/{len(keyword_groups['competitors'])}] '{kw}' 검색 중...")
                results = collector.search(query=kw, max_results=50, progress_callback=_log)
                new_count = self._add_articles(all_articles, seen_urls, results, "competitor", kw)
                _log(f"    → {len(results)}건 중 {new_count}건 신규")

        # 업계: 각 최대 30건
        if keyword_groups['industry']:
            _log("\n── 🏷️ 업계 키워드 검색 ──")
            for i, kw in enumerate(keyword_groups['industry']):
                _log(f"  🔍 [{i+1}/{len(keyword_groups['industry'])}] '{kw}' 검색 중...")
                results = collector.search(query=kw, max_results=30, progress_callback=_log)
                new_count = self._add_articles(all_articles, seen_urls, results, "industry", kw)
                _log(f"    → {len(results)}건 중 {new_count}건 신규")

        _log(f"\n📊 총 {len(all_articles)}건 수집 완료")

        # ═══════════════════════════════
        #  Step 3: 매체 필터링
        # ═══════════════════════════════
        _progress(3, "🏢 매체 필터링 중...")

        media_filter = MediaFilter()
        allowed_tiers = self.settings.get("media", {}).get("allowed_tiers", [1, 2])
        filtered = media_filter.filter_articles(all_articles, allowed_tiers)
        _log(f"  매체 필터: {len(all_articles)}건 → {len(filtered)}건 (Tier {allowed_tiers})")

        # ═══════════════════════════════
        #  Step 4: 날짜 필터링
        # ═══════════════════════════════
        _progress(4, "📅 날짜 필터링 중...")

        range_days = self.settings.get("schedule", {}).get("range_days", 7)
        date_filter = DateFilter()
        dated = date_filter.filter_articles(filtered, range_days)
        _log(f"  날짜 필터: {len(filtered)}건 → {len(dated)}건 (최근 {range_days}일)")

        # ═══════════════════════════════
        #  Step 5: 중복 기사 병합
        # ═══════════════════════════════
        _progress(5, "🔄 중복 기사 병합 중...")

        # 감도 레벨 → 임계값 매핑
        sensitivity_level = self.settings.get("dedup", {}).get("sensitivity_level", 3)
        threshold_map = {
            1: 0.45,   # 거의 동일한 기사만
            2: 0.35,   # 보수적
            3: 0.25,   # 표준 (권장)
            4: 0.15,   # 적극적
            5: 0.10,   # 같은 주제면 대부분
        }
        noun_overlap_map = {
            1: 0.70,
            2: 0.60,
            3: 0.50,
            4: 0.40,
            5: 0.30,
        }

        sim_threshold = threshold_map.get(sensitivity_level, 0.35)
        noun_threshold = noun_overlap_map.get(sensitivity_level, 0.60)

        deduplicator = ArticleDeduplicator(
            similarity_threshold=sim_threshold,
            noun_overlap_threshold=noun_threshold
        )
        _log(f"  병합 감도: {sensitivity_level}단계 (TF-IDF≥{sim_threshold}, 명사겹침≥{noun_threshold})")

        deduplicated = deduplicator.deduplicate(dated)
        _log(f"  중복 병합: {len(dated)}건 → {len(deduplicated)}건")

        # ═══════════════════════════════
        #  Step 6: 관련도 분류 + 정렬
        # ═══════════════════════════════
        _progress(6, "🏷️ 관련도 분석 및 정렬 중...")

        product_keywords = [kw.lower() for kw in keyword_groups['products']]
        company_keywords = [kw.lower() for kw in keyword_groups['company']]
        competitor_keywords = [kw.lower() for kw in keyword_groups['competitors']]

        final = []
        for article in deduplicated:
            title = article.get("title", "").lower()
            desc = article.get("description", "").lower()
            text = title + " " + desc

            # 매칭 카운트
            matched_products = [kw for kw in product_keywords if kw in text]
            matched_company = [kw for kw in company_keywords if kw in text]
            matched_competitor = [kw for kw in competitor_keywords if kw in text]

            product_count = len(matched_products)
            company_count = len(matched_company)
            competitor_count = len(matched_competitor)

            # 태그 생성
            matched_tags = []
            for kw in matched_products:
                matched_tags.append(f"🎯{kw}")
            for kw in matched_company:
                matched_tags.append(f"🏢{kw}")
            for kw in matched_competitor:
                matched_tags.append(f"⚔️{kw}")

            # 섹션 분류 + 점수
            if product_count >= 1:
                # 제품명이 언급된 기사 = 제품/브랜드 기사
                section = "product"
                score = 300 + (product_count * 100) + (company_count * 30) + (competitor_count * 10)
            elif company_count >= 1:
                # 회사명만 언급 = 기업 기사
                section = "company"
                score = 100 + (company_count * 50)
            elif competitor_count >= 1:
                # 경쟁사만 언급
                section = "competitor"
                score = 50 + (competitor_count * 30)
            else:
                # 키워드 매칭 없음 → 제외
                continue

            # 티어 보너스
            tier = article.get("tier", 3)
            score += (4 - tier) * 5

            article["relevance_score"] = score
            article["matched_tags"] = matched_tags
            article["section"] = section
            article["product_match_count"] = product_count
            article["company_match_count"] = company_count
            article["competitor_match_count"] = competitor_count

            final.append(article)

        # 정렬
        section_order = {"product": 0, "company": 1, "competitor": 2}
        final.sort(key=lambda x: (
            section_order.get(x.get("section", ""), 9),
            -x.get("relevance_score", 0),
            x.get("tier", 99),
        ))

        # 통계
        product_cnt = len([a for a in final if a.get("section") == "product"])
        company_cnt = len([a for a in final if a.get("section") == "company"])
        competitor_cnt = len([a for a in final if a.get("section") == "competitor"])

        _log(f"\n🏷️ 관련도 필터: {len(deduplicated)}건 → {len(final)}건")
        _log(f"  🎯 제품/브랜드 기사: {product_cnt}건")
        _log(f"  🏢 기업 기사: {company_cnt}건")
        _log(f"  ⚔️ 경쟁사 기사: {competitor_cnt}건")

        self.results["articles"] = final
        self.results["stats"] = {
            "total_collected": len(all_articles),
            "after_media_filter": len(filtered),
            "after_date_filter": len(dated),
            "after_dedup": len(deduplicated),
            "final_count": len(final),
            "keywords_used": total_kw,
            "tiers_used": allowed_tiers,
            "range_days": range_days,
            "product_count": product_cnt,
            "company_count": company_cnt,
            "competitor_count": competitor_cnt,
        }

        _progress(total_steps, f"✅ 완료! 최종 {len(final)}건 (제품 {product_cnt} / 기업 {company_cnt} / 경쟁사 {competitor_cnt})")
        return self.results

    def _add_articles(self, all_articles, seen_urls, results, group, keyword):
        """중복 URL 제거하며 기사 추가. 신규 건수 반환."""
        new_count = 0
        for article in results:
            url = article.get("originallink") or article.get("link", "")
            if url and url not in seen_urls:
                seen_urls.add(url)
                article["keyword_group"] = group
                article["matched_keyword"] = keyword
                all_articles.append(article)
                new_count += 1
        return new_count

    def _build_search_keywords(self) -> dict:
        search = self.settings.get("search", {})
        keywords_config = search.get("keywords", {})

        products = keywords_config.get("products", [])
        company = keywords_config.get("company", [])
        competitors = keywords_config.get("competitors", [])

        # 업계 키워드: 대표 제품명과 조합
        industry_keywords = []
        general = keywords_config.get("industry_general", [])
        industry_keywords.extend(general)

        industries = search.get("industries", [])
        industry_data = self._load_industry_keywords()

        if products:
            main_product = products[0]
            for ind in industries:
                ind_kws = industry_data.get("industries", {}).get(ind, {}).get("keywords", [])
                for kw in ind_kws:
                    combined = f"{main_product} {kw}"
                    if combined not in industry_keywords:
                        industry_keywords.append(combined)

        return {
            "products": products,
            "company": company,
            "competitors": competitors,
            "industry": industry_keywords
        }

    def _load_industry_keywords(self) -> dict:
        path = os.path.join("config", "industry_keywords.yaml")
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        return {}
