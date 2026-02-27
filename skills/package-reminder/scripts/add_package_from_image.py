#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.8"
# dependencies = []
# ///
"""
从图片中提取快递信息并添加提醒
使用 macOS Vision 框架进行 OCR
"""
import sys
import os
import subprocess
import json
from pathlib import Path

def ocr_with_vision(image_path):
    """使用 macOS Vision 框架进行 OCR"""
    # 使用 shortcuts 或 AppleScript 调用 Vision
    # 这里使用一种简单方式：通过预览/截图工具的 OCR

    # 方法1：使用 tesseract (如果已安装)
    try:
        result = subprocess.run(
            ['tesseract', image_path, '-', '-l', 'chi_sim+eng'],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except FileNotFoundError:
        pass
    except Exception:
        pass

    # 方法2：使用 macOS 原生 OCR (通过快捷指令或 AppleScript)
    # 这里用一个简单的 AppleScript 方案
    applescript = f'''
    use framework "Vision"
    use scripting additions

    set imagePath to POSIX file "{image_path}"
    set theImage to current application's NSImage's alloc()'s initWithContentsOfFile:(imagePath)

    -- 使用 Vision 进行文字识别
    set requestHandler to current application's VNImageRequestHandler's alloc()'s initWithData:(theImage's TIFFRepresentation()) options:{{}}
    set request to current application's VNRecognizeTextRequest's alloc()'s init()
    request's setRecognitionLanguages:{{"zh-Hans", "en"}}

    set success to requestHandler's performRequests:{{request}} error:(missing value)

    set results to request's results()
    set textList to {{}}
    repeat with aResult in results
        set topCandidate to (aResult's topCandidates:1)'s firstObject()
        set end of textList to (topCandidate's |string|() as string)
    end repeat

    return textList as string
    '''

    try:
        result = subprocess.run(
            ['osascript', '-e', applescript],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass

    # 方法3：使用 image-to-text 工具 (如果可用)
    # 或者使用 Python 的 pytesseract
    try:
        from PIL import Image
        import pytesseract
        img = Image.open(image_path)
        text = pytesseract.image_to_string(img, lang='chi_sim+eng')
        return text.strip()
    except ImportError:
        pass
    except Exception:
        pass

    return None

def main():
    if len(sys.argv) < 2:
        print("用法: uv run add_package_from_image.py <图片路径>")
        print("示例: uv run add_package_from_image.py ~/Downloads/package.jpg")
        sys.exit(1)

    image_path = sys.argv[1]

    if not os.path.exists(image_path):
        print(f"❌ 图片不存在: {image_path}", file=sys.stderr)
        sys.exit(1)

    print("🔍 正在识别图片中的文字...")

    # OCR 识别
    text = ocr_with_vision(image_path)

    if not text:
        print("❌ 无法识别图片中的文字", file=sys.stderr)
        print("请尝试安装 Tesseract: brew install tesseract tesseract-lang", file=sys.stderr)
        sys.exit(1)

    print(f"📝 识别内容:\n{text}\n")

    # 调用文字处理脚本
    script_dir = Path(__file__).parent
    add_package_script = script_dir / 'add_package.py'

    result = subprocess.run(
        ['uv', 'run', str(add_package_script), text],
        capture_output=True, text=True
    )

    print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)

    sys.exit(result.returncode)

if __name__ == '__main__':
    main()
