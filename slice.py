import os
import csv
from PyPDF2 import PdfReader

# 知识点文件路径
knowledge_file_path = './course_knowledge.csv'

# PDF文件所在目录
pdf_directory = './dataset'

# 读取知识点文件
with open(knowledge_file_path, 'r', encoding='utf-8') as file:
    reader = csv.reader(file)
    for row in reader:
        # 获取章节标题
        chapter_title = row[2]
        # 获取课程名称
        course_code = row[0] + "_" + row[1]
        for root, dirs, files in os.walk(pdf_directory):
            for file in files:
                if file.endswith('.pdf'):
                    file_name = file.split('.')[-2]
                    # 判断该文件是否是该门课程
                    if not file_name.startswith(course_code):
                        continue
                    print(file_name)
                    pdf_path = os.path.join(root, file)
                    # print(pdf_path)
        #             reader = PdfReader(pdf_path)
        #             content = ""
        #             found_chapter = False
                    # if chapter_title
                    # for page in reader.pages:
                    #     # 书本内容
                    #     text = page.extract_text()
                        # if chapter_title in text:
        #                     found_chapter = True
        #                 if found_chapter:
        #                     content += text
        #                     # 这里简单假设下一个章节标题出现前的内容都属于当前章节
        #                     # 如果有更明确的章节结束标识，需要更复杂的逻辑判断
        #                     for next_chapter in [row[1] for row in reader if row[1]!= chapter_title]:
        #                         if next_chapter in text:
        #                             found_chapter = False
        #                             break
        #             if content:
        #                 # 将提取的内容保存到文件，文件名可以自定义
        #                 output_file_path = f"/mnt/extracted_{os.path.splitext(file)[0]}_{chapter_title}.txt"
        #                 with open(output_file_path, 'w', encoding='utf-8') as output_file:
        #                     output_file.write(content)