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

from pynini import accep, cross, string_file
from pynini.lib.pynutil import add_weight, delete, insert

from tn.chinese.rules.cardinal import Cardinal
from tn.processor import Processor
from tn.utils import get_abs_path


class Measure(Processor):

    def __init__(self):
        super().__init__(name="measure")
        self.build_tagger()
        self.build_verbalizer()

    def build_tagger(self):
        units_en = string_file(get_abs_path("chinese/data/measure/units_en.tsv"))
        units_zh = string_file(get_abs_path("chinese/data/measure/units_zh.tsv"))
        units = add_weight((cross("k", "千") | cross("w", "万")), 0.1).ques + (units_en | units_zh)
        rmspace = delete(" ").ques
        # 与常见「数字-数字+单位」范围写法一致（如 4-5级、4/5级）
        to = cross("-", "到") | cross("~", "到") | cross("/", "到") | accep("到")

        # 数字后紧跟单位时按「数值」读（四百五十公里），不由位数决定；单位表见 units_*.tsv
        number = Cardinal().number
        number @= self.build_rule(cross("二", "两"), "[BOS]", "[EOS]")
        # 1-11个，1个-11个
        prefix = number + (rmspace + units).ques + to
        measure = prefix.ques + number + rmspace + units

        for unit in ["两", "月", "号"]:
            measure @= self.build_rule(cross("两" + unit, "二" + unit), l="[BOS]")
            measure @= self.build_rule(cross("到两" + unit, "到二" + unit), r="[EOS]")
        # 楼层读「二层」不读「两层」（避免 number 侧「二→两」与层连用）
        measure @= self.build_rule(cross("两层", "二层"), l="[BOS]")

        # -xxxx年, -xx年
        digits = Cardinal().digits
        cardinal = digits**2 | digits**4
        unit = accep("年") | accep("年度") | accep("赛季")
        prefix = cardinal + (rmspace + unit).ques + to
        annual = prefix.ques + cardinal + unit

        # −5℃ / −5°C → 零下五摄氏度（不用「负」）；须压过「负五 + 摄氏度」整条 measure
        minus = delete("-") | delete("\u2212") | delete("\uFF0D")
        neg_celsius = (
            minus
            + insert("零下")
            + Cardinal().positive_number
            + rmspace
            + (cross("℃", "摄氏度") | cross("°C", "摄氏度"))
        )

        # 6.058m*2.438m*2.591m 等：数字+单位 用 * 连接，读作「乘」
        measure_dim = number + rmspace + units + (cross("*", "乘") + number + rmspace + units).plus

        # 30%-40%：两段各带 %
        pct_range = (
            insert("百分之")
            + Cardinal().positive_number
            + delete("%")
            + (cross("-", "到") | cross("~", "到"))
            + insert("百分之")
            + Cardinal().positive_number
            + delete("%")
        )
        # 1-2%、3-4% 等：仅末尾一个 %，读作「百分之一到二」（不重复第二段「百分之」）
        pct_hyphen_single = (
            insert("百分之")
            + Cardinal().positive_number
            + (cross("-", "到") | cross("~", "到"))
            + Cardinal().positive_number
            + delete("%")
        )
        # 62%:38% 控球率等：百分数比百分数，冒号读「比」
        pct_colon_pct = (
            insert("百分之")
            + Cardinal().positive_number
            + delete("%")
            + cross(":", "比")
            + insert("百分之")
            + Cardinal().positive_number
            + delete("%")
        )
        # 1-3章：章节范围用「到」，不用数学「减」
        chapter_span = (
            Cardinal().positive_number
            + (cross("-", "到") | cross("~", "到"))
            + Cardinal().positive_number
            + accep("章")
        )
        # 配速「约2分52秒/公里」→ 约每公里二分五十二秒
        # 须用 cross 吃掉输入里的「分」「秒」；仅用 insert 不会在输入侧前进，无法接上后一段数字
        pace_per_km = (
            accep("约").ques
            + insert("每公里")
            + Cardinal().positive_number
            + cross("分", "分")
            + Cardinal().positive_number
            + cross("秒", "秒")
            + delete("/")
            + delete("公里")
        )
        # 「5.5分钟/公里」→ 每公里五点五分钟（须压过 slash 分式与 math）
        pace_decimal_min_km = (
            accep("约").ques
            + insert("每公里")
            + Cardinal().decimal_positive
            + cross("分钟/公里", "分钟")
        )
        # 「6-12位密码」：须压过 math「减」
        digit_range_wei = (
            Cardinal().positive_number
            + (cross("-", "到") | cross("~", "到"))
            + Cardinal().positive_number
            + accep("位")
        )
        # 「2.4GHz」：小数点走 digit.tsv 读「点」，勿拆成「二」+「.」
        dec_ghz = Cardinal().decimal_positive + rmspace + accep("GHz")
        # 心率「72次/分」→ 七十二次每分（与「每分七十二次」的 slash  verbalizer 区分）
        pulse_per_min = Cardinal().positive_number + cross("次/分", "次每分")

        tagger = insert('value: "') + (
            add_weight(neg_celsius, -0.55)
            | add_weight(measure_dim, -0.12)
            | add_weight(pace_per_km, -0.62)
            | add_weight(pace_decimal_min_km, -0.63)
            | add_weight(digit_range_wei, -0.58)
            | add_weight(dec_ghz, -0.15)
            | add_weight(pulse_per_min, -0.13)
            | add_weight(pct_colon_pct, -0.095)
            | add_weight(chapter_span, -0.11)
            | add_weight(pct_hyphen_single, -0.09)
            | add_weight(pct_range, -0.08)
            | measure
            | annual
        ) + insert('"')

        # 10km/h
        rmsign = rmspace + delete("/") + rmspace
        # 略抬高权重，减轻与「N分 + M秒/公里」拆条竞争（配速条已能整段匹配时更稳）
        tagger |= add_weight(
            insert('numerator: "') + measure + rmsign + insert('" denominator: "') + units + insert('"'),
            0.08,
        )
        self.tagger = self.add_tokens(tagger)

    def build_verbalizer(self):
        super().build_verbalizer()
        denominator = delete('denominator: "') + self.SIGMA + delete('" ')
        numerator = delete('numerator: "') + self.SIGMA + delete('"')
        verbalizer = insert("每") + denominator + numerator
        self.verbalizer |= self.delete_tokens(verbalizer)
