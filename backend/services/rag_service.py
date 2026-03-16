import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from services.vector_service import VectorService
from database import SessionLocal, KnowledgeDatasource, KnowledgeTableSchema, ChatMessage

class RAGService:
    def __init__(self, deepseek_api_key, sql_service):
        self.deepseek_api_key = deepseek_api_key
        self.sql_service = sql_service
        self.deepseek_api_url = "https://api.deepseek.com/v1/chat/completions"
        self.vector_service = VectorService()
        
        # 配置重试机制
        self.session = requests.Session()
        retry = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["POST"]
        )
        adapter = HTTPAdapter(max_retries=retry)
        self.session.mount("https://", adapter)
    
    def build_schema_context(self, datasource_id):
        # 从数据库动态构建 Schema 描述
        db = SessionLocal()
        try:
            schemas = db.query(KnowledgeTableSchema).filter(KnowledgeTableSchema.datasource_id == datasource_id).all()
            
            schema_map = {}
            for schema in schemas:
                if schema.table_name not in schema_map:
                    schema_map[schema.table_name] = []
                
                col_def = f"- {schema.column_name} ({schema.column_type})"
                if schema.column_comment:
                    col_def += f" : {schema.column_comment}"
                if schema.is_primary_key:
                    col_def += " [PK]"
                
                schema_map[schema.table_name].append(col_def)
            
            context = ""
            for table, cols in schema_map.items():
                context += f"Table: {table}\n" + "\n".join(cols) + "\n\n"
            
            return context
        finally:
            db.close()

    def build_prompt(self, query, retrieved_docs, metadatas=None):
        # 检查是否包含数据库 Schema
        is_sql_query = False
        schema_context = ""
        normal_docs = []
        datasource_id = None
        
        if metadatas:
            for i, meta in enumerate(metadatas):
                if meta.get('source') == 'database_schema':
                    is_sql_query = True
                    # 尝试获取 datasource_id 并动态构建最新的 Schema
                    ds_id = meta.get('datasource_id')
                    if ds_id:
                        datasource_id = ds_id
                        schema_context = self.build_schema_context(ds_id)
                        break # 只需要一个 Schema 上下文即可
                    else:
                        # 兼容旧逻辑，使用 doc 文本
                        if i < len(retrieved_docs):
                            schema_context = retrieved_docs[i]
                            break
        
        # 如果没有通过 metadata 找到，尝试通过 doc 内容判断（兼容旧逻辑）
        if not is_sql_query:
            for doc in retrieved_docs:
                if "Table " in doc and "Database Schema" in doc: 
                    is_sql_query = True
                    schema_context += doc + "\n\n"
                else:
                    normal_docs.append(doc)

        if is_sql_query:
            # Text-to-SQL Prompt
            prompt = f"""你是SQL专家。请根据以下数据库结构，将用户的自然语言问题转换为SQL查询语句。

数据库结构：
{schema_context}

用户问题：
{query}

请遵循以下规则：
1. 只返回 SQL 语句，不要包含 markdown 格式（如 ```sql ... ```），也不要包含任何解释。
2. 确保 SQL 语法正确，兼容 MySQL。
3. 这是一个只读操作，只能使用 SELECT 语句。

SQL："""
            return prompt, True, datasource_id # 返回 datasource_id 以便后续查询
            
        context = "\n\n".join(normal_docs)
        
        prompt = f"""请遵循以下行为规范：
1. 回复风格：自然、友好、结构清晰，避免一次性输出过长文本。
2. 思考过程：在回答复杂问题前，可以先简要说明你的思考方向，使用格式：
[思考]：简要说明你如何理解问题
[回答]：给出最终答案
如果问题简单，可以直接回答，不必显示思考部分。
3. 交互体验：在开始回答复杂问题时，可以先输出"让我思考一下..."。
4. 知识回答：请根据以下参考文档回答用户的问题。如果参考文档中没有相关信息，请使用您的知识回答，但请说明信息来自通用知识。

参考文档：
{context}

用户问题：
{query}

回答："""
        return prompt, False, None
    
    def get_chat_history(self, session_id, limit=5):
        if not session_id:
            return []
            
        db = SessionLocal()
        try:
            # 获取最近的 N 条消息，按时间倒序
            messages = db.query(ChatMessage).filter(ChatMessage.session_id == session_id).order_by(ChatMessage.create_time.desc()).limit(limit).all()
            # 转为正序并转换为字典，避免 DetachedInstanceError
            return [
                {'role': msg.role, 'content': msg.content, 'id': msg.id} 
                for msg in sorted(messages, key=lambda x: x.id)
            ]
        finally:
            db.close()

    def query(self, user_query, top_k=3, stream=False, knowledge_id=None, session_id=None):
        try:
            where = None
            if knowledge_id:
                where = {"knowledge_id": str(knowledge_id)}
                
            search_results = self.vector_service.similarity_search(user_query, n_results=top_k, where=where)
            
            documents = search_results['documents'][0] if search_results['documents'] else []
            metadatas = search_results['metadatas'][0] if 'metadatas' in search_results and search_results['metadatas'] else []
            
            # 获取历史上下文
            history_messages = self.get_chat_history(session_id)
            history_context = ""
            if history_messages:
                history_context = "历史对话：\n"
                for msg in history_messages:
                    role_name = "用户" if msg['role'] == 'user' else "AI"
                    history_context += f"{role_name}: {msg['content']}\n"
                history_context += "\n"
            
            if not documents:
                # ... (no documents prompt logic)
                prompt = f"""请遵循以下行为规范：
1. 回复风格：自然、友好、结构清晰。
2. 思考过程：使用[思考]...[回答]格式。
3. 交互体验：可以先输出"让我思考一下..."。

{history_context}
用户问题：{user_query}"""
                is_sql_mode = False
                target_datasource_id = None
            else:
                prompt, is_sql_mode, target_datasource_id = self.build_prompt(user_query, documents, metadatas)
                
                # 将历史记录插入到 Prompt 中
                if is_sql_mode:
                    # 对于 SQL 模式，历史记录可能有助于理解上下文（例如“刚才查的那些人里...”）
                    # 但为了简化，暂不修改 SQL Prompt 结构，或者简单附加在问题前
                    # 更好的做法是让 LLM 理解上下文
                    prompt = prompt.replace("用户问题：\n", f"{history_context}用户问题：\n")
                else:
                    # 普通 RAG 模式
                    prompt = prompt.replace("用户问题：\n", f"{history_context}用户问题：\n")
                
                if is_sql_mode:
                    # Text-to-SQL 流程
                    # ... (call LLM to get SQL)
                    sql_query = self.call_deepseek_api(prompt, stream=False)
                    sql_query = sql_query.replace('```sql', '').replace('```', '').strip()
                    
                    # 执行 SQL
                    db = SessionLocal()
                    try:
                        # 优先使用 build_prompt 返回的 datasource_id，如果没有则尝试从数据库查找
                        ds = None
                        if target_datasource_id:
                            ds = db.query(KnowledgeDatasource).filter(KnowledgeDatasource.id == target_datasource_id).first()
                        
                        if not ds:
                            # 兼容旧逻辑：如果只通过文本匹配到了 schema 但没有 datasource_id，尝试通过 knowledge_id 查找
                            # 注意：这种情况下可能会有多个数据源，这里只取第一个
                            ds = db.query(KnowledgeDatasource).filter(KnowledgeDatasource.knowledge_id == knowledge_id).first()
                            
                        if ds:
                            query_result = self.sql_service.execute_query(
                                ds.db_type, ds.host, ds.port, ds.username, ds.password, ds.database_name, sql_query
                            )
                            # ... (format result logic)
                            columns = query_result['columns']
                            data = query_result['data']
                            
                            markdown_table = "| " + " | ".join(columns) + " |\n"
                            markdown_table += "| " + " | ".join(["---"] * len(columns)) + " |\n"
                            
                            for row in data:
                                # 处理每一行数据，确保 bytes 类型被解码
                                formatted_row = []
                                for col in columns:
                                    val = row.get(col, '')
                                    if isinstance(val, bytes):
                                        # 尝试解码 bytes，如果是 b'\x01' 这种通常是 bit(1) -> boolean
                                        if len(val) == 1:
                                            # 处理 bit(1)
                                            val = ord(val)
                                        else:
                                            try:
                                                val = val.decode('utf-8')
                                            except:
                                                val = str(val) # 无法解码则转字符串
                                    formatted_row.append(str(val))
                                markdown_table += "| " + " | ".join(formatted_row) + " |\n"
                                
                            final_response = f"""[思考]：
1.  **意图识别**: 用户希望查询数据库中的信息。
2.  **SQL生成**: 根据 Schema 生成了 SQL: `{sql_query}`。
3.  **执行结果**: 执行成功，共检索到 {len(data)} 条记录。

[回答]：
以下是为您查询到的结果：

{markdown_table}
"""
                            if stream:
                                import time
                                def generator():
                                    chunk_size = 10
                                    for i in range(0, len(final_response), chunk_size):
                                        yield final_response[i:i+chunk_size]
                                        time.sleep(0.01)
                                return generator()
                                
                            return final_response
                        else:
                            return "无法找到关联的数据源配置，无法执行 SQL 查询。"
                    except Exception as e:
                         return f"执行 SQL 失败: {str(e)} (SQL: {sql_query})"
                    finally:
                        db.close()
            
            if stream:
                return self.call_deepseek_api(prompt, stream=True)
            
            response = self.call_deepseek_api(prompt)
            
            return {
                'answer': response,
                'retrieved_docs': documents
            }
        except Exception as e:
            raise Exception(f"RAG查询失败: {str(e)}")
    
    def call_deepseek_api(self, prompt, stream=False):
        headers = {
            'Authorization': f'Bearer {self.deepseek_api_key}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'model': 'deepseek-chat',
            'messages': [
                {'role': 'user', 'content': prompt}
            ],
            'stream': stream
        }
        
        response = self.session.post(self.deepseek_api_url, headers=headers, json=payload, timeout=60, stream=stream)
        response.raise_for_status()
        
        if stream:
            return response
            
        result = response.json()
        return result['choices'][0]['message']['content']
