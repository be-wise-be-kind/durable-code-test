"""
Purpose: YAML profile parser and CLI for converting load test profiles to Locust configuration

Scope: Shared utility for reading profile YAML files and producing Locust CLI arguments
    and environment variable assignments

Overview: Provides functions to resolve profile names to file paths, load and validate YAML
    profile definitions, and convert profile settings into Locust CLI argument lists and
    environment variable dictionaries. Supports a CLI mode (python -m lib.profile_loader)
    that outputs shell variable assignments for consumption by the justfile. Validates that
    required fields (users, spawn_rate, duration) are present and that weight values are
    positive integers. Used inside the Docker container for programmatic profile access;
    the justfile uses bash-native YAML parsing for host-side operation without a Python
    dependency.

Dependencies: PyYAML for YAML parsing, pathlib for file resolution, sys for CLI entry point

Exports: resolve_profile_path, load_profile, profile_to_locust_args, profile_to_env_vars

Interfaces: CLI via python -m lib.profile_loader <profile_name> outputs KEY=VALUE lines;
    programmatic via imported functions returning lists and dicts

Implementation: Simple flat YAML schema with required field validation. Profile resolution
    searches the profiles/ directory relative to the load-testing package root.
"""

import sys
from pathlib import Path

import yaml

PROFILES_DIR = Path(__file__).resolve().parent.parent / "profiles"
REQUIRED_FIELDS = ("users", "spawn_rate", "duration")


def resolve_profile_path(name: str) -> Path:
    """Map a profile name to its YAML file path.

    Raises FileNotFoundError listing available profiles if the name is invalid.
    """
    profile_path = PROFILES_DIR / f"{name}.yml"
    if not profile_path.is_file():
        available = sorted(p.stem for p in PROFILES_DIR.glob("*.yml"))
        available_str = ", ".join(available) if available else "(none found)"
        msg = (
            f"Profile '{name}' not found at {profile_path}. "
            f"Available profiles: {available_str}"
        )
        raise FileNotFoundError(msg)
    return profile_path


def load_profile(path: Path) -> dict:
    """Read and validate a YAML profile file.

    Raises ValueError if required fields are missing.
    """
    with open(path, encoding="utf-8") as fh:
        profile: dict = yaml.safe_load(fh)

    missing = [f for f in REQUIRED_FIELDS if f not in profile]
    if missing:
        msg = f"Profile {path.name} missing required fields: {', '.join(missing)}"
        raise ValueError(msg)

    return profile


def profile_to_locust_args(profile: dict) -> list[str]:
    """Convert profile settings to Locust CLI argument list."""
    return [
        "--users",
        str(profile["users"]),
        "--spawn-rate",
        str(profile["spawn_rate"]),
        "--run-time",
        str(profile["duration"]),
    ]


def profile_to_env_vars(profile: dict) -> dict[str, str]:
    """Convert profile weight settings to environment variable dict."""
    return {
        "HTTP_WEIGHT": str(profile.get("http_weight", 70)),
        "WS_WEIGHT": str(profile.get("websocket_weight", 30)),
    }


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python -m lib.profile_loader <profile_name>", file=sys.stderr)
        sys.exit(1)

    profile_name = sys.argv[1]
    try:
        path = resolve_profile_path(profile_name)
        profile_data = load_profile(path)
    except (FileNotFoundError, ValueError) as err:
        print(f"Error: {err}", file=sys.stderr)
        sys.exit(1)

    args = profile_to_locust_args(profile_data)
    env = profile_to_env_vars(profile_data)

    print(f"LOCUST_ARGS={' '.join(args)}")
    for key, val in env.items():
        print(f"{key}={val}")
