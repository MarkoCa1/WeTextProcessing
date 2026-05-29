# Copyright (c) 2022 Zhendong Peng (pzd17@tsinghua.org.cn)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""ISO 日期 sentinel 预处理。

将「2026-04-25」这类四位年-两位月-两位日替换为私有 sentinel token `___DATE_20260425___`，
让 Date 规则能最高优先级匹配，避免被 math/cardinal/fraction 抢走「-」和数字。
"""

from __future__ import annotations

import re

# 匹配 yyyy-mm-dd（支持 2026-04-25 或 2026/04/25 或 2026.04.25）
_ISO_DATE = re.compile(
    r"(?<![0-9A-Za-z])([12]\d{3})[-/.](0[1-9]|1[0-2])[-/.](0[1-9]|[12]\d|3[01])(?![0-9A-Za-z])"
)


def insert_date_sentinels(text: str) -> str:
    """将 ISO 日期替换为 sentinel token。
    例如：2026-04-25 → ___DATE_20260425___
    """
    if not text:
        return text

    def repl(m: re.Match) -> str:
        y, mth, d = m.group(1), m.group(2), m.group(3)
        return f"___DATE_{y}{mth}{d}___"

    return _ISO_DATE.sub(repl, text)
