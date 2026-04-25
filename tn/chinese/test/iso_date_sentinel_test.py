# Copyright (c) 2022 Zhendong Peng (pzd17@tsinghua.org.cn)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.

from tn.chinese.iso_date_sentinel import insert_date_sentinels


def test_iso_date_to_sentinel():
    """测试预处理将 ISO 日期转为 sentinel token"""
    assert insert_date_sentinels("日期：2026-04-25 时间：10:30") == "日期：___DATE_20260425___ 时间：10:30"
    assert insert_date_sentinels("2026/04/25") == "___DATE_20260425___"
    assert insert_date_sentinels("2026.04.25") == "___DATE_20260425___"
    assert insert_date_sentinels("2024-01-01-2024-01-05") == "___DATE_20240101___-___DATE_20240105___"


def test_non_iso_unchanged():
    assert insert_date_sentinels("截至2008-08") == "截至2008-08"
    assert insert_date_sentinels("版本 1.2.3") == "版本 1.2.3"


def test_empty():
    assert insert_date_sentinels("") == ""
