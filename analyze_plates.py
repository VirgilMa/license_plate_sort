"""
车牌识别与评分主程序
输入图片地址，自动识别车牌并进行评分排序
"""

import sys
import os
import re
from typing import List, Tuple
from plate_scorer import create_default_scorer
from dataclasses import dataclass


@dataclass
class PlateInfo:
    """车牌信息"""

    plate_number: str
    bbox: List[List[float]]
    confidence: float
    center_pos: Tuple[int, int]  # (中心X坐标, 中心Y坐标)


def calculate_grid_positions(plates_data: List[Tuple]) -> List[Tuple[int, int]]:
    """
    根据所有车牌的位置自动计算每个车牌在网格中的行列位置

    参数:
        plates_data: [(bbox, text, confidence), ...] 列表

    返回:
        [(行号, 列号), ...] 列表，从1开始计数
    """
    if not plates_data:
        return []

    # 提取所有车牌的中心点
    centers = []
    for bbox, text, confidence in plates_data:
        center_x = sum(point[0] for point in bbox) / 4
        center_y = sum(point[1] for point in bbox) / 4
        centers.append((center_x, center_y, bbox, text, confidence))

    # 按Y坐标排序，识别行
    centers_sorted_by_y = sorted(centers, key=lambda c: c[1])

    # 使用聚类方法识别行
    rows = []
    current_row = [centers_sorted_by_y[0]]
    row_threshold = 50  # Y坐标差异阈值，可以调整

    for i in range(1, len(centers_sorted_by_y)):
        prev_y = centers_sorted_by_y[i - 1][1]
        curr_y = centers_sorted_by_y[i][1]

        if abs(curr_y - prev_y) < row_threshold:
            # 同一行
            current_row.append(centers_sorted_by_y[i])
        else:
            # 新的一行
            rows.append(current_row)
            current_row = [centers_sorted_by_y[i]]

    # 添加最后一行
    if current_row:
        rows.append(current_row)

    # 为每行内的车牌按X坐标排序，确定列
    positions = {}
    for row_idx, row in enumerate(rows, 1):
        # 按X坐标排序
        row_sorted = sorted(row, key=lambda c: c[0])
        for col_idx, (center_x, center_y, bbox, text, confidence) in enumerate(
            row_sorted, 1
        ):
            # 使用bbox作为key
            bbox_tuple = tuple(tuple(point) for point in bbox)
            positions[bbox_tuple] = (row_idx, col_idx)

    # 返回位置列表，按原始顺序
    result = []
    for bbox, text, confidence in plates_data:
        bbox_tuple = tuple(tuple(point) for point in bbox)
        if bbox_tuple in positions:
            result.append(positions[bbox_tuple])
        else:
            result.append((0, 0))  # 未找到位置

    return result


def recognize_plates_from_image(image_path: str) -> List[PlateInfo]:
    """
    从图片中识别车牌号码及其位置信息

    参数:
        image_path: 图片路径

    返回:
        车牌信息列表
    """
    try:
        import easyocr
        import cv2
        import numpy as np

        print(f"正在识别图片: {image_path}")
        print("初始化 EasyOCR...")

        # 读取图片获取尺寸
        img = cv2.imread(image_path)
        if img is None:
            print(f"错误: 无法读取图片 {image_path}")
            return []

        image_height, image_width = img.shape[:2]

        # 初始化 EasyOCR（只使用英文模型）
        reader = easyocr.Reader(["en"], gpu=False, verbose=False)

        # 直接识别原始图片 - 使用基础参数
        results = reader.readtext(
            image_path,
            detail=1,
            paragraph=False,
            allowlist="ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789",
        )

        print(f"DEBUG - OCR原始结果数量: {len(results)}")

        # 第一步：收集所有可能的车牌，并过滤重复结果
        plate_dict = {}  # 用于去重，key为位置，value为(text, confidence)
        print(f"\n识别到 {len(results)} 个文本区域")

        for bbox, text, confidence in results:
            # 过滤置信度低于50%的结果
            if confidence < 0.5:
                print(f"DEBUG - 置信度过低({confidence:.2%})，跳过: {text}")
                continue

            # 清理文本
            text_clean = text.replace(" ", "").replace("\n", "").upper()
            text_clean = re.sub(r"[^A-Z0-9]", "", text_clean)  # 只保留字母和数字

            # 简单的车牌格式验证
            if is_likely_plate(text_clean):
                # 计算bbox中心点作为唯一标识
                center_x = sum(point[0] for point in bbox) / 4
                center_y = sum(point[1] for point in bbox) / 4

                # 检查是否与已有车牌位置重复（容差30像素）
                is_duplicate = False
                for existing_cx, existing_cy in plate_dict.keys():
                    if (
                        abs(center_x - existing_cx) < 30
                        and abs(center_y - existing_cy) < 30
                    ):
                        # 位置重复，保留置信度更高的
                        if confidence > plate_dict[(existing_cx, existing_cy)][2]:
                            del plate_dict[(existing_cx, existing_cy)]
                            print(
                                f"DEBUG - 更新重复位置的车牌: {text_clean} (置信度: {confidence:.2%})"
                            )
                        else:
                            is_duplicate = True
                            print(f"DEBUG - 跳过重复位置的低置信度结果: {text_clean}")
                        break

                if not is_duplicate:
                    plate_dict[(center_x, center_y)] = (bbox, text_clean, confidence)
                    print(f"DEBUG - 接受车牌: {text_clean} (置信度: {confidence:.2%})")
            else:
                print(f"DEBUG - 格式不符，跳过: {text_clean}")

        # 转换为列表
        valid_plates = [plate_dict[key] for key in plate_dict]

        # 第二步：创建PlateInfo对象，使用中心坐标
        if not valid_plates:
            return []

        plates = []
        for bbox, text_clean, confidence in valid_plates:
            # 计算 bounding box 中心坐标
            center_x = int(sum(point[0] for point in bbox) / 4)
            center_y = int(sum(point[1] for point in bbox) / 4)

            # 计算左上角坐标（可选，用于更精确的定位）
            top_left_x = int(min(point[0] for point in bbox))
            top_left_y = int(min(point[1] for point in bbox))

            plate_info = PlateInfo(
                plate_number=text_clean,
                bbox=bbox,
                confidence=confidence,
                center_pos=(center_x, center_y),
            )
            plates.append(plate_info)
            print(
                f"  - {text_clean:15s} (置信度: {confidence:.2%}, 中心坐标: ({center_x}, {center_y}), 左上角: ({top_left_x}, {top_left_y}))"
            )

        return plates

    except ImportError:
        print("错误: 未安装 easyocr，尝试使用 pytesseract...")
        return recognize_plates_tesseract(image_path)
    except Exception as e:
        print(f"识别出错: {e}")
        import traceback

        traceback.print_exc()
        return []


def recognize_plates_tesseract(image_path: str) -> List[str]:
    """使用 Tesseract OCR 识别车牌（备用方案）"""
    try:
        import pytesseract
        from PIL import Image
        import re

        print("使用 Tesseract OCR 进行识别...")

        img = Image.open(image_path)
        custom_config = r"--oem 3 --psm 6 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
        text = pytesseract.image_to_string(img, config=custom_config, lang="eng")

        # 使用正则表达式提取车牌模式
        pattern = r"[A-Z]{2,3}[A-Z0-9]{4,5}"
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
    text = re.sub(r"[^A-Z0-9]", "", text.upper())

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
        r"^[A-Z]{2,3}[A-Z0-9]{4,5}$",
        r"^[A-Z]{2}[0-9]{4,5}$",
        r"^[A-Z]{3}[0-9]{4}$",
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
    print("=" * 120)
    print("车牌识别与评分系统")
    print("=" * 120)

    # 检查文件是否存在
    if not os.path.exists(image_path):
        print(f"错误: 文件不存在 - {image_path}")
        return

    # 识别车牌
    plate_infos = recognize_plates_from_image(image_path)

    if not plate_infos:
        print("\n未识别到车牌号码")
        return

    print(f"\n成功识别 {len(plate_infos)} 个车牌号码")
    print("=" * 120)

    # 创建评分器
    scorer = create_default_scorer()

    # 评分
    scored_plates = []
    for plate_info in plate_infos:
        total_score, details = scorer.score_plate(plate_info.plate_number)
        scored_plates.append((plate_info, total_score, details))

    # 按分数从高到低排序
    scored_plates.sort(key=lambda x: x[1], reverse=True)

    # 输出结果
    print("\n车牌评分结果（按分数从高到低排序）:")
    print("=" * 120)

    output_lines = []
    for rank, (plate_info, total_score, details) in enumerate(scored_plates, 1):
        # 格式化评分报告
        active_rules = [r for r in details if r.score != 0]
        if not active_rules:
            rule_summary = "无特殊加分项"
        else:
            rule_summary = " | ".join(
                [f"{r.rule_name}: {r.reason}" for r in active_rules]
            )

        # 添加位置信息和置信度
        center_x, center_y = plate_info.center_pos
        position_str = f"[坐标:({center_x:4d},{center_y:4d})]"
        confidence_str = f"[置信度:{plate_info.confidence:.2%}]"

        report = f"{rank:2d}. {plate_info.plate_number:12s} {position_str:18s} {confidence_str:13s} | 总分: {total_score:6.1f} | {rule_summary}"
        print(report)
        output_lines.append(report)

    # 保存到文件
    if output_file:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write("车牌评分结果\n")
            f.write("=" * 120 + "\n")
            f.write(f"图片: {image_path}\n")
            f.write(f"识别到 {len(plate_infos)} 个车牌\n")
            f.write("=" * 120 + "\n\n")
            for line in output_lines:
                f.write(line + "\n")
        print(f"\n结果已保存到: {output_file}")

    # 统计信息
    print("\n" + "=" * 120)
    print("评分统计:")
    print(f"  最高分: {scored_plates[0][1]:.1f} ({scored_plates[0][0].plate_number})")
    print(f"  最低分: {scored_plates[-1][1]:.1f} ({scored_plates[-1][0].plate_number})")
    avg_score = sum(s[1] for s in scored_plates) / len(scored_plates)
    print(f"  平均分: {avg_score:.1f}")

    # 推荐
    print("\n推荐选择:")
    top_5 = scored_plates[: min(5, len(scored_plates))]
    for i, (plate_info, score, _) in enumerate(top_5, 1):
        center_x, center_y = plate_info.center_pos
        print(
            f"  {i}. {plate_info.plate_number} (分数: {score:.1f}, 中心坐标: ({center_x}, {center_y}), 置信度: {plate_info.confidence:.2%})"
        )


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
