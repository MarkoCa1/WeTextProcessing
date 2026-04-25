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

from pynini import cross, string_file
from pynini.lib.pynutil import add_weight, delete, insert

from tn.chinese.equation_div_slash import DIV_SLASH_SENTINEL
from tn.chinese.rules.cardinal import Cardinal
from tn.processor import Processor
from tn.utils import get_abs_path


class Math(Processor):

    def __init__(self):
        super().__init__(name="math")
        self.build_tagger()
        self.build_verbalizer()

    def build_tagger(self):
        operator = string_file(get_abs_path("chinese/data/math/operator.tsv"))
        # When it appears alone, it is treated as punctuation
        # 冒号不映射「比」，避免与时刻 0:45:32、7:30 冲突；比分等依赖 sport/whitelist
        symbols = cross("~", "到") | cross("<", "小于") | cross(">", "大于")

        card = Cardinal()
        number = card.number
        # 2^10 → 二的十次方；指数专用 pow_exponent（digit 极高权 + 无 positive_number 回退），避免 2^1+0
        pow_num = add_weight(
            card.positive_number + cross("^", "的") + card.pow_exponent + insert("次方"),
            -0.12,
        )
        pow_var_sq = self.LOWER + cross("^2", "的平方")
        # [-5, 10] 等闭区间写法：去掉括号与逗号，读作「负五到十」
        # BYTE/UTF8 下 [ ] 为特殊语法，字面量须写成 \[ \]（见 PyniniStringDoc）
        bracket_range = (
            delete("\\[")
            + Cardinal().number
            + delete(",").ques + delete(" ").ques
            + insert("到")
            + Cardinal().positive_number
            + delete("\\]")
        )
        # 计分/比分 N:M（冒号读「比」）；时刻由 normalizer 里 Time 优先，不与此条抢
        score_colon = Cardinal().positive_number + cross(":", "比") + Cardinal().positive_number
        # 括号内减法：(x-2)、(8 - 3.5) 读「减」不读「负」；兼容全角括号与 Unicode 减号
        hyphen_as_minus = cross("-", "减") | cross("\u2212", "减") | cross("\uFF0D", "减")
        paren_open = delete("(") | delete("（")
        paren_close = delete(")") | delete("）")
        paren_minus = (
            paren_open
            + delete(" ").star
            + (
                (self.LOWER + delete(" ").star + hyphen_as_minus + delete(" ").star + Cardinal().positive_number)
                | (
                    Cardinal().positive_number
                    + delete(" ").star
                    + hyphen_as_minus
                    + delete(" ").star
                    + Cardinal().positive_number
                )
            )
            + delete(" ").star
            + paren_close
        )
        # 等式语境下数字间「/」经 preprocess 变为 DIV_SLASH_SENTINEL，读「除以」（与分之、秒/公里等区分）
        div_slash = cross(DIV_SLASH_SENTINEL, "除以")
        # 「=」后紧跟阿拉伯数字：与数字并成一条 math，整块按 positive_number 读，避免长串在 cardinal 里被按位读（如 65536）
        math_value = card.positive_number | card.percent_with_number
        equals_rhs = (
            (cross("=", "等于") | cross("\uff1d", "等于"))
            + delete(" ").star
            + math_value
        ).optimize()
        # 式子开头「+1」读「加一」不读「正一」（number 含 sign.tsv 的 +→正）；后续操作数只用 positive_number，避免 +1 再被读成正一
        lead_operand = add_weight(cross("+", "加") + card.positive_number, -0.07) | number
        # 至少含一处运算符，避免与「纯数字」cardinal 重复构图（否则调低 math 权重时会抢走 450 等）
        main = lead_operand + (
            delete(" ").star + (operator | symbols | div_slash) + delete(" ").star + math_value
        ).plus
        tagger = insert('value: "') + (
            bracket_range
            | pow_var_sq
            | pow_num
            | add_weight(equals_rhs, -0.14)
            | add_weight(paren_minus, -0.06)
            | score_colon
            | main
            | operator
        ) + insert('"')
        self.tagger = self.add_tokens(tagger)
