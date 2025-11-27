"""Módulo de configurações do projeto."""

from .settings import *
from .secrets_manager import SecretsManager

__all__ = ['SecretsManager', 'Settings']
