"""
PyInstaller 빌드 환경과 개발 환경 모두에서 동작하는 경로 헬퍼.

사용 구분:
  - resource_path():  앱과 함께 배포되는 읽기 전용 리소스 (yaml, ico, png 등)
  - user_data_path(): 사용자가 수정/저장하는 파일 (settings.yaml, reports 등)
"""

import sys
import os


def resource_path(relative_path: str) -> str:
    """
    읽기 전용 리소스의 절대 경로를 반환.
    
    - 개발 환경(.py): 프로젝트 루트 기준
    - PyInstaller exe (--onefile): sys._MEIPASS (임시 폴더)
    - PyInstaller exe (--onedir): exe 옆의 _internal 폴더
    
    예: resource_path("config/industry_keywords.yaml")
    """
    if getattr(sys, 'frozen', False):
        # PyInstaller로 빌드된 환경
        if hasattr(sys, '_MEIPASS'):
            # --onefile 모드 (임시 폴더에 풀림)
            base_path = sys._MEIPASS
        else:
            # --onedir 모드 (exe 옆의 _internal 폴더)
            exe_dir = os.path.dirname(sys.executable)
            internal_dir = os.path.join(exe_dir, '_internal')
            base_path = internal_dir if os.path.exists(internal_dir) else exe_dir
    else:
        # 개발 환경: 프로젝트 루트
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path)


def user_data_path(relative_path: str) -> str:
    """
    사용자 데이터 파일의 절대 경로를 반환.
    
    - 개발 환경: 프로젝트 루트 (현재 동작과 동일)
    - exe 환경:  exe가 있는 폴더 (사용자가 직접 접근 가능한 위치)
    
    예: user_data_path("config/settings.yaml")
        user_data_path("reports/news_clip.html")
    """
    if getattr(sys, 'frozen', False):
        # exe 옆 폴더 (사용자가 보고 수정할 수 있는 위치)
        base_path = os.path.dirname(sys.executable)
    else:
        # 개발 환경: 프로젝트 루트
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path)
