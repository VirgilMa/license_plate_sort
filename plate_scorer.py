"""
车牌评分系统
支持灵活添加和配置评分规则
"""

import re
import json
import os
from abc import ABC, abstractmethod
from typing import List, Tuple, Dict, Optional
from dataclasses import dataclass


@dataclass
class ScoreResult:
    """单个规则的评分结果"""
    rule_name: str
    score: float
    reason: str


class ScoringRule(ABC):
    """评分规则抽象基类"""

    def __init__(self, name: str, weight: float = 1.0):
        """
        参数:
            name: 规则名称
            weight: 规则权重系数
        """
        self.name = name
        self.weight = weight

    @abstractmethod
    def calculate_score(self, plate_number: str) -> ScoreResult:
        """
        计算评分

        参数:
            plate_number: 车牌号码

        返回:
            ScoreResult: 包含得分和原因的结果
        """
        pass

    def extract_digits(self, plate_number: str) -> str:
        """提取车牌中的数字部分"""
        return ''.join(c for c in plate_number if c.isdigit())

    def extract_letters(self, plate_number: str) -> str:
        """提取车牌中的字母部分"""
        return ''.join(c for c in plate_number if c.isalpha())


class Rule1_NoFour(ScoringRule):
    """规则1: 含有4的评分低"""

    def __init__(self, no_four_bonus: float = 10, four_penalty_per_count: float = 5):
        super().__init__("避免数字4", weight=1.0)
        self.no_four_bonus = no_four_bonus
        self.four_penalty_per_count = four_penalty_per_count

    def calculate_score(self, plate_number: str) -> ScoreResult:
        digits = self.extract_digits(plate_number)
        count_4 = digits.count('4')

        if count_4 == 0:
            score = self.no_four_bonus
            return ScoreResult(self.name, score * self.weight, f"无数字4 (+{score:.0f})")
        else:
            penalty = count_4 * self.four_penalty_per_count
            return ScoreResult(self.name, -penalty * self.weight,
                             f"含有{count_4}个数字4 (-{penalty:.0f})")


class Rule2_ConsecutiveRepeats(ScoringRule):
    """规则2: 连续重复的数字评分高，重复越多评分越高"""

    def __init__(self, repeat_base_score: float = 15):
        super().__init__("连续重复数字", weight=1.0)
        self.repeat_base_score = repeat_base_score

    def calculate_score(self, plate_number: str) -> ScoreResult:
        digits = self.extract_digits(plate_number)

        if not digits:
            return ScoreResult(self.name, 0, "无数字")

        max_repeat = 1
        current_repeat = 1
        repeat_digit = ''

        for i in range(1, len(digits)):
            if digits[i] == digits[i - 1]:
                current_repeat += 1
                if current_repeat > max_repeat:
                    max_repeat = current_repeat
                    repeat_digit = digits[i]
            else:
                current_repeat = 1

        if max_repeat >= 2:
            score = (max_repeat - 1) * self.repeat_base_score  # 2连得base分，3连得2*base分
            return ScoreResult(self.name, score * self.weight,
                             f"连续{max_repeat}个{repeat_digit} (+{score:.0f})")
        else:
            return ScoreResult(self.name, 0, "无连续重复")


class Rule3_Lucky68(ScoringRule):
    """规则3: 含有6/8的评分高"""

    def __init__(self, lucky_digit_score: float = 8):
        super().__init__("吉祥数字6/8", weight=1.0)
        self.lucky_digit_score = lucky_digit_score

    def calculate_score(self, plate_number: str) -> ScoreResult:
        digits = self.extract_digits(plate_number)
        count_6 = digits.count('6')
        count_8 = digits.count('8')

        total_count = count_6 + count_8

        if total_count == 0:
            return ScoreResult(self.name, 0, "无6或8")
        else:
            score = total_count * self.lucky_digit_score
            details = []
            if count_6 > 0:
                details.append(f"{count_6}个6")
            if count_8 > 0:
                details.append(f"{count_8}个8")
            return ScoreResult(self.name, score * self.weight,
                             f"含有{', '.join(details)} (+{score:.0f})")


class Rule4_IncreasingSequence(ScoringRule):
    """规则4: 递增序列评分高"""

    def __init__(self, sequence_base_score: float = 20):
        super().__init__("递增序列", weight=1.0)
        self.sequence_base_score = sequence_base_score

    def calculate_score(self, plate_number: str) -> ScoreResult:
        digits = self.extract_digits(plate_number)

        if len(digits) < 2:
            return ScoreResult(self.name, 0, "数字不足")

        max_sequence = 1
        current_sequence = 1

        for i in range(1, len(digits)):
            if int(digits[i]) == int(digits[i - 1]) + 1:
                current_sequence += 1
                max_sequence = max(max_sequence, current_sequence)
            else:
                current_sequence = 1

        if max_sequence >= 3:
            score = (max_sequence - 2) * self.sequence_base_score  # 3连得base分，4连得2*base分
            return ScoreResult(self.name, score * self.weight,
                             f"{max_sequence}位递增序列 (+{score:.0f})")
        else:
            return ScoreResult(self.name, 0, "无明显递增序列")


class Rule5_AllEvenOrOdd(ScoringRule):
    """规则5: 全是偶数或者全是奇数评分高"""

    def __init__(self, all_even_odd_score: float = 25):
        super().__init__("全偶数或全奇数", weight=1.0)
        self.all_even_odd_score = all_even_odd_score

    def calculate_score(self, plate_number: str) -> ScoreResult:
        digits = self.extract_digits(plate_number)

        if len(digits) < 3:
            return ScoreResult(self.name, 0, "数字不足")

        digit_nums = [int(d) for d in digits]

        all_even = all(d % 2 == 0 for d in digit_nums)
        all_odd = all(d % 2 == 1 for d in digit_nums)

        if all_even:
            score = self.all_even_odd_score
            return ScoreResult(self.name, score * self.weight,
                             f"全部{len(digits)}位为偶数 (+{score:.0f})")
        elif all_odd:
            score = self.all_even_odd_score
            return ScoreResult(self.name, score * self.weight,
                             f"全部{len(digits)}位为奇数 (+{score:.0f})")
        else:
            return ScoreResult(self.name, 0, "奇偶混合")


class Rule6_AllPrimes(ScoringRule):
    """规则6: 全是质数评分高"""

    def __init__(self, all_prime_score: float = 30, mostly_prime_score: float = 10):
        super().__init__("全质数", weight=1.0)
        self.all_prime_score = all_prime_score
        self.mostly_prime_score = mostly_prime_score

    def calculate_score(self, plate_number: str) -> ScoreResult:
        digits = self.extract_digits(plate_number)

        if len(digits) < 3:
            return ScoreResult(self.name, 0, "数字不足")

        primes = {'2', '3', '5', '7'}
        digit_list = list(digits)

        prime_count = sum(1 for d in digit_list if d in primes)
        all_prime = all(d in primes for d in digit_list)

        if all_prime:
            score = self.all_prime_score
            return ScoreResult(self.name, score * self.weight,
                             f"全部{len(digits)}位为质数 (+{score:.0f})")
        elif prime_count >= len(digits) * 0.6:  # 超过60%是质数
            score = self.mostly_prime_score
            return ScoreResult(self.name, score * self.weight,
                             f"{prime_count}/{len(digits)}位为质数 (+{score:.0f})")
        else:
            return ScoreResult(self.name, 0, f"仅{prime_count}位质数")


class Rule7_SpecialLetters(ScoringRule):
    """规则7: 含有MJTQ这几个字母的评分高"""

    def __init__(self, special_letter_score: float = 12):
        super().__init__("特殊字母MJTQ", weight=1.0)
        self.special_letter_score = special_letter_score

    def calculate_score(self, plate_number: str) -> ScoreResult:
        letters = self.extract_letters(plate_number).upper()
        special_letters = set('MJTQ')

        found_letters = [l for l in letters if l in special_letters]

        if not found_letters:
            return ScoreResult(self.name, 0, "无特殊字母")
        else:
            score = len(found_letters) * self.special_letter_score
            return ScoreResult(self.name, score * self.weight,
                             f"含有字母{', '.join(found_letters)} (+{score:.0f})")


class Rule8_LuckySequences(ScoringRule):
    """规则8: 幸运连号（12, 312, 0312, 0228, 228, 28）"""

    def __init__(self, lucky_sequence_score: float = 30):
        super().__init__("幸运连号", weight=1.0)
        self.lucky_sequence_score = lucky_sequence_score
        # 定义幸运连号列表，按长度从长到短排序（优先匹配长的）
        self.lucky_sequences = ['0312', '0228', '312', '228', '28']

    def calculate_score(self, plate_number: str) -> ScoreResult:
        digits = self.extract_digits(plate_number)

        if not digits:
            return ScoreResult(self.name, 0, "无数字")

        # 查找所有匹配的幸运连号
        found_sequences = []
        for seq in self.lucky_sequences:
            if seq in digits:
                found_sequences.append(seq)

        if not found_sequences:
            return ScoreResult(self.name, 0, "无幸运连号")
        else:
            # 每个幸运连号得分
            score = len(found_sequences) * self.lucky_sequence_score
            seq_str = ', '.join(found_sequences)
            return ScoreResult(self.name, score * self.weight,
                             f"含有幸运连号: {seq_str} (+{score:.0f})")


class Rule9_Pronunciation(ScoringRule):
    """规则9: 读起来顺口的评分高"""

    def __init__(self, smooth_phrase_score: float = 25, tone_variety_score: float = 10):
        super().__init__("读音顺口", weight=1.0)
        self.smooth_phrase_score = smooth_phrase_score
        self.tone_variety_score = tone_variety_score

        # 数字的音调 (1=阴平, 2=阳平, 3=上声, 4=去声, 5=轻声)
        self.digit_tones = {
            '0': 2,  # 零 líng
            '1': 1,  # 一 yī
            '2': 4,  # 二 èr
            '3': 1,  # 三 sān
            '4': 4,  # 四 sì
            '5': 3,  # 五 wǔ
            '6': 4,  # 六 liù
            '7': 1,  # 七 qī
            '8': 1,  # 八 bā
            '9': 3,  # 九 jiǔ
        }

        # 常见的顺口谐音组合（吉利寓意）
        self.smooth_phrases = {
            '168': '一路发',
            '518': '我要发',
            '668': '路路发',
            '888': '发发发',
            '666': '六六大顺',
            '999': '久久久',
            '520': '我爱你',
            '1314': '一生一世',
            '366': '三六六',
            '289': '易发久',
            '678': '路起发',
            '789': '起发久',
            '258': '易我发',
            '358': '生我发',
            '189': '要发久',
            '689': '六发久',
            '368': '生路发',
            '566': '我路路',
            '688': '路发发',
            '588': '我发发',
        }

    def calculate_score(self, plate_number: str) -> ScoreResult:
        digits = self.extract_digits(plate_number)

        if len(digits) < 3:
            return ScoreResult(self.name, 0, "数字不足")

        total_score = 0
        reasons = []

        # 1. 检查是否包含顺口谐音组合
        for phrase, meaning in self.smooth_phrases.items():
            if phrase in digits:
                total_score += self.smooth_phrase_score
                reasons.append(f"含'{phrase}'({meaning})")

        # 2. 检查音调变化（抑扬顿挫更顺口）
        if len(digits) >= 3:
            tones = [self.digit_tones.get(d, 0) for d in digits]

            # 计算音调多样性
            unique_tones = len(set(tones))

            # 检查是否有音调变化（避免单调）
            has_tone_change = False
            for i in range(1, len(tones)):
                if abs(tones[i] - tones[i-1]) >= 2:  # 音调差异较大
                    has_tone_change = True
                    break

            # 音调丰富度评分
            if unique_tones >= 3 and has_tone_change:
                total_score += self.tone_variety_score
                reasons.append("音调抑扬顿挫")

        if total_score > 0:
            reason_str = ", ".join(reasons)
            return ScoreResult(self.name, total_score * self.weight,
                             f"{reason_str} (+{total_score:.0f})")
        else:
            return ScoreResult(self.name, 0, "无顺口组合")


class Rule10_PatternAABB(ScoringRule):
    """规则10: AABB模式 (如1122、5566)"""

    def __init__(self, aabb_score: float = 20):
        super().__init__("AABB模式", weight=1.0)
        self.aabb_score = aabb_score

    def calculate_score(self, plate_number: str) -> ScoreResult:
        digits = self.extract_digits(plate_number)

        if len(digits) < 4:
            return ScoreResult(self.name, 0, "数字不足")

        # 查找AABB模式
        aabb_patterns = []
        for i in range(len(digits) - 3):
            if digits[i] == digits[i+1] and digits[i+2] == digits[i+3] and digits[i] != digits[i+2]:
                pattern = digits[i:i+4]
                aabb_patterns.append(pattern)

        if aabb_patterns:
            score = len(aabb_patterns) * self.aabb_score
            patterns_str = ', '.join(aabb_patterns)
            return ScoreResult(self.name, score * self.weight,
                             f"含AABB模式: {patterns_str} (+{score:.0f})")
        else:
            return ScoreResult(self.name, 0, "无AABB模式")


class Rule11_Palindrome(ScoringRule):
    """规则11: 回文数字 (如121、1221、12321)"""

    def __init__(self, palindrome_base_score: float = 15):
        super().__init__("回文数字", weight=1.0)
        self.palindrome_base_score = palindrome_base_score

    def calculate_score(self, plate_number: str) -> ScoreResult:
        digits = self.extract_digits(plate_number)

        if len(digits) < 3:
            return ScoreResult(self.name, 0, "数字不足")

        # 检查整体是否为回文
        if digits == digits[::-1]:
            score = len(digits) * self.palindrome_base_score
            return ScoreResult(self.name, score * self.weight,
                             f"完整回文数: {digits} (+{score:.0f})")

        # 查找最长的回文子串
        max_palindrome_len = 0
        max_palindrome = ""

        for i in range(len(digits)):
            for j in range(i + 3, len(digits) + 1):  # 至少3位
                substring = digits[i:j]
                if substring == substring[::-1]:
                    if len(substring) > max_palindrome_len:
                        max_palindrome_len = len(substring)
                        max_palindrome = substring

        if max_palindrome_len >= 3:
            score = max_palindrome_len * self.palindrome_base_score
            return ScoreResult(self.name, score * self.weight,
                             f"含回文数: {max_palindrome} (+{score:.0f})")
        else:
            return ScoreResult(self.name, 0, "无回文数")


class Rule12_PatternABAB(ScoringRule):
    """规则12: ABAB模式 (如1212、3434)"""

    def __init__(self, abab_score: float = 20):
        super().__init__("ABAB模式", weight=1.0)
        self.abab_score = abab_score

    def calculate_score(self, plate_number: str) -> ScoreResult:
        digits = self.extract_digits(plate_number)

        if len(digits) < 4:
            return ScoreResult(self.name, 0, "数字不足")

        # 查找ABAB模式
        abab_patterns = []
        for i in range(len(digits) - 3):
            if digits[i] == digits[i+2] and digits[i+1] == digits[i+3] and digits[i] != digits[i+1]:
                pattern = digits[i:i+4]
                abab_patterns.append(pattern)

        if abab_patterns:
            score = len(abab_patterns) * self.abab_score
            patterns_str = ', '.join(abab_patterns)
            return ScoreResult(self.name, score * self.weight,
                             f"含ABAB模式: {patterns_str} (+{score:.0f})")
        else:
            return ScoreResult(self.name, 0, "无ABAB模式")


class PlateScorer:
    """车牌评分器"""

    def __init__(self):
        self.rules: List[ScoringRule] = []

    def add_rule(self, rule: ScoringRule):
        """添加评分规则"""
        self.rules.append(rule)

    def remove_rule(self, rule_name: str):
        """移除评分规则"""
        self.rules = [r for r in self.rules if r.name != rule_name]

    def score_plate(self, plate_number: str) -> Tuple[float, List[ScoreResult]]:
        """
        对车牌进行评分

        参数:
            plate_number: 车牌号码

        返回:
            (总分, 各规则评分详情列表)
        """
        results = []
        total_score = 0.0

        for rule in self.rules:
            result = rule.calculate_score(plate_number)
            results.append(result)
            total_score += result.score

        return total_score, results


def load_config(config_path: str = "scoring_rules.json") -> Optional[Dict]:
    """
    加载配置文件

    参数:
        config_path: 配置文件路径

    返回:
        配置字典，如果文件不存在则返回None
    """
    if not os.path.exists(config_path):
        return None

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        return config
    except Exception as e:
        print(f"警告: 加载配置文件失败 - {e}")
        return None


def create_default_scorer(config_path: str = "scoring_rules.json") -> PlateScorer:
    """
    创建带有默认规则的评分器

    参数:
        config_path: 配置文件路径，默认为 scoring_rules.json

    返回:
        PlateScorer: 配置好的评分器
    """
    scorer = PlateScorer()

    # 尝试加载配置文件
    config = load_config(config_path)

    # 获取分数权重配置
    score_weights = {}
    if config and "score_weights" in config:
        score_weights = config["score_weights"]

    # 创建规则实例，传入配置的分数
    rule_map = {
        "避免数字4": Rule1_NoFour(
            no_four_bonus=score_weights.get("no_four_bonus", 10),
            four_penalty_per_count=score_weights.get("four_penalty_per_count", 5)
        ),
        "连续重复数字": Rule2_ConsecutiveRepeats(
            repeat_base_score=score_weights.get("repeat_base_score", 15)
        ),
        "吉祥数字6/8": Rule3_Lucky68(
            lucky_digit_score=score_weights.get("lucky_digit_score", 8)
        ),
        "递增序列": Rule4_IncreasingSequence(
            sequence_base_score=score_weights.get("sequence_base_score", 20)
        ),
        "全偶数或全奇数": Rule5_AllEvenOrOdd(
            all_even_odd_score=score_weights.get("all_even_odd_score", 25)
        ),
        "全质数": Rule6_AllPrimes(
            all_prime_score=score_weights.get("all_prime_score", 30),
            mostly_prime_score=score_weights.get("mostly_prime_score", 10)
        ),
        "特殊字母MJTQ": Rule7_SpecialLetters(
            special_letter_score=score_weights.get("special_letter_score", 12)
        ),
        "幸运连号": Rule8_LuckySequences(
            lucky_sequence_score=score_weights.get("lucky_sequence_score", 30)
        ),
        "读音顺口": Rule9_Pronunciation(
            smooth_phrase_score=score_weights.get("smooth_phrase_score", 25),
            tone_variety_score=score_weights.get("tone_variety_score", 10)
        ),
        "AABB模式": Rule10_PatternAABB(
            aabb_score=score_weights.get("aabb_score", 20)
        ),
        "回文数字": Rule11_Palindrome(
            palindrome_base_score=score_weights.get("palindrome_base_score", 15)
        ),
        "ABAB模式": Rule12_PatternABAB(
            abab_score=score_weights.get("abab_score", 20)
        )
    }

    # 如果有配置文件，根据配置添加规则
    if config and "rules" in config:
        for rule_config in config["rules"]:
            rule_name = rule_config.get("name")
            enabled = rule_config.get("enabled", True)
            weight = rule_config.get("weight", 1.0)

            if rule_name in rule_map and enabled:
                rule = rule_map[rule_name]
                rule.weight = weight
                scorer.add_rule(rule)
    else:
        # 没有配置文件，使用默认设置
        for rule in rule_map.values():
            scorer.add_rule(rule)

    return scorer


def format_score_report(plate_number: str, total_score: float,
                       score_details: List[ScoreResult]) -> str:
    """格式化评分报告"""
    # 只显示得分不为0的规则
    active_rules = [r for r in score_details if r.score != 0]

    if not active_rules:
        rule_summary = "无特殊加分项"
    else:
        rule_summary = " | ".join([f"{r.rule_name}: {r.reason}" for r in active_rules])

    return f"{plate_number:12s} | 总分: {total_score:6.1f} | {rule_summary}"


if __name__ == "__main__":
    # 测试代码
    test_plates = [
        "CDP5747",
        "CD32024",
        "CD88888",
        "CDM6789",
        "CDQ2357",
        "CD46666",
    ]

    scorer = create_default_scorer()

    print("车牌评分测试")
    print("=" * 100)

    for plate in test_plates:
        total, details = scorer.score_plate(plate)
        print(format_score_report(plate, total, details))
