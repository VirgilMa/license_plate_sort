"""
自定义评分规则示例
展示如何添加新的评分规则
"""

from plate_scorer import ScoringRule, ScoreResult, PlateScorer, create_default_scorer


# ==================== 自定义规则示例 ====================

class Rule8_AvoidNumber7(ScoringRule):
    """示例规则8: 避免数字7"""

    def __init__(self):
        super().__init__("避免数字7", weight=1.0)

    def calculate_score(self, plate_number: str) -> ScoreResult:
        digits = self.extract_digits(plate_number)
        count_7 = digits.count('7')

        if count_7 == 0:
            return ScoreResult(self.name, 5 * self.weight, "无数字7 (+5)")
        else:
            penalty = count_7 * 3
            return ScoreResult(self.name, -penalty * self.weight,
                             f"含有{count_7}个数字7 (-{penalty})")


class Rule9_PalindromeNumber(ScoringRule):
    """示例规则9: 回文数字（对称数字）"""

    def __init__(self):
        super().__init__("回文数字", weight=1.0)

    def calculate_score(self, plate_number: str) -> ScoreResult:
        digits = self.extract_digits(plate_number)

        if len(digits) < 3:
            return ScoreResult(self.name, 0, "数字不足")

        if digits == digits[::-1]:
            score = 35
            return ScoreResult(self.name, score * self.weight,
                             f"完美回文 {digits} (+{score})")
        else:
            # 检查部分回文
            for length in range(len(digits), 2, -1):
                for i in range(len(digits) - length + 1):
                    substring = digits[i:i+length]
                    if substring == substring[::-1] and length >= 3:
                        score = (length - 2) * 8
                        return ScoreResult(self.name, score * self.weight,
                                         f"部分回文 {substring} (+{score})")

            return ScoreResult(self.name, 0, "无回文")


class Rule10_SumDivisibleBy(ScoringRule):
    """示例规则10: 数字之和能被特定数整除"""

    def __init__(self, divisor: int = 10):
        super().__init__(f"数字和能被{divisor}整除", weight=1.0)
        self.divisor = divisor

    def calculate_score(self, plate_number: str) -> ScoreResult:
        digits = self.extract_digits(plate_number)

        if not digits:
            return ScoreResult(self.name, 0, "无数字")

        digit_sum = sum(int(d) for d in digits)

        if digit_sum % self.divisor == 0:
            score = 15
            return ScoreResult(self.name, score * self.weight,
                             f"数字和={digit_sum} (+{score})")
        else:
            return ScoreResult(self.name, 0, f"数字和={digit_sum}")


class Rule11_DecreasingSequence(ScoringRule):
    """示例规则11: 递减序列"""

    def __init__(self):
        super().__init__("递减序列", weight=1.0)

    def calculate_score(self, plate_number: str) -> ScoreResult:
        digits = self.extract_digits(plate_number)

        if len(digits) < 2:
            return ScoreResult(self.name, 0, "数字不足")

        max_sequence = 1
        current_sequence = 1

        for i in range(1, len(digits)):
            if int(digits[i]) == int(digits[i - 1]) - 1:
                current_sequence += 1
                max_sequence = max(max_sequence, current_sequence)
            else:
                current_sequence = 1

        if max_sequence >= 3:
            score = (max_sequence - 2) * 18
            return ScoreResult(self.name, score * self.weight,
                             f"{max_sequence}位递减序列 (+{score})")
        else:
            return ScoreResult(self.name, 0, "无递减序列")


class Rule12_SpecificPattern(ScoringRule):
    """示例规则12: 特定数字模式（如AABB, ABAB等）"""

    def __init__(self):
        super().__init__("特殊数字模式", weight=1.0)

    def calculate_score(self, plate_number: str) -> ScoreResult:
        digits = self.extract_digits(plate_number)

        if len(digits) < 4:
            return ScoreResult(self.name, 0, "数字不足")

        # AABB 模式
        if len(digits) >= 4:
            for i in range(len(digits) - 3):
                if (digits[i] == digits[i+1] and
                    digits[i+2] == digits[i+3] and
                    digits[i] != digits[i+2]):
                    score = 25
                    pattern = f"{digits[i]}{digits[i]}{digits[i+2]}{digits[i+3]}"
                    return ScoreResult(self.name, score * self.weight,
                                     f"AABB模式 {pattern} (+{score})")

        # ABAB 模式
        if len(digits) >= 4:
            for i in range(len(digits) - 3):
                if (digits[i] == digits[i+2] and
                    digits[i+1] == digits[i+3] and
                    digits[i] != digits[i+1]):
                    score = 28
                    pattern = f"{digits[i]}{digits[i+1]}{digits[i]}{digits[i+1]}"
                    return ScoreResult(self.name, score * self.weight,
                                     f"ABAB模式 {pattern} (+{score})")

        # ABC 模式（如123, 234, 345）
        if len(digits) >= 3:
            for i in range(len(digits) - 2):
                if (int(digits[i+1]) == int(digits[i]) + 1 and
                    int(digits[i+2]) == int(digits[i+1]) + 1):
                    score = 20
                    pattern = f"{digits[i]}{digits[i+1]}{digits[i+2]}"
                    return ScoreResult(self.name, score * self.weight,
                                     f"ABC模式 {pattern} (+{score})")

        return ScoreResult(self.name, 0, "无特殊模式")


# ==================== 使用示例 ====================

def create_custom_scorer() -> PlateScorer:
    """创建带有自定义规则的评分器"""
    # 首先创建默认评分器
    scorer = create_default_scorer()

    # 添加自定义规则
    scorer.add_rule(Rule8_AvoidNumber7())
    scorer.add_rule(Rule9_PalindromeNumber())
    scorer.add_rule(Rule10_SumDivisibleBy(divisor=10))
    scorer.add_rule(Rule11_DecreasingSequence())
    scorer.add_rule(Rule12_SpecificPattern())

    return scorer


def demo_custom_rules():
    """演示自定义规则"""
    print("自定义规则演示")
    print("=" * 100)

    test_plates = [
        "CDP5747",    # 含有7和4
        "CDM12321",   # 回文数字
        "CDA55555",   # 多个重复
        "CDQ6543",    # 递减序列
        "CDT3366",    # AABB模式
        "CD2828",     # ABAB模式
        "CDM8888",    # 全8
    ]

    # 使用默认规则
    print("\n【默认规则评分】")
    default_scorer = create_default_scorer()
    for plate in test_plates:
        total, details = default_scorer.score_plate(plate)
        print(f"{plate:12s} | 总分: {total:6.1f}")

    # 使用自定义规则
    print("\n\n【添加自定义规则后的评分】")
    custom_scorer = create_custom_scorer()
    for plate in test_plates:
        total, details = custom_scorer.score_plate(plate)
        active_rules = [r for r in details if r.score != 0]
        rules_str = " | ".join([r.reason for r in active_rules])
        print(f"{plate:12s} | 总分: {total:6.1f} | {rules_str}")


if __name__ == "__main__":
    demo_custom_rules()
