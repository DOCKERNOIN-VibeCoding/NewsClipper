"""메인 윈도우 — 좌측 네이비 패널 + 우측 결과 패널"""

import customtkinter as ctk
import yaml
import os
import threading
import webbrowser
from ui.theme import *


class MainWindow(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("News Clipper — AI 뉴스 클리핑")
        self.geometry("1200x750")
        self.minsize(1000, 600)
        self.configure(fg_color=BG_MAIN)

        self.settings = self._load_settings()
        self.last_results = None

        self.grid_columnconfigure(0, weight=0, minsize=320)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.left_panel = ctk.CTkFrame(self, fg_color=NAVY, corner_radius=0)
        self.left_panel.grid(row=0, column=0, sticky="nswe")
        self.left_panel.grid_propagate(False)
        self.left_panel.configure(width=320)

        self.right_panel = ctk.CTkFrame(self, fg_color=BG_MAIN, corner_radius=0)
        self.right_panel.grid(row=0, column=1, sticky="nswe")

        self._build_left_panel()
        self._build_right_panel()

    # ══════════════════════════════════════
    #  왼쪽 패널
    # ══════════════════════════════════════
    def _build_left_panel(self):
        title_frame = ctk.CTkFrame(self.left_panel, fg_color="transparent")
        title_frame.pack(fill="x", padx=20, pady=(25, 5))

        ctk.CTkLabel(
            title_frame, text="📰 News Clipper",
            font=(FONT_FAMILY, 22, "bold"),
            text_color=TEXT_ON_NAVY
        ).pack(anchor="w")

        ctk.CTkLabel(
            title_frame, text="AI 기반 뉴스 클리핑 & 미디어 모니터링",
            font=FONT_CAPTION,
            text_color=TEXT_ON_NAVY_DIM
        ).pack(anchor="w", pady=(2, 0))

        ctk.CTkFrame(self.left_panel, fg_color=NAVY_LIGHT, height=1).pack(
            fill="x", padx=20, pady=(15, 15)
        )

        self.summary_frame = ctk.CTkScrollableFrame(
            self.left_panel, fg_color="transparent",
            scrollbar_button_color=NAVY_LIGHT,
            scrollbar_button_hover_color=TEXT_ON_NAVY_DIM
        )
        self.summary_frame.pack(fill="both", expand=True, padx=15, pady=(0, 10))

        self._refresh_settings_summary()

        bottom_frame = ctk.CTkFrame(self.left_panel, fg_color=NAVY_DARK, corner_radius=0)
        bottom_frame.pack(fill="x", side="bottom")

        # 크래딧
        ctk.CTkLabel(
            bottom_frame,
            text="Developed by DOCKERNOIN with Claude AI",
            font=FONT_CAPTION,
            text_color=TEXT_ON_NAVY_DIM
        ).pack(side="bottom", pady=(0, 8))

        self.start_button = ctk.CTkButton(
            bottom_frame,
            text="🚀  뉴스 클리핑 시작",
            font=FONT_SUBTITLE,
            fg_color=COBALT,
            hover_color=COBALT_HOVER,
            height=48,
            corner_radius=10,
            command=self._on_start_click
        )
        self.start_button.pack(fill="x", padx=20, pady=(15, 8))
        self._update_start_button_state()

        settings_btn_frame = ctk.CTkFrame(bottom_frame, fg_color="transparent")
        settings_btn_frame.pack(fill="x", padx=20, pady=(0, 15))
        settings_btn_frame.grid_columnconfigure(0, weight=1)
        settings_btn_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkButton(
            settings_btn_frame,
            text="🔍 검색 조건",
            font=FONT_SMALL,
            fg_color=NAVY_LIGHT,
            hover_color=NAVY,
            height=34,
            corner_radius=8,
            command=self._open_settings_search
        ).grid(row=0, column=0, sticky="we", padx=(0, 4))

        ctk.CTkButton(
            settings_btn_frame,
            text="🔑 API 설정",
            font=FONT_SMALL,
            fg_color=NAVY_LIGHT,
            hover_color=NAVY,
            height=34,
            corner_radius=8,
            command=self._open_settings_api
        ).grid(row=0, column=1, sticky="we", padx=(4, 0))

    # ══════════════════════════════════════
    #  오른쪽 패널
    # ══════════════════════════════════════
    def _build_right_panel(self):
        header = ctk.CTkFrame(self.right_panel, fg_color=BG_WHITE, height=60, corner_radius=0)
        header.pack(fill="x", padx=0, pady=0)
        header.pack_propagate(False)

        ctk.CTkLabel(
            header, text="클리핑 결과",
            font=FONT_SUBTITLE,
            text_color=TEXT_PRIMARY
        ).pack(side="left", padx=20, pady=15)

        self.export_button = ctk.CTkButton(
            header,
            text="📥 HTML로 내보내기",
            font=FONT_SMALL,
            fg_color="#E5E7EB",
            text_color=TEXT_SECONDARY,
            hover_color="#D1D5DB",
            height=32,
            corner_radius=8,
            state="disabled",
            command=self._on_export_click
        )
        self.export_button.pack(side="right", padx=20, pady=15)

        self.result_area = ctk.CTkScrollableFrame(
            self.right_panel, fg_color=BG_MAIN,
            scrollbar_button_color="#CBD5E1",
            scrollbar_button_hover_color="#94A3B8"
        )
        self.result_area.pack(fill="both", expand=True, padx=10, pady=10)

        self._show_empty_state()

    # ══════════════════════════════════════
    #  설정 요약
    # ══════════════════════════════════════
    def _refresh_settings_summary(self):
        for widget in self.summary_frame.winfo_children():
            widget.destroy()

        search = self.settings.get("search", {})
        keywords = search.get("keywords", {})
        schedule = self.settings.get("schedule", {})
        api = self.settings.get("api", {})

        if self._is_setup_complete():
            self._add_badge(self.summary_frame, "✅ 설정 완료", SUCCESS, BG_WHITE)
        else:
            self._add_badge(self.summary_frame, "⚠️ 설정 필요", WARNING, TEXT_PRIMARY)

        industries = search.get("industries", [])
        self._add_summary_item("산업군", ", ".join(industries) if industries else "미설정")

        products = keywords.get("products", [])
        self._add_summary_item("제품/브랜드", ", ".join(products) if products else "미설정")

        company = keywords.get("company", [])
        self._add_summary_item("회사명", ", ".join(company) if company else "미설정")


        industry_general = keywords.get("industry_general", [])
        self._add_summary_item(
            "업계 키워드",
            ", ".join(industry_general) if industry_general else "없음 (선택사항)",
            dim=not bool(industry_general)
        )


        freq = schedule.get("frequency", "미설정")
        range_days = schedule.get("range_days", "?")
        freq_kr = {"daily": "매일", "weekly": "매주", "monthly": "매월"}.get(freq, freq)
        self._add_summary_item("취합 주기", f"{freq_kr} / 최근 {range_days}일")

        naver_ok = bool(api.get("naver", {}).get("client_id"))
        gemini_ok = bool(api.get("gemini", {}).get("api_key"))

        api_frame = ctk.CTkFrame(self.summary_frame, fg_color="transparent")
        api_frame.pack(fill="x", pady=(6, 0))

        ctk.CTkLabel(
            api_frame, text="API",
            font=FONT_CAPTION, text_color=TEXT_ON_NAVY_DIM
        ).pack(anchor="w")

        api_value_frame = ctk.CTkFrame(api_frame, fg_color="transparent")
        api_value_frame.pack(anchor="w", pady=(1, 0))

        ctk.CTkLabel(
            api_value_frame, text="Naver",
            font=FONT_SMALL_BOLD, text_color=TEXT_ON_NAVY
        ).pack(side="left")
        ctk.CTkLabel(
            api_value_frame,
            text=" ✅ " if naver_ok else " ✘ ",
            font=FONT_SMALL_BOLD,
            text_color=SUCCESS if naver_ok else ERROR
        ).pack(side="left")

        ctk.CTkLabel(
            api_value_frame, text="  Gemini",
            font=FONT_SMALL_BOLD, text_color=TEXT_ON_NAVY
        ).pack(side="left")
        ctk.CTkLabel(
            api_value_frame,
            text=" ✅ " if gemini_ok else " ✘ ",
            font=FONT_SMALL_BOLD,
            text_color=SUCCESS if gemini_ok else ERROR
        ).pack(side="left")

    def _add_summary_item(self, label: str, value: str, dim: bool = False):
        frame = ctk.CTkFrame(self.summary_frame, fg_color="transparent")
        frame.pack(fill="x", pady=(6, 0))

        ctk.CTkLabel(
            frame, text=label,
            font=FONT_CAPTION,
            text_color=TEXT_ON_NAVY_DIM
        ).pack(anchor="w")

        ctk.CTkLabel(
            frame, text=value,
            font=FONT_SMALL_BOLD if not dim else FONT_SMALL,
            text_color=TEXT_ON_NAVY if not dim else TEXT_ON_NAVY_DIM
        ).pack(anchor="w", pady=(1, 0))

    def _add_badge(self, parent, text: str, bg_color: str, text_color: str):
        badge = ctk.CTkLabel(
            parent, text=text,
            font=FONT_SMALL_BOLD,
            fg_color=bg_color,
            text_color=text_color,
            corner_radius=12,
            height=26
        )
        badge.pack(anchor="w", pady=(0, 10))

    # ══════════════════════════════════════
    #  빈 상태
    # ══════════════════════════════════════
    def _show_empty_state(self):
        for widget in self.result_area.winfo_children():
            widget.destroy()

        empty_frame = ctk.CTkFrame(self.result_area, fg_color="transparent")
        empty_frame.pack(fill="x", pady=(80, 20))

        ctk.CTkLabel(
            empty_frame, text="📰",
            font=(FONT_FAMILY, 48),
            text_color=TEXT_SECONDARY
        ).pack()

        ctk.CTkLabel(
            empty_frame, text="뉴스 클리핑 결과가 여기에 표시됩니다",
            font=FONT_BODY_BOLD,
            text_color=TEXT_SECONDARY
        ).pack(pady=(10, 5))

        ctk.CTkLabel(
            empty_frame, text="왼쪽 패널에서 설정을 확인하고 시작 버튼을 눌러주세요",
            font=FONT_SMALL,
            text_color=TEXT_PLACEHOLDER
        ).pack()

    # ══════════════════════════════════════
    #  시작 버튼 + 파이프라인
    # ══════════════════════════════════════
    def _on_start_click(self):
        self.start_button.configure(state="disabled", text="⏳ 수집 중...")
        self._show_progress_view()
        thread = threading.Thread(target=self._run_pipeline_thread, daemon=True)
        thread.start()

    def _show_progress_view(self):
        for widget in self.result_area.winfo_children():
            widget.destroy()

        self.progress_container = ctk.CTkFrame(self.result_area, fg_color="transparent")
        self.progress_container.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(
            self.progress_container,
            text="🔄 뉴스 클리핑 진행 중",
            font=FONT_SUBTITLE,
            text_color=TEXT_PRIMARY
        ).pack(anchor="w", pady=(0, 15))

        self.step_label = ctk.CTkLabel(
            self.progress_container,
            text="준비 중...",
            font=FONT_BODY_BOLD,
            text_color=COBALT
        )
        self.step_label.pack(anchor="w", pady=(0, 8))

        self.progress_bar = ctk.CTkProgressBar(
            self.progress_container,
            width=500, height=20,
            corner_radius=10,
            fg_color=SKY_BLUE,
            progress_color=COBALT
        )
        self.progress_bar.pack(fill="x", pady=(0, 5))
        self.progress_bar.set(0)

        self.percent_label = ctk.CTkLabel(
            self.progress_container,
            text="0%",
            font=FONT_SMALL,
            text_color=TEXT_SECONDARY
        )
        self.percent_label.pack(anchor="e", pady=(0, 15))

        ctk.CTkFrame(self.progress_container, fg_color="#E5E7EB", height=1).pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(
            self.progress_container,
            text="📋 상세 로그",
            font=FONT_SMALL_BOLD,
            text_color=TEXT_SECONDARY
        ).pack(anchor="w", pady=(0, 5))

        self.log_textbox = ctk.CTkTextbox(
            self.progress_container,
            font=FONT_SMALL,
            fg_color=BG_WHITE,
            text_color=TEXT_PRIMARY,
            corner_radius=8,
            border_width=1,
            border_color="#E5E7EB",
            state="disabled"
        )
        self.log_textbox.pack(fill="both", expand=True)

    def _run_pipeline_thread(self):
        from pipeline import NewsPipeline

        pipeline = NewsPipeline(self.settings)

        def on_progress(step, total, message):
            progress = step / total
            self.after(0, self._update_progress, progress, message)

        def on_log(message):
            self.after(0, self._append_log, message)

        try:
            results = pipeline.run(
                progress_callback=on_progress,
                log_callback=on_log
            )
            self.after(0, self._on_pipeline_complete, results)
        except Exception as e:
            self.after(0, self._on_pipeline_error, str(e))

    def _update_progress(self, progress: float, message: str):
        self.progress_bar.set(progress)
        self.step_label.configure(text=message)
        self.percent_label.configure(text=f"{int(progress * 100)}%")

    def _append_log(self, message: str):
        self.log_textbox.configure(state="normal")
        self.log_textbox.insert("end", message + "\n")
        self.log_textbox.see("end")
        self.log_textbox.configure(state="disabled")

    def _on_pipeline_complete(self, results: dict):
        self.start_button.configure(state="normal", text="🚀  뉴스 클리핑 시작")
        self.last_results = results
        self._show_results(results)

    def _on_pipeline_error(self, error_msg: str):
        self.start_button.configure(state="normal", text="🚀  뉴스 클리핑 시작")
        self._append_log(f"\n❌ 오류 발생: {error_msg}")
        self.step_label.configure(text="❌ 오류가 발생했습니다", text_color=ERROR)

    # ══════════════════════════════════════
    #  결과 표시
    # ══════════════════════════════════════
    def _show_results(self, results: dict):
        for widget in self.result_area.winfo_children():
            widget.destroy()

        articles = results.get("articles", [])
        stats = results.get("stats", {})

        self._last_articles = articles
        self._last_stats = stats        

        # ── 통계 요약 ──
        stats_frame = ctk.CTkFrame(self.result_area, fg_color=BG_WHITE, corner_radius=10)
        stats_frame.pack(fill="x", padx=15, pady=(10, 15))

        stats_inner = ctk.CTkFrame(stats_frame, fg_color="transparent")
        stats_inner.pack(fill="x", padx=15, pady=12)

        stat_items = [
            ("수집", str(stats.get("total_collected", 0)) + "건"),
            ("매체필터", str(stats.get("after_media_filter", 0)) + "건"),
            ("중복병합", str(stats.get("after_dedup", 0)) + "건"),
            ("최종", str(stats.get("final_count", 0)) + "건"),
            ("제품", str(stats.get("product_count", 0)) + "건"),
            ("기업", str(stats.get("company_count", 0)) + "건"),
            ("경쟁사", str(stats.get("competitor_count", 0)) + "건"),
        ]


        for i, (label, value) in enumerate(stat_items):
            col = ctk.CTkFrame(stats_inner, fg_color="transparent")
            col.pack(side="left", expand=True, fill="x")

            ctk.CTkLabel(col, text=label, font=FONT_CAPTION, text_color=TEXT_SECONDARY).pack()
            ctk.CTkLabel(col, text=value, font=FONT_BODY_BOLD, text_color=COBALT).pack()

            if i < len(stat_items) - 1:
                ctk.CTkFrame(stats_inner, fg_color="#E5E7EB", width=1).pack(
                    side="left", fill="y", padx=5, pady=5
                )

        # ── 기사 없으면 안내 ──
        if not articles:
            ctk.CTkLabel(
                self.result_area,
                text="검색 조건에 맞는 기사가 없습니다.\n키워드나 매체 범위를 확인해주세요.",
                font=FONT_BODY,
                text_color=TEXT_SECONDARY
            ).pack(pady=40)
            return

        # ── 섹션별 기사 표시 ──
        sections = [
            ("product", "🎯 제품/브랜드 기사", COBALT),
            ("company", "🏢 기업 기사", NAVY_LIGHT),
            ("competitor", "⚔️ 경쟁사 기사", ACCENT_ORANGE),
        ]


        for section_key, section_title, section_color in sections:
            section_articles = [a for a in articles if a.get("section") == section_key]
            if not section_articles:
                continue

            header_frame = ctk.CTkFrame(
                self.result_area,
                fg_color=section_color,
                corner_radius=8,
                height=36
            )
            header_frame.pack(fill="x", padx=15, pady=(15, 8))
            header_frame.pack_propagate(False)

            ctk.CTkLabel(
                header_frame,
                text=f"  {section_title} ({len(section_articles)}건)",
                font=FONT_SMALL_BOLD,
                text_color="white"
            ).pack(side="left", padx=10, pady=5)

            for article in section_articles:
                self._create_article_card(article)

        # ── 내보내기 버튼 활성화 ──
        self.export_button.configure(
            state="normal",
            fg_color=COBALT,
            text_color="white",
            hover_color=COBALT_HOVER
        )

    def _create_article_card(self, article: dict):
        card = ctk.CTkFrame(
            self.result_area,
            fg_color=BG_WHITE,
            corner_radius=10,
            border_width=1,
            border_color="#E5E7EB"
        )
        card.pack(fill="x", padx=15, pady=(0, 8))

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="x", padx=15, pady=12)

        # 상단: 티어 뱃지 + 매체명 + 날짜
        top_row = ctk.CTkFrame(inner, fg_color="transparent")
        top_row.pack(fill="x", pady=(0, 6))

        tier = article.get("tier", 0)
        tier_colors = {1: TIER_1_BG, 2: TIER_2_BG, 3: TIER_3_BG}
        tier_fg = {1: TIER_1_FG, 2: TIER_2_FG, 3: TIER_3_FG}

        ctk.CTkLabel(
            top_row,
            text=f" T{tier} ",
            font=FONT_CAPTION,
            fg_color=tier_colors.get(tier, "#999"),
            text_color=tier_fg.get(tier, "white"),
            corner_radius=4
        ).pack(side="left")

        ctk.CTkLabel(
            top_row,
            text=f"  {article.get('media_name', '')}",
            font=FONT_SMALL_BOLD,
            text_color=TEXT_SECONDARY
        ).pack(side="left")

        ctk.CTkLabel(
            top_row,
            text=article.get("pubDate", ""),
            font=FONT_CAPTION,
            text_color=TEXT_PLACEHOLDER
        ).pack(side="right")

        # 제목
        ctk.CTkLabel(
            inner,
            text=article.get("title", ""),
            font=FONT_BODY_BOLD,
            text_color=TEXT_PRIMARY,
            anchor="w",
            wraplength=600
        ).pack(fill="x", pady=(0, 4))

        # 요약
        desc = article.get("description", "")
        if desc:
            ctk.CTkLabel(
                inner,
                text=desc,
                font=FONT_SMALL,
                text_color=TEXT_SECONDARY,
                anchor="w",
                wraplength=600
            ).pack(fill="x", pady=(0, 6))

        # 매칭 키워드 태그
        matched_tags = article.get("matched_tags", [])
        if matched_tags:
            tag_frame = ctk.CTkFrame(inner, fg_color="transparent")
            tag_frame.pack(fill="x", pady=(0, 4))
            for tag in matched_tags[:5]:
                tag_color = COBALT if tag.startswith("🏢") else ACCENT_ORANGE
                ctk.CTkLabel(
                    tag_frame,
                    text=f" {tag} ",
                    font=FONT_CAPTION,
                    fg_color=tag_color,
                    text_color="white",
                    corner_radius=4
                ).pack(side="left", padx=(0, 4))

        # 커버리지 (유사 기사 — 펼침/접힘)
        similar_count = article.get("similar_count", 0)
        if similar_count > 0:
            similar_articles = article.get("similar_articles", [])
            similar_sources = article.get("similar_sources", [])

            coverage_container = ctk.CTkFrame(inner, fg_color="transparent")
            coverage_container.pack(fill="x", pady=(0, 4))

            # 요약 바 (클릭 가능)
            summary_btn = ctk.CTkButton(
                coverage_container,
                text=f"  📰 유사 기사 {similar_count}건 ▸ 클릭하여 펼치기",
                font=FONT_CAPTION,
                fg_color=SKY_BLUE,
                text_color=NAVY,
                hover_color="#CBD5F0",
                height=28,
                corner_radius=6,
                anchor="w",
                command=None  # 아래에서 설정
            )
            summary_btn.pack(fill="x")

            # 펼침 영역 (처음에는 숨김)
            detail_frame = ctk.CTkFrame(
                coverage_container,
                fg_color=BG_WHITE,
                border_width=1,
                border_color="#E2E8F0",
                corner_radius=6
            )
            detail_is_visible = {"value": False}

            # 유사 기사 상세 목록 채우기
            if similar_articles:
                for sim_art in similar_articles:
                    row = ctk.CTkFrame(detail_frame, fg_color="transparent")
                    row.pack(fill="x", padx=10, pady=(4, 0))

                    # 매체명
                    sim_name = sim_art.get("media_name", sim_art.get("source", ""))
                    sim_tier = sim_art.get("tier", 0)
                    tier_colors = {1: TIER_1_BG, 2: TIER_2_BG, 3: TIER_3_BG}
                    tier_fg_colors = {1: TIER_1_FG, 2: TIER_2_FG, 3: TIER_3_FG}

                    row_top = ctk.CTkFrame(row, fg_color="transparent")
                    row_top.pack(fill="x")

                    ctk.CTkLabel(
                        row_top,
                        text=f" T{sim_tier} ",
                        font=FONT_CAPTION,
                        fg_color=tier_colors.get(sim_tier, "#999"),
                        text_color=tier_fg_colors.get(sim_tier, "white"),
                        corner_radius=3
                    ).pack(side="left")

                    ctk.CTkLabel(
                        row_top,
                        text=f"  {sim_name}",
                        font=FONT_CAPTION,
                        text_color=TEXT_SECONDARY
                    ).pack(side="left")

                    ctk.CTkLabel(
                        row_top,
                        text=sim_art.get("pubDate", ""),
                        font=FONT_CAPTION,
                        text_color=TEXT_PLACEHOLDER
                    ).pack(side="right")

                    # 제목 (클릭 가능)
                    sim_title = sim_art.get("title", "제목 없음")
                    sim_url = sim_art.get("originallink") or sim_art.get("link", "")

                    if sim_url:
                        title_btn = ctk.CTkButton(
                            row,
                            text=sim_title,
                            font=FONT_CAPTION,
                            fg_color="transparent",
                            text_color=COBALT,
                            hover_color=SKY_BLUE,
                            height=20,
                            anchor="w",
                            command=lambda url=sim_url: self._open_url(url)
                        )
                        title_btn.pack(fill="x", pady=(0, 4))
                    else:
                        ctk.CTkLabel(
                            row,
                            text=sim_title,
                            font=FONT_CAPTION,
                            text_color=TEXT_PRIMARY,
                            anchor="w"
                        ).pack(fill="x", pady=(0, 4))

                # 하단 여백
                ctk.CTkFrame(detail_frame, fg_color="transparent", height=6).pack()

            else:
                # similar_articles가 없으면 매체명만 표시 (하위 호환)
                sources_text = ", ".join(similar_sources[:10])
                if len(similar_sources) > 10:
                    sources_text += f" 외 {len(similar_sources) - 10}개"
                ctk.CTkLabel(
                    detail_frame,
                    text=f"  {sources_text}",
                    font=FONT_CAPTION,
                    text_color=TEXT_SECONDARY,
                    anchor="w"
                ).pack(fill="x", padx=10, pady=6)

            # 토글 함수
            def toggle_detail(df=detail_frame, btn=summary_btn, vis=detail_is_visible, cnt=similar_count):
                if vis["value"]:
                    df.pack_forget()
                    btn.configure(text=f"  📰 유사 기사 {cnt}건 ▸ 클릭하여 펼치기")
                    vis["value"] = False
                else:
                    df.pack(fill="x", pady=(4, 0))
                    btn.configure(text=f"  📰 유사 기사 {cnt}건 ▾ 클릭하여 접기")
                    vis["value"] = True

            summary_btn.configure(command=toggle_detail)

        # 링크 버튼
        link_url = article.get("originallink") or article.get("link", "")
        if link_url:
            ctk.CTkButton(
                inner,
                text="🔗 원문 보기",
                font=FONT_CAPTION,
                fg_color="transparent",
                text_color=COBALT,
                hover_color=SKY_BLUE,
                height=24,
                anchor="w",
                command=lambda url=link_url: self._open_url(url)
            ).pack(anchor="w")

    def _open_url(self, url: str):
        webbrowser.open(url)

    # ══════════════════════════════════════
    #  내보내기
    # ══════════════════════════════════════
    def _on_export_click(self):
        """HTML 리포트 내보내기 — 저장 위치 선택"""
        if not hasattr(self, '_last_articles') or not self._last_articles:
            return

        try:
            from tkinter import filedialog
            from datetime import datetime
            from output.report_builder import build_html_report, save_report

            # 기본 파일명 생성
            default_name = f"뉴스클리핑_{datetime.now().strftime('%Y%m%d_%H%M')}.html"

            # 저장 경로 선택 다이얼로그
            filepath = filedialog.asksaveasfilename(
                parent=self,
                title="HTML 리포트 저장",
                initialfile=default_name,
                defaultextension=".html",
                filetypes=[("HTML 파일", "*.html"), ("모든 파일", "*.*")]
            )

            # 사용자가 취소를 눌렀으면 중단
            if not filepath:
                return

            # 설정 로드
            settings = {}
            settings_path = os.path.join("config", "settings.yaml")
            if os.path.exists(settings_path):
                with open(settings_path, "r", encoding="utf-8") as f:
                    settings = yaml.safe_load(f) or {}

            stats = getattr(self, '_last_stats', {})

            # HTML 생성
            html = build_html_report(self._last_articles, stats, settings)

            # 선택한 경로에 저장
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(html)

            print(f"✅ HTML 리포트 저장 완료: {filepath}")

        except Exception as e:
            print(f"❌ HTML 내보내기 실패: {e}")
            import traceback
            traceback.print_exc()


    # ══════════════════════════════════════
    #  설정 다이얼로그
    # ══════════════════════════════════════
    def _open_settings_search(self):
        from ui.settings_search_dialog import SettingsSearchDialog
        dialog = SettingsSearchDialog(self, self.settings)
        self.wait_window(dialog)
        self.settings = self._load_settings()
        self._refresh_settings_summary()
        self._update_start_button_state()

    def _open_settings_api(self):
        from ui.settings_api_dialog import SettingsApiDialog
        dialog = SettingsApiDialog(self, self.settings)
        self.wait_window(dialog)
        self.settings = self._load_settings()
        self._refresh_settings_summary()
        self._update_start_button_state()

    def _update_start_button_state(self):
        if self._is_setup_complete():
            self.start_button.configure(state="normal", fg_color=COBALT)
        else:
            self.start_button.configure(state="disabled", fg_color="#4A6FA5")

    # ══════════════════════════════════════
    #  유틸리티
    # ══════════════════════════════════════
    def _is_setup_complete(self) -> bool:
        api = self.settings.get("api", {})
        naver = api.get("naver", {})
        gemini = api.get("gemini", {})
        search = self.settings.get("search", {})
        keywords = search.get("keywords", {})

        return all([
            naver.get("client_id"),
            naver.get("client_secret"),
            gemini.get("api_key"),
            search.get("industries"),
            keywords.get("products"),
            keywords.get("company")
        ])

    def _load_settings(self):
        """config/settings.yaml 로드"""
        import yaml
        settings_path = os.path.join("config", "settings.yaml")
        if os.path.exists(settings_path):
           with open(settings_path, "r", encoding="utf-8") as f:
             return yaml.safe_load(f) or {}
        return {}

