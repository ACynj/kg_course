from py2neo import Graph, Node, Relationship  # 导入 py2neo 模块，Graph 用于连接 Neo4j，Node 和 Relationship 用于创建节点和关系
import pandas as pd  # 导入 pandas，用于处理课程数据文件

# 连接到 Neo4j 数据库
graph = Graph("neo4j://localhost:7687", auth=("neo4j", "ynj123456"))  # 连接到 Neo4j 数据库，替换为你自己的数据库地址和认证信息

# graph.run("MATCH (n) DETACH DELETE n")  # 删除所有节点和与之关联的关系

# 加载课程数据
file_path = 'course.csv'  # 定义文件路径，指向课程数据的 CSV 文件
# 加载课程类别数据
course_type_file_path = 'course_type.csv'  # 定义课程类别数据文件路径
course_type_data = pd.read_csv(course_type_file_path, encoding='utf-8')  # 加载课程类别数据

# 加载课程标签数据
course_label_file_path = 'course_label.csv'  # 定义课程类别数据文件路径
course_label_data = pd.read_csv(course_label_file_path, encoding='utf-8')  # 加载课程类别数据

# 学期文件
term_file_path = 'term.csv'  # 学期文件
term_data = pd.read_csv(term_file_path, encoding='utf-8')  # 假设文件没有列名
term_mappings = {i + 1: row["学期"] for i, row in term_data.iterrows()}  # 创建学期编号与学期名称的映射字典

# 创建学期节点
term_nodes = {}  # 存储学期节点
for term_id, term_name in term_mappings.items():
    term_node = Node("Term", name=term_name)
    graph.merge(term_node, "Term", "name")
    term_nodes[term_id] = term_node  # 用学期编号作为键，学期节点为值


course_data = pd.read_csv(file_path)  # 使用 pandas 加载 CSV 文件数据，读取课程信息到 DataFrame 中


# 创建课程节点并建立学时分配关系
# 加载课程知识点文件
knowledge_file_path = 'course_knowledge.csv'  # 知识点文件路径
knowledge_data = pd.read_csv(knowledge_file_path, encoding='utf-8')  # 假设文件包含课程编号和知识点




# 创建学习类型节点
hours_types = ["讲课", "实验", "课程实践", "自主学习"]  # 定义学习类型列表
hours_type_nodes = {}  # 创建一个空字典用于存储每个学习类型的节点

# 遍历学习类型并为每个学习类型创建一个节点
for lt in hours_types:
    lt_node = Node("LearningType", name=lt)  # 创建一个新的学习类型节点，类型是 HoursType，属性是学习类型名称
    graph.merge(lt_node, "LearningType", "name")  # 将学习类型节点合并到图中，避免重复节点
    hours_type_nodes[lt] = lt_node  # 将节点存储到字典中，以学习类型为键

# 创建必修课和选修课节点
required_course_node = Node("CourseCategory", name="必修课")
graph.merge(required_course_node, "CourseCategory", "name")
optional_course_node = Node("CourseCategory", name="选修课")
graph.merge(optional_course_node, "CourseCategory", "name")

# 创建课程标签结点
# 遍历 CSV 中的每一行来创建节点和关系
for index, row in course_label_data.iterrows():
    course_label = row['课程标签']
    course_label_node = Node("CourseLabel", name=course_label)
    graph.merge(course_label_node, "CourseLabel", "name")  # merge以避免重复创建课程类别节点


# 创建课程节点并建立学时分配关系
for index, row in course_data.iterrows():  # 遍历课程数据中的每一行
    print(f'处理第{index + 1}条数据...')
    # 创建课程节点
    course_node = Node("Course",  # 创建一个新的课程节点，类型是 Course
                       course_code=row["课程编号"],  # 设置课程编号
                       course_name=row["课程名称"],  # 设置课程名称
                       credits=row["学分数"],  # 设置课程学分
                       total_hours=row["总学时"],  # 设置课程总学时
                       week_hours=row["周学时"],
                       start_end_time=row["起止周数"])  # 设置是否必修课程

    # 合并课程节点（避免重复）
    graph.merge(course_node, "Course", "course_code")  # 将课程节点合并到图中，避免重复课程节点（通过课程编号判断）


    # 根据原始学时数据建立与学习类型的关系
    for lt, hours in zip(hours_types, [row["讲课"], row["实验"], row["课程实践"], row["自主学习"]]):  # 遍历每个学习类型及其对应的学时
        if hours > 0:  # 如果该学习类型的学时大于 0，则建立关系
            # 创建学时分配关系，直接使用原始学时数据
            rel = Relationship(course_node, "分配学时", hours_type_nodes[lt], hours=hours)  # 创建课程与学习类型之间的关系，并设置学时属性
            graph.merge(rel)  # 将关系合并到图中，避免重复关系

    # 创建课程类别与课程子类的关系
    course_category = row['课程类别']  # 课程类别列的值

    # 判断课程类别是否存在于上传的课程类别数据中
    category_node = None
    sub1type_node = None
    sub2type_node = None

    # 查找是否是课程类别，若不是则可能是课程子类
    course_type_row = course_type_data[course_type_data['课程类别'] == course_category]

    if not course_type_row.empty:  # 课程类别存在
        category_node = Node("CourseType", name=course_category)
        graph.merge(category_node, "CourseType", "name")  # 合并到图中
        course_type_rel = Relationship(course_node, "课程类别", category_node)
        graph.merge(course_type_rel)
    else:  # 如果课程类别不存在，检查是否是课程子类
        course_sub1type_row = course_type_data[course_type_data['课程子类1'] == course_category]
        if not course_sub1type_row.empty:  # 课程子类存在
            sub1type_node = Node("CourseSub1type", name=course_category)
            graph.merge(sub1type_node, "CourseSub1type", "name")  # 合并到图中
            course_sub1type_rel = Relationship(course_node, "课程类别", sub1type_node)
            graph.merge(course_sub1type_rel)
        else:
            course_sub2type_row = course_type_data[course_type_data['课程子类2'] == course_category]
            if not course_sub2type_row.empty:
                sub2type_node = Node("CourseSub2type", name=course_category)
                graph.merge(sub2type_node, "CourseSub2type", "name")  # 合并到图中
                course_sub2type_rel = Relationship(course_node, "课程类别", sub2type_node)
                graph.merge(course_sub2type_rel)

    # 可选：链接课程与开课部门（如果需要）
    department_node = Node("Department", name=row["开课部门"])  # 创建开课部门节点，类型是 Department
    graph.merge(department_node, "Department", "name")  # 合并开课部门节点到图中，避免重复
    department_rel = Relationship(course_node, "归属部门", department_node)  # 创建课程与开课部门之间的关系
    graph.merge(department_rel)  # 将关系合并到图中

    # 课程体系
    if not pd.isna(row["课程体系"]):
        course_struct_node = Node("CourseStruct", name=row["课程体系"])
        graph.merge(course_struct_node, "CourseStruct", "name")
        course_type_rel = Relationship(course_node, "课程体系", course_struct_node)
        graph.merge(course_type_rel)  # 将关系合并到图中

    # 根据是否必修属性建立关系
    if row["是否必修"] == "是":
        rel = Relationship(course_node, "属于", required_course_node)
        graph.merge(rel)
    else:
        rel = Relationship(course_node, "属于", optional_course_node)
        graph.merge(rel)

    # 处理修读说明标签
    if isinstance(row["修读说明"], str):  # 确保修读说明是字符串类型
        labels = row["修读说明"].split("、")  # 使用 `、` 分割标签
        for label in labels:
            label = label.strip()  # 去除标签前后的空白字符
            # 查找或创建对应的课程标签节点
            label_node = graph.nodes.match("CourseLabel", name=label).first()
            if not label_node:
                label_node = Node("CourseLabel", name=label)
                graph.merge(label_node, "CourseLabel", "name")  # merge以避免重复创建课程标签节点
            # 创建课程与标签之间的关系
            rel = Relationship(course_node, "属于", label_node)
            graph.merge(rel)  # 将关系合并到图中

    # 处理建议修读学期
    suggested_term = row["建议修读学期"]
    if pd.notna(suggested_term):
        term_id = int(suggested_term)  # 将学期编号转换为整数
        term_name = term_mappings.get(term_id)
        if term_name:
            term_node = term_nodes.get(term_id)
            if term_node:
                # 创建建议修读关系
                rel = Relationship(course_node, "建议修读", term_node)
                graph.merge(rel)
            else:
                print(f"警告：学期编号 {term_id} 未找到对应的学期节点")
        else:
            print(f"警告：学期编号 {term_id} 未找到对应的学期名称")

    # 处理修读学期
    study_term = row["修读学期"]
    if pd.notna(study_term):
        term_id = int(study_term)  # 将学期编号转换为整数
        term_name = term_mappings.get(term_id)
        if term_name:
            term_node = term_nodes.get(term_id)
            if term_node:
                # 创建修读关系
                rel = Relationship(course_node, "修读", term_node)
                graph.merge(rel)
            else:
                print(f"警告：学期编号 {term_id} 未找到对应的学期节点")
        else:
            print(f"警告：学期编号 {term_id} 未找到对应的学期名称")

    # 处理平时成绩构成
    if pd.notna(row["平时成绩构成"]):
        components = row["平时成绩构成"].split("；")  # 假设平时成绩构成用 `；` 分隔
        for component in components:
            component = component.strip()
            parts = component.split("（")
            if len(parts) >= 2:
                name = parts[0].strip()
                ratio = parts[1].replace("）", "").replace("%", "").strip()
                # 创建成绩构成节点
                grade_component_node = Node("GradeComponent", name=name, ratio=ratio)
                graph.merge(grade_component_node, "GradeComponent", "name")
                # 创建课程与成绩构成的关系
                rel = Relationship(course_node, "平时成绩由", grade_component_node, ratio=ratio)
                graph.merge(rel)

    # 处理期末成绩构成
    if pd.notna(row["期末成绩构成"]):
        components = row["期末成绩构成"].split("；")  # 假设期末成绩构成用 `；` 分隔
        for component in components:
            component = component.strip()
            parts = component.split("（")
            if len(parts) >= 2:
                name = parts[0].strip()
                ratio = parts[1].replace("）", "").replace("%", "").strip()
                # 创建成绩构成节点
                grade_component_node = Node("GradeComponent", name=name, ratio=ratio)
                graph.merge(grade_component_node, "GradeComponent", "name")
                # 创建课程与成绩构成的关系
                rel = Relationship(course_node, "期末成绩由", grade_component_node, ratio=ratio)
                graph.merge(rel)

# 创建章和知识点节点
course_groups = knowledge_data.groupby("课程编号")

for course_code, course_group in course_groups:
    print(f'处理编号为{course_code}的课程的数据...')
    course_node = graph.nodes.match("Course", course_code=course_code).first()
    if not course_node:
        continue

    current_chapter = None
    chapter_order = 1  # 章节顺序索引（按课程独立计数）

    for index, row in course_group.iterrows():
        chapter_name = row["章"]
        knowledge_point = row["知识点"]

        if chapter_name != current_chapter:
            # 生成章的 knowledge_code（课程编号_CH_章节顺序）
            chapter_knowledge_code = f"{course_code}_CH_{chapter_order}"
            chapter_node = Node(
                "Chapter",
                course_code=course_code,
                name=chapter_name,
                order=chapter_order,
                knowledge_code=chapter_knowledge_code  # 新增唯一标识
            )
            graph.merge(chapter_node, "Chapter", "knowledge_code")  # 改用 knowledge_code 作为唯一标识

            rel_course_chapter = Relationship(
                course_node, "章节", chapter_node, order=chapter_order
            )
            graph.merge(rel_course_chapter)

            current_chapter = chapter_name
            chapter_order += 1  # 章节顺序递增
            kp_order = 1  # 知识点顺序重置为 1（每个章节独立计数）
        else:
            # 获取已有章节点（通过 knowledge_code 确保唯一性）
            chapter_knowledge_code = f"{course_code}_CH_{chapter_order - 1}"  # 当前章节的 code（前一次递增前的值）
            chapter_node = graph.nodes.match("Chapter", knowledge_code=chapter_knowledge_code).first()

        # 生成知识点的 knowledge_code（课程编号_CH_章节顺序_KP_知识点顺序）
        knowledge_knowledge_code = f"{course_code}_CH_{chapter_order - 1}_KP_{kp_order}"  # 章节顺序是当前章节的顺序（未递增前）
        kp_node = Node(
            "KnowledgePoint",
            name=knowledge_point,
            knowledge_code=knowledge_knowledge_code  # 新增唯一标识
        )
        graph.merge(kp_node, "KnowledgePoint", "knowledge_code")  # 改用 knowledge_code 作为唯一标识

        rel_chapter_kp = Relationship(
            chapter_node, "包含", kp_node, order=kp_order
        )
        graph.merge(rel_chapter_kp)

        kp_order += 1  # 知识点顺序递增

print("课程知识图谱创建成功。")  # 打印提示信息，表示知识图谱已经成功创建