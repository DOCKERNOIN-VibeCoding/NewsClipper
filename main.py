"""NewsClipper 진입점"""

"""NewsClipper 진입점"""

import os
import logging
from datetime import datetime
import customtkinter as ctk
from ui.main_window import MainWindow


def setup_logging():
    """디버깅을 위한 로그 파일 설정.
    logs/ 폴더에 날짜별 로그 파일 생성."""
    os.makedirs("logs", exist_ok=True)
    log_path = os.path.join(
        "logs",
        f"newsclipper_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    )

    # 루트 로거 설정 — DEBUG 레벨까지 모두 캡처
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
        handlers=[
            logging.FileHandler(log_path, encoding="utf-8"),
            logging.StreamHandler(),  # 콘솔에도 출력
        ],
    )

    # 외부 라이브러리의 너무 시끄러운 로그는 WARNING 이상만
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("PIL").setLevel(logging.WARNING)
    logging.getLogger("google").setLevel(logging.INFO)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)

    logging.info(f"=== NewsClipper 시작 (로그: {log_path}) ===")
    return log_path


def main():
    log_path = setup_logging()

    ctk.set_appearance_mode("light")

    app = MainWindow()

    # ── 메인 윈도우 숨기고 스플래시 먼저 표시 ──
    app.withdraw()

    from ui.splash import SplashScreen
    splash_duration = 2500

    splash = SplashScreen(app, duration=splash_duration)

    def show_main():
        app.deiconify()
        app.lift()
        app.focus_force()

    app.after(splash_duration + 200, show_main)
    app.mainloop()


if __name__ == "__main__":
    main()


import customtkinter as ctk
from ui.main_window import MainWindow


def main():
    ctk.set_appearance_mode("light")

    app = MainWindow()

    # ── 메인 윈도우 숨기고 스플래시 먼저 표시 ──
    app.withdraw()

    from ui.splash import SplashScreen
    splash_duration = 2500  # 2.5초

    splash = SplashScreen(app, duration=splash_duration)

    # 스플래시 종료 후 메인 윈도우 표시
    def show_main():
        app.deiconify()       # 메인 윈도우 표시
        app.lift()            # 앞으로 가져오기
        app.focus_force()     # 포커스

    app.after(splash_duration + 200, show_main)
    app.mainloop()


if __name__ == "__main__":
    main()
