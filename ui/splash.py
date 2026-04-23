"""스플래시 스크린 — 프로그램 시작 시 로고 이미지 표시"""

import customtkinter as ctk
import os
import sys
from PIL import Image
from ui.theme import *


def resource_path(relative_path):
    """PyInstaller exe에서도 리소스 경로를 찾을 수 있도록"""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)


class SplashScreen(ctk.CTkToplevel):
    def __init__(self, parent, duration=2500):
        super().__init__(parent)

        # ── 창 설정 ──
        self.overrideredirect(True)
        self.configure(fg_color=NAVY)

        width, height = 500, 400
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        x = (screen_w - width) // 2
        y = (screen_h - height) // 2
        self.geometry(f"{width}x{height}+{x}+{y}")

        self.attributes("-topmost", True)
        self.lift()

        # ── 컨텐츠 ──
        container = ctk.CTkFrame(self, fg_color=NAVY, corner_radius=0)
        container.pack(fill="both", expand=True)

        # ── 로고 이미지 ──
        logo_path = resource_path(os.path.join("config", "splash_logo.png"))
        try:
            logo_image = Image.open(logo_path)
            self.logo = ctk.CTkImage(
                light_image=logo_image,
                dark_image=logo_image,
                size=(180, 180)
            )
            ctk.CTkLabel(
                container, image=self.logo, text=""
            ).pack(pady=(40, 15))
        except Exception:
            # 이미지 로드 실패 시 이모지 대체
            ctk.CTkLabel(
                container, text="📰",
                font=(FONT_FAMILY, 56),
                text_color=TEXT_ON_NAVY
            ).pack(pady=(50, 10))

        # 타이틀
        ctk.CTkLabel(
            container, text="News Clipper",
            font=(FONT_FAMILY, 28, "bold"),
            text_color=TEXT_ON_NAVY
        ).pack()

        # 부제
        ctk.CTkLabel(
            container, text="AI 기반 뉴스 클리핑 & 미디어 모니터링",
            font=FONT_BODY,
            text_color=TEXT_ON_NAVY_DIM
        ).pack(pady=(6, 0))

        # 로딩 바
        progress = ctk.CTkProgressBar(
            container, width=220, height=4,
            corner_radius=2,
            fg_color=NAVY_LIGHT,
            progress_color=SKY_BLUE
        )
        progress.pack(pady=(25, 0))
        progress.set(0)
        self._animate_progress(progress, 0, duration)

        # 크래딧
        ctk.CTkLabel(
            container,
            text="Developed by DOCKERNOIN with Claude AI",
            font=FONT_CAPTION,
            text_color=TEXT_ON_NAVY_DIM
        ).pack(side="bottom", pady=(0, 15))

        self.after(duration, self._close_splash)

    def _animate_progress(self, bar, current, total, step=50):
        if current <= total:
            bar.set(current / total)
            self.after(step, self._animate_progress, bar, current + step, total, step)

    def _close_splash(self):
        self.destroy()
"""스플래시 스크린 — 프로그램 시작 시 로고 이미지 표시"""

import customtkinter as ctk
import os
import sys
from PIL import Image
from ui.theme import *


def resource_path(relative_path):
    """PyInstaller exe에서도 리소스 경로를 찾을 수 있도록"""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)


class SplashScreen(ctk.CTkToplevel):
    def __init__(self, parent, duration=2500):
        super().__init__(parent)

        # ── 창 설정 ──
        self.overrideredirect(True)
        self.configure(fg_color=NAVY)

        width, height = 500, 400
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        x = (screen_w - width) // 2
        y = (screen_h - height) // 2
        self.geometry(f"{width}x{height}+{x}+{y}")

        self.attributes("-topmost", True)
        self.lift()

        # ── 컨텐츠 ──
        container = ctk.CTkFrame(self, fg_color=NAVY, corner_radius=0)
        container.pack(fill="both", expand=True)

        # ── 로고 이미지 ──
        logo_path = resource_path(os.path.join("config", "splash_logo.png"))
        try:
            logo_image = Image.open(logo_path)
            self.logo = ctk.CTkImage(
                light_image=logo_image,
                dark_image=logo_image,
                size=(180, 180)
            )
            ctk.CTkLabel(
                container, image=self.logo, text=""
            ).pack(pady=(40, 15))
        except Exception:
            # 이미지 로드 실패 시 이모지 대체
            ctk.CTkLabel(
                container, text="📰",
                font=(FONT_FAMILY, 56),
                text_color=TEXT_ON_NAVY
            ).pack(pady=(50, 10))

        # 타이틀
        ctk.CTkLabel(
            container, text="News Clipper",
            font=(FONT_FAMILY, 28, "bold"),
            text_color=TEXT_ON_NAVY
        ).pack()

        # 부제
        ctk.CTkLabel(
            container, text="AI 기반 뉴스 클리핑 & 미디어 모니터링",
            font=FONT_BODY,
            text_color=TEXT_ON_NAVY_DIM
        ).pack(pady=(6, 0))

        # 로딩 바
        progress = ctk.CTkProgressBar(
            container, width=220, height=4,
            corner_radius=2,
            fg_color=NAVY_LIGHT,
            progress_color=SKY_BLUE
        )
        progress.pack(pady=(25, 0))
        progress.set(0)
        self._animate_progress(progress, 0, duration)

        # 크래딧
        ctk.CTkLabel(
            container,
            text="Developed by DOCKERNOIN with Claude AI",
            font=FONT_CAPTION,
            text_color=TEXT_ON_NAVY_DIM
        ).pack(side="bottom", pady=(0, 15))

        self.after(duration, self._close_splash)

    def _animate_progress(self, bar, current, total, step=50):
        if current <= total:
            bar.set(current / total)
            self.after(step, self._animate_progress, bar, current + step, total, step)

    def _close_splash(self):
        self.destroy()
