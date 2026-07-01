from __future__ import annotations

from pathlib import Path

from parser.config import find_project_root

ENV_KEYS = {
    "VK_ACCESS_TOKEN": "vk_access_token",
    "YANDEX_SEARCH_API_KEY": "yandex_search_api_key",
    "YANDEX_FOLDER_ID": "yandex_folder_id",
}

REVERSE_KEYS = {v: k for k, v in ENV_KEYS.items()}


def env_file_path() -> Path:
    return find_project_root() / "env.txt"


def read_env_file() -> dict[str, str]:
    path = env_file_path()
    values = {field: "" for field in ENV_KEYS.values()}
    if not path.exists():
        return values

    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        env_field = ENV_KEYS.get(key)
        if env_field:
            values[env_field] = value.strip()
    return values


def write_env_file(values: dict[str, str]) -> None:
    path = env_file_path()
    lines = [
        "# Токены и API-ключи для парсера ИЦАЭ",
        "# Формат: KEY=значение",
        "",
    ]
    for file_key, field in ENV_KEYS.items():
        lines.append(f"{file_key}={values.get(field, '')}")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def env_file_exists() -> bool:
    return env_file_path().exists()
