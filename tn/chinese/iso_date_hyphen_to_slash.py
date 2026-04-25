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

"""ISO 日历「四位年-两位月-两位日」在 TN 前的规范化。

改写为「年-月.日」：`2026-04.25`

- 年-月仍为半角「-」，与 `year + rmsign_month_day + mm_month_day` 等一致。
- 月-日改为「.」：`date.rmsign` 已含 `delete(".")`，整块仍走 `date_yyyy_mm_dd`。
- 不用「/」：避免 fraction 抢「04/25」；不用全角「－」：避免与 FST 优化后 flex 里 `d|dd` 仍抢「25」首位。

`rewrite_iso_calendar_hyphen_dates_to_slashes` 为历史函数名，语义为上述 ISO 规范化（非斜杠）。
"""

from __future__ import annotations

import re

# 月日取常见日历范围；两侧不得紧贴字母数字，避免误伤版本号等
_ISO_CAL_YMD = re.compile(
    r"(?<![0-9A-Za-z])([12]\d{3})-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])(?![0-9A-Za-z])"
)


def rewrite_iso_calendar_hyphen_dates_to_slashes(text: str) -> str:
    if not text:
        return text
    return _ISO_CAL_YMD.sub(lambda m: f"{m.group(1)}-{m.group(2)}.{m.group(3)}", text)
