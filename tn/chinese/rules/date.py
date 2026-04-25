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

from tn.processor import Processor
from tn.utils import get_abs_path


class Date(Processor):

    def __init__(self):
        super().__init__(name="date")
        self.build_tagger()
        self.build_verbalizer()

    def build_tagger(self):
        digit = string_file(get_abs_path("chinese/data/number/digit.tsv"))
        zero = string_file(get_abs_path("chinese/data/number/zero.tsv"))

        yyyy = digit + (digit | zero) ** 3
        m = string_file(get_abs_path("chinese/data/date/m.tsv"))
        mm_src = string_file(get_abs_path("chinese/data/date/mm.tsv"))
        d = string_file(get_abs_path("chinese/data/date/d.tsv"))
        dd_src = string_file(get_abs_path("chinese/data/date/dd.tsv"))
        rmsign = (delete("/") | delete("-") | delete(".")) + insert(" ")
        # 仅「月-日」「月/日」视为无年份月日；不用「.」，避免与小数(如 10.5)冲突。
        rmsign_month_day = (delete("/") | delete("-")) + insert(" ")

        year = insert('year: "') + yyyy + insert('年"')
        # 严格「四位年-两位月-两位日」：月、日只用 mm/dd 表，不经 (d|dd)，避免 d 先吃「25」的首位二（→ 四月负二十五）
        date_yyyy_mm_dd = (
            year
            + rmsign
            + insert('month: "')
            + mm_src
            + insert('"')
            + rmsign
            + insert('day: "')
            + dd_src
            + insert('"')
        )

        # === Sentinel for ISO dates (最高优先级) ===
        # 匹配预处理插入的 ___DATE_YYYYMMDD___ token
        # year 必须带「年」才能正确 verbalize（原 date_yyyy_mm_dd 也是如此）
        date_sentinel = (
            delete("___DATE_")
            + insert('year: "')
            + yyyy
            + insert('年" month: "')
            + mm_src
            + insert('" day: "')
            + dd_src
            + insert('"')
            + delete("___")
        )

        # 单数字月/日等仍走 flex
        month = insert('month: "') + (add_weight(mm_src, -0.5) | m) + insert('"')
        day = insert('day: "') + (add_weight(dd_src, -0.5) | d) + insert('"')

        # yyyy/m/d | yyyy/mm/dd | dd/mm/yyyy
        # yyyy/0m | 0m/yyyy | 0m/dd
        mm_month_day = insert('month: "') + mm_src + insert('"')
        # yyyy-mm-dd 与 flex 可同时匹配「2026-04-25」：须极大压低 ISO 条、略抬高 flex，否则 optimize 后仍可能走 (d|dd) 吃「25」
        date_flex_ymd = year + rmsign + month + rmsign + day

        date = (
            add_weight(date_sentinel, -10.0)  # 最高优先级
            | add_weight(date_yyyy_mm_dd, -5.0)
            | add_weight(date_flex_ymd, 0.2)
            | (day + rmsign + month + rmsign + year)
            | (year + rmsign_month_day + mm_month_day)
            | (mm_month_day + rmsign_month_day + year)
        )
        tagger = self.add_tokens(date)

        to = (delete("-") | delete("~")) + insert(' char { value: "到" } ')
        self.tagger = tagger + (to + tagger).ques

    def build_verbalizer(self):
        year = delete('year: "') + self.SIGMA + delete('" ')
        month = delete('month: "') + self.SIGMA + delete('"')
        # 与 tagger 衔接：有的构图在「月」与 day: 之间带空格，有的不带，两种都删
        day = (delete(' day: "') | delete('day: "')) + self.SIGMA + delete('"')
        verbalizer = year.ques + month + day.ques
        self.verbalizer = self.delete_tokens(verbalizer)
