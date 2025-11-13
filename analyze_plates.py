"""
车牌识别与评分主程序
输入图片地址，自动识别车牌并进行评分排序
"""

import sys
import os
from typing import List, Tuple
from plate_scorer import create_default_scorer, format_score_report


def recognize_plates_from_image(image_path: str) -> List[str]:
    """
    从图片中识别车牌号码

    参数:
        image_path: 图片路径

    返回:
        车牌号码列表
    """
    try:
        import easyocr
        import cv2
        import numpy as np

        print(f"正在识别图片: {image_path}")
        print("初始化 EasyOCR...")

        # 初始化 EasyOCR
        reader = easyocr.Reader(['ch_sim', 'en'], gpu=False, verbose=False)

        # 识别文本
        results = reader.readtext(image_path)

        plates = []
        print(f"\n识别到 {len(results)} 个文本区域")

        for (bbox, text, confidence) in results:
            # 清理文本
            text_clean = text.replace(' ', '').replace('\n', '').upper()

            # 简单的车牌格式验证
            if is_likely_plate(text_clean):
                plates.append(text_clean)
                print(f"  - {text_clean:15s} (置信度: {confidence:.2%})")

        return plates

    except ImportError:
        print("错误: 未安装 easyocr，尝试使用 pytesseract...")
        return recognize_plates_tesseract(image_path)


def recognize_plates_tesseract(image_path: str) -> List[str]:
    """使用 Tesseract OCR 识别车牌（备用方案）"""
    try:
        import pytesseract
        from PIL import Image
        import re

        print("使用 Tesseract OCR 进行识别...")

        img = Image.open(image_path)
        custom_config = r'--oem 3 --psm 6 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
        text = pytesseract.image_to_string(img, config=custom_config, lang='eng')

        # 使用正则表达式提取车牌模式
        pattern = r'[A-Z]{2,3}[A-Z0-9]{4,5}'
        plates = re.findall(pattern, text)

        plates = list(set(plates))  # 去重
        print(f"识别到 {len(plates)} 个车牌")
        for plate in plates:
            print(f"  - {plate}")

        return plates

    except ImportError:
        print("错误: 未安装 pytesseract")
        print("请安装: pip install easyocr 或 pip install pytesseract")
        return []


def is_likely_plate(text: str) -> bool:
    """判断文本是否可能是车牌"""
    import re

    # 移除非字母数字字符
    text = re.sub(r'[^A-Z0-9]', '', text.upper())

    # 长度检查
    if len(text) < 5 or len(text) > 8:
        return False

    # 必须包含字母和数字
    has_letter = any(c.isalpha() for c in text)
    has_digit = any(c.isdigit() for c in text)

    if not (has_letter and has_digit):
        return False

    # 匹配常见车牌模式
    patterns = [
        r'^[A-Z]{2,3}[A-Z0-9]{4,5}$',
        r'^[A-Z]{2}[0-9]{4,5}$',
        r'^[A-Z]{3}[0-9]{4}$',
    ]

    for pattern in patterns:
        if re.match(pattern, text):
            return True

    # 宽松匹配：字母数字混合且格式合理
    if 2 <= len([c for c in text if c.isalpha()]) <= 4:
        return True

    return False


def analyze_and_score_plates(image_path: str, output_file: str = None):
    """
    分析图片中的车牌并评分排序

    参数:
        image_path: 图片路径
        output_file: 可选的输出文件路径
    """
    print("=" * 100)
    print("车牌识别与评分系统")
    print("=" * 100)

    # 检查文件是否存在
    if not os.path.exists(image_path):
        print(f"错误: 文件不存在 - {image_path}")
        return

    # 识别车牌
    plates = recognize_plates_from_image(image_path)

    if not plates:
        print("\n未识别到车牌号码")
        return

    print(f"\n成功识别 {len(plates)} 个车牌号码")
    print("=" * 100)

    # 创建评分器
    scorer = create_default_scorer()

    # 评分
    scored_plates = []
    for plate in plates:
        total_score, details = scorer.score_plate(plate)
        scored_plates.append((plate, total_score, details))

    # 按分数从高到低排序
    scored_plates.sort(key=lambda x: x[1], reverse=True)

    # 输出结果
    print("\n车牌评分结果（按分数从高到低排序）:")
    print("=" * 100)

    output_lines = []
    for rank, (plate, total_score, details) in enumerate(scored_plates, 1):
        report = f"{rank:2d}. {format_score_report(plate, total_score, details)}"
        print(report)
        output_lines.append(report)

    # 保存到文件
    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("车牌评分结果\n")
            f.write("=" * 100 + "\n")
            f.write(f"图片: {image_path}\n")
            f.write(f"识别到 {len(plates)} 个车牌\n")
            f.write("=" * 100 + "\n\n")
            for line in output_lines:
                f.write(line + "\n")
        print(f"\n结果已保存到: {output_file}")

    # 统计信息
    print("\n" + "=" * 100)
    print("评分统计:")
    print(f"  最高分: {scored_plates[0][1]:.1f} ({scored_plates[0][0]})")
    print(f"  最低分: {scored_plates[-1][1]:.1f} ({scored_plates[-1][0]})")
    avg_score = sum(s[1] for s in scored_plates) / len(scored_plates)
    print(f"  平均分: {avg_score:.1f}")

    # 推荐
    print("\n推荐选择:")
    top_5 = scored_plates[:min(5, len(scored_plates))]
    for i, (plate, score, _) in enumerate(top_5, 1):
        print(f"  {i}. {plate} (分数: {score:.1f})")


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("用法: python analyze_plates.py <图片路径> [输出文件路径]")
        print("示例: python analyze_plates.py screenshot.jpg result.txt")
        sys.exit(1)

    image_path = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None

    try:
        analyze_and_score_plates(image_path, output_file)
    except Exception as e:
        print(f"\n发生错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
