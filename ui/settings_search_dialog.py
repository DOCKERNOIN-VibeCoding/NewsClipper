"""기사 검색 조건 설정 다이얼로그"""

import customtkinter as ctk
import yaml
import os
from ui.theme import *


class SettingsSearchDialog(ctk.CTkToplevel):
    def __init__(self, parent, settings: dict):
        super().__init__(parent)

        self.settings = settings.copy()
        self.title("🔍 기사 검색 조건 설정")
        self.geometry("550x780")
        self.resizable(False, False)
        self.configure(fg_color=BG_MAIN)
        self.transient(parent)
        self.grab_set()

        self.industry_data = self._load_industry_keywords()
        self._build_ui()

    def _build_ui(self):
        search = self.settings.get("search", {})
        keywords = search.get("keywords", {})
        schedule = self.settings.get("schedule", {})
        media = self.settings.get("media", {})

        # ── 헤더 ──
        header = ctk.CTkFrame(self, fg_color=NAVY, height=60, corner_radius=0)
        header.pack(fill="x")
        header.pack_propagate(False)
        ctk.CTkLabel(
            header, text="🔍 기사 검색 조건 설정",
            font=FONT_SUBTITLE, text_color=TEXT_ON_NAVY
        ).pack(side="left", padx=20, pady=15)

        # ── 본문 스크롤 ──
        body = ctk.CTkScrollableFrame(self, fg_color=BG_MAIN)
        body.pack(fill="both", expand=True, padx=20, pady=15)

        # ══════════════════════════════
        #  1. 산업군 선택
        # ══════════════════════════════
        ctk.CTkLabel(body, text="🏭 산업군 선택 (필수, 최대 3개)", font=FONT_BODY_BOLD, text_color=TEXT_PRIMARY).pack(anchor="w", pady=(0, 8))

        available = list(self.industry_data.get("industries", {}).keys())
        selected = search.get("industries", [])

        self.industry_vars = {}
        for ind in available:
            var = ctk.BooleanVar(value=(ind in selected))
            self.industry_vars[ind] = var
            ctk.CTkCheckBox(
                body, text=f"{ind}",
                variable=var, font=FONT_SMALL,
                fg_color=COBALT, hover_color=COBALT_HOVER,
                text_color=TEXT_PRIMARY
            ).pack(anchor="w", pady=2)

        ctk.CTkFrame(body, fg_color="#E5E7EB", height=1).pack(fill="x", pady=12)

        # ══════════════════════════════
        #  2. 키워드 — 제품/브랜드명
        # ══════════════════════════════
        ctk.CTkLabel(body, text="🎯 제품/브랜드명 (필수)", font=FONT_BODY_BOLD, text_color=TEXT_PRIMARY).pack(anchor="w", pady=(0, 3))
        ctk.CTkLabel(body, text="모니터링할 제품명, 브랜드명을 쉼표로 구분하여 입력\n이 키워드가 포함된 기사에 최우선 가중치가 부여됩니다", font=FONT_CAPTION, text_color=TEXT_SECONDARY).pack(anchor="w", pady=(0, 5))
        self.products_entry = ctk.CTkEntry(body, placeholder_text="예: 비비고, 비비고 군만두, 비비고 왕만두, 햇반", height=36)
        self.products_entry.pack(fill="x", pady=(0, 10))
        if keywords.get("products"):
            self.products_entry.insert(0, ", ".join(keywords["products"]))

        # ══════════════════════════════
        #  3. 키워드 — 회사명
        # ══════════════════════════════
        ctk.CTkLabel(body, text="🏢 회사명 (필수, 1~2개)", font=FONT_BODY_BOLD, text_color=TEXT_PRIMARY).pack(anchor="w", pady=(0, 3))
        ctk.CTkLabel(body, text="제품을 만드는 회사명 입력\n회사명만 언급된 기사는 별도 섹션(기업 기사)으로 분류됩니다", font=FONT_CAPTION, text_color=TEXT_SECONDARY).pack(anchor="w", pady=(0, 5))
        self.company_entry = ctk.CTkEntry(body, placeholder_text="예: 제일제당, CJ", height=36)
        self.company_entry.pack(fill="x", pady=(0, 10))
        if keywords.get("company"):
            self.company_entry.insert(0, ", ".join(keywords["company"]))

        # ══════════════════════════════
        #  4. 유의주시 경쟁사
        # ══════════════════════════════
        ctk.CTkLabel(body, text="⚔️ 유의주시 경쟁사 (선택사항)", font=FONT_BODY_BOLD, text_color=TEXT_PRIMARY).pack(anchor="w", pady=(0, 3))
        ctk.CTkLabel(body, text="경쟁사 회사명을 입력하면 해당 기사에 우선순위가 부여됩니다\nAI가 제품 관련 vs 경영 뉴스를 자동 구분합니다 (v2.2)", font=FONT_CAPTION, text_color=TEXT_SECONDARY).pack(anchor="w", pady=(0, 5))
        self.competitors_entry = ctk.CTkEntry(body, placeholder_text="예: 오뚜기, 풀무원, 대상", height=36)
        self.competitors_entry.pack(fill="x", pady=(0, 10))
        if keywords.get("competitors"):
            self.competitors_entry.insert(0, ", ".join(keywords["competitors"]))

        # ══════════════════════════════
        #  5. 업계 공통 키워드
        # ══════════════════════════════
        ctk.CTkLabel(body, text="🏷️ 업계 공통 키워드 (선택사항)", font=FONT_BODY_BOLD, text_color=TEXT_PRIMARY).pack(anchor="w", pady=(0, 3))
        self.general_entry = ctk.CTkEntry(body, placeholder_text="예: 식품안전, HMR, 간편식", height=36)
        self.general_entry.pack(fill="x", pady=(0, 10))
        if keywords.get("industry_general"):
            self.general_entry.insert(0, ", ".join(keywords["industry_general"]))

        ctk.CTkFrame(body, fg_color="#E5E7EB", height=1).pack(fill="x", pady=12)

        # ══════════════════════════════
        #  6. 스케줄
        # ══════════════════════════════
        ctk.CTkLabel(body, text="📅 취합 스케줄", font=FONT_BODY_BOLD, text_color=TEXT_PRIMARY).pack(anchor="w", pady=(0, 8))

        sched_frame = ctk.CTkFrame(body, fg_color="transparent")
        sched_frame.pack(fill="x", pady=(0, 5))
        sched_frame.grid_columnconfigure(0, weight=1)
        sched_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(sched_frame, text="주기", font=FONT_SMALL, text_color=TEXT_SECONDARY).grid(row=0, column=0, sticky="w")
        self.freq_var = ctk.StringVar(value=schedule.get("frequency", "weekly"))
        ctk.CTkOptionMenu(
            sched_frame, variable=self.freq_var,
            values=["daily", "weekly", "monthly"],
            fg_color=BG_WHITE, button_color=COBALT,
            text_color=TEXT_PRIMARY, height=34
        ).grid(row=1, column=0, sticky="we", padx=(0, 5), pady=(2, 0))

        ctk.CTkLabel(sched_frame, text="취합 범위 (일)", font=FONT_SMALL, text_color=TEXT_SECONDARY).grid(row=0, column=1, sticky="w")
        self.range_entry = ctk.CTkEntry(sched_frame, height=34)
        self.range_entry.grid(row=1, column=1, sticky="we", padx=(5, 0), pady=(2, 0))
        self.range_entry.insert(0, str(schedule.get("range_days", 7)))

        ctk.CTkFrame(body, fg_color="#E5E7EB", height=1).pack(fill="x", pady=12)

        # ══════════════════════════════
        #  6.5 중복 기사 병합 감도
        # ══════════════════════════════
        ctk.CTkLabel(body, text="🔄 중복 기사 병합 감도", font=FONT_BODY_BOLD, text_color=TEXT_PRIMARY).pack(anchor="w", pady=(0, 3))
        ctk.CTkLabel(body, text="높을수록 더 많은 기사를 '같은 이슈'로 묶습니다\n낮으면 거의 동일한 기사만 병합합니다", font=FONT_CAPTION, text_color=TEXT_SECONDARY).pack(anchor="w", pady=(0, 8))

        dedup = self.settings.get("dedup", {})
        current_level = dedup.get("sensitivity_level", 3)

        # 감도 라벨 프레임
        level_labels_frame = ctk.CTkFrame(body, fg_color="transparent")
        level_labels_frame.pack(fill="x", pady=(0, 2))
        ctk.CTkLabel(level_labels_frame, text="최소", font=FONT_CAPTION, text_color=TEXT_SECONDARY).pack(side="left")
        ctk.CTkLabel(level_labels_frame, text="최대", font=FONT_CAPTION, text_color=TEXT_SECONDARY).pack(side="right")

        # 슬라이더
        self.sensitivity_slider = ctk.CTkSlider(
            body,
            from_=1, to=5,
            number_of_steps=4,
            fg_color="#E5E7EB",
            progress_color=COBALT,
            button_color=COBALT,
            button_hover_color=COBALT_HOVER,
            height=20
        )
        self.sensitivity_slider.set(current_level)
        self.sensitivity_slider.pack(fill="x", pady=(0, 4))

        # 현재 선택 표시 라벨
        level_descriptions = {
            1: "1단계 — 거의 동일한 기사만 병합",
            2: "2단계 — 보수적 병합",
            3: "3단계 — 표준 (권장)",
            4: "4단계 — 적극적 병합",
            5: "5단계 — 같은 주제면 대부분 병합"
        }

        self.sensitivity_label = ctk.CTkLabel(
            body,
            text=level_descriptions.get(current_level, ""),
            font=FONT_SMALL,
            text_color=COBALT
        )
        self.sensitivity_label.pack(anchor="w", pady=(0, 5))

        def on_slider_change(value):
            level = int(round(value))
            self.sensitivity_label.configure(text=level_descriptions.get(level, ""))

        self.sensitivity_slider.configure(command=on_slider_change)

        ctk.CTkFrame(body, fg_color="#E5E7EB", height=1).pack(fill="x", pady=12)

        # ══════════════════════════════
        #  7. 매체 티어
        # ══════════════════════════════
        ctk.CTkLabel(body, text="📡 매체 범위", font=FONT_BODY_BOLD, text_color=TEXT_PRIMARY).pack(anchor="w", pady=(0, 8))

        allowed = media.get("allowed_tiers", [1, 2])
        self.tier_vars = {}
        for t, desc in [(1, "Tier 1 — 주요 레거시 매체"), (2, "Tier 2 — 경제지/전문지"), (3, "Tier 3 — 주요 인터넷 언론")]:
            var = ctk.BooleanVar(value=(t in allowed))
            self.tier_vars[t] = var
            ctk.CTkCheckBox(
                body, text=desc, variable=var,
                font=FONT_SMALL, fg_color=COBALT,
                hover_color=COBALT_HOVER, text_color=TEXT_PRIMARY
            ).pack(anchor="w", pady=2)

        self.tier3_coverage_var = ctk.BooleanVar(value=media.get("include_tier3_coverage", True))
        ctk.CTkCheckBox(
            body, text="Tier 3 매체도 커버리지 건수에 포함",
            variable=self.tier3_coverage_var,
            font=FONT_CAPTION, fg_color=COBALT,
            hover_color=COBALT_HOVER, text_color=TEXT_SECONDARY
        ).pack(anchor="w", pady=(5, 0))

        # ── 하단 버튼 ──
        btn_frame = ctk.CTkFrame(self, fg_color=BG_MAIN)
        btn_frame.pack(fill="x", padx=20, pady=(0, 15))

        ctk.CTkButton(
            btn_frame, text="💾 저장", font=FONT_BODY_BOLD,
            fg_color=COBALT, hover_color=COBALT_HOVER, height=42,
            command=self._save
        ).pack(side="left", expand=True, fill="x", padx=(0, 5))

        ctk.CTkButton(
            btn_frame, text="취소", font=FONT_BODY,
            fg_color="#E5E7EB", hover_color="#D1D5DB",
            text_color=TEXT_SECONDARY, height=42,
            command=self.destroy
        ).pack(side="right", expand=True, fill="x", padx=(5, 0))

    def _save(self):
        # 산업군
        selected_ind = [k for k, v in self.industry_vars.items() if v.get()]
        if not selected_ind:
            self._show_error("산업군을 1개 이상 선택해주세요.")
            return
        if len(selected_ind) > 3:
            self._show_error("산업군은 최대 3개까지 선택 가능합니다.")
            return

        # 제품/브랜드명 (필수)
        products = [k.strip() for k in self.products_entry.get().split(",") if k.strip()]
        if not products:
            self._show_error("제품/브랜드명을 1개 이상 입력해주세요.")
            return

        # 회사명 (필수)
        company = [k.strip() for k in self.company_entry.get().split(",") if k.strip()]
        if not company:
            self._show_error("회사명을 1개 이상 입력해주세요.")
            return
        if len(company) > 2:
            self._show_error("회사명은 최대 2개까지 입력 가능합니다.")
            return

        # 경쟁사 (선택)
        competitors = [k.strip() for k in self.competitors_entry.get().split(",") if k.strip()]

        # 업계 공통 (선택)
        general = [k.strip() for k in self.general_entry.get().split(",") if k.strip()]

        # 스케줄
        try:
            range_days = int(self.range_entry.get())
            if range_days < 1 or range_days > 30:
                raise ValueError
        except ValueError:
            self._show_error("취합 범위는 1~30 사이 숫자를 입력해주세요.")
            return

        # 매체 티어
        allowed_tiers = [t for t, v in self.tier_vars.items() if v.get()]
        if not allowed_tiers:
            self._show_error("매체 티어를 1개 이상 선택해주세요.")
            return

        # 저장
        self.settings["search"] = {
            "industries": selected_ind,
            "keywords": {
                "products": products,
                "company": company,
                "competitors": competitors,
                "industry_general": general
            }
        }
        self.settings["schedule"] = {
            "frequency": self.freq_var.get(),
            "range_days": range_days
        }

        # 중복 병합 감도
        self.settings["dedup"] = {
            "sensitivity_level": int(round(self.sensitivity_slider.get()))
        }
       
        self.settings["media"] = {
            "allowed_tiers": allowed_tiers,
            "include_tier3_coverage": self.tier3_coverage_var.get()
        }

        os.makedirs("config", exist_ok=True)
        with open(os.path.join("config", "settings.yaml"), "w", encoding="utf-8") as f:
            yaml.dump(self.settings, f, allow_unicode=True, default_flow_style=False)

        self.destroy()

    def _show_error(self, msg: str):
        err_window = ctk.CTkToplevel(self)
        err_window.title("⚠️")
        err_window.geometry("350x120")
        err_window.resizable(False, False)
        err_window.transient(self)
        err_window.grab_set()
        ctk.CTkLabel(err_window, text=msg, font=FONT_BODY, text_color=ERROR, wraplength=300).pack(expand=True, padx=20, pady=10)
        ctk.CTkButton(err_window, text="확인", command=err_window.destroy, fg_color=COBALT, height=34).pack(pady=(0, 15))

    def _load_industry_keywords(self) -> dict:
        path = os.path.join("config", "industry_keywords.yaml")
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        return {}
