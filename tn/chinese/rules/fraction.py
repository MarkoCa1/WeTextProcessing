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

from pynini import string_file
from pynini.lib.pynutil import add_weight, delete, insert

from tn.chinese.rules.cardinal import Cardinal
from tn.processor import Processor
from tn.utils import get_abs_path


class Fraction(Processor):

    def __init__(self):
        super().__init__(name="fraction")
        self.build_tagger()
        self.build_verbalizer()

    def build_tagger(self):
        rmspace = delete(" ").ques
        # 分母仍用完整 number；分子仅用 1–9 单字符，避免「+1/2」被读成正一、「10/4」误作四分之十
        card = Cardinal()
        number = card.number
        numerator_fst = string_file(get_abs_path("chinese/data/number/digit.tsv"))

        digit_frac = (
            insert('numerator: "')
            + numerator_fst
            + rmspace
            + delete("/")
            + rmspace
            + insert('" denominator: "')
            + number
            + insert('"')
        ).optimize()
        # 至少一侧带小数点：2.3/5.8、2/5.8 等读「分之」，且不会匹配 10/4
        slash = rmspace + delete("/") + rmspace
        dec_ratio = (
            (
                insert('numerator: "')
                + card.decimal_positive
                + slash
                + insert('" denominator: "')
                + card.positive_number
                + insert('"')
            )
            | (
                insert('numerator: "')
                + card.positive_number
                + slash
                + insert('" denominator: "')
                + card.decimal_positive
                + insert('"')
            )
        ).optimize()
        # 分母 ≥10、分子至多两位整数（可小数）：十八分之十三等；不抢「145/95」等三位分子
        int_frac = (
            insert('numerator: "')
            + card.positive_upto99
            + slash
            + insert('" denominator: "')
            + card.positive_ge_ten
            + insert('"')
        ).optimize()
        # 小数比例 → 整数分母分数 → 单位数字分子（略加重 int_frac，压过「1」+「3/18」双 token）
        tagger = add_weight(dec_ratio, -0.02) | add_weight(int_frac, -0.045) | digit_frac
        self.tagger = self.add_tokens(tagger.optimize())

    def build_verbalizer(self):
        denominator = delete('denominator: "') + self.SIGMA + delete('" ')
        numerator = delete('numerator: "') + self.SIGMA + delete('"')
        verbalizer = denominator + insert("分之") + numerator
        self.verbalizer = self.delete_tokens(verbalizer)
