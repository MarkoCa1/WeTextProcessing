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

from pynini import accep, cross, difference, string_file, union
from pynini.lib.pynutil import add_weight, delete, insert

from tn.chinese.context_keywords import (
    CN_ID_HEAD_FULL_TEMPLATES,
    CN_ID_HEAD_WITH_CROSS,
    SERIAL_CONTEXT_KEYWORDS,
)
from tn.processor import Processor
from tn.utils import get_abs_path


class Cardinal(Processor):

    def __init__(self):
        super().__init__("cardinal")
        self.number = None
        self.positive_number = None
        self.decimal_positive = None
        self.positive_ge_ten = None
        self.positive_upto99 = None
        self.pow_exponent = None
        self.digits = None
        self.percent_with_number = None
        self.build_tagger()
        self.build_verbalizer()

    def build_tagger(self):
        zero = string_file(get_abs_path("chinese/data/number/zero.tsv"))
        digit = string_file(get_abs_path("chinese/data/number/digit.tsv"))
        teen = string_file(get_abs_path("chinese/data/number/teen.tsv"))
        sign = string_file(get_abs_path("chinese/data/number/sign.tsv"))
        dot = string_file(get_abs_path("chinese/data/number/dot.tsv"))

        rmzero = delete("0") | delete("０")
        rmpunct = delete(",").ques
        digits = zero | digit
        self.digits = digits

        # 11 => 十一
        ten = teen + insert("十") + (digit | rmzero)
        # 11 => 一十一
        tens = digit + insert("十") + (digit | rmzero)
        # 111, 101, 100
        hundred = digit + insert("百") + (tens | (zero + digit) | rmzero**2)
        # 1111, 1011, 1001, 1000
        thousand = digit + insert("千") + rmpunct + (hundred | (zero + tens) | (rmzero + zero + digit) | rmzero**3)
        # 10001111, 1001111, 101111, 11111, 10111, 10011, 10001, 10000
        ten_thousand = (
            (thousand | hundred | ten | digit)
            + insert("万")
            + (
                thousand
                | (zero + rmpunct + hundred)
                | (rmzero + rmpunct + zero + tens)
                | (rmzero + rmpunct + rmzero + zero + digit)
                | rmzero**4
            )
        )

        # ten|tens 须在 digits 前；须含 tens，否则「43」「52」等会按位拆读；「10」仍由 ten 优先于 tens
        # 压低末项「单位 digit」；万级略加重，与「65536」等长整数整块读法一致
        # 整亿（1 后跟 8 个 0）：一亿；略优于万级拆法，避免读成「一千零零…」
        yi_pow8 = digit + insert("亿") + rmzero**8
        core_number = (
            add_weight(yi_pow8, -0.025)
            | add_weight(ten_thousand, -0.02)
            | ten
            | tens
            | hundred
            | thousand
            | add_weight(digits, 2.05)
        )
        core_number = core_number + (dot + digits.plus).ques
        core_number @= self.build_rule(cross("二百", "两百") | cross("二千", "两千") | cross("二万", "两万"), "[BOS]").optimize()
        number = sign.ques + core_number
        percent = insert("百分之") + number + delete("%")
        # 供 math 等内嵌：整块「N%」，分子用完整 number，无位数限制
        self.percent_with_number = percent.optimize()
        self.number = accep("约").ques + accep("人均").ques + (number | percent)
        # 无正负号，用于气温「零下」等（负号在别处单独处理）
        self.positive_number = accep("约").ques + accep("人均").ques + core_number
        # 必含小数点，用于「2.3/5.8」等分数式比例，避免与「10/4」整除写法混淆
        core_decimal = (ten | tens | hundred | thousand | ten_thousand | digits) + dot + digits.plus
        core_decimal @= self.build_rule(cross("二百", "两百") | cross("二千", "两千") | cross("二万", "两万"), "[BOS]").optimize()
        self.decimal_positive = accep("约").ques + accep("人均").ques + core_decimal
        # 分母 ≥10 的分数（不含纯个位分母），与「10/4」等整除写法区分
        core_ge_ten = ten | tens | hundred | thousand | ten_thousand
        core_ge_ten @= self.build_rule(cross("二百", "两百") | cross("二千", "两千") | cross("二万", "两万"), "[BOS]").optimize()
        self.positive_ge_ten = accep("约").ques + accep("人均").ques + core_ge_ten + (dot + digits.plus).ques
        # 分数分子侧上限两位整数（可带小数），避免「145/95」走分数抢 measure
        core_upto99 = ten | tens | digit
        core_upto99 @= self.build_rule(cross("二百", "两百") | cross("二千", "两千") | cross("二万", "两万"), "[BOS]").optimize()
        self.positive_upto99 = accep("约").ques + accep("人均").ques + core_upto99 + (dot + digits.plus).ques
        # 幂指数：digit 权须极高，否则「10」会先走单字符 digit 留下「0」→ math 读成「一次方零」；勿回退 positive_number（同样含 digit 短路）
        exp_core = (
            add_weight(ten, -0.12)
            | add_weight(tens, -0.12)
            | add_weight(hundred, -0.04)
            | add_weight(thousand, -0.04)
            | add_weight(ten_thousand, -0.04)
            | add_weight(digits, 4.0)
        )
        exp_core = exp_core + (dot + digits.plus).ques
        exp_core @= self.build_rule(cross("二百", "两百") | cross("二千", "两千") | cross("二万", "两万"), "[BOS]").optimize()
        self.pow_exponent = (accep("约").ques + exp_core).optimize()

        digit_sym = self.DIGIT | union(*[accep(c) for c in "０１２３４５６７８９"])
        # 关键词「包含」：前缀/间隙为非数字字符，不要求整段以关键词开头（如「订单编号89757」）
        kw_gap = difference(self.VCHAR, digit_sym).star

        # 默认阿拉伯数字按中文数值读法；仅在下列显式模式或「关键词+数字」时按位读。
        # 须显式写三段「点+数字」，勿用 **3：在部分 pynini 版本下可能与 digits.plus 组合成「无点也可匹配」→ 长整串被按位读
        _dot_block = dot + digits.plus
        cardinal = digits.plus + _dot_block + _dot_block + _dot_block
        cardinal |= percent
        # 勿写「digits+(-digits)+2」：会与 yyyy-mm-dd 抢，且与 Date 日期区间冲突（改由 phone 等专用条覆盖）
        # xxx-xxxxxxxx
        cardinal |= digits**3 + delete("-") + digits**8
        # 电话长串仍用幺读法，与「数字+单位」的整条 measure 竞争时由 normalizer 中 measure 权重保证先切单位短语
        phone_digits = digits @ self.build_rule(cross("一", "幺"))
        phone = phone_digits**5 | phone_digits**11
        phone |= accep("尾号") + (accep("是") | accep("为")).ques + phone_digits**4
        # 大陆手机 3-4-4 分段（与 hyphen 预处理跳过杠一致，须整块幺读）
        phone_hyphen_344 = phone_digits**3 + delete("-") + phone_digits**4 + delete("-") + phone_digits**4
        room_id = accep("房间号") + self.digits**4
        kw_cores_plain = union(*[accep(k) for k in SERIAL_CONTEXT_KEYWORDS]).optimize()
        kw_digit_plain = (kw_gap + kw_cores_plain + kw_gap + self.digits.plus).optimize()
        kw_cores_yao = (
            accep("信道")
            | accep("密码是")
            | (accep("密码") + ((accep("：") | accep(":") | accep("为")).ques))
        )
        kw_digit_yao = (kw_gap + kw_cores_yao + kw_gap + phone_digits.plus).optimize()
        # 打印机/设备型号：单个大写字母 + 数字 + 小写后缀
        product_model_linear = self.UPPER + phone_digits.plus + self.LOWER.plus
        train_series = self.UPPER + phone_digits.plus + accep("次")
        # IATA 后须至少三位数字，避免「SPF30」中的 PF+30 被误当成航班号读成三零
        flight_iata_digits = self.UPPER + self.UPPER + (self.digits**3 + self.digits.star)
        flight_kw_iata = accep("航班") + self.UPPER + self.UPPER + (self.digits**3 + self.digits.star)
        # B-2、F-16、B-3 等：字母+连字符+数字为编号，读「杠」不读「负」（避免 -3 走 sign.tsv）
        designation_hyphen = self.UPPER + delete("-") + insert("杠") + self.digits.plus
        # 车牌常见「数字+字母+数字」如 5D八八六（D 后幺读）
        plate_mixed = self.digits + self.UPPER + phone_digits.plus
        # 停车位 A区023 → 区后逐位读
        zone_bay = self.UPPER + accep("区") + self.digits.plus
        # 身份证地区码：前 4/5/6 位（阿拉伯或全中文「位」）后逐位读；前缀见 context_keywords
        cn_id_parts = []
        for ar, zh, nd in (("4", "四", 4), ("5", "五", 5), ("6", "六", 6)):
            cx = cross(f"前{ar}位是", f"前{zh}位是")
            branches = [accep(p) + cx for p in CN_ID_HEAD_WITH_CROSS]
            branches.extend(accep(t.format(zh=zh)) for t in CN_ID_HEAD_FULL_TEMPLATES)
            br = union(*branches).optimize()
            cn_id_parts.append((br + self.digits**nd).optimize())
        cn_id = union(*cn_id_parts).optimize()
        cardinal |= add_weight(phone, -1.0)
        cardinal |= add_weight(phone_hyphen_344, -1.02)
        cardinal |= add_weight(room_id, -0.4)
        cardinal |= add_weight(kw_digit_yao, -0.45)
        cardinal |= add_weight(kw_digit_plain, -0.44)
        cardinal |= add_weight(product_model_linear, -0.43)
        cardinal |= add_weight(train_series, -0.43)
        cardinal |= add_weight(flight_kw_iata, -0.43)
        cardinal |= add_weight(flight_iata_digits, -0.43)
        cardinal |= add_weight(designation_hyphen, -0.42)
        cardinal |= add_weight(plate_mixed, -0.42)
        cardinal |= add_weight(zone_bay, -0.41)
        cardinal |= add_weight(cn_id, -0.41)
        cardinal |= self.number

        tagger = insert('value: "') + cardinal + insert('"')
        self.tagger = self.add_tokens(tagger)
