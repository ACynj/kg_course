import PyPDF2
from PyPDF2 import PdfReader, PdfWriter
from pdf2image import convert_from_path
import io
from PIL import Image
import os
import pandas as pd
from aip import AipOcr

# 百度云 OCR 配置
APP_ID = '118686718'
API_KEY = 'KClZpOwYLfGTOPld2HCGpCqk'
SECRET_KEY = 'uSFKgyLa2tfqR6y9MSQOeJEqwUwcYJTb'
client = AipOcr(APP_ID, API_KEY, SECRET_KEY)


def extract_text_from_pdf(pdf_path, start_page=1, end_page=None, password=None, dpi=300, poppler_path=None):
    """
    增强版 PDF 内容提取工具（默认处理所有页面，支持批量处理）
    """
    extracted_text = ""

    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PdfReader(file, strict=False)  # 宽松模式处理非标准 PDF

            # 处理加密 PDF
            if pdf_reader.is_encrypted:
                if password:
                    decrypted = pdf_reader.decrypt(password)
                    if not decrypted:
                        raise ValueError("无效密码或不支持的加密版本")
                else:
                    raise ValueError("PDF 已加密，请提供解密密码")

            total_pages = len(pdf_reader.pages)
            end_page = end_page or total_pages  # 默认处理到最后一页
            page_range = range(max(1, start_page), min(total_pages, end_page) + 1)  # 1 - based 页码范围

            for page_num in page_range:
                page_index = page_num - 1  # 转换为 0 - based 索引
                page = pdf_reader.pages[page_index]

                try:
                    # 优先文本提取（增加健壮性处理）
                    text = page.extract_text()
                    if text.strip():  # 忽略空白文本页
                        extracted_text += f"{text}\n"
                        continue

                except PyPDF2.errors.PdfReadError as e:
                    # 捕获文本提取时的解析错误（如未知宽度问题）
                    print(f"文本提取错误（第{page_num}页）: {str(e)}，尝试 OCR 处理")
                    text = None  # 强制进入 OCR 模式

                # 文本提取失败或异常，启用 OCR 模式
                print(f"开始处理第{page_num}页（OCR 模式）...")
                try:
                    # 生成单页图像（显式指定 Poppler 路径，解决引擎查找问题）
                    images = convert_from_path(
                        pdf_path,
                        dpi=dpi,
                        first_page=page_num,
                        last_page=page_num,
                        fmt='png',
                        poppler_path=poppler_path  # 关键参数：指定 Poppler 的 bin 目录
                    )

                    if not images:
                        print(f"警告：第{page_num}页未生成有效图像")
                        continue

                    for img in images:
                        # 将图像转换为字节流
                        img_byte_arr = io.BytesIO()
                        img.save(img_byte_arr, format='PNG')
                        img_byte_arr = img_byte_arr.getvalue()

                        # 使用百度云 OCR 进行文字识别
                        result = client.basicGeneral(img_byte_arr)
                        if 'words_result' in result:
                            for item in result['words_result']:
                                extracted_text += f"{item['words']}\n"
                        else:
                            extracted_text += f"第{page_num}页 OCR 失败: {str(result)}\n"
                            print(f"OCR 处理错误（第{page_num}页）: {str(result)}")

                except Exception as e:
                    extracted_text += f"第{page_num}页 OCR 失败: {str(e)}\n"
                    print(f"OCR 处理错误（第{page_num}页）: {str(e)}")

    except FileNotFoundError:
        raise FileNotFoundError(f"错误：文件路径不存在 - {pdf_path}")
    except ValueError as e:
        raise ValueError(f"加密处理错误: {str(e)}")
    except PyPDF2.errors.PdfReadError as e:
        raise RuntimeError(f"PDF 解析错误: 可能文件损坏或格式不支持 - {str(e)}")
    except Exception as e:
        raise Exception(f"发生未知错误: {str(e)}")

    return extracted_text


def process_csv(csv_path, input_dir, output_dir, dpi=300, poppler_path=None):
    """
    处理 CSV 文件中的每一条记录，提取对应 PDF 文件的指定页面文本并保存
    """
    # 创建输出目录（如果不存在）
    os.makedirs(output_dir, exist_ok=True)

    # 读取 CSV 文件
    df = pd.read_csv(csv_path)

    # 遍历 CSV 文件中的每一行
    for index, row in df.iterrows():
        book_filename = row['书籍文件名称']
        start_page = int(row['开始页码'])
        end_page = int(row['结束页码'])
        course_number = row['课程编号']
        course_name = row['课程名称']
        chapter = row['章']
        knowledge_point = row['知识点']

        pdf_filename = f"{book_filename}.pdf"
        pdf_path = os.path.join(input_dir, pdf_filename)
        txt_filename = f"{course_number}_{course_name}_{chapter}_{knowledge_point}.txt"
        txt_path = os.path.join(output_dir, txt_filename)

        print(f"正在处理文件: {pdf_path}，从第{start_page}页到第{end_page}页")

        try:
            # 提取文本
            text = extract_text_from_pdf(
                pdf_path,
                start_page=start_page,
                end_page=end_page,
                dpi=dpi,
                poppler_path=poppler_path
            )

            # 保存为 TXT 文件
            with open(txt_path, 'w', encoding='utf-8') as txt_file:
                txt_file.write(text)

            print(f"成功保存到: {txt_path}")

        except Exception as e:
            print(f"处理文件 {book_filename} 时出错: {str(e)}")
            continue


# ------------------- 使用说明 -------------------
# 1. 安装 Poppler（关键步骤！）：
#   - Windows: 下载二进制包并配置 poppler_path（见上方步骤）
#   - macOS: brew install poppler
#   - Linux: sudo apt - get install poppler - utils

# 2. 配置参数
if __name__ == "__main__":
    csv_path = "mapper/course_knowledge_mapper38.csv"  # 上传的 CSV 文件路径
    input_directory = "./dataset"  # 输入 PDF 文件目录
    output_directory = "./dataset/textbook_slice"  # 输出 TXT 文件目录
    poppler_path = r'D:\develop\popper\Release-24.08.0-0\poppler-24.08.0\Library\bin'  # Windows用户必须填写实际路径
    # poppler_path = None  # macOS/Linux 用户若已添加到 PATH，可设为 None

    # 处理 CSV 文件中的所有记录
    process_csv(
        csv_path=csv_path,
        input_dir=input_directory,
        output_dir=output_directory,
        dpi=300,
        poppler_path=poppler_path
    )