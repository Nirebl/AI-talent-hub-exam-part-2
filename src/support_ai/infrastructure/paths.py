from __future__ import annotations

import os
from pathlib import Path


def resolve_knowledge_base_path(
    explicit_path: str | Path | None = None,
) -> Path:
    if explicit_path is not None:
        return Path(explicit_path)

    configured = os.getenv("KNOWLEDGE_BASE_PATH")
    if configured:
        return Path(configured)

    return Path.cwd() / "data" / "knowledge_base.json"
