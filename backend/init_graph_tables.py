#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
初始化知识图谱相关的数据库表
"""

from database import init_db

if __name__ == "__main__":
    print("开始初始化知识图谱数据库表...")
    init_db()
    print("数据库表初始化完成！")
