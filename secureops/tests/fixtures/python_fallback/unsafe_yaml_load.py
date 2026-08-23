"""Fallback fixture for reviewed-template remediation when AI is unavailable."""

import yaml


def load_user_supplied_config(raw_yaml: str):
    return yaml.load(raw_yaml, Loader=yaml.Loader)
