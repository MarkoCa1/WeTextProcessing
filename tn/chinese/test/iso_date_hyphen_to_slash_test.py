# Copyright (c) 2022 Zhendong Peng (pzd17@tsinghua.org.cn)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.

from tn.chinese.iso_date_hyphen_to_slash import rewrite_iso_calendar_hyphen_dates_to_slashes


def test_iso_yyyymmdd_becomes_hyphen_dot():
    assert rewrite_iso_calendar_hyphen_dates_to_slashes("日期：2026-04-25 时间：10:30") == "日期：2026-04.25 时间：10:30"


def test_yyyy_mm_unchanged():
    assert rewrite_iso_calendar_hyphen_dates_to_slashes("截至2008-08") == "截至2008-08"


def test_empty():
    assert rewrite_iso_calendar_hyphen_dates_to_slashes("") == ""
