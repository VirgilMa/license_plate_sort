# 车牌识别与评分系统

智能车牌选号助手：自动识别图片中的车牌号码并根据多维度规则进行评分排序。

## 功能特点

- **自动识别**: 使用 OCR 技术从图片中识别车牌号码
- **智能评分**: 基于多条可配置规则对车牌进行评分
- **灵活扩展**: 支持自定义添加新的评分规则
- **详细报告**: 显示每个车牌的总分和各规则的得分详情
- **排序推荐**: 自动按分数从高到低排序，推荐最优选择

## 目录结构

```
license_plate/
├── analyze_plates.py          # 主程序：识别图片并评分
├── plate_scorer.py            # 评分系统核心引擎
├── add_custom_rule.py         # 自定义规则示例
├── scoring_rules.json         # 规则配置文件
├── requirements.txt           # 依赖包列表
└── README.md                  # 本文档
```

## 快速开始

### 1. 安装依赖

```bash
pip install easyocr opencv-python numpy Pillow
```

或安装所有依赖：
```bash
pip install -r requirements.txt
```

### 2. 运行识别和评分

```bash
python analyze_plates.py <图片路径> [输出文件.txt]
```

**示例：**
```bash
python analyze_plates.py screenshot.jpg result.txt
```

### 3. 查看结果

程序会在控制台输出评分结果，格式如下：

```
车牌评分结果（按分数从高到低排序）:
====================================================================================================
 1. CDM88888      | 总分:   73.0 | 连续重复数字: 连续7个8 (+90) | 吉祥数字6/8: 含有5个8 (+40)
 2. CDQ2357       | 总分:   55.0 | 全质数: 全部4位为质数 (+30) | 特殊字母MJTQ: 含有字母Q (+12)
 3. CDP6789       | 总分:   52.0 | 递增序列: 4位递增序列 (+40) | 吉祥数字6/8: 含有1个6, 1个8 (+16)
```

## 评分规则说明

### 当前内置规则（7条）

| 规则 | 说明 | 评分逻辑 |
|------|------|---------|
| **1. 避免数字4** | 含有4的评分低 | 无4: +10分<br>每个4: -5分 |
| **2. 连续重复数字** | 连续重复越多评分越高 | 2连: +15分<br>3连: +30分<br>4连: +45分 |
| **3. 吉祥数字6/8** | 含有6或8的评分高 | 每个6/8: +8分 |
| **4. 递增序列** | 递增序列评分高 | 3位递增: +20分<br>4位递增: +40分 |
| **5. 全偶数或全奇数** | 全偶数或全奇数 | 符合: +25分 |
| **6. 全质数** | 全是质数(2,3,5,7) | 全质数: +30分<br>60%以上质数: +10分 |
| **7. 特殊字母MJTQ** | 含有M/J/T/Q字母 | 每个字母: +12分 |

### 规则组合示例

- `CD88888`: 连续7个8 (+90) + 5个8 (+40) = **130分**
- `CDM2357`: 全质数 (+30) + 递增序列 (+20) + 特殊字母M (+12) = **62分**
- `CDP4444`: 连续4个4 (+45) - 4个4 (-20) = **25分**

## 添加自定义规则

### 方法1: 编程方式添加

创建新的规则类，继承自 `ScoringRule`：

```python
from plate_scorer import ScoringRule, ScoreResult

class Rule8_MyCustomRule(ScoringRule):
    """我的自定义规则"""

    def __init__(self):
        super().__init__("规则名称", weight=1.0)

    def calculate_score(self, plate_number: str) -> ScoreResult:
        # 提取数字部分
        digits = self.extract_digits(plate_number)

        # 实现评分逻辑
        score = 0
        reason = ""

        # ... 你的评分逻辑 ...

        return ScoreResult(self.name, score * self.weight, reason)
```

然后添加到评分器：

```python
from plate_scorer import create_default_scorer

scorer = create_default_scorer()
scorer.add_rule(Rule8_MyCustomRule())
```

### 方法2: 使用示例模板

查看 `add_custom_rule.py` 文件，其中包含多个自定义规则示例：

- **避免数字7**: 不喜欢数字7
- **回文数字**: 对称数字（如12321）
- **数字和能被10整除**: 数字之和是10的倍数
- **递减序列**: 数字递减（如987）
- **特殊模式**: AABB, ABAB, ABC等模式

运行示例：
```bash
python add_custom_rule.py
```

## 高级用法

### 调整规则权重

```python
from plate_scorer import create_default_scorer, Rule3_Lucky68

scorer = create_default_scorer()

# 修改规则权重
for rule in scorer.rules:
    if isinstance(rule, Rule3_Lucky68):
        rule.weight = 2.0  # 吉祥数字权重加倍
```

### 禁用某个规则

```python
scorer = create_default_scorer()
scorer.remove_rule("避免数字4")  # 移除该规则
```

### 仅使用特定规则

```python
from plate_scorer import PlateScorer, Rule2_ConsecutiveRepeats, Rule3_Lucky68

scorer = PlateScorer()
scorer.add_rule(Rule2_ConsecutiveRepeats())
scorer.add_rule(Rule3_Lucky68())
```

## 评分系统设计

### 核心架构

```
analyze_plates.py (主程序)
    ↓
    ├─ OCR识别车牌
    │   ├─ EasyOCR (优先)
    │   └─ Tesseract (备用)
    ↓
plate_scorer.py (评分引擎)
    ↓
    ├─ ScoringRule (抽象基类)
    │   ├─ Rule1_NoFour
    │   ├─ Rule2_ConsecutiveRepeats
    │   ├─ Rule3_Lucky68
    │   ├─ Rule4_IncreasingSequence
    │   ├─ Rule5_AllEvenOrOdd
    │   ├─ Rule6_AllPrimes
    │   └─ Rule7_SpecialLetters
    ↓
    └─ PlateScorer
        ├─ add_rule()      # 添加规则
        ├─ remove_rule()   # 移除规则
        └─ score_plate()   # 计算评分
```

### 扩展性设计

1. **规则独立性**: 每个规则是独立的类，互不影响
2. **可配置权重**: 每个规则可设置权重系数
3. **详细报告**: 返回每条规则的得分和原因
4. **灵活组合**: 可以自由添加/移除规则

## 性能优化

### 识别速度优化

如果图片很大，可以降低分辨率加快识别：

```python
# 在 analyze_plates.py 中修改
img = cv2.imread(image_path)
img = cv2.resize(img, None, fx=0.5, fy=0.5)  # 缩小一半
```

### 内存优化

EasyOCR 首次运行会下载模型（约100MB），后续会缓存。如果内存不足，可以：

```python
reader = easyocr.Reader(['en'], gpu=False, verbose=False)  # 只使用英文
```

## 常见问题

### Q: 识别不准确怎么办？

A:
1. 确保图片清晰，分辨率足够
2. 车牌文字与背景对比度要好
3. 尝试裁剪图片只保留车牌区域
4. 调整图片亮度和对比度

### Q: 如何修改评分标准？

A:
1. 修改 `plate_scorer.py` 中各规则的评分逻辑
2. 调整规则权重 `rule.weight = 2.0`
3. 编辑 `scoring_rules.json` 配置文件

### Q: 能识别哪些格式的车牌？

A: 目前主要识别中国车牌格式：
- 标准格式: 2-3个字母 + 4-5位数字/字母
- 示例: CDP5747, CDL3034, CA74475

### Q: 如何只测试评分而不识别？

A: 直接使用评分器：

```python
from plate_scorer import create_default_scorer

scorer = create_default_scorer()
total, details = scorer.score_plate("CDP8888")

for detail in details:
    if detail.score != 0:
        print(f"{detail.rule_name}: {detail.reason}")
```

## 评分建议规则示例

以下是一些可以添加的规则建议：

1. **生日数字**: 包含特定日期的车牌加分
2. **谐音吉祥**: 168、888、666等组合
3. **避免不吉利数字**: 如444、13等
4. **易记性**: 对称、规律性强的数字
5. **字母意义**: 特定字母组合（如VIP）
6. **数字和**: 数字和为吉利数字
7. **平衡性**: 数字分布均匀
8. **稀有度**: 号码的独特性

## 技术栈

- **Python 3.7+**
- **EasyOCR**: 深度学习OCR引擎（推荐）
- **Tesseract**: 传统OCR引擎（备用）
- **OpenCV**: 图像处理
- **NumPy**: 数值计算

## 更新日志

### v1.0 (2025-11-13)
- 初始版本
- 实现7条基础评分规则
- 支持 EasyOCR 和 Tesseract 双引擎
- 可扩展的规则系统架构

## 开发者指南

### 添加新规则步骤

1. 在 `plate_scorer.py` 中创建新的规则类
2. 继承 `ScoringRule` 基类
3. 实现 `calculate_score()` 方法
4. 在 `create_default_scorer()` 中注册规则

### 代码风格

- 遵循 PEP 8 规范
- 使用类型注解
- 添加详细的文档字符串
- 单元测试覆盖

## 许可证

本项目为个人使用工具，欢迎修改和扩展。

## 联系与反馈

如有问题或建议，欢迎反馈！

---

**祝您选到心仪的车牌号！** 🚗
