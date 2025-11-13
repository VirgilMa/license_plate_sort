"""
车牌评分系统
支持灵活添加和配置评分规则
"""

import re
from abc import ABC, abstractmethod
from typing import List, Tuple, Dict
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

    def __init__(self):
        super().__init__("避免数字4", weight=1.0)

    def calculate_score(self, plate_number: str) -> ScoreResult:
        digits = self.extract_digits(plate_number)
        count_4 = digits.count('4')

        if count_4 == 0:
            return ScoreResult(self.name, 10 * self.weight, "无数字4 (+10)")
        else:
            penalty = count_4 * 5
            return ScoreResult(self.name, -penalty * self.weight,
                             f"含有{count_4}个数字4 (-{penalty})")


class Rule2_ConsecutiveRepeats(ScoringRule):
    """规则2: 连续重复的数字评分高，重复越多评分越高"""

    def __init__(self):
        super().__init__("连续重复数字", weight=1.0)

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
            score = (max_repeat - 1) * 15  # 2连得15分，3连得30分，以此类推
            return ScoreResult(self.name, score * self.weight,
                             f"连续{max_repeat}个{repeat_digit} (+{score})")
        else:
            return ScoreResult(self.name, 0, "无连续重复")


class Rule3_Lucky68(ScoringRule):
    """规则3: 含有6/8的评分高"""

    def __init__(self):
        super().__init__("吉祥数字6/8", weight=1.0)

    def calculate_score(self, plate_number: str) -> ScoreResult:
        digits = self.extract_digits(plate_number)
        count_6 = digits.count('6')
        count_8 = digits.count('8')

        total_count = count_6 + count_8

        if total_count == 0:
            return ScoreResult(self.name, 0, "无6或8")
        else:
            score = total_count * 8
            details = []
            if count_6 > 0:
                details.append(f"{count_6}个6")
            if count_8 > 0:
                details.append(f"{count_8}个8")
            return ScoreResult(self.name, score * self.weight,
                             f"含有{', '.join(details)} (+{score})")


class Rule4_IncreasingSequence(ScoringRule):
    """规则4: 递增序列评分高"""

    def __init__(self):
        super().__init__("递增序列", weight=1.0)

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
            score = (max_sequence - 2) * 20  # 3连得20分，4连得40分
            return ScoreResult(self.name, score * self.weight,
                             f"{max_sequence}位递增序列 (+{score})")
        else:
            return ScoreResult(self.name, 0, "无明显递增序列")


class Rule5_AllEvenOrOdd(ScoringRule):
    """规则5: 全是偶数或者全是奇数评分高"""

    def __init__(self):
        super().__init__("全偶数或全奇数", weight=1.0)

    def calculate_score(self, plate_number: str) -> ScoreResult:
        digits = self.extract_digits(plate_number)

        if len(digits) < 3:
            return ScoreResult(self.name, 0, "数字不足")

        digit_nums = [int(d) for d in digits]

        all_even = all(d % 2 == 0 for d in digit_nums)
        all_odd = all(d % 2 == 1 for d in digit_nums)

        if all_even:
            score = 25
            return ScoreResult(self.name, score * self.weight,
                             f"全部{len(digits)}位为偶数 (+{score})")
        elif all_odd:
            score = 25
            return ScoreResult(self.name, score * self.weight,
                             f"全部{len(digits)}位为奇数 (+{score})")
        else:
            return ScoreResult(self.name, 0, "奇偶混合")


class Rule6_AllPrimes(ScoringRule):
    """规则6: 全是质数评分高"""

    def __init__(self):
        super().__init__("全质数", weight=1.0)

    def calculate_score(self, plate_number: str) -> ScoreResult:
        digits = self.extract_digits(plate_number)

        if len(digits) < 3:
            return ScoreResult(self.name, 0, "数字不足")

        primes = {'2', '3', '5', '7'}
        digit_list = list(digits)

        prime_count = sum(1 for d in digit_list if d in primes)
        all_prime = all(d in primes for d in digit_list)

        if all_prime:
            score = 30
            return ScoreResult(self.name, score * self.weight,
                             f"全部{len(digits)}位为质数 (+{score})")
        elif prime_count >= len(digits) * 0.6:  # 超过60%是质数
            score = 10
            return ScoreResult(self.name, score * self.weight,
                             f"{prime_count}/{len(digits)}位为质数 (+{score})")
        else:
            return ScoreResult(self.name, 0, f"仅{prime_count}位质数")


class Rule7_SpecialLetters(ScoringRule):
    """规则7: 含有MJTQ这几个字母的评分高"""

    def __init__(self):
        super().__init__("特殊字母MJTQ", weight=1.0)

    def calculate_score(self, plate_number: str) -> ScoreResult:
        letters = self.extract_letters(plate_number).upper()
        special_letters = set('MJTQ')

        found_letters = [l for l in letters if l in special_letters]

        if not found_letters:
            return ScoreResult(self.name, 0, "无特殊字母")
        else:
            score = len(found_letters) * 12
            return ScoreResult(self.name, score * self.weight,
                             f"含有字母{', '.join(found_letters)} (+{score})")


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


def create_default_scorer() -> PlateScorer:
    """创建带有默认规则的评分器"""
    scorer = PlateScorer()

    # 添加所有默认规则
    scorer.add_rule(Rule1_NoFour())
    scorer.add_rule(Rule2_ConsecutiveRepeats())
    scorer.add_rule(Rule3_Lucky68())
    scorer.add_rule(Rule4_IncreasingSequence())
    scorer.add_rule(Rule5_AllEvenOrOdd())
    scorer.add_rule(Rule6_AllPrimes())
    scorer.add_rule(Rule7_SpecialLetters())

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
