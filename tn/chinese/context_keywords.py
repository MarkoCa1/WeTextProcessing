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

"""编号/门牌/地址等语境关键词集中定义。

- ``SERIAL_CONTEXT_KEYWORDS``：供 ``hyphen_three_gang``（有句中等式仍做三段连字符→杠）
  与 ``cardinal``（关键词后出现长数字时按位读）共用。
- 同表内较长串优先（去重后按长度降序），减轻 FST 中短词抢先匹配（如「订单」与「订单号」）。
- ``CN_ID_HEAD_*`` 与 ``SERIAL`` 里「身份证」词条**不是重复配置**：前者只给 ``cardinal.cn_id`` 拼「前 N 位是 + 恰好 n 位数字」及
  ``前4位是``↔``前四位是`` 交叉；后者只给 ``kw_digit_plain`` 做「短关键词 + 间隙 + 任意长数字」。
"""

from __future__ import annotations


def _unique_sorted_by_len_desc(phrases: tuple[str, ...]) -> tuple[str, ...]:
    seen: set[str] = set()
    out: list[str] = []
    for s in sorted(phrases, key=len, reverse=True):
        if s not in seen:
            seen.add(s)
            out.append(s)
    return tuple(out)


# 合并原 hyphen_three_gang 门牌/地址类 + cardinal「关键词+按位读」+ 身份证相关
_SERIAL_RAW: tuple[str, ...] = (
    # —— 原 cardinal kw_cores_plain ——
    "验证码",
    "班次",
    "车次",
    "单号",
    "编号",
    "工号",
    "票号",
    "取号",
    # —— 身份证（仅关键词；整段按位读走 kw_digit_plain，与下方 cn_id 地区码句式不同）——
    "身份证",
    "身份证号",
    "身份证号码",
    # —— 原 hyphen_three_gang 语境 ——
    "门牌",
    "门牌号",
    "地址",
    "住址",
    "详细地址",
    "联系地址",
    "收货地址",
    "收件地址",
    "房号",
    "室号",
    "单元",
    "楼栋",
    "邮编",
    "邮政编码",
    "订单号",
    "订单",
    "快递单",
    "运单号",
    "运单",
    "追踪码",
    "追踪号",
)

SERIAL_CONTEXT_KEYWORDS: tuple[str, ...] = _unique_sorted_by_len_desc(_SERIAL_RAW)

# 仅用于 cardinal.cn_id（非 SERIAL）：前缀 + cross(前4位是↔前四位是) + digits**n，n∈{4,5,6}
CN_ID_HEAD_WITH_CROSS: tuple[str, ...] = (
    "身份证号码",
    "身份证号码的",
    "身份证号",
    "身份证号的",
)

# 仅用于 cn_id：整句「…前四位是」等 + digits**n（阿拉伯/中文「位」已在串内），format(zh=「四」等)
CN_ID_HEAD_FULL_TEMPLATES: tuple[str, ...] = (
    "身份证号码前{zh}位是",
    "身份证号码的前{zh}位是",
    "身份证号前{zh}位是",
    "身份证号的前{zh}位是",
)
