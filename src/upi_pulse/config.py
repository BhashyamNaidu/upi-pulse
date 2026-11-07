"""Central configuration: where the lake lives and which environment we run in.

Everything that differs between a laptop run and a cloud run is resolved here, from
environment variables, so the rest of the code never hard-codes a path.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

LAYERS: tuple[str, ...] = ("landing", "bronze", "silver", "gold")


@dataclass(frozen=True)
class Settings:
    """Runtime settings for one pipeline run.

    Attributes:
        env: ``"local"`` or ``"cloud"``.
        lake_root: Root URI of the lake. A local path (``./data/lake``) or an
            ``abfss://`` URI when running against Azure ADLS Gen2.
    """

    env: str
    lake_root: str

    def layer_path(self, layer: str) -> str:
        """Return the URI of one lake layer (``landing``/``bronze``/``silver``/``gold``).

        Raises:
            ValueError: If ``layer`` is not one of the known layers.
        """
        if layer not in LAYERS:
            raise ValueError(f"Unknown lake layer {layer!r}; expected one of {LAYERS}")
        return f"{self.lake_root.rstrip('/')}/{layer}"


def load_settings(environ: dict[str, str] | None = None) -> Settings:
    """Build :class:`Settings` from environment variables.

    Args:
        environ: Mapping to read from. Defaults to ``os.environ`` (injectable for tests).

    Returns:
        Settings with ``UPI_PULSE_ENV`` (default ``local``) and ``UPI_PULSE_LAKE_ROOT``
        (default ``<project>/data/lake``).
    """
    env_vars = os.environ if environ is None else environ
    env = env_vars.get("UPI_PULSE_ENV", "local")
    if env not in {"local", "cloud"}:
        raise ValueError(f"UPI_PULSE_ENV must be 'local' or 'cloud', got {env!r}")
    default_root = (PROJECT_ROOT / "data" / "lake").as_posix()
    lake_root = env_vars.get("UPI_PULSE_LAKE_ROOT", default_root)
    return Settings(env=env, lake_root=lake_root)
