"""API 설정 다이얼로그 (Naver + Gemini)"""

import customtkinter as ctk
import requests
import yaml
import os
import threading
from ui.theme import *

class SettingsApiDialog(ctk.CTkToplevel):
    def __init__(self, parent, settings: dict):
        super().__init__(parent)

        self.settings = settings.copy()
        self.title("🔑 API 설정")
        self.geometry("500x620")
        self.resizable(False, False)
        self.configure(fg_color=BG_MAIN)
        self.transient(parent)
        self.grab_set()

        self._build_ui()

    def _build_ui(self):
        api = self.settings.get("api", {})
        naver = api.get("naver", {})
        gemini = api.get("gemini", {})

        # ── 헤더 ──
        header = ctk.CTkFrame(self, fg_color=NAVY, height=60, corner_radius=0)
        header.pack(fill="x")
        header.pack_propagate(False)
        ctk.CTkLabel(
            header, text="🔑 API 설정",
            font=FONT_SUBTITLE, text_color=TEXT_ON_NAVY
        ).pack(side="left", padx=20, pady=15)

        # ── 본문 스크롤 ──
        body = ctk.CTkScrollableFrame(self, fg_color=BG_MAIN)
        body.pack(fill="both", expand=True, padx=20, pady=15)

        # ══ Naver API ══
        ctk.CTkLabel(body, text="📗 Naver News Search API", font=FONT_BODY_BOLD, text_color=TEXT_PRIMARY).pack(anchor="w", pady=(0, 5))
        ctk.CTkLabel(body, text="https://developers.naver.com 에서 발급", font=FONT_CAPTION, text_color=TEXT_SECONDARY).pack(anchor="w", pady=(0, 8))

        ctk.CTkLabel(body, text="Client ID", font=FONT_SMALL, text_color=TEXT_SECONDARY).pack(anchor="w")
        self.naver_id_entry = ctk.CTkEntry(body, placeholder_text="예: A1b2C3d4E5f6G7h8", height=36)
        self.naver_id_entry.pack(fill="x", pady=(2, 8))
        if naver.get("client_id"):
            self.naver_id_entry.insert(0, naver["client_id"])

        ctk.CTkLabel(body, text="Client Secret", font=FONT_SMALL, text_color=TEXT_SECONDARY).pack(anchor="w")
        self.naver_secret_entry = ctk.CTkEntry(body, placeholder_text="예: x1Y2z3W4", show="●", height=36)
        self.naver_secret_entry.pack(fill="x", pady=(2, 8))
        if naver.get("client_secret"):
            self.naver_secret_entry.insert(0, naver["client_secret"])

        # Naver 테스트 버튼 + 결과
        naver_test_frame = ctk.CTkFrame(body, fg_color="transparent")
        naver_test_frame.pack(fill="x", pady=(0, 5))
        ctk.CTkButton(
            naver_test_frame, text="🔗 연결 테스트", font=FONT_SMALL,
            fg_color=COBALT, hover_color=COBALT_HOVER, height=32, width=120,
            command=self._test_naver
        ).pack(side="left")
        self.naver_status = ctk.CTkLabel(naver_test_frame, text="", font=FONT_SMALL)
        self.naver_status.pack(side="left", padx=10)

        # ── 구분선 ──
        ctk.CTkFrame(body, fg_color="#E5E7EB", height=1).pack(fill="x", pady=15)

        # ══ Gemini API ══
        ctk.CTkLabel(body, text="🤖 Gemini API", font=FONT_BODY_BOLD, text_color=TEXT_PRIMARY).pack(anchor="w", pady=(0, 5))
        ctk.CTkLabel(body, text="https://aistudio.google.com 에서 발급", font=FONT_CAPTION, text_color=TEXT_SECONDARY).pack(anchor="w", pady=(0, 8))

        ctk.CTkLabel(body, text="API Key", font=FONT_SMALL, text_color=TEXT_SECONDARY).pack(anchor="w")
        self.gemini_key_entry = ctk.CTkEntry(body, placeholder_text="예: AIzaSy...", show="●", height=36)
        self.gemini_key_entry.pack(fill="x", pady=(2, 8))
        if gemini.get("api_key"):
            self.gemini_key_entry.insert(0, gemini["api_key"])

        ctk.CTkLabel(body, text="모델 선택", font=FONT_SMALL, text_color=TEXT_SECONDARY).pack(anchor="w")
        self.gemini_model_var = ctk.StringVar(value=gemini.get("model", "gemini-2.5-flash-lite"))
        self.gemini_model_menu = ctk.CTkOptionMenu(
            body,
            variable=self.gemini_model_var,
            values=["gemini-2.5-flash-lite", "gemini-2.5-flash", "gemini-2.0-flash"],
            fg_color=BG_WHITE, button_color=COBALT,
            button_hover_color=COBALT_HOVER,
            text_color=TEXT_PRIMARY, height=36
        )
        self.gemini_model_menu.pack(fill="x", pady=(2, 8))

        # Gemini 테스트 버튼 + 결과
        gemini_test_frame = ctk.CTkFrame(body, fg_color="transparent")
        gemini_test_frame.pack(fill="x", pady=(0, 5))
        ctk.CTkButton(
            gemini_test_frame, text="🔗 연결 테스트", font=FONT_SMALL,
            fg_color=COBALT, hover_color=COBALT_HOVER, height=32, width=120,
            command=self._test_gemini
        ).pack(side="left")
        self.gemini_status = ctk.CTkLabel(gemini_test_frame, text="", font=FONT_SMALL)
        self.gemini_status.pack(side="left", padx=10)

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

    # ── 테스트 함수 ──
    def _test_naver(self):
        self.naver_status.configure(text="테스트 중...", text_color=TEXT_SECONDARY)
        cid = self.naver_id_entry.get().strip()
        secret = self.naver_secret_entry.get().strip()
        if not cid or not secret:
            self.naver_status.configure(text="❌ ID와 Secret을 모두 입력하세요", text_color=ERROR)
            return

        def _do_test():
            try:
                resp = requests.get(
                    "https://openapi.naver.com/v1/search/news.json",
                    headers={"X-Naver-Client-Id": cid, "X-Naver-Client-Secret": secret},
                    params={"query": "테스트", "display": 1},
                    timeout=10
                )
                if resp.status_code == 200:
                    count = resp.json().get("total", 0)
                    self.naver_status.configure(text=f"✅ 성공 ({count}건)", text_color=SUCCESS)
                else:
                    self.naver_status.configure(text=f"❌ HTTP {resp.status_code}", text_color=ERROR)
            except Exception as e:
                self.naver_status.configure(text=f"❌ {str(e)[:30]}", text_color=ERROR)

        threading.Thread(target=_do_test, daemon=True).start()

    def _test_gemini(self):
        self.gemini_status.configure(text="테스트 중...", text_color=TEXT_SECONDARY)
        key = self.gemini_key_entry.get().strip()
        model = self.gemini_model_var.get()
        if not key:
            self.gemini_status.configure(text="❌ API Key를 입력하세요", text_color=ERROR)
            return

        def _do_test():
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
                resp = requests.post(
                    url,
                    headers={"Content-Type": "application/json", "x-goog-api-key": key},
                    json={"contents": [{"parts": [{"text": "Reply OK"}]}]},
                    timeout=15
                )
                if resp.status_code == 200:
                    self.gemini_status.configure(text=f"✅ 성공 ({model})", text_color=SUCCESS)
                else:
                    self.gemini_status.configure(text=f"❌ HTTP {resp.status_code}", text_color=ERROR)
            except Exception as e:
                self.gemini_status.configure(text=f"❌ {str(e)[:30]}", text_color=ERROR)

        threading.Thread(target=_do_test, daemon=True).start()

    def _save(self):
        self.settings.setdefault("api", {})
        self.settings["api"]["naver"] = {
            "client_id": self.naver_id_entry.get().strip(),
            "client_secret": self.naver_secret_entry.get().strip()
        }
        self.settings["api"]["gemini"] = {
            "api_key": self.gemini_key_entry.get().strip(),
            "model": self.gemini_model_var.get()
        }

        os.makedirs("config", exist_ok=True)
        with open(os.path.join("config", "settings.yaml"), "w", encoding="utf-8") as f:
            yaml.dump(self.settings, f, allow_unicode=True, default_flow_style=False)

        self.destroy()
