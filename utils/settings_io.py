"""
settings.yaml 로드/저장 공용 헬퍼.

- 기존 설정 파일이 없으면 settings_template.yaml을 복사
- 저장 시 기존 파일의 다른 섹션을 보존 (deep merge)
"""
from __future__ import annotations

import os
import shutil
import yaml
from typing import Dict, Any

from utils.paths import resource_path, user_data_path


SETTINGS_FILENAME = "settings.yaml"
TEMPLATE_FILENAME = "settings_template.yaml"


def _settings_path() -> str:
    """사용자 settings.yaml 경로 (exe와 같은 위치 또는 dev에서는 config/)."""
    return user_data_path(os.path.join("config", SETTINGS_FILENAME))


def _template_path() -> str:
    """읽기전용 템플릿 경로 (_internal/config/ 또는 dev의 config/)."""
    return resource_path(os.path.join("config", TEMPLATE_FILENAME))


def ensure_settings_file() -> str:
    """settings.yaml이 없으면 템플릿을 복사해 생성. 경로 반환."""
    target = _settings_path()
    if os.path.exists(target):
        return target

    os.makedirs(os.path.dirname(target), exist_ok=True)
    template = _template_path()
    if os.path.exists(template):
        shutil.copyfile(template, target)
    else:
        # 템플릿도 없으면 빈 파일이라도 생성
        with open(target, "w", encoding="utf-8") as f:
            f.write("")
    return target


def load_settings() -> Dict[str, Any]:
    """settings.yaml 로드. 없으면 템플릿 복사 후 로드."""
    path = ensure_settings_file()
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """base 위에 override를 재귀적으로 덮어쓴 새 dict 반환.
    같은 키가 둘 다 dict이면 재귀 병합, 아니면 override가 이김.
    """
    result = dict(base)
    for k, v in override.items():
        if (
            k in result
            and isinstance(result[k], dict)
            and isinstance(v, dict)
        ):
            result[k] = deep_merge(result[k], v)
        else:
            result[k] = v
    return result


def save_settings(partial: Dict[str, Any]) -> str:
    """기존 settings.yaml에 partial을 deep-merge 해서 저장. 경로 반환."""
    path = ensure_settings_file()
    existing = load_settings()
    merged = deep_merge(existing, partial)
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(merged, f, allow_unicode=True, sort_keys=False)
    return path
