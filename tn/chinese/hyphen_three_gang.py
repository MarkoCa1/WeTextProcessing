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

"""恰好三段「字母或数字」由两个半角连字符连接时，连字符读「杠」。

- 句中无等式标记（=、等于、结果）时整句替换；
- 有句中等式但句中含门牌、编号、地址等语境词时仍替换（与 designation_hyphen、等式内 / 等分工互补）。
"""

import re

from tn.chinese.context_keywords import SERIAL_CONTEXT_KEYWORDS

_EQ_KEYS = ("=", "等于", "结果")

# 两段连字符、三段；后接「-」也允许匹配（如 yyyy-mm-dd-yyyy 区间），由 repl 内 ISO/区间规则决定是否替换
_TRIPLE_HYPHEN = re.compile(
    r"(?<![A-Za-z0-9-])"
    r"([A-Za-z0-9]+)-([A-Za-z0-9]+)-([A-Za-z0-9]+)"
)


def _looks_like_iso_date(a: str, b: str, c: str) -> bool:
    if not (a.isdigit() and b.isdigit() and c.isdigit()):
        return False
    if len(a) == 4 and len(b) == 2 and len(c) == 2:
        return True
    if len(a) == 2 and len(b) == 2 and len(c) == 4:
        return True
    return False


def _looks_like_mobile_hyphenated(a: str, b: str, c: str) -> bool:
    """大陆常见 3-4-4 分段手机号，保持整号读音，不插「杠」。"""
    if a.isdigit() and b.isdigit() and c.isdigit():
        return len(a) == 3 and len(b) == 4 and len(c) == 4
    return False


def _looks_like_date_range_digit_triple(a: str, b: str, c: str) -> bool:
    """yyyy-mm-dd-yyyy-mm-dd 中间的「01-2024-01」等，勿插杠。"""
    if not (a.isdigit() and b.isdigit() and c.isdigit()):
        return False
    if len(b) == 4 and len(a) <= 2 and len(c) <= 2:
        return True
    if len(c) == 4 and len(a) <= 2 and len(b) <= 2:
        return True
    return False


def _looks_like_calendar_digit_triple(a: str, b: str, c: str) -> bool:
    """仅当首段不能作「月」（>12）且后两段像月/日时，视为日-月-年连减（如 26-4-25），不插「杠」。

    首段 ≤12 时（如 4-7-1）保留给编号「杠」，勿与日历混淆。
    """
    if not (a.isdigit() and b.isdigit() and c.isdigit()):
        return False
    try:
        ai, bi, ci = int(a), int(b), int(c)
    except ValueError:
        return False
    if not (1 <= bi <= 12 and 1 <= ci <= 31):
        return False
    if len(a) > 2 or len(b) > 2 or len(c) > 2:
        return False
    return ai > 12


def _should_apply_gang_expansion(text: str) -> bool:
    if any(k in text for k in SERIAL_CONTEXT_KEYWORDS):
        return True
    return not any(k in text for k in _EQ_KEYS)


def expand_three_hyphen_to_gang(text: str) -> str:
    if not text or not _should_apply_gang_expansion(text):
        return text
    # 统一为半角减号，便于 ISO 与区间判断
    text = text.replace("\u2013", "-").replace("\u2014", "-").replace("\uff0d", "-")

    def repl(m: re.Match) -> str:
        a, b, c = m.group(1), m.group(2), m.group(3)
        if (
            _looks_like_iso_date(a, b, c)
            or _looks_like_mobile_hyphenated(a, b, c)
            or _looks_like_date_range_digit_triple(a, b, c)
            or _looks_like_calendar_digit_triple(a, b, c)
        ):
            return m.group(0)
        # 四段连号 a-b-c-d 时勿只改前三段（恢复原先 (?!-) 的意图）
        tail = m.string[m.end() :]
        if tail.startswith("-") and len(tail) > 1 and tail[1].isalnum():
            return m.group(0)
        return f"{a}杠{b}杠{c}"

    return _TRIPLE_HYPHEN.sub(repl, text)
