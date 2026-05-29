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

"""句级标记：含等式语境时，将数字与数字之间的「/」交给 math 读作「除以」。"""

# 私用区字符，仅经本模块写入、math 读出，不进入用户可见文本流（经 TN 后即变为「除以」）
DIV_SLASH_SENTINEL = "\ue001"

_EQ_KEYS = ("=", "等于", "结果")


def _is_arabic_digit(ch: str) -> bool:
    if not ch:
        return False
    if ch.isdigit():
        return True
    o = ord(ch)
    return 0xFF10 <= o <= 0xFF19


def _right_ok_for_eq_div(ch: str) -> bool:
    """等式内「/」右侧可为数字或括号起头的子式（如 10 / (2+3)）。"""
    if not ch:
        return False
    if _is_arabic_digit(ch):
        return True
    return ch in "([（【《"


def mark_slash_in_equation_context(text: str) -> str:
    if not text or not any(k in text for k in _EQ_KEYS):
        return text
    out = []
    n = len(text)
    i = 0
    while i < n:
        if text[i] == "/":
            j = i - 1
            while j >= 0 and text[j] in " \t":
                j -= 1
            k = i + 1
            while k < n and text[k] in " \t":
                k += 1
            if j >= 0 and k < n and _is_arabic_digit(text[j]) and _right_ok_for_eq_div(text[k]):
                out.append(DIV_SLASH_SENTINEL)
                i += 1
                continue
        out.append(text[i])
        i += 1
    return "".join(out)
