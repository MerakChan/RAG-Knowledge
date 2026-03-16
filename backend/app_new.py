from flask import Flask, send_from_directory, request, jsonify, Response, stream_with_context
from flask_cors import CORS
import os
import uuid
import json
from werkzeug.utils import secure_filename
from sqlalchemy.orm import Session
from sqlalchemy import func, distinct, cast, Date
from datetime import datetime, date, timedelta
from database import SessionLocal, KnowledgeBase, KnowledgeData, KnowledgeChunk, KnowledgeItem, KnowledgeDocument, KnowledgeDatasource, KnowledgeTableSchema, ChatSession, ChatMessage, init_db

from services.document_service import DocumentService
from services.sql_service import SQLService
from services.chunk_service import ChunkService
from services.vector_service import VectorService
from services.rag_service import RAGService

app = Flask(__name__)
CORS(app)

# 初始化数据库
# 注意：在生产环境中通常使用迁移工具，这里简单起见直接调用
# init_db() # 表已经存在，可以注释掉

# 数据库会话依赖
def get_db_session():
    return SessionLocal()

# 配置
DEEPSEEK_API_KEY = "sk-f99dbcc54bef432ea5a9ecff869ddde4"
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), '..', 'data', 'uploads')
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'docx', 'doc', 'rtf', 'md'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# 初始化服务
sql_service = SQLService()
document_service = DocumentService()
chunk_service = ChunkService(chunk_size=500, overlap=50)
vector_service = VectorService()
rag_service = RAGService(DEEPSEEK_API_KEY, sql_service)
rag_service.vector_service = vector_service

# 历史记录存储
chat_history = []

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/")
def index():
    frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'frontend'))
    return send_from_directory(frontend_dir, 'login.html')

@app.route('/<path:path>')
def serve_static(path):
    frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'frontend'))
    return send_from_directory(frontend_dir, path)

# 文件上传接口
@app.route('/api/upload', methods=['POST'])
def upload():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file part'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type'}), 400
        
        # 保存文件
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        # 获取 knowledge_id
        knowledge_id = request.form.get('knowledgeId')
        if not knowledge_id:
            return jsonify({'error': 'knowledgeId is required'}), 400
            
        db = get_db_session()
        try:
            # 1. 记录到 knowledge_item 表
            new_item = KnowledgeItem(
                knowledge_id=knowledge_id,
                title=filename,
                source_type='file',
                file_name=filename,
                file_path=file_path,
                status='processing'
            )
            db.add(new_item)
            db.commit()
            db.refresh(new_item)

            # 解析文档
            text = document_service.parse_document(file_path)
            
            # 更新 content
            new_item.content = text
            
            # 文本分块
            chunks = chunk_service.split_text(text)
            
            # 更新 chunk_count
            new_item.chunk_count = len(chunks)
            
            # 添加到向量数据库
            doc_ids = [str(uuid.uuid4()) for _ in range(len(chunks))]
            metadatas = [{
                'knowledge_id': str(knowledge_id),
                'item_id': str(new_item.id),
                'filename': filename, 
                'source': 'file',
                'chunk': i
            } for i in range(len(chunks))]
            
            vector_service.add_documents(chunks, ids=doc_ids, metadatas=metadatas)
            
            # 更新状态
            new_item.status = 'finished'
            db.commit()
            
            return jsonify({
                'message': '文档上传成功',
                'filename': filename,
                'chunks': len(chunks)
            })
        except Exception as e:
            db.rollback()
            return jsonify({'error': str(e)}), 500
        finally:
            db.close()
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# 手动输入知识接口
@app.route('/api/knowledge/data/manual', methods=['POST'])
def add_manual_knowledge():
    data = request.get_json()
    knowledge_id = data.get('knowledgeId')
    title = data.get('title')
    content = data.get('content')
    
    if not knowledge_id or not content:
        return jsonify({'error': 'Knowledge ID and content are required'}), 400
        
    db = get_db_session()
    try:
        # 1. 保存 knowledge_item
        new_item = KnowledgeItem(
            knowledge_id=knowledge_id,
            title=title,
            content=content,
            source_type='manual',
            status='processing'
        )
        db.add(new_item)
        db.commit()
        db.refresh(new_item)
        
        # 2. 文本切分
        chunks = chunk_service.split_text(content)
        
        # 3. 更新 chunk_count
        new_item.chunk_count = len(chunks)
        
        # 4. 存入向量数据库
        doc_ids = [str(uuid.uuid4()) for _ in range(len(chunks))]
        metadatas = [{
            'knowledge_id': str(knowledge_id),
            'item_id': str(new_item.id),
            'source': 'manual',
            'title': title or '',
            'chunk': i
        } for i in range(len(chunks))]
        
        vector_service.add_documents(chunks, ids=doc_ids, metadatas=metadatas)
        
        # 更新状态
        new_item.status = 'finished'
        db.commit()
        
        return jsonify({
            'message': '知识添加成功',
            'item_id': new_item.id,
            'chunks_count': len(chunks)
        })
        
    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()

from datetime import datetime

# ----------------- 聊天会话管理接口 -----------------

@app.route('/api/chat/sessions', methods=['GET'])
def get_chat_sessions():
    knowledge_id = request.args.get('knowledge_id')
    if not knowledge_id:
        return jsonify({'error': 'knowledge_id is required'}), 400
        
    db = get_db_session()
    try:
        sessions = db.query(ChatSession).filter(ChatSession.knowledge_id == knowledge_id).order_by(ChatSession.update_time.desc()).all()
        return jsonify([session.to_dict() for session in sessions])
    finally:
        db.close()

@app.route('/api/chat/session/create', methods=['POST'])
def create_chat_session():
    data = request.get_json()
    knowledge_id = data.get('knowledgeId') or data.get('knowledge_id')
    
    if not knowledge_id:
        return jsonify({'error': 'knowledgeId is required'}), 400
        
    db = get_db_session()
    try:
        # 自动生成会话名称，例如 "会话 2023-10-27 10:00"
        session_name = f"会话 {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        
        new_session = ChatSession(
            knowledge_id=knowledge_id,
            session_name=session_name
        )
        db.add(new_session)
        db.commit()
        db.refresh(new_session)
        return jsonify(new_session.to_dict())
    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()

@app.route('/api/chat/messages', methods=['GET'])
def get_chat_messages():
    session_id = request.args.get('session_id')
    if not session_id:
        return jsonify({'error': 'session_id is required'}), 400
        
    db = get_db_session()
    try:
        messages = db.query(ChatMessage).filter(ChatMessage.session_id == session_id).order_by(ChatMessage.id.asc()).all()
        return jsonify([msg.to_dict() for msg in messages])
    finally:
        db.close()

@app.route('/api/chat/session/<int:session_id>', methods=['DELETE'])
def delete_chat_session(session_id):
    db = get_db_session()
    try:
        session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
        if not session:
            return jsonify({'error': 'Session not found'}), 404
            
        # 手动级联删除消息
        db.query(ChatMessage).filter(ChatMessage.session_id == session_id).delete()
        
        # 删除会话
        db.delete(session)
        db.commit()
        return jsonify({'message': 'Session deleted successfully'})
    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()

# RAG提问接口 (更新版)
@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        message = data.get('message', '')
        knowledge_id = data.get('knowledgeId') or data.get('knowledge_id')
        session_id = data.get('sessionId') or data.get('session_id') # 支持两种命名风格
        
        if not message:
            return jsonify({'error': 'Message is required'}), 400
            
        if not session_id:
            # 如果没有 session_id，应该先创建会话，这里为了简化，报错或者自动创建
            # 前端应该保证传递 session_id
            return jsonify({'error': 'Session ID is required'}), 400
        
        # 1. 保存用户消息
        db = get_db_session()
        try:
            user_msg = ChatMessage(
                session_id=session_id,
                role='user',
                content=message
            )
            db.add(user_msg)
            
            # 更新会话时间
            session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
            if session:
                session.update_time = datetime.now()
                # 如果是新会话的第一条消息，可以用消息内容更新会话名称
                # 简单判断：如果只有这一条消息
                msg_count = db.query(ChatMessage).filter(ChatMessage.session_id == session_id).count()
                if msg_count == 0: # 刚插入的这条还没提交，所以是0？不对，add了但没commit
                     # 在同一个 transaction 中，count 应该能看到？或者直接更新
                     session.session_name = message[:20] # 截取前20个字
            
            db.commit()
        except Exception as e:
            db.rollback()
            return jsonify({'error': f'保存消息失败: {str(e)}'}), 500
        finally:
            db.close()
        
        def generate():
            full_answer = ""
            try:
                # 获取流式响应，传入 knowledge_id 和 session_id (用于上下文)
                response = rag_service.query(message, top_k=3, stream=True, knowledge_id=knowledge_id, session_id=session_id)
                
                # 判断 response 类型
                if hasattr(response, 'iter_lines'):
                    # 这是 requests.Response 对象 (DeepSeek API 流式)
                    iterator = response.iter_lines()
                    for line in iterator:
                        if line:
                            line = line.decode('utf-8')
                            if line.startswith('data: '):
                                json_str = line[6:] # 去掉 'data: ' 前缀
                                if json_str == '[DONE]':
                                    break
                                try:
                                    chunk_data = json.loads(json_str)
                                    if 'choices' in chunk_data and len(chunk_data['choices']) > 0:
                                        delta = chunk_data['choices'][0].get('delta', {})
                                        content = delta.get('content', '')
                                        if content:
                                            full_answer += content
                                            yield content
                                except json.JSONDecodeError:
                                    pass
                else:
                    # 这是 Python generator 对象 (本地生成的 SQL 结果流)
                    for content in response:
                        full_answer += content
                        yield content
                
                # 在流结束时保存 AI 回答
                if full_answer:
                    # 使用新的 session 来保存，避免线程问题
                    db_inner = get_db_session()
                    try:
                        ai_msg = ChatMessage(
                            session_id=session_id,
                            role='assistant',
                            content=full_answer
                        )
                        db_inner.add(ai_msg)
                        db_inner.commit()
                    except Exception as e:
                        print(f"Error saving AI response: {e}")
                    finally:
                        db_inner.close()
                    
            except Exception as e:
                yield f"Error: {str(e)}"

        return Response(stream_with_context(generate()), mimetype='text/plain')

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# 清除知识库接口
@app.route('/api/knowledge/clear', methods=['POST'])
def clear_knowledge():
    knowledge_id = request.args.get('knowledge_id')
    
    if not knowledge_id:
        # 如果没有传 ID，暂时不支持全局清除，或者报错
        return jsonify({'error': 'knowledge_id is required'}), 400

    db = get_db_session()
    try:
        # 1. 获取该知识库下的所有 item
        items = db.query(KnowledgeItem).filter(KnowledgeItem.knowledge_id == knowledge_id).all()
        
        # 2. 从向量数据库中删除
        # 由于 vector_service 可能不支持 where knowledge_id (取决于实现)，我们先遍历删除
        # 或者 vector_service.collection.delete(where={"knowledge_id": str(knowledge_id)})
        # 假设 metadata 中有 knowledge_id
        try:
             vector_service.collection.delete(where={"knowledge_id": str(knowledge_id)})
        except Exception as e:
             print(f"Vector delete error: {e}")
             
        # 3. 删除数据库记录
        db.query(KnowledgeItem).filter(KnowledgeItem.knowledge_id == knowledge_id).delete()
        
        # 4. 删除 chat_session 和 chat_message (可选，用户可能想保留聊天记录但清除文档？)
        # 用户说 "清除该知识库下的所有文档"，所以应该只清除文档。
        
        # 5. 删除文件 (可选，如果只是逻辑删除)
        # 这里比较复杂，因为 file_path 是绝对路径。
        # 简单起见，暂不物理删除文件，或者后续添加垃圾清理任务
        
        db.commit()
        return jsonify({'message': '知识库文档已成功清除'})
    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()

# 历史记录接口
@app.route('/api/history', methods=['GET'])
def get_history():
    return jsonify({'history': chat_history})

# --- 新功能接口预留 ---

# 1. 系统看板接口
@app.route('/api/dashboard/stats', methods=['GET'])
def get_dashboard_stats():
    db = get_db_session()
    try:
        today = date.today()
        
        # --- 模块一：系统总体统计 ---
        kb_count = db.query(KnowledgeBase).count()
        # 文档数量 (假设 KnowledgeItem 中 source_type='file' 或 'manual' 为文档)
        doc_count = db.query(KnowledgeItem).filter(KnowledgeItem.source_type.in_(['file', 'manual'])).count()
        ds_count = db.query(KnowledgeDatasource).count()
        total_qa_count = db.query(ChatMessage).filter(ChatMessage.role == 'assistant').count()
        
        # --- 模块二：今日系统统计 ---
        today_qa_count = db.query(ChatMessage).filter(
            ChatMessage.role == 'assistant',
            cast(ChatMessage.create_time, Date) == today
        ).count()
        
        today_doc_count = db.query(KnowledgeItem).filter(
            KnowledgeItem.source_type.in_(['file', 'manual']),
            cast(KnowledgeItem.create_time, Date) == today
        ).count()
        
        today_kb_count = db.query(KnowledgeBase).filter(
            cast(KnowledgeBase.create_time, Date) == today
        ).count()
        
        today_ds_count = db.query(KnowledgeDatasource).filter(
            cast(KnowledgeDatasource.create_time, Date) == today
        ).count()
        
        # --- 模块三：知识库数据统计 ---
        chunk_count = db.query(KnowledgeChunk).count()
        # 数据库表数量 (去重)
        # 假设 KnowledgeTableSchema 中 id 是唯一的，但我们要统计的是逻辑表的数量
        # 需要对 (datasource_id, table_name) 进行去重统计
        table_count = db.query(func.count(distinct(func.concat(KnowledgeTableSchema.datasource_id, '_', KnowledgeTableSchema.table_name)))).scalar()
        column_count = db.query(KnowledgeTableSchema).count()
        
        # --- 模块四：最近问答记录 ---
        recent_qa = []
        recent_msgs = db.query(ChatMessage).filter(ChatMessage.role == 'user').order_by(ChatMessage.create_time.desc()).limit(5).all()
        for msg in recent_msgs:
            # 获取对应的 KnowledgeBase 名称
            session = db.query(ChatSession).filter(ChatSession.id == msg.session_id).first()
            kb_name = "未知知识库"
            if session:
                kb = db.query(KnowledgeBase).filter(KnowledgeBase.id == session.knowledge_id).first()
                if kb:
                    kb_name = kb.name
            
            recent_qa.append({
                'question': msg.content,
                'kb_name': kb_name,
                'time': msg.create_time.strftime('%H:%M') if msg.create_time else ''
            })
            
        # --- 模块七：系统趋势图 (最近7天) ---
        trend_data = []
        for i in range(6, -1, -1):
            day = today - timedelta(days=i)
            day_str = day.strftime('%m-%d')
            count = db.query(ChatMessage).filter(
                ChatMessage.role == 'assistant',
                cast(ChatMessage.create_time, Date) == day
            ).count()
            trend_data.append({
                'date': day_str,
                'count': count
            })

        return jsonify({
            'overall': {
                'kb_count': kb_count,
                'doc_count': doc_count,
                'ds_count': ds_count,
                'qa_count': total_qa_count
            },
            'today': {
                'qa_count': today_qa_count,
                'doc_count': today_doc_count,
                'kb_count': today_kb_count,
                'ds_count': today_ds_count
            },
            'knowledge': {
                'chunk_count': chunk_count,
                'table_count': table_count or 0,
                'column_count': column_count
            },
            'recent_qa': recent_qa,
            'trend': trend_data
        })
    except Exception as e:
        print(f"Dashboard Error: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()

# 2. 知识库管理接口
@app.route('/api/knowledge/list', methods=['GET'])
def list_knowledge_bases():
    db = get_db_session()
    try:
        kbs = db.query(KnowledgeBase).all()
        return jsonify([kb.to_dict() for kb in kbs])
    finally:
        db.close()

@app.route('/api/knowledge/create', methods=['POST'])
def create_knowledge_base():
    data = request.get_json()
    name = data.get('name')
    if not name:
        return jsonify({'error': 'Knowledge base name is required'}), 400
    
    db = get_db_session()
    try:
        new_kb = KnowledgeBase(
            name=name,
            description=data.get('description'),
            embedding_model=data.get('embedding_model', 'bge-large'),
            vector_store=data.get('vector_store', 'faiss')
        )
        db.add(new_kb)
        db.commit()
        db.refresh(new_kb)
        return jsonify(new_kb.to_dict()), 201
    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()

@app.route('/api/knowledge/update', methods=['PUT'])
def update_knowledge_base():
    data = request.get_json()
    kb_id = data.get('id')
    if not kb_id:
        return jsonify({'error': 'Knowledge base ID is required'}), 400
    
    db = get_db_session()
    try:
        kb = db.query(KnowledgeBase).filter(KnowledgeBase.id == kb_id).first()
        if not kb:
            return jsonify({'error': 'Knowledge base not found'}), 404
        
        if 'name' in data:
            kb.name = data['name']
        if 'description' in data:
            kb.description = data['description']
        if 'embedding_model' in data:
            kb.embedding_model = data['embedding_model']
        if 'vector_store' in data:
            kb.vector_store = data['vector_store']
            
        db.commit()
        db.refresh(kb)
        return jsonify(kb.to_dict())
    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()

@app.route('/api/knowledge/delete/<int:kb_id>', methods=['DELETE'])
def delete_knowledge_base(kb_id):
    db = get_db_session()
    try:
        kb = db.query(KnowledgeBase).filter(KnowledgeBase.id == kb_id).first()
        if not kb:
            return jsonify({'error': 'Knowledge base not found'}), 404
        
        # 级联删除相关文档项
        db.query(KnowledgeItem).filter(KnowledgeItem.knowledge_id == kb_id).delete()
        
        db.delete(kb)
        db.commit()
        return jsonify({'message': 'Knowledge base deleted successfully'})
    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()

# ----------------- 文档/数据项管理接口 -----------------

@app.route('/api/knowledge/items/<int:kb_id>', methods=['GET'])
def list_knowledge_items(kb_id):
    db = get_db_session()
    try:
        items = db.query(KnowledgeItem).filter(KnowledgeItem.knowledge_id == kb_id).order_by(KnowledgeItem.create_time.desc()).all()
        return jsonify([item.to_dict() for item in items])
    finally:
        db.close()

@app.route('/api/knowledge/item/<int:item_id>', methods=['DELETE'])
def delete_knowledge_item(item_id):
    db = get_db_session()
    try:
        item = db.query(KnowledgeItem).filter(KnowledgeItem.id == item_id).first()
        if not item:
            return jsonify({'error': 'Item not found'}), 404
            
        # 注意：这里也需要从向量数据库中删除对应的 chunk
        # 由于我们之前将 item_id 存入了 metadata，我们可以根据 item_id 删除
        if vector_service.use_chroma:
            vector_service.collection.delete(
                where={"item_id": str(item_id)}
            )
            
        db.delete(item)
        db.commit()
        return jsonify({'message': 'Item deleted successfully'})
    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()

# 3. 数据源管理接口
@app.route('/api/datasources', methods=['GET', 'POST'])
def manage_datasources():
    # TODO: 管理数据源
    return jsonify([])

@app.route('/api/datasource/test', methods=['POST'])
def test_datasource_connection():
    data = request.get_json()
    try:
        success, message = sql_service.test_connection(
            data['dbType'], data['host'], data['port'], 
            data['username'], data['password'], data['databaseName']
        )
        if success:
            return jsonify({'message': '连接成功'})
        else:
            return jsonify({'error': message}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/datasource/add', methods=['POST'])
def add_datasource():
    data = request.get_json()
    knowledge_id = data.get('knowledgeId')
    
    if not knowledge_id:
        return jsonify({'error': 'knowledgeId is required'}), 400
        
    db = get_db_session()
    try:
        # 1. 验证连接
        success, message = sql_service.test_connection(
            data['dbType'], data['host'], data['port'], 
            data['username'], data['password'], data['databaseName']
        )
        if not success:
            return jsonify({'error': f'连接测试失败: {message}'}), 400
            
        # 2. 获取 Schema (结构化)
        structured_schema = sql_service.get_schema(
            data['dbType'], data['host'], data['port'], 
            data['username'], data['password'], data['databaseName']
        )
        
        # 3. 保存数据源配置
        new_ds = KnowledgeDatasource(
            knowledge_id=knowledge_id,
            datasource_name=data['datasourceName'],
            db_type=data['dbType'],
            host=data['host'],
            port=data['port'],
            database_name=data['databaseName'],
            username=data['username'],
            password=data['password'] # 实际生产中应加密存储
        )
        db.add(new_ds)
        db.commit()
        db.refresh(new_ds)
        
        # 4. 保存结构化 Schema 到 knowledge_table_schema 表
        for col_info in structured_schema:
            new_schema = KnowledgeTableSchema(
                datasource_id=new_ds.id,
                table_name=col_info['table_name'],
                column_name=col_info['column_name'],
                column_type=col_info['column_type'],
                column_comment=col_info['column_comment'],
                is_primary_key=col_info['is_primary_key']
            )
            db.add(new_schema)
            
        # 5. 为了保持兼容性和 RAG 检索，我们仍然生成一个 Schema 文本并存入 KnowledgeItem
        # 但这次我们从 structured_schema 构建文本
        schema_map = {}
        for item in structured_schema:
            table = item['table_name']
            if table not in schema_map:
                schema_map[table] = []
            col_def = f"{item['column_name']} {item['column_type']}"
            if item['column_comment']:
                col_def += f" -- {item['column_comment']}"
            if item['is_primary_key']:
                col_def += " (PK)"
            schema_map[table].append(col_def)
        
        schema_text = ""
        for table, cols in schema_map.items():
            schema_text += f"Table {table}\n" + "\n".join(cols) + "\n\n"
            
        new_item = KnowledgeItem(
            knowledge_id=knowledge_id,
            title=f"Database Schema: {data['databaseName']}",
            source_type='database_schema',
            content=schema_text,
            datasource_config={
                'id': new_ds.id,
                'type': data['dbType'],
                'host': data['host'],
                'port': data['port'],
                'db': data['databaseName'],
                'user': data['username']
            },
            status='finished'
        )
        db.add(new_item)
        db.commit()
        
        # 将 Schema item 存入向量库
        chunks = [schema_text] # 简单起见，整个 schema 作为一个 chunk，如果很大可能需要切分
        doc_ids = [str(uuid.uuid4())]
        metadatas = [{
            'knowledge_id': str(knowledge_id),
            'item_id': str(new_item.id),
            'source': 'database_schema',
            'title': new_item.title,
            'chunk': 0,
            'datasource_id': str(new_ds.id)
        }]
        vector_service.add_documents(chunks, ids=doc_ids, metadatas=metadatas)
        
        return jsonify({'message': '数据源添加成功', 'id': new_ds.id})
    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()

# 5. 模型管理接口
@app.route('/api/models', methods=['GET', 'POST'])
def manage_models():
    # TODO: 管理模型配置
    return jsonify([])

# 6. 系统管理接口
@app.route('/api/system/config', methods=['GET', 'POST'])
def manage_system_config():
    # TODO: 管理系统配置
    return jsonify({})

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080, debug=True)