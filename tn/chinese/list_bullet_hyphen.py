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

"""列表项目符号「 - 」或「- 」规范化。

当「-」前后没有数字（或前后是空格且附近无数字）时，删除它，避免被 math 读成「减」。
适用于天气预报、列表等场景，如「 - 昨天（4月23日）」→ 「昨天（4月23日）」。
"""

import re

# 匹配列表项目符号：前面是标点、行首或空格，后面是中文、日期、括号或天气描述
# 只匹配**列表/天气上下文**的 bullet `- `，不匹配纯负数 `-5` 或 math 中的 `(3 - 1)`、`100 - 25`
# 这样负数由 Cardinal.sign 处理，math 由 Math.paren_minus/main 处理
# bullet 删除优先级：高于 char（保底），但低于 math/date/cardinal（不会覆盖它们）
_BULLET_PATTERN = re.compile(
    r"(^|[:：。，；、\s]+)[-—–]\s*(?![ \d])(?=[（(【\[（一二三四五六七八九十零〇]|昨天|今天|明天|后天|大后天|前天|晴|多云|阴|雨|雪|风|℃|建议|注意|计算|公式)",
    flags=re.MULTILINE,
)


def remove_list_bullet_hyphens(text: str) -> str:
    """删除非数值范围的列表项目符号「 - 」，保留后面的内容并清理空格。"""
    if not text:
        return text

    # 统一 dash 为半角
    text = text.replace("\u2013", "-").replace("\u2014", "-").replace("\uFF0D", "-")

    # 删除 bullet，替换为单个空格
    text = _BULLET_PATTERN.sub(r"\1 ", text)

    # 清理多余空格
    text = re.sub(r"\s+", " ", text)
    return text.strip()
