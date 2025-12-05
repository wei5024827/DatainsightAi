#!/usr/bin/env python3
"""
DataInsight AI 后端API测试脚本
"""

import requests
import json

# API基础URL
BASE_URL = "http://localhost:8000"


def test_schema():
    """测试获取数据库结构"""
    print("=== 测试数据库结构接口 ===")
    try:
        response = requests.get(f"{BASE_URL}/schema")
        if response.status_code == 200:
            schema = response.json()
            print("✅ 数据库结构获取成功")
            print(f"数据库表数量: {len(schema['schema'])}")
            for table_name, columns in schema["schema"].items():
                print(f"  - {table_name}: {len(columns)}个字段")
        else:
            print(f"❌ 获取失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 连接失败: {e}")


def test_nl2sql(question):
    """测试自然语言转SQL"""
    print(f"\n=== 测试自然语言转SQL: '{question}' ===")
    try:
        response = requests.post(f"{BASE_URL}/nl2sql", json={"text": question})
        if response.status_code == 200:
            result = response.json()
            print("✅ SQL生成成功")
            print(f"生成的SQL: {result['sql']}")
            print(f"原始输出: {result['raw_output'][:100]}...")
            return result["sql"]
        else:
            print(f"❌ 转换失败: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ 连接失败: {e}")
    return None


def test_query(sql):
    """测试SQL执行"""
    print(f"\n=== 测试SQL执行: '{sql}' ===")
    try:
        response = requests.post(f"{BASE_URL}/query", json={"sql": sql})
        if response.status_code == 200:
            result = response.json()
            print("✅ SQL执行成功")
            print(66666666, result)
            if len(result) > 0:
                print(f"返回行数: {len(result)}")
                print("前5行数据:")
                for i, row in enumerate(result[:5]):
                    print(f"  第{i+1}行: {row}")
            else:
                print("查询结果为空")
        else:
            print(f"❌ 执行失败: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ 连接失败: {e}")


def main():
    """主测试函数"""
    print("🚀 DataInsight AI 后端API测试")
    print("=" * 50)

    # 1. 测试数据库结构
    test_schema()

    # 2. 测试自然语言转SQL
    # test_questions = [
    #     "查询所有用户",
    #     "统计北京的用户数量",
    #     "查询订单总金额",
    #     "显示最近7天的订单",
    #     "查询价格最高的产品",
    # ]
    test_questions = ["统计北京的用户数量",]

    for question in test_questions:
        sql = test_nl2sql(question)
        if sql:
            # 3. 测试SQL执行
            test_query(sql)

    print("\n" + "=" * 50)
    print("📖 更多测试方法:")
    print("1. 访问API文档: http://localhost:8000/docs")
    print("2. 使用curl命令测试")
    print("3. 使用Postman等API测试工具")


if __name__ == "__main__":
    # main()
    print('-------------------------')
    test_query("SELECT * FROM users;")
    print('-------------------------')
