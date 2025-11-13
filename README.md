# 车牌识别与评分系统 - 完整使用指南

智能车牌选号助手：自动识别图片中的车牌号码，根据多维度规则进行评分排序，并显示车牌在图中的位置。

---

## 📖 目录

1. [快速开始](#快速开始)
2. [功能特点](#功能特点)
3. [安装依赖](#安装依赖)
4. [基本使用](#基本使用)
5. [配置文件详解](#配置文件详解)
6. [评分规则说明](#评分规则说明)
7. [配置示例](#配置示例)
8. [高级用法](#高级用法)
9. [常见问题](#常见问题)
10. [文件结构](#文件结构)

---

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install easyocr opencv-python numpy Pillow
```

### 2. 准备配置文件

编辑 `scoring_rules.json`，根据个人喜好调整评分（可选）：

```json
{
  "score_weights": {
    "lucky_digit_score": 30,         // 改这里！每个6/8得30分
    "four_penalty_per_count": 15     // 改这里！每个4扣15分
  }
}
```

### 3. 运行识别和评分

```bash
python analyze_plates.py 你的图片.jpg 结果.txt
```

### 4. 查看结果

```
车牌评分结果（按分数从高到低排序）:
========================================================
 1. CDM88888  [第3行第2列] | 总分: 200.0 | 连续重复数字: 连续7个8 (+90) | 吉祥数字6/8: 含有5个8 (+100)
 2. CDQ2357   [第2行第5列] | 总分:  62.0 | 全质数: 全部4位为质数 (+20) | 特殊字母MJTQ: 含有字母Q (+10)
```

---

## ✨ 功能特点

- ✅ **自动识别**: 使用 OCR 技术从图片中识别车牌号码
- ✅ **高准确率**: 图像预处理 + 优化模型 + 字符过滤，提高识别准确率
- ✅ **自动定位**: 自动检测车牌的行列布局，无需手动配置（左上角为第1行第1列）
- ✅ **智能评分**: 基于7条可配置规则对车牌进行评分
- ✅ **直接调分**: 在配置文件中直接修改具体分数值
- ✅ **灵活扩展**: 支持自定义添加新的评分规则
- ✅ **详细报告**: 显示每个车牌的总分和各规则的得分详情
- ✅ **排序推荐**: 自动按分数从高到低排序，推荐Top 5

---

## 📦 安装依赖

### 方法1：安装推荐引擎（EasyOCR）

```bash
pip install easyocr opencv-python numpy Pillow
```

**优点**：识别准确率高，支持中文

### 方法2：安装备用引擎（Tesseract）

```bash
pip install pytesseract opencv-python numpy Pillow
```

然后安装 Tesseract OCR 引擎：
- Windows: 从 https://github.com/UB-Mannheim/tesseract/wiki 下载安装

### 方法3：安装所有依赖

```bash
pip install -r requirements.txt
```

---

## 📝 基本使用

### 命令行运行

```bash
# 基本用法
python analyze_plates.py <图片路径>

# 保存结果到文件
python analyze_plates.py <图片路径> <输出文件.txt>

# 示例
python analyze_plates.py screenshot.jpg result.txt
```

### 输出内容

1. **识别过程**：显示识别到的车牌数量和位置
2. **评分结果**：每个车牌的总分、位置和评分详情
3. **统计信息**：最高分、最低分、平均分
4. **Top 5推荐**：分数最高的5个车牌

---

## ⚙️ 配置文件详解

配置文件 `scoring_rules.json` 包含两部分：

### 一、规则启用配置

控制每条规则是否启用以及权重系数。

```json
{
  "rules": [
    {
      "name": "吉祥数字6/8",
      "enabled": true,       // true=启用，false=禁用
      "weight": 1.0,         // 权重系数（可选，一般保持1.0）
      "description": "含有6或8的评分高"
    }
  ]
}
```

**禁用某个规则**：

```json
{
  "name": "全质数",
  "enabled": false      // 禁用该规则
}
```

### 二、分数配置（重点）

**直接设置每条规则的具体分数值，改这里最直观！**

```json
{
  "score_weights": {
    // 规则1: 避免数字4
    "no_four_bonus": 10,              // 无4奖励：10分
    "four_penalty_per_count": 10,     // 每个4扣分：10分

    // 规则2: 连续重复数字
    "repeat_base_score": 15,          // 连号基础分：2连15分，3连30分

    // 规则3: 吉祥数字6/8
    "lucky_digit_score": 20,          // 每个6/8：20分

    // 规则4: 递增序列
    "sequence_base_score": 20,        // 递增基础分：3连20分，4连40分

    // 规则5: 全偶数或全奇数
    "all_even_odd_score": 20,         // 全偶/奇：20分

    // 规则6: 全质数
    "all_prime_score": 20,            // 全质数：20分
    "mostly_prime_score": 10,         // 大部分质数：10分

    // 规则7: 特殊字母MJTQ
    "special_letter_score": 10        // 每个特殊字母：10分
  }
}
```

---

## 📊 评分规则说明

### 规则1: 避免数字4

```json
"no_four_bonus": 10,              // 无4奖励
"four_penalty_per_count": 10      // 每个4扣分
```

**示例**：
- `CD88888`: 无4 → +10分
- `CDP4444`: 4个4 → -40分

---

### 规则2: 连续重复数字

```json
"repeat_base_score": 15           // 基础分
```

**计算公式**：`(连续数量 - 1) × repeat_base_score`

**示例**（基础分15）：
- `CD88888`: 7个连续的8 → (7-1)×15 = **90分**
- `CDP5555`: 4个连续的5 → (4-1)×15 = **45分**
- `CD6677`: 2个连续的6 → (2-1)×15 = **15分**

---

### 规则3: 吉祥数字6/8

```json
"lucky_digit_score": 20           // 每个6或8
```

**计算公式**：`(6的数量 + 8的数量) × lucky_digit_score`

**示例**（每个20分）：
- `CD88888`: 5个8 → 5×20 = **100分**
- `CD6789`: 1个6+1个8 → 2×20 = **40分**
- `CDM6666`: 4个6 → 4×20 = **80分**

---

### 规则4: 递增序列

```json
"sequence_base_score": 20         // 基础分
```

**计算公式**：`(序列长度 - 2) × sequence_base_score`

**示例**（基础分20）：
- `CDM6789`: 4位递增 → (4-2)×20 = **40分**
- `CD123`: 3位递增 → (3-2)×20 = **20分**

**注意**：只统计最长连续递增序列，至少3位才算。

---

### 规则5: 全偶数或全奇数

```json
"all_even_odd_score": 20          // 全偶/奇分数
```

**示例**：
- `CD2468`: 全偶数 → **20分**
- `CD1357`: 全奇数 → **20分**
- `CD2467`: 奇偶混合 → 0分

---

### 规则6: 全质数

```json
"all_prime_score": 20,            // 全质数
"mostly_prime_score": 10          // 60%以上质数
```

**示例**：
- `CDQ2357`: 全是质数(2,3,5,7) → **20分**
- `CD2348`: 3个质数，占75% → **10分**

---

### 规则7: 特殊字母MJTQ

```json
"special_letter_score": 10        // 每个特殊字母
```

**计算公式**：`特殊字母数量 × special_letter_score`

**示例**（每个10分）：
- `CDM8888`: 有M → 1×10 = **10分**
- `CDQ2357`: 有Q → 1×10 = **10分**
- `CDMJ888`: 有M和J → 2×10 = **20分**

---

## 🎯 配置示例

### 示例1：偏好吉祥数字（推荐6/8，严惩4）

```json
{
  "rules": [
    {"name": "避免数字4", "enabled": true, "weight": 1.0},
    {"name": "连续重复数字", "enabled": true, "weight": 1.0},
    {"name": "吉祥数字6/8", "enabled": true, "weight": 1.0},
    {"name": "递增序列", "enabled": false},
    {"name": "全偶数或全奇数", "enabled": false},
    {"name": "全质数", "enabled": false},
    {"name": "特殊字母MJTQ", "enabled": true, "weight": 1.0}
  ],
  "score_weights": {
    "no_four_bonus": 15,
    "four_penalty_per_count": 20,    // 严惩4
    "repeat_base_score": 20,
    "lucky_digit_score": 30,         // 大幅提高6/8
    "special_letter_score": 15
  }
}
```

**效果**：
- `CD88888`: 超高分（连号90 + 吉祥150 = 240分）
- `CDP4444`: 很低分（连号45 - 扣分80 = -35分）

---

### 示例2：偏好规律性（连号、递增）

```json
{
  "rules": [
    {"name": "避免数字4", "enabled": true, "weight": 1.0},
    {"name": "连续重复数字", "enabled": true, "weight": 1.0},
    {"name": "吉祥数字6/8", "enabled": true, "weight": 1.0},
    {"name": "递增序列", "enabled": true, "weight": 1.0},
    {"name": "全偶数或全奇数", "enabled": true, "weight": 1.0},
    {"name": "全质数", "enabled": false},
    {"name": "特殊字母MJTQ", "enabled": false}
  ],
  "score_weights": {
    "no_four_bonus": 10,
    "four_penalty_per_count": 10,
    "repeat_base_score": 25,         // 提高连号
    "lucky_digit_score": 15,
    "sequence_base_score": 30,       // 提高递增
    "all_even_odd_score": 25
  }
}
```

**效果**：
- `CD5555`: 高分（连号75分）
- `CD1234`: 高分（递增60分）

---

### 示例3：均衡配置（默认推荐）

```json
{
  "score_weights": {
    "no_four_bonus": 10,
    "four_penalty_per_count": 10,
    "repeat_base_score": 15,
    "lucky_digit_score": 20,
    "sequence_base_score": 20,
    "all_even_odd_score": 20,
    "all_prime_score": 20,
    "mostly_prime_score": 10,
    "special_letter_score": 10
  }
}
```

**效果**：综合考虑各种因素，平衡选号。

---

## 🔧 高级用法

### 1. 调整车牌位置网格

**位置逻辑**：左上角为第1行第1列，向右递增列号，向下递增行号。

如果位置显示不准确，修改 `analyze_plates.py` 中的网格参数：

```python
# 在 calculate_grid_position 函数中（约第40-41行）
cols = 5  # 改为实际列数（从左到右有几列）
rows = 6  # 改为实际行数（从上到下有几行）
```

**示例**：
- 如果车牌排列是 4列×8行，改为 `cols = 4` 和 `rows = 8`
- 左上角第一个 = 第1行第1列
- 右上角最后一个 = 第1行第4列（4列的情况）

### 2. 添加自定义规则

查看 `add_custom_rule.py` 文件，其中包含多个自定义规则示例：

```python
from plate_scorer import ScoringRule, ScoreResult

class Rule8_MyRule(ScoringRule):
    """我的自定义规则"""

    def __init__(self, my_score: float = 20):
        super().__init__("我的规则", weight=1.0)
        self.my_score = my_score

    def calculate_score(self, plate_number: str) -> ScoreResult:
        # 实现评分逻辑
        digits = self.extract_digits(plate_number)

        # 你的评分逻辑...
        score = self.my_score if 某个条件 else 0

        return ScoreResult(self.name, score, "原因说明")
```

### 3. 批量处理多张图片

创建批处理脚本：

```python
import os
from analyze_plates import analyze_and_score_plates

image_folder = "screenshots"
output_folder = "results"

for filename in os.listdir(image_folder):
    if filename.endswith(('.jpg', '.png')):
        image_path = os.path.join(image_folder, filename)
        output_path = os.path.join(output_folder, f"{filename}_result.txt")
        analyze_and_score_plates(image_path, output_path)
```

### 4. 只测试评分（不识别）

```python
from plate_scorer import create_default_scorer

scorer = create_default_scorer()

# 测试单个车牌
total, details = scorer.score_plate("CDP8888")
print(f"总分: {total}")

for detail in details:
    if detail.score != 0:
        print(f"{detail.rule_name}: {detail.reason}")
```

---

## ❓ 常见问题

### Q1: 如何调整评分？

**A**: 直接修改 `scoring_rules.json` 中的 `score_weights` 部分：

```json
"lucky_digit_score": 30,         // 改这里！
"four_penalty_per_count": 15     // 改这里！
```

改完后直接运行，立即生效，无需修改代码。

---

### Q2: 车牌位置显示不准确怎么办？

**A**: 系统会**自动检测**车牌的行列布局，无需手动配置！

**位置逻辑**：
- 自动识别车牌的行（Y坐标相近的为同一行）
- 每行内按X坐标从左到右排序确定列号
- 左上角为第1行第1列，向右递增列号，向下递增行号

**如果位置仍不准确**，可能原因：
1. **车牌间距过小或过大** → 调整行识别阈值（`analyze_plates.py` 第49行）
   ```python
   row_threshold = 50  # 默认50像素，可以改为30-100
   ```
2. **车牌排列不规则** → 系统会尽量识别，但不规则布局可能不准确

**位置说明**：
- 第1行第1列 = 左上角第一个车牌
- 第1行第2列 = 第1行中从左数第二个
- 第2行第1列 = 第2行中最左边的车牌

---

### Q3: 某个车牌没被识别？或者识别不准确？

**A**: 系统已经做了以下优化：

**内置优化**：
1. ✅ 图像预处理（灰度化、对比度增强、二值化）
2. ✅ 只使用英文模型（不加载中文，更准确识别字母数字）
3. ✅ 限制字符集为大写字母和数字（提高准确率）
4. ✅ 优化识别参数（更严格的阈值）

**如果仍有问题**：

1. **图片不清晰** → 提高图片分辨率或截图更清晰的部分
2. **对比度低** → 调整图片亮度和对比度
3. **车牌格式不符** → 检查车牌格式是否为：2-3个字母 + 4-5位数字
4. **混淆字符** → 常见混淆：O和0、I和1、Z和2、S和5
   - 系统已自动过滤特殊字符，只保留字母和数字

---

### Q4: 如何禁用某个规则？

**A**: 在配置文件中设置 `enabled: false`：

```json
{
  "name": "全质数",
  "enabled": false      // 禁用
}
```

---

### Q5: weight 和 score_weights 有什么区别？

**A**:
- **`score_weights`**（推荐）：直接设置具体分数，如 `"lucky_digit_score": 30` 表示每个6/8得30分
- **`weight`**（可选）：权重系数，如 `"weight": 2.0` 表示该规则最终得分乘以2

**推荐使用 `score_weights` 直接改分数，更直观！**

---

### Q6: 如何测试不同的配置？

**A**: 创建多个配置文件：

```bash
# 保存当前配置
cp scoring_rules.json scoring_rules_backup.json

# 修改配置
# 编辑 scoring_rules.json

# 运行测试
python analyze_plates.py image.jpg

# 恢复原配置
cp scoring_rules_backup.json scoring_rules.json
```

---

### Q7: 识别速度慢怎么办？

**A**: 降低图片分辨率：

```python
# 在 recognize_plates_from_image 函数中（约第75行后添加）
img = cv2.imread(image_path)
img = cv2.resize(img, None, fx=0.5, fy=0.5)  # 缩小一半
```

---

## 📁 文件结构

```
license_plate/
├── analyze_plates.py          # 主程序：识别+评分
├── plate_scorer.py            # 评分引擎核心
├── scoring_rules.json         # 配置文件（重点）
├── add_custom_rule.py         # 自定义规则示例
├── requirements.txt           # 依赖列表
└── 使用指南.md                # 本文档
```

### 核心文件说明

| 文件 | 作用 | 是否需要修改 |
|------|------|------------|
| `analyze_plates.py` | 主程序 | 一般不需要 |
| `plate_scorer.py` | 评分引擎 | 一般不需要 |
| **`scoring_rules.json`** | **配置文件** | **需要修改** ⭐ |
| `add_custom_rule.py` | 自定义规则示例 | 可选 |

---

## 🎓 调整建议

### 步骤1：确定优先级

问自己以下问题：
1. **最看重什么？** 吉祥数字？连号？递增？
2. **最忌讳什么？** 数字4？
3. **无所谓的因素？** 质数？奇偶？

### 步骤2：设置分数

根据优先级设置分数：
- **高优先级**：分数设为 20-30
- **中优先级**：分数设为 10-15
- **低优先级**：分数设为 5 或禁用规则

### 步骤3：测试验证

运行程序测试几个车牌，看评分是否符合预期：

```bash
python plate_scorer.py
```

查看输出，根据需要调整分数。

---

## 🌟 快速参考卡

### 修改分数（推荐）

```json
"lucky_digit_score": 30      // 每个6/8得30分
```

### 禁用规则

```json
{"name": "全质数", "enabled": false}
```

### 运行程序

```bash
python analyze_plates.py 图片.jpg [输出.txt]
```

### 查看位置信息

```
输出格式: 车牌号 [第X行第Y列] | 总分 | 评分详情
```

---

## 📊 你的当前配置

根据你修改的 `scoring_rules.json`：

| 项目 | 原始值 | 当前值 | 变化 |
|------|--------|--------|------|
| `four_penalty_per_count` | 5 | **10** | ⬆️ 加倍 |
| `lucky_digit_score` | 8 | **20** | ⬆️ +150% |
| `all_even_odd_score` | 25 | **20** | ⬇️ -20% |
| `all_prime_score` | 30 | **20** | ⬇️ -33% |
| `special_letter_score` | 12 | **10** | ⬇️ -17% |

**你的配置特点**：
- ✅ 大幅提升吉祥数字6/8的重要性
- ✅ 加强对数字4的惩罚
- ✅ 平衡其他规则以保持整体合理性

**预期效果**：
- 含6/8的车牌会**明显优先**
- 含4的车牌会被**严格过滤**
- 整体偏好**传统吉祥数字**

---

## 🎉 总结

### 核心优势

1. **直接改分数** - 在 `scoring_rules.json` 中直接修改，无需改代码
2. **显示位置** - 自动显示车牌在图中的位置（第几行第几列）
3. **灵活配置** - 7条规则，可启用/禁用/调整分数
4. **详细报告** - 每个车牌显示总分和评分详情
5. **易于扩展** - 支持添加自定义评分规则

### 使用流程

```
准备图片 → 调整配置（可选）→ 运行程序 → 查看结果 → 选择车牌
```

### 关键配置

**修改这里最有效**：

```json
{
  "score_weights": {
    "lucky_digit_score": 30,         // 改这个！
    "four_penalty_per_count": 15,    // 改这个！
    "repeat_base_score": 20          // 改这个！
  }
}
```

---

**祝您选到心仪的车牌号！** 🚗✨

如有问题，请参考本文档的常见问题部分，或查看示例代码 `add_custom_rule.py`。
