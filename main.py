"""NewsClipper 진입점"""

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
