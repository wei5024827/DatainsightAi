# DatainsightAi
## 1. 项目简介
基于 LLM 的智能数据分析与 NL2SQL 平台
业务输入自然语言->text2vec将自然语言转换为向量->RAG检索需要的schema->将检索到的schema上下文添加到自然语言->LLM生成SQL
系统通过AI将自然语言生成 SQL，通过数据库执行查询，自动生成图表可视化的展示结果

## 2. 技术栈
- Backend: 
  - Python,FastAPI
- RAG:
  - text2vec + FAISS
- LLM: 
  - DeepSeek API
- Frontend: 
  - React + ECharts
- Database: 
  - DuckDB

## 3. 安装与运行

#### 1. 克隆项目
```bash {cmd=true}
git clone https://github.com/reslack/datainsight-ai.git
cd datainsight-ai
```

#### 2. 启动项目
```bash {cmd=true}
##启动后端
cd backend
./app-manager.sh start
#或者直接运行
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

##启动前端
cd frontend
pnpm dev --host 0.0.0.0
```

#### 3. 查看样例

https://localhost:5173/

![alt text](Demo-1.gif)

## 4. 项目架构图

![alt text](image-1.png)




## 5. API文档
- 可直接访问**FastAPI**内置文档：http://localhost:8000/docs
- API列表：
  
    | name   | type | url     | description           |
    | ------ | ---- | -------- | ------------------ |
    | LLM    | POST | /nl2sql  | 返回 LLM 响应的 SQL |
    | Query  | POST | /query   | 返回查询 SQL        |
    | Schema | GET  | /schema  | 获取数据库元数据    |
    | RAG Seach | GET  | /rag/search  | RAG检索    |

## 6. 项目目录结构
```
datainsight-ai/
├─ app-manager.sh
├─ README.md
├─ backend/
│  ├─ backend-manager.sh  # 后端管理脚本
│  ├─ init_db.py          # 初始化数据库脚本
│  └─ app/
│     ├─ main.py
│     ├─ api/
│     │  └─ v1/
│     │     ├─ nl2sql.py
│     │     ├─ query.py
│     │     ├─ rag.py
│     │     └─ schema.py
│     ├─ core/
│     │  ├─ llm_client.py
│     │  ├─ query_executor.py
│     │  └─ schema_index.py
│     ├─ models/
│     │  └─ nl_request.py
│     └─ utils/
│        └─ sql_parser.py
├─ frontend/
│  ├─ package.json
│  ├─ pnpm-lock.yaml
│  ├─ vite.config.js
│  ├─ eslint.config.js
│  ├─ index.html
│  ├─ src/
│  │  ├─ main.jsx
│  │  ├─ App.jsx
│  │  ├─ App.css
│  │  └─ index.css
│  ├─ css/styles.css
│  └─ js/app.js
└─ log/
   ├─ app.log
   ├─ backend.log
   └─ frontend.log 

```
## 7. 项目文件说明
- `nl2sql.py`:`nl2sql_handler()` 处理NL2SQL请求，返回LLM响应的SQL
  - step1: `schema_index.init_schema_index()` 获取所有表的scheme，将scheme向量化，存储到FAISS索引中
  - step2: `schema_index.get_relevant_tables()` 根据用户输入的自然语言，从FAISS索引中检索相关的表
  - step3: `schema_index.format_tables_for_prompt()` 将检索到的表信息格式化为字符串，用于添加到自然语言中
  - step4: `llm_client.generate_sql()` 将自然语言和格式化后的表信息发送给LLM，获取SQL响应
  - step5: `sql_parser.parse_sql()` 从LLM返回SQL后，用正则处理，提取SQL语句
  - step6: `query_executor.execute_query()` 执行SQL查询，返回结果
- `query.py` 查询接口
- `rag.py` RAG 检索接口,用于接口测试
  - `get_all_tables()` 获取数据库所有表
  - `rag_search()` 用于测试RAG检索接口
- `schema.py` 获取数据库所有元数据接口
  - `get_table()`：show table获取所有表
  - `get_table_schema()`: duckdb默认表duckdb_columns获取
  - `get_table_comment()`: 获取表的注释，为了让embeding模型更容易理解表是做什么的
  - `get_full_schema()`: 通过以上三个函数获取所有表的信息，返回schema json,返回样例：
  ```json
  {
  "tables": {
    "table_name:categories;comment:商品分类，如数码、美妆、食品等": [
      {
        "name": "category_id",
        "type": "INTEGER",
        "comment": "分类主键 ID",
        "cid": 1
      },
      {
        "name": "category_name",
        "type": "VARCHAR",
        "comment": "分类名称",
        "cid": 2
      }
    ]}
  ```
- `query_executor.py` 查询执行器
  - `execute_query()` 执行SQL查询，返回结果
- `schema_index.py` 索引数据库元数据，RAG检索
  - `_get_embedding_model()` 获取embedding模型，默认使用text2vec（bge-large-zh对中文支持好）
  - `_table_meta_to_text` 将schema转为文本
  - `init_schema_index()` 将所有表的文本向量化，存储到FAISS索引中
  - `get_relevant_tables` 根据用户输入的自然语言，从FAISS索引中检索相关的表
  - `format_tables_for_prompt`: 将检索到的表信息格式化为字符串，用于添加到自然语言中,返回样例：
  ```json
  {
  "query": "查询用户订单金额",
  "matched_tables": [
    {
      "table_name": "table_name:orders;comment:订单主表",
      "score": 136.9623260498047,
      "columns": [
        {
          "name": "order_id",
          "type": "INTEGER",
          "comment": "订单主键 ID",
          "cid": 1
        },
        {
          "name": "user_id",
          "type": "INTEGER",
          "comment": "用户 ID",
          "cid": 2
        },
        {
          "name": "order_date",
          "type": "DATE",
          "comment": "订单创建时间",
          "cid": 3
        }
      ]
    }
  ],
  "formatted_schema": "表 table_name:orders;comment:订单主表:\n  - order_id INTEGER\n  - user_id INTEGER\n  - order_date DATE\n  - status VARCHAR\n  - total_amount DOUBLE\n\n表 table_name:order_items;comment:订单明细表:\n  - item_id INTEGER\n  - order_id INTEGER\n  - product_id INTEGER\n  - quantity INTEGER\n  - amount DOUBLE\n\n表 table_name:payments;comment:订单支付记录表:\n  - payment_id INTEGER\n  - order_id INTEGER\n  - pay_method VARCHAR\n  - pay_amount DOUBLE\n  - pay_time DATE\n\n表 table_name:categories;comment:商品分类，如数码、美妆、食品等:\n  - category_id INTEGER\n  - category_name VARCHAR\n\n表 table_name:inventory;comment:商品库存表（按仓库维度统计）:\n  - product_id INTEGER\n  - warehouse VARCHAR\n  - stock INTEGER\n"
  }
  ```
- `llm_client.py` LLM 客户端
  - `get_llm_response()` 调用LLM API(此项目使用deepseek-chat模型)，返回响应
- `nl_request.py` pydantic模型，定义NL2SQL请求的参数
- `sql_parser.py` SQL 解析器
  - `parse_sql()` 从LLM返回SQL后，用正则处理，提取SQL语句
- `main.py` 项目入口文件，启动FastAPI服务
- `init_db.py` 初始化数据库脚本(可选)

## 8. TODO
- 支持更多数据库类型
- 前端支持更多图表类型
- LLM切换为本地大模型，兼容OpenAI API



## 9. 常见问题
- duckdb文件被锁住
```bash {cmd=true}
lsof /home/reslack/opt/github/datainsight-ai/example.duckdb
kill -9 PID
```