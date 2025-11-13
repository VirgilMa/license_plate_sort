# 车牌号码识别脚本

识别车辆自助选号系统界面中的车牌选项。

## 功能特点

- 支持两种 OCR 引擎：Tesseract 和 EasyOCR
- 自动图像预处理提高识别率
- 区域检测和全图识别两种模式
- 车牌格式验证
- 结果可视化标注

## 安装依赖

### 方法1: 使用 Tesseract OCR

1. 安装 Tesseract OCR 引擎：
   - Windows: 从 https://github.com/UB-Mannheim/tesseract/wiki 下载安装
   - 安装后添加到系统 PATH，或设置环境变量

2. 安装 Python 依赖：
```bash
pip install pytesseract Pillow opencv-python numpy
```

### 方法2: 使用 EasyOCR (推荐)

```bash
pip install easyocr opencv-python numpy Pillow
```

或者安装所有依赖：
```bash
pip install -r requirements.txt
```

## 使用方法

### 使用 Tesseract OCR

```bash
python license_plate_ocr.py <图片路径> [输出路径]
```

示例：
```bash
python license_plate_ocr.py screenshot.jpg result.jpg
```

### 使用 EasyOCR (推荐用于中文环境)

```bash
python license_plate_easyocr.py <图片路径> [输出路径]
```

示例：
```bash
python license_plate_easyocr.py screenshot.jpg result_easyocr.jpg
```

## 识别结果

脚本会：
1. 在控制台打印所有识别到的车牌号码
2. 生成标注图像，用绿色框标记识别区域
3. 显示每个车牌的识别置信度

## 示例输出

从您提供的图片中，应该能识别到以下车牌号码：

左列：
- CDP5747
- CD32024
- CD39848
- CDL6194
- CDB8524

中列：
- CDS8434
- CDB6694
- CD67742
- CA74475
- CDL1541

右列：
- CDZ8457
- CDF7644
- CD82694
- CDM6145
- CDM2884
- CDL3034
- CDM2407
- CD58364
- CDG9364
- CDH1594
- CDK5204
- CDC6499
- CD48437
- CDL0840
- CA45527

当前选择号码：14422

## 车牌格式说明

中国车牌格式通常为：
- 省份简称（1个汉字）
- 地区代码（1个字母）
- 序号（5位字母或数字组合）

本脚本针对英文字母和数字部分进行识别。

## 故障排除

### Tesseract 方法

如果提示找不到 tesseract：
```python
# 在脚本开头添加
import pytesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
```

### EasyOCR 方法

首次运行会自动下载模型文件（约 100MB），请确保网络连接正常。

如果内存不足，可以修改脚本降低图像分辨率：
```python
# 在读取图像后添加
img = cv2.resize(img, None, fx=0.5, fy=0.5)
```

## 提高识别率的技巧

1. 确保图片清晰，分辨率足够高
2. 车牌文字与背景对比度要好
3. 避免倾斜和变形
4. 光照均匀，避免反光

## 技术说明

### license_plate_ocr.py (Tesseract)
- 使用 OpenCV 进行图像预处理
- CLAHE 对比度增强
- Otsu 自适应二值化
- 轮廓检测定位车牌区域
- 正则表达式验证车牌格式

### license_plate_easyocr.py (EasyOCR)
- 基于深度学习的 OCR 引擎
- 原生支持中文识别
- 自动文本检测和识别
- 更高的识别准确率
- 返回置信度评分
