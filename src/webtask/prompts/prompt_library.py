"""Centralized prompt management system."""

from pathlib import Path
from typing import Dict, Optional
import yaml


class PromptLibrary:
    """
    Manages prompts loaded from YAML files.

    Provides simple key-based access: PromptLibrary.get("key")
    """

    _instance: Optional["PromptLibrary"] = None
    _prompts: Dict[str, str] = {}
    _loaded: bool = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def get(cls, key: str) -> str:
        """Get prompt by key."""
        instance = cls()
        if not instance._loaded:
            instance._load_prompts()

        if key not in instance._prompts:
            raise KeyError(
                f"Prompt '{key}' not found. Available prompts: {list(instance._prompts.keys())}"
            )

        return instance._prompts[key]

    @classmethod
    def reload(cls) -> None:
        """Force reload all prompts from disk."""
        instance = cls()
        instance._loaded = False
        instance._prompts.clear()
        instance._load_prompts()

    @classmethod
    def list_keys(cls) -> list[str]:
        """List all available prompt keys."""
        instance = cls()
        if not instance._loaded:
            instance._load_prompts()
        return list(instance._prompts.keys())

    def _load_prompts(self) -> None:
        current_file = Path(__file__)
        prompts_dir = current_file.parent.parent / "prompts_data"

        if not prompts_dir.exists():
            raise RuntimeError(
                f"Prompts directory not found at {prompts_dir}. "
                "Please ensure the prompts_data/ directory exists in the webtask package."
            )

        # Recursively load all .yaml and .yml files
        for yaml_file in prompts_dir.rglob("*.yaml"):
            self._load_yaml_file(yaml_file)
        for yml_file in prompts_dir.rglob("*.yml"):
            self._load_yaml_file(yml_file)

        self._loaded = True

    def _load_yaml_file(self, file_path: Path) -> None:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)

            if not isinstance(data, dict):
                print(f"Warning: {file_path} does not contain a dictionary, skipping")
                return

            # Extract prompts from YAML structure
            for key, value in data.items():
                if isinstance(value, dict) and "content" in value:
                    # Store the content string
                    self._prompts[key] = value["content"].strip()
                elif isinstance(value, str):
                    # Direct string value
                    self._prompts[key] = value.strip()

        except Exception as e:
            print(f"Warning: Failed to load {file_path}: {e}")


def get_prompt(key: str) -> str:
    """Get prompt by key."""
    return PromptLibrary.get(key)
