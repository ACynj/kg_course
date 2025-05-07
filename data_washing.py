import os
import re


def clean_text(text):
    # 去除多余的空白字符（包括换行符、制表符等）
    text = re.sub(r'\s+', ' ', text).strip()
    # 去除特殊字符
    text = re.sub(r'[!"#$%&\'()*+,\-./:;<=>?@\[\]^_`{|}~]{2,}', '', text)
    # 清除页码、行号或编号格式
    text = re.sub(r'\[\d+\]|\(\d+\)', '', text)
    # 去除多余的编程符号 如注释符号
    text = re.sub(r'/\*.*?\*/|//.*', '', text)
    # 去除数字或日期格式
    text = re.sub(r'\d{1,4}[-/.\s]?\d{1,2}[-/.\s]?\d{1,4}', '', text)
    # 去除网址链接和电子邮件地址
    text = re.sub(r'https?://[^\s]+', '', text)
    text = re.sub(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}', '', text)

    # 去除冗余的标点符号
    text = re.sub(r'[!"#$%&\'()*+,\-./:;<=>?@\[\]^_`{|}~]{2,}', lambda m: m.group(0)[0], text)
    return text


def process_files(directory):
    for root, dirs, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root, file)
            if file.endswith(('.txt')):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        text = f.read()
                except Exception as e:
                    print(f"Error reading {file_path}: {e}")
                    continue

                cleaned_text = clean_text(text)

                try:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(cleaned_text)
                    print(f"Processed and updated {file_path}")
                except Exception as e:
                    print(f"Error writing to {file_path}: {e}")


if __name__ == "__main__":
    directory = './dataset/textbook_slice'
    process_files(directory)
