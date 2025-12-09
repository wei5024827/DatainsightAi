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

## 3. 运行方法

#### 1. 启动项目
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

#### 2. 查看样例

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


## 7. 未来工作
- 支持更多数据库类型
- 前端支持更多图表类型
- LLM切换为本地大模型，兼容OpenAI API



## 8. 常见问题
- duckdb文件被锁住
```bash {cmd=true}
lsof /home/reslack/opt/github/datainsight-ai/example.duckdb
kill -9 PID
```