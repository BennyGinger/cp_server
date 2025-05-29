# Usage:
# # from cp_server.docker_manager import ComposeManager
# # with ComposeManager():
# #     # Your code here
from pathlib import Path

from cp_server.docker_manager import ComposeManager

ROOT = Path(__file__).parent.parent.resolve()

__all__ = ["ComposeManager",]
