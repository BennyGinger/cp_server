# Usage:
# # from cp_server.docker_manager import ComposeManager
# # with ComposeManager():
# #     # Your code here
from pathlib import Path

ROOT = Path(__file__).parent.parent.resolve()

from cp_server.docker_manager import ComposeManager

__all__ = ["ComposeManager",]
