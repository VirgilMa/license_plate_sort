"""测试模式规则: AABB、回文、ABAB"""

from plate_scorer import create_default_scorer

scorer = create_default_scorer()

test_plates = [
    "CD1122",  # AABB模式
    "CD5566",  # AABB模式
    "CD121",  # 回文数字
    "CD1221",  # 回文数字
    "CDM12321",  # 完整回文数字
    "CD1212",  # ABAB模式
    "CD3434",  # ABAB模式
    "CD112233",  # 多个AABB模式
    "CDP1331",  # 回文数字1331
    "CD7878",  # ABAB模式
]

print("=" * 100)
print("测试模式规则: AABB、回文、ABAB")
print("=" * 100)

for plate in test_plates:
    total_score, details = scorer.score_plate(plate)

    # 找出模式相关规则的评分
    pattern_details = []
    for detail in details:
        if (
            detail.rule_name in ["AABB模式", "回文数字", "ABAB模式"]
            and detail.score > 0
        ):
            pattern_details.append(f"{detail.rule_name}: {detail.reason}")

    if pattern_details:
        patterns_str = " | ".join(pattern_details)
        print(f"{plate:10s} | 总分: {total_score:6.1f} | {patterns_str}")
    else:
        print(f"{plate:10s} | 总分: {total_score:6.1f} | 无模式加分")
