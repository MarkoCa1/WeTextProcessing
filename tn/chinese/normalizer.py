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

from importlib_resources import files
from pynini.lib.pynutil import add_weight, delete

from tn.chinese.address_path_expand import expand_address_path_spans
from tn.chinese.equation_div_slash import mark_slash_in_equation_context
from tn.chinese.hyphen_three_gang import expand_three_hyphen_to_gang
from tn.chinese.iso_date_sentinel import insert_date_sentinels
from tn.chinese.list_bullet_hyphen import remove_list_bullet_hyphens
from tn.chinese.measure_range_wei_expand import expand_hyphen_to_dao_before_wei
from tn.chinese.rules.cardinal import Cardinal
from tn.chinese.rules.char import Char
from tn.chinese.rules.date import Date
from tn.chinese.rules.fraction import Fraction
from tn.chinese.rules.math import Math
from tn.chinese.rules.measure import Measure
from tn.chinese.rules.money import Money
from tn.chinese.rules.postprocessor import PostProcessor
from tn.chinese.rules.preprocessor import PreProcessor
from tn.chinese.rules.sport import Sport
from tn.chinese.rules.time import Time
from tn.chinese.rules.whitelist import Whitelist
from tn.processor import Processor


class Normalizer(Processor):

    def __init__(
        self,
        cache_dir=None,
        overwrite_cache=False,
        remove_interjections=True,
        remove_erhua=True,
        traditional_to_simple=True,
        remove_puncts=False,
        full_to_half=True,
        tag_oov=False,
    ):
        super().__init__(name="zh_normalizer")
        self.remove_interjections = remove_interjections
        self.remove_erhua = remove_erhua
        self.traditional_to_simple = traditional_to_simple
        self.remove_puncts = remove_puncts
        self.full_to_half = full_to_half
        self.tag_oov = tag_oov
        if cache_dir is None:
            cache_dir = files("tn")
        self.build_fst("zh_tn", cache_dir, overwrite_cache)

    def build_tagger(self):
        processor = PreProcessor(traditional_to_simple=self.traditional_to_simple).processor

        # 权重越小越优先：date 须明显低于 time/math/cardinal，整块 yyyy-mm-dd 先于拆数字（四月负二十五）
        date = add_weight(Date().tagger, 0.8)
        whitelist = add_weight(Whitelist().tagger, 1.03)
        sport = add_weight(Sport().tagger, 1.04)
        # 略低于 math，使「3/5」「1/10000」等优先走分数「分之」，「10/4」仍因分子非单位数字不匹配分数
        fraction = add_weight(Fraction().tagger, 1.04)
        measure = add_weight(Measure().tagger, 1.05)
        money = add_weight(Money().tagger, 1.05)
        # 须低于 math，否则「7:30」「6:20-23:30」会被 math 的冒号「比」、减号「减」抢走；须高于 date(0.95)，避免抢 yyyy-mm-dd
        time = add_weight(Time().tagger, 1.01)
        cardinal = add_weight(Cardinal().tagger, 1.06)
        # 低于 cardinal（^、式子），高于 time（时刻），避免与纯数字 cardinal 抢且不误伤时刻
        math = add_weight(Math().tagger, 1.05)
        char = add_weight(Char().tagger, 100)

        tagger = (date | whitelist | sport | fraction | measure | money | time | cardinal | math | char).optimize()
        tagger = (processor @ tagger).star
        # delete the last space
        self.tagger = tagger @ self.build_rule(delete(" "), r="[EOS]")

    def build_verbalizer(self):
        cardinal = Cardinal().verbalizer
        char = Char().verbalizer
        date = Date().verbalizer
        fraction = Fraction().verbalizer
        math = Math().verbalizer
        measure = Measure().verbalizer
        money = Money().verbalizer
        sport = Sport().verbalizer
        time = Time().verbalizer
        whitelist = Whitelist(remove_erhua=self.remove_erhua).verbalizer

        verbalizer = (cardinal | char | date | fraction | math | measure | money | sport | time | whitelist).optimize()

        processor = PostProcessor(
            remove_interjections=self.remove_interjections,
            remove_puncts=self.remove_puncts,
            full_to_half=self.full_to_half,
            tag_oov=self.tag_oov,
        ).processor
        self.verbalizer = (verbalizer @ processor).star

    def tag(self, input):
        # 先于 TN：http(s)://、盘符路径等读「冒号」「斜杠」及 IP/版本号等，避免被 cardinal/time 误拆
        input = expand_address_path_spans(input)
        input = expand_hyphen_to_dao_before_wei(input)
        input = expand_three_hyphen_to_gang(input)
        # ISO yyyy-mm-dd → sentinel token，避免被 math/cardinal/fraction 抢「-」和数字
        input = insert_date_sentinels(input)
        # 删除列表项目符号「 - 」或「- 」（前后无数字），避免被 math 读成「减」
        input = remove_list_bullet_hyphens(input)
        input = mark_slash_in_equation_context(input)
        return super().tag(input)
