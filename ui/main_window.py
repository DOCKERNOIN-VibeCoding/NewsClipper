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

        # ── 창 닫기 시 백그라운드 작업 안전하게 종료 ──
        self._closing = False
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _on_close(self):
        """X 버튼 클릭 시 호출. 백그라운드 작업이 자기 자신 정리하도록 플래그만 세팅."""
        self._closing = True
        try:
            self.destroy()
        except Exception:
            pass
        # 강제 종료 (백그라운드 데몬 스레드도 정리됨)
        import os
        os._exit(0)


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

        def safe_after(func, *args):
            """창이 이미 파괴된 경우 무시하고, 살아있을 때만 UI 업데이트."""
            if getattr(self, "_closing", False):
                return
            try:
                self.after(0, func, *args)
            except Exception:
                pass

        def on_progress(step, total, message):
            progress = step / total
            safe_after(self._update_progress, progress, message)

        def on_log(message):
            safe_after(self._append_log, message)

        try:
            results = pipeline.run(
                progress_callback=on_progress,
                log_callback=on_log
            )
            safe_after(self._on_pipeline_complete, results)
        except Exception as e:
            import traceback
            traceback.print_exc()
            safe_after(self._on_pipeline_error, str(e))


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

        # ── 통계 요약 (1줄, 컴팩트) ──
        stats_frame = ctk.CTkFrame(
            self.result_area, fg_color=BG_WHITE,
            corner_radius=8, height=56,  # 고정 높이로 컴팩트하게
        )
        stats_frame.pack(fill="x", padx=15, pady=(8, 6))
        stats_frame.pack_propagate(False)  # 자식이 늘려도 높이 고정

        stats_inner = ctk.CTkFrame(stats_frame, fg_color="transparent")
        stats_inner.pack(fill="both", expand=True, padx=12, pady=4)


        stat_items = [
            ("수집", str(stats.get("total_collected", 0)) + "건"),
            ("매체필터", str(stats.get("after_media_filter", 0)) + "건"),
            ("중복병합", str(stats.get("after_dedup", 0)) + "건"),
            ("AI필터", str(stats.get("after_ai_filter", 0)) + "건"),
            ("최종", str(stats.get("final_count", 0)) + "건"),
            ("제품", str(stats.get("product_count", 0)) + "건"),
            ("기업", str(stats.get("company_count", 0)) + "건"),
            ("경쟁사", str(stats.get("competitor_count", 0)) + "건"),
        ]

        for i, (label, value) in enumerate(stat_items):
            col = ctk.CTkFrame(stats_inner, fg_color="transparent")
            col.pack(side="left", expand=True, fill="both")

            ctk.CTkLabel(
                col, text=label,
                font=FONT_CAPTION, text_color=TEXT_SECONDARY
            ).pack(pady=(2, 0))
            ctk.CTkLabel(
                col, text=value,
                font=FONT_SMALL_BOLD, text_color=COBALT  # FONT_BODY_BOLD → FONT_SMALL_BOLD
            ).pack(pady=(0, 2))

            if i < len(stat_items) - 1:
                ctk.CTkFrame(stats_inner, fg_color="#E5E7EB", width=1).pack(
                    side="left", fill="y", padx=5, pady=5
                )

        # ── AI 분석 결과 카드 (v2.0 신규) ──
        if stats.get("ai_enabled"):
            ai_card = ctk.CTkFrame(
                self.result_area,
                fg_color=AI_SUMMARY_BG,
                corner_radius=10,
                border_width=1,
                border_color=AI_SUMMARY_BORDER,
            )
            ai_card.pack(fill="x", padx=15, pady=(0, 12))

            ai_inner = ctk.CTkFrame(ai_card, fg_color="transparent")
            ai_inner.pack(fill="x", padx=15, pady=10)

            ai_succeeded = stats.get("ai_succeeded", 0)
            ai_fallback = stats.get("ai_fallback", 0)
            by_rel = stats.get("ai_by_relevance", {}) or {}

            top = ctk.CTkFrame(ai_inner, fg_color="transparent")
            top.pack(fill="x")
            ctk.CTkLabel(
                top, text="🤖 AI 분석 결과",
                font=FONT_SMALL_BOLD, text_color=AI_SUMMARY_TEXT,
            ).pack(side="left")
            ctk.CTkLabel(
                top,
                text=f"  성공 {ai_succeeded}건  ·  Fallback {ai_fallback}건",
                font=FONT_CAPTION, text_color=TEXT_SECONDARY,
            ).pack(side="left")

            rel_row = ctk.CTkFrame(ai_inner, fg_color="transparent")
            rel_row.pack(fill="x", pady=(6, 0))
            relevance_chips = [
                ("🟢 핵심",   by_rel.get("core", 0),       RELEVANCE_CORE_BG),
                ("🔵 관련",   by_rel.get("relevant", 0),   RELEVANCE_RELEVANT_BG),
                ("🟡 간접",   by_rel.get("passing", 0),    RELEVANCE_PASSING_BG),
                ("⚫ 무관",    by_rel.get("irrelevant", 0), RELEVANCE_IRRELEVANT_BG),
            ]
            for label, count, color in relevance_chips:
                ctk.CTkLabel(
                    rel_row,
                    text=f"  {label} {count}건  ",
                    font=FONT_CAPTION,
                    fg_color=color, text_color="white",
                    corner_radius=10,
                ).pack(side="left", padx=(0, 6))

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
        # passing 등급은 별도의 접힌 섹션으로 분리
        sections = [
            ("product", "🎯 제품/브랜드 기사", COBALT, False),
            ("company", "🏢 기업 기사", NAVY_LIGHT, False),
            ("competitor", "⚔️ 경쟁사 기사", ACCENT_ORANGE, False),
            ("industry", "🏭 업계 기사", "#5A6F8A", False),
        ]

        ai_filter_cfg = self.settings.get("ai", {}).get("filter", {}) or {}
        passing_collapsed = ai_filter_cfg.get("passing_to_collapsed", True)

        # 메인 섹션 (passing 제외)
        for section_key, section_title, section_color, _ in sections:
            section_articles = [
                a for a in articles
                if a.get("section") == section_key
                and (not passing_collapsed or a.get("ai_relevance") != "passing")
            ]
            if not section_articles:
                continue

            self._render_section_header(section_title, section_color, len(section_articles))
            for article in section_articles:
                self._create_article_card(article)

        # 간접 언급(passing) 통합 섹션 — 접힌 상태로
        if passing_collapsed:
            passing_articles = [a for a in articles if a.get("ai_relevance") == "passing"]
            if passing_articles:
                self._render_collapsible_section(
                    "💬 간접 언급 기사",
                    "#9CA3AF",
                    passing_articles,
                )

        # ── 내보내기 버튼 활성화 ──
        self.export_button.configure(
            state="normal",
            fg_color=COBALT,
            text_color="white",
            hover_color=COBALT_HOVER
        )

    def _render_section_header(self, title: str, color: str, count: int):
        """일반 섹션 헤더 렌더링"""
        header_frame = ctk.CTkFrame(
            self.result_area, fg_color=color, corner_radius=8, height=36
        )
        header_frame.pack(fill="x", padx=15, pady=(15, 8))
        header_frame.pack_propagate(False)
        ctk.CTkLabel(
            header_frame,
            text=f"  {title} ({count}건)",
            font=FONT_SMALL_BOLD, text_color="white",
        ).pack(side="left", padx=10, pady=5)

    def _render_collapsible_section(self, title: str, color: str, articles: list):
        """접힌 상태의 섹션 (간접 언급용)"""
        # 헤더 (클릭 가능)
        header_frame = ctk.CTkFrame(
            self.result_area, fg_color=color, corner_radius=8, height=36
        )
        header_frame.pack(fill="x", padx=15, pady=(15, 4))
        header_frame.pack_propagate(False)

        toggle_btn = ctk.CTkButton(
            header_frame,
            text=f"  {title} ({len(articles)}건)  ▸  클릭하여 펼치기",
            font=FONT_SMALL_BOLD,
            fg_color=color, text_color="white",
            hover_color=color, anchor="w",
            corner_radius=8, height=36,
        )
        toggle_btn.pack(fill="both", expand=True)

        # 컨테이너 (처음에는 비어 있음)
        container = ctk.CTkFrame(self.result_area, fg_color="transparent")
        # 접힌 상태로 시작 → pack 안 함

        is_visible = {"value": False}

        def toggle():
            if is_visible["value"]:
                container.pack_forget()
                toggle_btn.configure(
                    text=f"  {title} ({len(articles)}건)  ▸  클릭하여 펼치기"
                )
                is_visible["value"] = False
            else:
                container.pack(fill="x", before=None)
                toggle_btn.configure(
                    text=f"  {title} ({len(articles)}건)  ▾  클릭하여 접기"
                )
                # 처음 펼칠 때만 카드 생성 (lazy)
                if not container.winfo_children():
                    # result_area에서 container를 적절한 위치로 옮기기 위해
                    # 단순히 pack(fill="x") 후 카드들을 채움
                    pass
                # 카드는 매번 다시 그리지 말고 한 번만 생성
                if not getattr(container, "_built", False):
                    for art in articles:
                        self._create_article_card(art, parent=container)
                    container._built = True
                is_visible["value"] = True

        toggle_btn.configure(command=toggle)

    def _create_article_card(self, article: dict, parent=None):
        """기사 카드 렌더링.
        parent를 지정하면 그 안에, 아니면 result_area에 추가."""
        if parent is None:
            parent = self.result_area

        card = ctk.CTkFrame(
            parent,
            fg_color=BG_WHITE,
            corner_radius=10,
            border_width=1,
            border_color="#E5E7EB"
        )
        card.pack(fill="x", padx=15, pady=(0, 8))

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="x", padx=15, pady=12)

        # ── 상단: 티어 뱃지 + 매체명 + 관련도 뱃지 + 감성 + 날짜 ──
        top_row = ctk.CTkFrame(inner, fg_color="transparent")
        top_row.pack(fill="x", pady=(0, 6))

        tier = article.get("tier", 0)
        tier_colors = {1: TIER_1_BG, 2: TIER_2_BG, 3: TIER_3_BG}
        tier_fg = {1: TIER_1_FG, 2: TIER_2_FG, 3: TIER_3_FG}

        ctk.CTkLabel(
            top_row, text=f" T{tier} ",
            font=FONT_CAPTION,
            fg_color=tier_colors.get(tier, "#999"),
            text_color=tier_fg.get(tier, "white"),
            corner_radius=4
        ).pack(side="left")

        ctk.CTkLabel(
            top_row, text=f"  {article.get('media_name', '')}",
            font=FONT_SMALL_BOLD, text_color=TEXT_SECONDARY
        ).pack(side="left")

        # ── AI 관련도 뱃지 (v2.0 신규) ──
        ai_relevance = article.get("ai_relevance")
        relevance_meta = {
            "core":     ("🟢 핵심", RELEVANCE_CORE_BG),
            "relevant": ("🔵 관련", RELEVANCE_RELEVANT_BG),
            "passing":  ("🟡 간접", RELEVANCE_PASSING_BG),
        }
        if ai_relevance in relevance_meta:
            label, color = relevance_meta[ai_relevance]
            ctk.CTkLabel(
                top_row, text=f"  {label}  ",
                font=FONT_CAPTION,
                fg_color=color, text_color="white",
                corner_radius=8,
            ).pack(side="left", padx=(6, 0))

        # ── AI 감성 태그 (v2.0 신규) ──
        ai_sentiment = article.get("ai_sentiment")
        sentiment_meta = {
            "positive": ("긍정 ↑", SENTIMENT_POSITIVE),
            "neutral":  ("중립 —", SENTIMENT_NEUTRAL),
            "negative": ("부정 ↓", SENTIMENT_NEGATIVE),
        }
        if ai_sentiment in sentiment_meta:
            label, color = sentiment_meta[ai_sentiment]
            ctk.CTkLabel(
                top_row, text=f"  {label}  ",
                font=FONT_CAPTION,
                fg_color=color, text_color="white",
                corner_radius=8,
            ).pack(side="left", padx=(4, 0))

        # ── Fallback 뱃지 (AI 분석 실패 시) ──
        if article.get("ai_fallback"):
            ctk.CTkLabel(
                top_row, text="  ⚠ 키워드매칭  ",
                font=FONT_CAPTION,
                fg_color=FALLBACK_BADGE_BG, text_color=FALLBACK_BADGE_TEXT,
                corner_radius=8,
            ).pack(side="left", padx=(4, 0))

        ctk.CTkLabel(
            top_row, text=article.get("pubDate", ""),
            font=FONT_CAPTION, text_color=TEXT_PLACEHOLDER
        ).pack(side="right")


        # ── 제목 ──
        ctk.CTkLabel(
            inner, text=article.get("title", ""),
            font=FONT_BODY_BOLD, text_color=TEXT_PRIMARY,
            anchor="w", justify="left", wraplength=820   # ← 600 → 820
        ).pack(fill="x", expand=True, pady=(0, 4), anchor="w")


        # ── AI 요약 박스 (v2.0 신규) ──
        ai_summary = article.get("ai_summary", "").strip()
        if ai_summary and not article.get("ai_fallback"):
            summary_box = ctk.CTkFrame(
                inner,
                fg_color=AI_SUMMARY_BG,
                corner_radius=6,
                border_width=1,
                border_color=AI_SUMMARY_BORDER,
            )
            summary_box.pack(fill="x", pady=(2, 6))
            ctk.CTkLabel(
                summary_box,
                text=f"🤖 {ai_summary}",
                font=FONT_SMALL,
                text_color=AI_SUMMARY_TEXT,
                anchor="w",                   # 왼쪽 앵커
                justify="left",               # 줄바꿈된 줄도 왼쪽 정렬
                wraplength=820,               # ← 580 → 820 (이슈 3 적용)
            ).pack(fill="x", expand=True, padx=12, pady=8, anchor="w")
            #          ^^^^^^^^^^^^^^^^^^                  ^^^^^^^^^^
            # expand로 라벨이 좌우 꽉 채우게 + 라벨 위치 자체도 west로

        else:
            desc = article.get("description", "")
            if desc:
                ctk.CTkLabel(
                    inner, text=desc,
                    font=FONT_SMALL, text_color=TEXT_SECONDARY,
                    anchor="w", justify="left", wraplength=820
                ).pack(fill="x", expand=True, pady=(0, 6), anchor="w")


        # ── AI 엔티티 칩 (v2.0 신규) ──
        ai_entities = article.get("ai_entities", []) or []
        if ai_entities:
            entity_frame = ctk.CTkFrame(inner, fg_color="transparent")
            entity_frame.pack(fill="x", pady=(0, 4))
            ctk.CTkLabel(
                entity_frame, text="🏷️",
                font=FONT_CAPTION, text_color=TEXT_SECONDARY,
            ).pack(side="left", padx=(0, 4))
            for entity in ai_entities[:6]:  # 최대 6개
                ctk.CTkLabel(
                    entity_frame, text=f" {entity} ",
                    font=FONT_CAPTION,
                    fg_color=ENTITY_CHIP_BG, text_color=ENTITY_CHIP_TEXT,
                    corner_radius=4,
                ).pack(side="left", padx=(0, 4))

        # ── 매칭 키워드 태그 (v1 유지) ──
        matched_tags = article.get("matched_tags", [])
        if matched_tags:
            tag_frame = ctk.CTkFrame(inner, fg_color="transparent")
            tag_frame.pack(fill="x", pady=(0, 4))
            for tag in matched_tags[:5]:
                tag_color = COBALT if tag.startswith("🏢") else ACCENT_ORANGE
                ctk.CTkLabel(
                    tag_frame, text=f" {tag} ",
                    font=FONT_CAPTION,
                    fg_color=tag_color, text_color="white",
                    corner_radius=4
                ).pack(side="left", padx=(0, 4))

        # ── 유사 기사 (펼침/접힘 — v1 로직 그대로) ──
        similar_count = article.get("similar_count", 0)
        if similar_count > 0:
            similar_articles = article.get("similar_articles", [])
            similar_sources = article.get("similar_sources", [])

            coverage_container = ctk.CTkFrame(inner, fg_color="transparent")
            coverage_container.pack(fill="x", pady=(0, 4))

            summary_btn = ctk.CTkButton(
                coverage_container,
                text=f"  📰 유사 기사 {similar_count}건 ▸ 클릭하여 펼치기",
                font=FONT_CAPTION,
                fg_color=SKY_BLUE, text_color=NAVY,
                hover_color="#CBD5F0",
                height=28, corner_radius=6, anchor="w",
                command=None
            )
            summary_btn.pack(fill="x")

            detail_frame = ctk.CTkFrame(
                coverage_container,
                fg_color=BG_WHITE,
                border_width=1, border_color="#E2E8F0",
                corner_radius=6,
            )
            detail_is_visible = {"value": False}

            if similar_articles:
                for sim_art in similar_articles:
                    row = ctk.CTkFrame(detail_frame, fg_color="transparent")
                    row.pack(fill="x", padx=10, pady=(4, 0))

                    sim_name = sim_art.get("media_name", sim_art.get("source", ""))
                    sim_tier = sim_art.get("tier", 0)
                    tcols = {1: TIER_1_BG, 2: TIER_2_BG, 3: TIER_3_BG}
                    tfgs = {1: TIER_1_FG, 2: TIER_2_FG, 3: TIER_3_FG}

                    row_top = ctk.CTkFrame(row, fg_color="transparent")
                    row_top.pack(fill="x")
                    ctk.CTkLabel(
                        row_top, text=f" T{sim_tier} ",
                        font=FONT_CAPTION,
                        fg_color=tcols.get(sim_tier, "#999"),
                        text_color=tfgs.get(sim_tier, "white"),
                        corner_radius=3
                    ).pack(side="left")
                    ctk.CTkLabel(
                        row_top, text=f"  {sim_name}",
                        font=FONT_CAPTION, text_color=TEXT_SECONDARY
                    ).pack(side="left")
                    ctk.CTkLabel(
                        row_top, text=sim_art.get("pubDate", ""),
                        font=FONT_CAPTION, text_color=TEXT_PLACEHOLDER
                    ).pack(side="right")

                    sim_title = sim_art.get("title", "제목 없음")
                    sim_url = sim_art.get("originallink") or sim_art.get("link", "")
                    if sim_url:
                        ctk.CTkButton(
                            row, text=sim_title,
                            font=FONT_CAPTION,
                            fg_color="transparent", text_color=COBALT,
                            hover_color=SKY_BLUE,
                            height=20, anchor="w",
                            command=lambda url=sim_url: self._open_url(url)
                        ).pack(fill="x", pady=(0, 4))
                    else:
                        ctk.CTkLabel(
                            row, text=sim_title,
                            font=FONT_CAPTION, text_color=TEXT_PRIMARY,
                            anchor="w"
                        ).pack(fill="x", pady=(0, 4))
                ctk.CTkFrame(detail_frame, fg_color="transparent", height=6).pack()
            else:
                sources_text = ", ".join(similar_sources[:10])
                if len(similar_sources) > 10:
                    sources_text += f" 외 {len(similar_sources) - 10}개"
                ctk.CTkLabel(
                    detail_frame,
                    text=f"  {sources_text}",
                    font=FONT_CAPTION, text_color=TEXT_SECONDARY,
                    anchor="w"
                ).pack(fill="x", padx=10, pady=6)

            def toggle_detail(df=detail_frame, btn=summary_btn,
                              vis=detail_is_visible, cnt=similar_count):
                if vis["value"]:
                    df.pack_forget()
                    btn.configure(text=f"  📰 유사 기사 {cnt}건 ▸ 클릭하여 펼치기")
                    vis["value"] = False
                else:
                    df.pack(fill="x", pady=(4, 0))
                    btn.configure(text=f"  📰 유사 기사 {cnt}건 ▾ 클릭하여 접기")
                    vis["value"] = True

            summary_btn.configure(command=toggle_detail)

        # ── 원문 링크 ──
        link_url = article.get("originallink") or article.get("link", "")
        if link_url:
            ctk.CTkButton(
                inner, text="🔗 원문 보기",
                font=FONT_CAPTION,
                fg_color="transparent", text_color=COBALT,
                hover_color=SKY_BLUE,
                height=24, anchor="w",
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

