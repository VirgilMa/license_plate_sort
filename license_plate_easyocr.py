"""
使用 EasyOCR 识别车牌号码（支持中文）
更适合中国车牌识别
"""

import easyocr
import cv2
import numpy as np
from PIL import Image
import re

def recognize_plates_easyocr(image_path, output_path='result_easyocr.jpg'):
    """使用 EasyOCR 识别车牌"""
    # 初始化 EasyOCR reader（支持中文和英文）
    print("初始化 EasyOCR (首次运行会下载模型)...")
    reader = easyocr.Reader(['ch_sim', 'en'], gpu=False)

    # 读取图像
    img = cv2.imread(image_path)

    # 进行 OCR 识别
    print("正在识别图像...")
    results = reader.readtext(image_path)

    # 提取车牌号码
    license_plates = []
    result_img = img.copy()

    print("\n识别到的所有文本:")
    print("=" * 60)

    for (bbox, text, confidence) in results:
        # 清理文本
        text_clean = text.replace(' ', '').replace('\n', '')

        print(f"文本: {text_clean:20s} | 置信度: {confidence:.2f}")

        # 检查是否为车牌格式
        if is_license_plate(text_clean):
            license_plates.append({
                'plate': text_clean,
                'confidence': confidence,
                'bbox': bbox
            })

            # 在图像上绘制边界框
            points = np.array(bbox, dtype=np.int32)
            cv2.polylines(result_img, [points], True, (0, 255, 0), 2)

            # 添加文本标签
            x, y = int(bbox[0][0]), int(bbox[0][1])
            cv2.putText(result_img, text_clean, (x, y-10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

    # 保存结果图像
    cv2.imwrite(output_path, result_img)

    # 打印结果
    print("\n" + "=" * 60)
    print(f"识别到的车牌号码 (共 {len(license_plates)} 个):")
    print("=" * 60)

    for i, plate_info in enumerate(sorted(license_plates,
                                         key=lambda x: x['confidence'],
                                         reverse=True), 1):
        print(f"{i:2d}. {plate_info['plate']:15s} | 置信度: {plate_info['confidence']:.2%}")

    print(f"\n标注结果已保存到: {output_path}")

    return license_plates

def is_license_plate(text):
    """判断文本是否为车牌格式"""
    # 移除所有非字母数字字符
    text = re.sub(r'[^A-Z0-9]', '', text.upper())

    # 车牌长度检查（5-7位）
    if len(text) < 5 or len(text) > 8:
        return False

    # 检查是否包含字母和数字
    has_letter = any(c.isalpha() for c in text)
    has_digit = any(c.isdigit() for c in text)

    if not (has_letter and has_digit):
        return False

    # 匹配常见车牌模式
    patterns = [
        r'^[A-Z]{2,3}[A-Z0-9]{4,5}$',  # CDP5747, CDL3034
        r'^[A-Z]{2}[0-9]{4,5}$',        # CD82694
        r'^[A-Z]{3}[0-9]{4}$',          # CDL3034
    ]

    for pattern in patterns:
        if re.match(pattern, text):
            return True

    return False

def extract_all_plates(image_path):
    """提取所有可能的车牌号码"""
    reader = easyocr.Reader(['ch_sim', 'en'], gpu=False)
    results = reader.readtext(image_path)

    all_text = []
    for (bbox, text, confidence) in results:
        text_clean = text.replace(' ', '').upper()
        all_text.append(text_clean)

    # 使用正则表达式提取车牌模式
    combined_text = ' '.join(all_text)
    pattern = r'[A-Z]{2,3}[A-Z0-9]{4,5}'
    plates = re.findall(pattern, combined_text)

    return list(set(plates))

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("用法: python license_plate_easyocr.py <图片路径> [输出路径]")
        print("示例: python license_plate_easyocr.py screenshot.jpg result.jpg")
        sys.exit(1)

    image_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else 'result_easyocr.jpg'

    try:
        plates = recognize_plates_easyocr(image_path, output_path)

        # 额外尝试提取所有可能的车牌
        print("\n" + "=" * 60)
        print("使用模式匹配额外提取:")
        extra_plates = extract_all_plates(image_path)
        for plate in extra_plates:
            print(f"  - {plate}")

    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
