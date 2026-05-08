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

"""列表项目符号规范化（支持 -、*、**）。

规则：
1. 删除行首的 dash bullet（`- `、` - `），仅当后面不是数字。
2. 仅删除「行首或行首仅含空格」的单个 asterisk bullet（`* `、`   * `）。
   - 公式中的乘号 `1/2 * m`、`m * v^2` 不会被删除（前面有非空格字符）。
3. 删除成对的 Markdown 加粗标记 `**text**`（保留内容）。
4. 优先级高于 char（保底），但低于 math/date/cardinal，不会覆盖数值/算式中的符号。
"""

import re

# 匹配 dash 列表项目符号：前面是标点/行首/空格，后面紧跟非数字的中文/字母
# 这样 '-气温'、'：-风向'、' - 昨天' 等 bullet 被删除，'-5'、'25-30' 等保留
_BULLET_PATTERN = re.compile(
    r'(^|[:：。，；、\s]+)([-—–])\s*(?!\d)(?=[\u4e00-\u9fffA-Za-z])',
    flags=re.MULTILINE,
)

# 仅删除「行首或行首仅含空格」的单个 * bullet
# 例如：`* item`、`   * item` 会被删除
# 但 `1/2 * m`、`m * v^2`、`：* 子列表` 不会被删除（前面有非空格字符）
_ASTERISK_BULLET = re.compile(
    r'^\s*\*\s+(?!\d)(?=[\u4e00-\u9fffA-Za-z])',
    flags=re.MULTILINE,
)

# 移除成对的 **加粗** 标记（保留内部文本），但不移除单个 *
_BOLD_MARKER = re.compile(r'\*\*([^*]+)\*\*')


def remove_list_bullet_hyphens(text: str) -> str:
    """删除列表 bullet（-、*）和 Markdown **加粗** 标记，保留内容并清理空格。"""
    if not text:
        return text

    # 统一 dash 为半角
    text = text.replace("\u2013", "-").replace("\u2014", "-").replace("\uFF0D", "-")

    # 1. 先删除 **bold** 标记（保留内容），避免影响后续 bullet 匹配
    text = _BOLD_MARKER.sub(r"\1", text)

    # 2. 删除 dash bullet
    text = _BULLET_PATTERN.sub(r"\1 ", text)

    # 3. 删除行首的 * bullet（替换为单个空格）
    text = _ASTERISK_BULLET.sub(" ", text)

    # 清理多余空格
    text = re.sub(r"\s+", " ", text)
    return text.strip()
