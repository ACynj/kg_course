from py2neo import Graph, Node, Relationship  # 导入 py2neo 模块，Graph 用于连接 Neo4j，Node 和 Relationship 用于创建节点和关系
import pandas as pd  # 导入 pandas，用于处理课程数据文件

# 连接到 Neo4j 数据库
graph = Graph("neo4j://localhost:7687", auth=("neo4j", "ynj123456"))  # 连接到 Neo4j 数据库，替换为你自己的数据库地址和认证信息

graph.run("MATCH (n) DETACH DELETE n")  # 删除所有节点和与之关联的关系

# 读取 CSV 文件
file_path = 'course_type.csv'
data = pd.read_csv(file_path)

# 遍历 CSV 中的每一行来创建节点和关系
for index, row in data.iterrows():
    platform = row['课程平台']
    section = row['环节']
    course_type = row['课程类别']
    course_sub1type = row['课程子类1']
    course_sub2type = row['课程子类2']

    # 创建平台节点
    platform_node = Node("Platform", name=platform)
    graph.merge(platform_node, "Platform", "name")  # merge以避免重复创建平台节点

    # 创建环节节点
    section_node = Node("Section", type=section)
    graph.merge(section_node, "Section", "type")  # merge以避免重复创建环节节点

    # 创建课程类别节点
    course_type_node = Node("CourseType", name=course_type)
    graph.merge(course_type_node, "CourseType", "name")  # merge以避免重复创建课程类别节点

    # 创建课程子类1节点（如果有）
    if pd.notna(course_sub1type):
        course_sub1type_node = Node("CourseSub1type", name=course_sub1type)
        graph.merge(course_sub1type_node, "CourseSub1type", "name")  # merge以避免重复创建课程子类节点

        # 创建环节与课程子类之间的关系
        contains_relationship = Relationship(course_type_node, "包含", course_sub1type_node)
        graph.merge(contains_relationship)

    # 创建课程子类2节点（如果有）
    if pd.notna(course_sub2type):
        course_sub2type_node = Node("CourseSub2type", name=course_sub2type)
        graph.merge(course_sub2type_node, "CourseSub2type", "name")  # merge以避免重复创建课程子类节点

        # 创建环节与课程子类之间的关系
        contains_relationship = Relationship(course_sub1type_node, "包含", course_sub2type_node)
        graph.merge(contains_relationship)

    # 创建平台与环节之间的关系
    contains_relationship = Relationship(platform_node, "包含", section_node)
    graph.merge(contains_relationship)

    # 创建环节与课程类别之间的关系
    contains_relationship = Relationship(section_node, "包含", course_type_node)
    graph.merge(contains_relationship)
print("构建课程类型知识图谱成功！")
