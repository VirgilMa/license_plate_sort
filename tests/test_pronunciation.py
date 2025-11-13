"""测试读音顺口规则"""
from plate_scorer import create_default_scorer

scorer = create_default_scorer()

test_plates = [
    'CD168',   # 一路发
    'CD520',   # 我爱你
    'CD888',   # 发发发
    'CDM6789', # 路起发 + 起发久
    'CD1357',  # 无顺口组合，但音调变化
    'CDP666',  # 六六大顺
    'CD518',   # 我要发
    'CD2468',  # 全偶数，音调变化
]

print("=" * 100)
print("测试读音顺口规则")
print("=" * 100)

for plate in test_plates:
    total_score, details = scorer.score_plate(plate)

    # 找出读音顺口规则的评分
    pronunciation_detail = None
    for detail in details:
        if detail.rule_name == "读音顺口":
            pronunciation_detail = detail
            break

    if pronunciation_detail and pronunciation_detail.score > 0:
        print(f"{plate:10s} | 总分: {total_score:6.1f} | 读音顺口: {pronunciation_detail.reason}")
    else:
        print(f"{plate:10s} | 总分: {total_score:6.1f} | 读音顺口: 无加分")
