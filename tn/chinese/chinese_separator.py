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

"""中文分隔符规范化。

- `-`：将两个汉字之间的 `-` 替换为空格（地址分隔等场景），可立即处理。
- `/` 和 `\`：**延迟到最后处理**，只替换「纯汉字 / 纯汉字」且前后没有字母/数字/单位的情况。
  这样可以保护 `60km/h`（每小时）等合法用法。

典型场景：
- 地址：`深圳市-宝安区` → `深圳市 宝安区`
- 复合词：`高铁/动车` → `高铁 动车`
- 路径：`文件\目录` → `文件 目录`

注意：数字间的运算符（`-`、`/`）由 math/fraction/measure 负责处理。
"""

import re

# 匹配「汉字 + dash + 汉字」（安全，可以立即处理）
_CHINESE_DASH = re.compile(
    r'([\u4e00-\u9fff])([-—–])([\u4e00-\u9fff])'
)

# 匹配「汉字 + slash + 汉字」，但**前后不能有 ASCII 字母/数字/单位**
# 这样可以保护 "60km/h"、"100km/h" 等「每小时」用法
# 注意：使用 ASCII 字符类 [a-zA-Z0-9_/\\]，避免 \w 匹配汉字
_CHINESE_SLASH = re.compile(
    r'(?<![a-zA-Z0-9_/\\])([\u4e00-\u9fff])\s*([/\\])\s*(?![a-zA-Z0-9_/\\])([\u4e00-\u9fff])'
)


def normalize_chinese_separators(text: str) -> str:
    """将两个汉字之间的 `-` 替换为空格（立即处理）。"""
    if not text:
        return text

    def repl_dash(m: re.Match) -> str:
        left, sep, right = m.group(1), m.group(2), m.group(3)
        return f"{left} {right}"

    return _CHINESE_DASH.sub(repl_dash, text)


def normalize_chinese_slash(text: str) -> str:
    """将两个汉字之间的 `/` 和 `\` 替换为空格（最后处理）。

    只有当 `/` 或 `\` 前后都是纯汉字（没有字母、数字、单位）时才替换。
    这样可以保护 "60km/h"（每小时）等合法用法。

    Examples:
        "高铁/动车" → "高铁 动车"
        "文件\\目录" → "文件 目录"
        "60km/h" → "60km/h"（不变）
        "100km/h" → "100km/h"（不变）
    """
    if not text:
        return text

    def repl_slash(m: re.Match) -> str:
        left, sep, right = m.group(1), m.group(2), m.group(3)
        return f"{left} {right}"

    return _CHINESE_SLASH.sub(repl_slash, text)
