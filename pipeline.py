"""뉴스 클리핑 파이프라인 v2.0
   수집 → 매체필터 → 날짜필터 → 중복병합 → AI분석 → AI필터 → 섹션분류 → 정렬"""

import os
import yaml
from typing import Dict, List, Callable, Optional

from collectors.naver_api import NaverNewsCollector
from filters.media_filter import MediaFilter
from filters.date_filter import DateFilter
from dedup.deduplicator import ArticleDeduplicator
from ai.article_analyzer import analyze_with_ai


class NewsPipeline:
    """뉴스 클리핑 전체 파이프라인 v2.0"""

    def __init__(self, settings: dict):
        self.settings = settings
        self.results = {
            "articles": [],
            "stats": {},
            "log": []
        }

    def run(self,
            progress_callback: Optional[Callable] = None,
            log_callback: Optional[Callable] = None):
        import logging as _logging
        _pipeline_logger = _logging.getLogger("pipeline")

        total_steps = 8

        def _progress(step, msg):
            _pipeline_logger.info(f"[Step {step}/{total_steps}] {msg}")
            if progress_callback:
                progress_callback(step, total_steps, msg)
            if log_callback:
                log_callback(msg)

        def _log(msg):
            _pipeline_logger.info(msg)
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

        sensitivity_level = self.settings.get("dedup", {}).get("sensitivity_level", 3)
        threshold_map = {1: 0.45, 2: 0.35, 3: 0.25, 4: 0.15, 5: 0.10}
        noun_overlap_map = {1: 0.70, 2: 0.60, 3: 0.50, 4: 0.40, 5: 0.30}

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
        #  Step 6: ★ Gemini AI 통합 분석
        # ═══════════════════════════════
        _progress(6, "🤖 Gemini AI 통합 분석 중...")

        ai_cfg = self.settings.get("ai", {}) or {}
        ai_enabled = ai_cfg.get("enabled", True)
        gemini_api_key = (
            self.settings.get("api", {}).get("gemini", {}).get("api_key", "")
        )

        ai_stats = {
            "total": len(deduplicated),
            "ai_succeeded": 0,
            "fallback": len(deduplicated) if not ai_enabled else 0,
            "by_relevance": {"core": 0, "relevant": 0, "passing": 0, "irrelevant": 0},
        }

        if not ai_enabled:
            _log("  ℹ️ AI 분석 비활성화됨 (settings: ai.enabled=false). v1 로컬 분류로 동작합니다.")
            # AI 키 없이도 안전하게 동작하도록 fallback만 적용
            from ai.article_analyzer import ArticleAnalyzer
            analyzer = ArticleAnalyzer(api_key="")  # 즉시 fallback 모드
            analyzer.analyze_articles(
                deduplicated,
                keyword_groups,
                progress_callback=lambda d, t, m: _progress(6, m),
                log_callback=_log,
            )
        else:
            def _ai_progress(done, total, msg):
                # 6단계 안에서의 서브 진행
                if progress_callback:
                    progress_callback(6, total_steps, msg)

            _, ai_stats = analyze_with_ai(
                deduplicated,
                keyword_groups,
                api_key=gemini_api_key,
                model=ai_cfg.get("model", "gemini-2.5-flash"),
                batch_size=int(ai_cfg.get("batch_size", 5)),
                progress_callback=_ai_progress,
                log_callback=_log,
            )

            _log(
                f"  📊 AI 분석 결과: 성공 {ai_stats['ai_succeeded']}건, "
                f"fallback {ai_stats['fallback']}건"
            )
            br = ai_stats["by_relevance"]
            _log(
                f"     관련도 분포 — 🟢 core {br['core']} / 🔵 relevant {br['relevant']} / "
                f"🟡 passing {br['passing']} / 🔴 irrelevant {br['irrelevant']}"
            )

        # ═══════════════════════════════
        #  Step 7: ★ AI 관련도 기반 필터링
        # ═══════════════════════════════
        _progress(7, "🎯 AI 관련도 필터링 중...")

        filter_cfg = ai_cfg.get("filter", {}) or {}
        exclude_irrelevant = filter_cfg.get("exclude_irrelevant", True)

        if exclude_irrelevant:
            before = len(deduplicated)
            deduplicated = [
                a for a in deduplicated
                if a.get("ai_relevance") != "irrelevant"
            ]
            _log(f"  AI 필터: {before}건 → {len(deduplicated)}건 (irrelevant 제외)")
        else:
            _log("  AI 필터: 비활성화 (irrelevant 포함 유지)")

        # ═══════════════════════════════
        #  Step 8: 섹션 분류 + 정렬
        #    - AI 결과(ai_category)를 우선 사용
        #    - AI fallback 기사는 v1 키워드 매칭으로 분류
        # ═══════════════════════════════
        _progress(8, "🏷️ 섹션 분류 및 정렬 중...")

        product_keywords = [kw.lower() for kw in keyword_groups['products']]
        company_keywords = [kw.lower() for kw in keyword_groups['company']]
        competitor_keywords = [kw.lower() for kw in keyword_groups['competitors']]

        final = []
        for article in deduplicated:
            section, score, matched_tags = self._classify_article(
                article,
                product_keywords,
                company_keywords,
                competitor_keywords,
            )
            if section is None:
                # 분류 불가능한 기사 (industry로도 잡히지 않음) → 제외
                continue

            article["relevance_score"] = score
            article["matched_tags"] = matched_tags
            article["section"] = section

            final.append(article)

        # 정렬: 섹션 순서 → AI 관련도 순서 → 점수 → 티어
        section_order = {"product": 0, "company": 1, "competitor": 2, "industry": 3}
        relevance_order = {"core": 0, "relevant": 1, "passing": 2, "irrelevant": 3}
        final.sort(key=lambda x: (
            section_order.get(x.get("section", ""), 9),
            relevance_order.get(x.get("ai_relevance", "passing"), 9),
            -x.get("relevance_score", 0),
            x.get("tier", 99),
        ))

        # 통계
        product_cnt = sum(1 for a in final if a.get("section") == "product")
        company_cnt = sum(1 for a in final if a.get("section") == "company")
        competitor_cnt = sum(1 for a in final if a.get("section") == "competitor")
        industry_cnt = sum(1 for a in final if a.get("section") == "industry")
        core_cnt = sum(1 for a in final if a.get("ai_relevance") == "core")
        passing_cnt = sum(1 for a in final if a.get("ai_relevance") == "passing")

        _log(f"\n🏷️ 섹션 분류: {len(deduplicated)}건 → {len(final)}건")
        _log(f"  🎯 제품/브랜드: {product_cnt}건  🏢 기업: {company_cnt}건  "
             f"⚔️ 경쟁사: {competitor_cnt}건  🏭 업계: {industry_cnt}건")
        _log(f"  AI 관련도 — 🟢 core {core_cnt}  🟡 passing {passing_cnt}")

        # ═══════════════════════════════
        #  (Phase 2-3 예정) HOT KEYWORDS 집계
        # ═══════════════════════════════
        # TODO: from output.hot_keywords import build_hot_keywords
        #       hot_keywords = build_hot_keywords(final, keyword_groups)
        #       self.results["hot_keywords"] = hot_keywords

        # ═══════════════════════════════
        #  결과 저장
        # ═══════════════════════════════
        self.results["articles"] = final
        self.results["stats"] = {
            "total_collected": len(all_articles),
            "after_media_filter": len(filtered),
            "after_date_filter": len(dated),
            "after_dedup": len(deduplicated) if not exclude_irrelevant
                           else (len(deduplicated) + (ai_stats["by_relevance"].get("irrelevant", 0))),
            "after_ai_filter": len(deduplicated),
            "final_count": len(final),
            "keywords_used": total_kw,
            "tiers_used": allowed_tiers,
            "range_days": range_days,
            "product_count": product_cnt,
            "company_count": company_cnt,
            "competitor_count": competitor_cnt,
            "industry_count": industry_cnt,
            # AI 통계
            "ai_enabled": ai_enabled,
            "ai_succeeded": ai_stats.get("ai_succeeded", 0),
            "ai_fallback": ai_stats.get("fallback", 0),
            "ai_by_relevance": ai_stats.get("by_relevance", {}),
        }

        _progress(
            total_steps,
            f"✅ 완료! 최종 {len(final)}건 "
            f"(제품 {product_cnt} / 기업 {company_cnt} / 경쟁사 {competitor_cnt} / 업계 {industry_cnt})"
        )
        return self.results

    # ──────────────────────────────────────────────
    #  헬퍼 메서드
    # ──────────────────────────────────────────────
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

    def _classify_article(
        self,
        article: dict,
        product_keywords: list,
        company_keywords: list,
        competitor_keywords: list,
    ):
        """
        섹션 분류 + 점수 + 매칭 태그 산출.
        AI 결과(ai_category) 우선, fallback 시 v1 키워드 매칭.
        반환: (section, score, matched_tags) — 분류 불가 시 (None, 0, [])
        """
        title = (article.get("title") or "").lower()
        desc = (article.get("description") or "").lower()
        text = title + " " + desc

        # 키워드 매칭 (점수 계산용 — AI 분류 사용 여부와 무관하게 항상 수행)
        matched_products = [kw for kw in product_keywords if kw and kw in text]
        matched_company = [kw for kw in company_keywords if kw and kw in text]
        matched_competitor = [kw for kw in competitor_keywords if kw and kw in text]

        product_count = len(matched_products)
        company_count = len(matched_company)
        competitor_count = len(matched_competitor)

        matched_tags = (
            [f"🎯{kw}" for kw in matched_products]
            + [f"🏢{kw}" for kw in matched_company]
            + [f"⚔️{kw}" for kw in matched_competitor]
        )

        # ── AI 분류 우선 ──
        ai_category = article.get("ai_category", "")
        ai_relevance = article.get("ai_relevance", "")
        ai_used = article.get("ai_analyzed", False) and not article.get("ai_fallback", False)

        section = None
        if ai_used and ai_category in ("product", "company", "competitor", "industry"):
            section = ai_category
        else:
            # ── v1 키워드 매칭 fallback ──
            if product_count >= 1:
                section = "product"
            elif company_count >= 1:
                section = "company"
            elif competitor_count >= 1:
                section = "competitor"
            elif article.get("keyword_group") == "industry":
                section = "industry"
            else:
                return None, 0, []

        # ── 점수 산정 ──
        if section == "product":
            score = 300 + (product_count * 100) + (company_count * 30) + (competitor_count * 10)
        elif section == "company":
            score = 100 + (company_count * 50) + (product_count * 20)
        elif section == "competitor":
            score = 50 + (competitor_count * 30)
        else:  # industry
            score = 20

        # AI 관련도 보너스
        relevance_bonus = {"core": 200, "relevant": 100, "passing": 0, "irrelevant": -1000}
        score += relevance_bonus.get(ai_relevance, 0)

        # 티어 보너스
        tier = article.get("tier", 3)
        score += (4 - tier) * 5

        return section, score, matched_tags

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
