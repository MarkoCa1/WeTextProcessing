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

"""「N-M位」类：半角连字符在 TN 前改为「到」，避免被 math 读成「减」（如密码位数、门牌区间）。"""

import re

# 数字-数字+「位」且非三段连号尾部：6-12位、3-5位 等
_HYPHEN_BEFORE_WEI = re.compile(r"(?<=[0-9０-９])-(?=[0-9０-９]+位)")


def expand_hyphen_to_dao_before_wei(text: str) -> str:
    if not text:
        return text
    return _HYPHEN_BEFORE_WEI.sub("到", text)
