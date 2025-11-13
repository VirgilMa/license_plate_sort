"""
车牌号码识别脚本
使用 OCR 技术识别车辆自助选号系统界面中的车牌选项
"""

from PIL import Image
import pytesseract
import cv2
import numpy as np
import re

def preprocess_image(image_path):
    """预处理图像以提高 OCR 识别率"""
    # 读取图像
    img = cv2.imread(image_path)

    # 转换为灰度图
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # 增强对比度
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    enhanced = clahe.apply(gray)

    # 二值化
    _, binary = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    return img, binary

def detect_license_plate_regions(image, binary):
    """检测可能包含车牌号码的区域"""
    # 查找轮廓
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    plate_regions = []
    height, width = binary.shape

    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)

        # 筛选合适大小的区域（车牌号码区域）
        aspect_ratio = w / h if h > 0 else 0
        area = w * h

        # 车牌号码区域通常是横向矩形，宽高比约 2-6
        if (1.5 < aspect_ratio < 7 and
            area > 1000 and area < width * height * 0.1 and
            w > 80 and h > 20):
            plate_regions.append((x, y, w, h))

    return plate_regions

def extract_license_plates_ocr(image_path):
    """使用 OCR 提取车牌号码"""
    img, binary = preprocess_image(image_path)

    # 配置 tesseract 参数，优化车牌识别
    # --psm 6: 假设单个文本块
    # -c tessedit_char_whitelist: 限制字符集为数字和大写字母
    custom_config = r'--oem 3 --psm 6 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'

    # 直接对整个图像进行 OCR
    text = pytesseract.image_to_string(binary, config=custom_config, lang='eng')

    return text

def extract_license_plates_with_regions(image_path):
    """通过区域检测提取车牌号码"""
    img, binary = preprocess_image(image_path)
    plate_regions = detect_license_plate_regions(img, binary)

    license_plates = []
    result_img = img.copy()

    custom_config = r'--oem 3 --psm 7 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'

    for (x, y, w, h) in plate_regions:
        # 提取区域
        roi = binary[y:y+h, x:x+w]

        # 对区域进行 OCR
        text = pytesseract.image_to_string(roi, config=custom_config, lang='eng')
        text = text.strip().replace(' ', '').replace('\n', '')

        # 验证车牌格式（中国车牌格式）
        if is_valid_plate(text):
            license_plates.append(text)
            # 在图像上标记识别结果
            cv2.rectangle(result_img, (x, y), (x+w, y+h), (0, 255, 0), 2)
            cv2.putText(result_img, text, (x, y-10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

    return license_plates, result_img

def is_valid_plate(text):
    """验证是否为有效的车牌号码格式"""
    # 中国车牌格式：1个汉字 + 1个字母 + 5位数字/字母
    # 简化版：检查是否包含字母和数字的组合，长度 5-8 位
    if len(text) < 5 or len(text) > 8:
        return False

    # 检查是否包含字母和数字
    has_letter = any(c.isalpha() for c in text)
    has_digit = any(c.isdigit() for c in text)

    return has_letter and has_digit

def parse_plates_with_pattern(text):
    """使用正则表达式匹配车牌号码模式"""
    # 匹配模式：2-3个字母 + 4-5个数字，或混合组合
    patterns = [
        r'[A-Z]{2,3}[0-9]{4,5}',  # 如 CDP5747
        r'[A-Z]{3}[0-9]{4}',      # 如 CDL3034
        r'[A-Z]{2}[A-Z0-9]{5}',   # 混合模式
    ]

    plates = []
    for pattern in patterns:
        matches = re.findall(pattern, text)
        plates.extend(matches)

    return list(set(plates))  # 去重

def main(image_path, output_path='result.jpg'):
    """主函数"""
    print(f"正在处理图像: {image_path}")
    print("=" * 50)

    # 方法1: 全图 OCR + 正则匹配
    print("\n方法1: 全图 OCR 识别")
    text = extract_license_plates_ocr(image_path)
    print("OCR 识别原始文本:")
    print(text)
    print("\n提取的车牌号码:")
    plates_pattern = parse_plates_with_pattern(text)
    for plate in plates_pattern:
        print(f"  - {plate}")

    # 方法2: 区域检测 + OCR
    print("\n" + "=" * 50)
    print("方法2: 区域检测识别")
    plates_region, result_img = extract_license_plates_with_regions(image_path)
    print("识别的车牌号码:")
    for plate in plates_region:
        print(f"  - {plate}")

    # 保存标注结果
    cv2.imwrite(output_path, result_img)
    print(f"\n标注结果已保存到: {output_path}")

    # 合并所有结果
    all_plates = list(set(plates_pattern + plates_region))
    print("\n" + "=" * 50)
    print(f"总共识别到 {len(all_plates)} 个车牌号码:")
    for i, plate in enumerate(sorted(all_plates), 1):
        print(f"{i:2d}. {plate}")

    return all_plates

if __name__ == "__main__":
    import sys

    # 检查命令行参数
    if len(sys.argv) < 2:
        print("用法: python license_plate_ocr.py <图片路径> [输出路径]")
        print("示例: python license_plate_ocr.py screenshot.jpg result.jpg")
        sys.exit(1)

    image_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else 'result.jpg'

    try:
        plates = main(image_path, output_path)
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
