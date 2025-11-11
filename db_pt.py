# 1. 导入 pymysql 库
import pymysql
import json
import os

# --- 数据库配置信息 ---
# 把这些值改成你自己的数据库信息


def main():
    """主函数，执行所有数据库操作"""
    connection = None
    # 定义 JSON 配置文件的路径
    config_path = './configs/config.json'

    # 检查配置文件是否存在
    if not os.path.exists(config_path):
        print(f"错误：配置文件 '{config_path}' 不存在。")
        return None

    # 1. 打开并读取 JSON 文件
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            # 2. 使用 json.load() 解析 JSON 数据为 Python 字典
            db_config = json.load(f)
            
    except json.JSONDecodeError:
        print(f"错误：'{config_path}' 文件格式不正确，不是有效的 JSON。")
        return None
    except Exception as e:
        print(f"读取配置文件时发生错误: {e}")
        return None
    
    try:
        # 2. 连接数据库
        print("正在连接数据库...")
        # pymysql.connect() 会返回一个连接对象
        connection = pymysql.connect(**db_config)
        print("数据库连接成功！")

        # 3. 获取游标 (Cursor) 对象
        # 游标是用来执行 SQL 语句并获取结果的工具
        with connection.cursor() as cursor:

            # 4. 创建数据库（如果不存在）
            # 注意：这里我们先连接到 MySQL 服务器，然后创建数据库
            # 因此，初始的 DB_CONFIG 中可以不指定 'database'，或者指定一个已存在的（如 'mysql'）
            # 为了代码健壮性，我们先尝试创建数据库
            
            create_db_sql = f"CREATE DATABASE IF NOT EXISTS {db_config['python_test_db']} DEFAULT CHARACTER SET utf8mb4;"
            cursor.execute(create_db_sql)
            print(f"数据库 '{db_config['python_test_db']}' 已确保存在。")
            
            # 连接到新创建的数据库
            connection.select_db(db_config['python_test_db'])

            # 5. 创建数据表 (Table)
            # 我们创建一个名为 'students' 的表来存储学生信息
            create_table_sql = """
            CREATE TABLE IF NOT EXISTS students (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(50) NOT NULL,
                age INT,
                major VARCHAR(100),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """
            cursor.execute(create_table_sql)
            print("数据表 'students' 已确保存在。")

            # 6. 插入数据 (Insert)
            print("\n--- 插入数据 ---")
            student_name = "张三"
            student_age = 20
            student_major = "计算机科学"
            
            insert_sql = "INSERT INTO students (name, age, major) VALUES (%s, %s, %s);"
            # 使用 cursor.execute() 执行 SQL 语句
            # %s 是参数占位符，避免 SQL 注入风险，非常重要！
            affected_rows = cursor.execute(insert_sql, (student_name, student_age, student_major))
            print(f"成功插入 {affected_rows} 条数据。")
            
            # 获取刚刚插入的数据的 ID
            new_student_id = cursor.lastrowid
            print(f"新插入学生的 ID 是: {new_student_id}")

            # 7. 查询数据 (Select)
            print("\n--- 查询数据 ---")
            # 查询所有学生
            select_all_sql = "SELECT id, name, age, major, created_at FROM students;"
            cursor.execute(select_all_sql)
            
            # 使用 cursor.fetchall() 获取所有查询结果
            all_students = cursor.fetchall()
            print(f"查询到 {len(all_students)} 条学生记录：")
            for student in all_students:
                # student 是一个元组 (tuple)
                print(f"ID: {student[0]}, 姓名: {student[1]}, 年龄: {student[2]}, 专业: {student[3]}, 创建时间: {student[4]}")

            # 8. 更新数据 (Update)
            print("\n--- 更新数据 ---")
            # 把 ID 为 new_student_id 的学生的年龄增加 1
            update_sql = "UPDATE students SET age = age + 1 WHERE id = %s;"
            affected_rows = cursor.execute(update_sql, (new_student_id,))
            print(f"成功更新 {affected_rows} 条数据。")

            # 9. 删除数据 (Delete)
            # 我们先插入一条临时数据，然后再删除它，以演示删除功能
            print("\n--- 删除数据 ---")
            temp_name = "李四"
            cursor.execute("INSERT INTO students (name, age, major) VALUES (%s, %s, %s);", (temp_name, 22, "软件工程"))
            temp_id = cursor.lastrowid
            print(f"插入一条临时数据 (ID: {temp_id}, 姓名: {temp_name}) 用于演示删除。")

            delete_sql = "DELETE FROM students WHERE id = %s;"
            affected_rows = cursor.execute(delete_sql, (temp_id,))
            print(f"成功删除 {affected_rows} 条数据 (ID: {temp_id})。")

        # 10. 提交事务 (Commit)
        # 在执行 INSERT, UPDATE, DELETE 之后，必须调用 commit() 才能将更改永久保存到数据库中
        connection.commit()
        print("\n所有更改已提交到数据库。")

        # 再次查询，验证最终结果
        print("\n--- 最终数据状态 ---")
        with connection.cursor() as cursor:
            cursor.execute(select_all_sql)
            final_students = cursor.fetchall()
            for student in final_students:
                print(f"ID: {student[0]}, 姓名: {student[1]}, 年龄: {student[2]}, 专业: {student[3]}")

    except pymysql.MySQLError as e:
        # 如果发生错误，打印错误信息
        print(f"\n数据库操作失败: {e}")
        # 如果连接已建立且有未提交的事务，则回滚 (Rollback)
        if connection:
            connection.rollback()
            print("事务已回滚。")

    finally:
        # 11. 关闭连接
        if connection:
            connection.close()
            print("\n数据库连接已关闭。")

if __name__ == '__main__':
    main()