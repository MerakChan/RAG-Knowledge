# 企业知识库 RAG 系统 (AI Knowledge Platform)

这是一个基于检索增强生成 (RAG) 技术的企业级智能知识库问答系统。它允许用户上传文档、连接数据库，并通过大语言模型 (LLM) 进行基于内部知识的上下文对话。

## 🌟 核心功能

*   **📊 系统看板**: 可视化展示系统整体规模（知识库数、文档数、总问答数等），并提供近7天问答趋势折线图和最新问答记录。
*   **📚 知识库管理**: 支持创建多个独立的知识库，每个知识库可以配置不同的 Embedding 模型和向量数据库。
*   **📄 多源数据接入**:
    *   **本地文档**: 支持上传 TXT, PDF, DOCX, MD, RTF 等格式文档，自动解析并进行文本分块。
    *   **手动输入**: 支持直接在页面手动录入结构化文本。
    *   **数据库接入 (Text-to-SQL)**: 支持连接外部 MySQL 数据库，自动提取表结构 (Schema)，允许 AI 直接编写并执行 SQL 来回答数据类问题。
*   **💬 AI 智能对话**:
    *   **多会话管理**: 每个知识库下支持创建多个对话会话，方便管理不同主题的聊天。
    *   **上下文记忆**: 自动保存聊天记录到数据库，并在提问时携带历史上下文，使 AI 能够进行多轮连贯对话。
    *   **流式输出 (Streaming)**: 支持打字机效果的流式输出，提升用户体验。
    *   **思维链展示**: 能够展示 AI 的思考过程（[思考]...[回答] 格式）。
    *   **Markdown & 表格渲染**: 支持在对话框中完美渲染 Markdown 格式文本和数据表格。

## 🛠️ 技术栈

### 后端 (Backend)
*   **框架**: Python Flask
*   **数据库 ORM**: SQLAlchemy
*   **数据库**: MySQL (`pymysql`)
*   **向量数据库**: ChromaDB / FAISS
*   **LLM 接口**: DeepSeek API
*   **文本处理**: `langchain`, `sentence-transformers`, `pdfplumber`, `python-docx`, `striprtf`

### 前端 (Frontend)
*   **核心**: 原生 HTML5, CSS3, JavaScript (Vanilla JS)
*   **图表**: ECharts (通过 CDN 引入)
*   **架构**: 单页应用 (SPA) 架构，通过 JavaScript 控制视图切换。

## 📂 项目结构

```text
ai-knowledge-platform/
├── backend/                  # 后端代码目录
│   ├── services/             # 核心业务逻辑服务
│   │   ├── chunk_service.py    # 文本分块服务
│   │   ├── document_service.py # 文档解析服务
│   │   ├── rag_service.py      # RAG & LLM 对话核心服务
│   │   ├── sql_service.py      # 数据库连接与 Schema 提取服务
│   │   └── vector_service.py   # 向量数据库服务
│   ├── app_new.py            # Flask 应用入口 & 路由控制器
│   ├── database.py           # 数据库模型 (SQLAlchemy) & 连接配置
│   └── config.py             # 配置文件
├── frontend/                 # 前端代码目录
│   ├── index.html            # 主界面 (Dashboard, 知识库, 聊天室)
│   ├── chat.js               # 聊天逻辑、会话管理、API 交互
│   ├── login.html            # 登录界面
│   └── login.js              # 登录逻辑
├── requirements.txt          # Python 依赖清单
└── README.md                 # 项目说明文档
```

## 🚀 快速开始

### 1. 环境准备

确保您的系统中已安装以下软件：
*   Python 3.8+
*   MySQL 8.0+

### 2. 数据库配置

1. 在 MySQL 中创建一个名为 `myfinal-work` 的数据库，字符集设置为 `utf8mb4`。
   ```sql
   CREATE DATABASE `myfinal-work` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   ```
2. 修改 `backend/database.py` 中的 `DB_URL` 为您本地的 MySQL 连接信息：
   ```python
   DB_URL = "mysql+pymysql://root:你的密码@localhost:3306/myfinal-work?charset=utf8mb4"
   ```

### 3. 安装依赖

进入项目根目录，安装 Python 依赖包：

```bash
pip install -r requirements.txt
```

### 4. 启动服务

进入 `backend` 目录，启动 Flask 后端服务：

```bash
cd backend
python app_new.py
```
*服务默认运行在 `http://127.0.0.1:8080`*

### 5. 访问系统

打开浏览器，访问 `http://127.0.0.1:8080` 即可进入登录页面。
*(当前系统默认账号：admin / 123456)*

## 💡 使用指南

1. **新建知识库**：进入“知识库管理”，点击“新建知识库”。
2. **导入数据**：在知识库卡片上点击“管理文档”，可以通过“上传文档”、“手动输入”或“连接数据库”来丰富知识库。
3. **开始对话**：点击左侧菜单的“AI对话助手”，在左上角下拉框选择刚才创建的知识库，点击“新建会话”即可开始提问。

## ⚠️ 注意事项

*   **API Key**: 项目中目前硬编码了一个测试用的 DeepSeek API Key (在 `app_new.py` 中)。在生产环境中，请务必替换为您自己的 API Key，并通过环境变量进行管理。
*   **模型下载**: 首次运行时，`sentence-transformers` 可能会自动从 HuggingFace 下载 Embedding 模型，这需要一定时间并保持网络畅通。
*   **Text-to-SQL**: 连接外部数据库进行问答时，请确保提供的数据库用户具有只读权限，以防止 AI 生成破坏性 SQL。

## 截图展示
![界面截图](屏幕截图 2026-03-16 174659.png)
![界面截图](屏幕截图 2026-03-16 174706.png)
![界面截图](屏幕截图 2026-03-16 174712.png)
![界面截图](屏幕截图 2026-03-16 174717.png)
![界面截图](屏幕截图 2026-03-16 174721.png)
