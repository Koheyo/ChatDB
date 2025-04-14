"""
ChatDB - A Natural Language Interface for SQL/NoSQL Databases
"""

import os
import sys

# 确保 src 目录及其子模块可以被正确导入
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

# 让 src 作为 Python 包
__all__ = ["config", "ui", "llm", "db"]