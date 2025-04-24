import PyPDF2
from PyPDF2 import PdfReader, PdfWriter
from pdf2image import convert_from_path
import io
from PIL import Image
import pytesseract
import os

# 显式指定tesseract路径（解决Windows下找不到的问题）
try:
    pytesseract.pytesseract.tesseract_cmd = r'D:\develop\tessertact-QCR\tesseract.exe'  # Windows示例路径
except Exception:
    pass  # 保持默认行为，若用户已配置PATH则无需修改


def extract_text_from_pdf(pdf_path, start_page=1, end_page=None, password=None, dpi=300, poppler_path=None):
    """
    增强版PDF内容提取工具（默认处理所有页面，支持批量处理）
    """
    extracted_text = ""

    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PdfReader(file, strict=False)  # 宽松模式处理非标准PDF

            # 处理加密PDF
            if pdf_reader.is_encrypted:
                if password:
                    decrypted = pdf_reader.decrypt(password)
                    if not decrypted:
                        raise ValueError("无效密码或不支持的加密版本")
                else:
                    raise ValueError("PDF已加密，请提供解密密码")

            total_pages = len(pdf_reader.pages)
            end_page = end_page or total_pages  # 默认处理到最后一页
            page_range = range(max(1, start_page), min(total_pages, end_page) + 1)  # 1-based页码范围

            for page_num in page_range:
                page_index = page_num - 1  # 转换为0-based索引
                page = pdf_reader.pages[page_index]

                try:
                    # 优先文本提取（增加健壮性处理）
                    text = page.extract_text()
                    if text.strip():  # 忽略空白文本页
                        extracted_text += f"第{page_num}页（文本模式）:\n{text}\n\n"
                        continue

                except PyPDF2.errors.PdfReadError as e:
                    # 捕获文本提取时的解析错误（如未知宽度问题）
                    print(f"文本提取错误（第{page_num}页）: {str(e)}，尝试OCR处理")
                    text = None  # 强制进入OCR模式

                # 文本提取失败或异常，启用OCR模式
                print(f"开始处理第{page_num}页（OCR模式）...")
                try:
                    # 生成单页图像（显式指定Poppler路径，解决引擎查找问题）
                    images = convert_from_path(
                        pdf_path,
                        dpi=dpi,
                        first_page=page_num,
                        last_page=page_num,
                        fmt='png',
                        poppler_path=poppler_path  # 关键参数：指定Poppler的bin目录
                    )

                    if not images:
                        print(f"警告：第{page_num}页未生成有效图像")
                        continue

                    for img in images:
                        # 图像转文本
                        ocr_text = pytesseract.image_to_string(
                            img,
                            lang='chi_sim+eng',  # 中英文识别
                            config='--psm 6'  # 使用自动页面分割（适合常规文档）
                        )
                        extracted_text += f"第{page_num}页（OCR模式，DPI{dpi}）:\n{ocr_text.strip()}\n\n"

                except Exception as e:
                    extracted_text += f"第{page_num}页OCR失败: {str(e)}\n"
                    print(f"OCR处理错误（第{page_num}页）: {str(e)}")

    except FileNotFoundError:
        raise FileNotFoundError(f"错误：文件路径不存在 - {pdf_path}")
    except ValueError as e:
        raise ValueError(f"加密处理错误: {str(e)}")
    except PyPDF2.errors.PdfReadError as e:
        raise RuntimeError(f"PDF解析错误: 可能文件损坏或格式不支持 - {str(e)}")
    except Exception as e:
        raise Exception(f"发生未知错误: {str(e)}")

    return extracted_text


def process_directory(input_dir, output_dir, dpi=300, poppler_path=None, start_page=1, end_page=None):
    """
    处理指定目录下的所有PDF文件并保存为TXT（默认处理所有页面）
    """
    # 创建输出目录（如果不存在）
    os.makedirs(output_dir, exist_ok=True)

    # 遍历输入目录中的文件
    for filename in os.listdir(input_dir):
        if not filename.startswith("INF1350_Python高级程序设计"):
            continue
        if filename.endswith('.pdf'):
            pdf_path = os.path.join(input_dir, filename)
            txt_filename = os.path.splitext(filename)[0] + '.txt'
            txt_path = os.path.join(output_dir, txt_filename)

            print(f"正在处理文件: {pdf_path}")

            try:
                # 提取文本（使用默认参数处理所有页面）
                text = extract_text_from_pdf(
                    pdf_path,
                    start_page=start_page,
                    end_page=end_page,
                    dpi=dpi,
                    poppler_path=poppler_path
                )

                # 保存为TXT文件
                with open(txt_path, 'w', encoding='utf-8') as txt_file:
                    txt_file.write(text)

                print(f"成功保存到: {txt_path}")

            except Exception as e:
                print(f"处理文件 {filename} 时出错: {str(e)}")
                continue


# ------------------- 使用说明 -------------------
# 1. 安装Poppler（关键步骤！）：
#   - Windows: 下载二进制包并配置poppler_path（见上方步骤）
#   - macOS: brew install poppler
#   - Linux: sudo apt-get install poppler-utils

# 2. 配置参数（默认处理所有页面）
if __name__ == "__main__":
    input_directory = "./dataset"  # 输入PDF文件目录
    output_directory = "./dataset/processed"  # 输出TXT文件目录
    poppler_path = r'D:\develop\popper\Release-24.08.0-0\poppler-24.08.0\Library\bin'  # Windows用户必须填写实际路径
    # poppler_path = None  # macOS/Linux用户若已添加到PATH，可设为None

    # 处理目录中的所有PDF文件（移除start_page/end_page参数，使用默认值处理所有页面）
    process_directory(
        input_dir=input_directory,
        output_dir=output_directory,
        dpi=300,
        poppler_path=poppler_path
        # 不传入start_page/end_page参数，使用默认值（start_page=1, end_page=None）
    )