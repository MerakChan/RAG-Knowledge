
// 全局变量
let currentSessionId = null;
let currentAbortController = null;

document.addEventListener('DOMContentLoaded', () => {
    // 暴露函数给全局，以便 HTML 中的 onclick 调用
    window.createNewSession = createNewSession;
    window.loadSessions = loadSessions;
    window.selectSession = selectSession;
    window.deleteSession = deleteSession;

    const userInput = document.getElementById('userInput');
    const sendBtn = document.getElementById('sendBtn');
    const stopBtn = document.getElementById('stopBtn');
    const fileInput = document.getElementById('fileInput');
    const uploadBtn = document.getElementById('uploadBtn');
    const clearBtn = document.getElementById('clearBtn');
    
    // 恢复状态
    const savedKBId = localStorage.getItem('currentKBId');
    const savedKBName = localStorage.getItem('currentKBName');
    if (savedKBId) {
        window.currentKBId = savedKBId;
        window.currentKBName = savedKBName;
        // 如果当前在聊天界面或文档管理界面，可能需要刷新显示
        const kbInfo = document.getElementById('current-kb-info');
        if (kbInfo) kbInfo.textContent = savedKBName || '';
    }

    // 发送消息
    sendBtn.addEventListener('click', sendMessage);
    
    // 上传文件
    if (uploadBtn && fileInput) {
        uploadBtn.addEventListener('click', () => fileInput.click());
        fileInput.addEventListener('change', uploadFile);
    }
    
    // 清除知识库
    if (clearBtn) {
        clearBtn.addEventListener('click', clearKnowledgeBase);
    }
    
    // 停止生成
    stopBtn.addEventListener('click', () => {
        if (currentAbortController) {
            currentAbortController.abort();
            currentAbortController = null;
            // 找到最后一个 AI 消息的内容 div，追加 "(已停止)"
            const chatMessages = document.getElementById('chatMessages');
            const lastMessage = chatMessages.lastElementChild;
            if (lastMessage && lastMessage.classList.contains('ai')) {
                const contentDiv = lastMessage.querySelector('.message-content');
                if (contentDiv) {
                    contentDiv.innerHTML += '<br><i>(用户已终止对话)</i>';
                }
            }
            setLoading(false);
        }
    });

    userInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            if (currentAbortController) return;
            sendMessage();
        }
    });
});

// 加载会话列表
function loadSessions(kbId) {
    if (!kbId) return;
    const sessionList = document.getElementById('session-list');
    sessionList.innerHTML = '<div style="text-align:center; padding:10px; color:#666;">加载中...</div>';

    fetch(`/api/chat/sessions?knowledge_id=${kbId}`)
        .then(res => res.json())
        .then(sessions => {
            sessionList.innerHTML = '';
            if (sessions.length === 0) {
                sessionList.innerHTML = '<div style="text-align:center; padding:10px; color:#666;">暂无历史会话</div>';
                return;
            }
            
            sessions.forEach(session => {
                const div = document.createElement('div');
                div.className = `session-item ${session.id === currentSessionId ? 'active-session' : ''}`;
                
                // 使用 Flex 布局
                div.style.cssText = 'padding: 12px; cursor: pointer; border-bottom: 1px solid #eee; font-size: 14px; border-radius: 8px; margin: 4px 0; transition: background 0.2s; display: flex; justify-content: space-between; align-items: center;';
                
                if (session.id === currentSessionId) {
                    div.style.backgroundColor = '#e5e7eb';
                    div.style.fontWeight = '500';
                } else {
                    div.onmouseover = () => div.style.backgroundColor = '#f3f4f6';
                    div.onmouseout = () => div.style.backgroundColor = 'transparent';
                }

                // 会话名称
                const nameSpan = document.createElement('span');
                nameSpan.textContent = session.session_name || session.name || `会话 ${session.id}`;
                nameSpan.style.cssText = 'flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;';
                div.appendChild(nameSpan);

                // 删除按钮
                const delBtn = document.createElement('span');
                delBtn.innerHTML = '🗑️'; // 使用 emoji 或 fontawesome
                delBtn.title = '删除会话';
                delBtn.style.cssText = 'margin-left: 8px; font-size: 14px; padding: 4px; border-radius: 4px; opacity: 0.6; z-index: 10;';
                
                delBtn.onmouseover = (e) => {
                    e.stopPropagation();
                    delBtn.style.opacity = '1';
                    delBtn.style.backgroundColor = '#fee2e2';
                };
                delBtn.onmouseout = (e) => {
                    e.stopPropagation();
                    delBtn.style.opacity = '0.6';
                    delBtn.style.backgroundColor = 'transparent';
                };
                
                // 绑定删除事件
                delBtn.onclick = (e) => {
                    e.stopPropagation(); // 防止触发 session 选择
                    deleteSession(session.id);
                };
                div.appendChild(delBtn);

                // 绑定点击整个会话项的事件
                div.onclick = () => selectSession(session.id);
                
                sessionList.appendChild(div);
            });
        })
        .catch(err => {
            console.error(err);
            sessionList.innerHTML = '<div style="text-align:center; padding:10px; color:red;">加载失败</div>';
        });
}

// 删除会话
function deleteSession(sessionId) {
    if (!confirm('确定要删除这个会话吗？删除后无法恢复。')) {
        return;
    }
    
    fetch(`/api/chat/session/${sessionId}`, {
        method: 'DELETE'
    })
    .then(res => res.json())
    .then(data => {
        if (data.error) {
            alert('删除失败: ' + data.error);
        } else {
            // 如果删除的是当前选中的会话，清空聊天界面
            if (currentSessionId === sessionId) {
                currentSessionId = null;
                const chatMessages = document.getElementById('chatMessages');
                chatMessages.innerHTML = `
                    <div class="message ai">
                        <div class="message-avatar">🤖</div>
                        <div class="message-content">
                            会话已删除。请选择或新建会话。
                        </div>
                    </div>`;
                document.getElementById('current-session-title').textContent = '请选择或新建会话';
                document.getElementById('userInput').disabled = true;
                document.getElementById('sendBtn').disabled = true;
            }
            // 重新加载列表
            loadSessions(window.currentKBId);
        }
    })
    .catch(err => {
        console.error(err);
        alert('删除请求失败');
    });
}

// 创建新会话
function createNewSession() {
    if (!window.currentKBId) {
        alert('请先选择一个知识库');
        return;
    }
    
    fetch('/api/chat/session/create', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ knowledge_id: window.currentKBId })
    })
    .then(res => res.json())
    .then(data => {
        if (data.session_id) {
            // 选中新会话
            selectSession(data.session_id);
            // 重新加载列表以显示新会话
            // 注意：selectSession 内部也会更新 UI 状态，但列表需要刷新
            setTimeout(() => loadSessions(window.currentKBId), 100);
        }
    });
}

// 选择会话
function selectSession(sessionId) {
    currentSessionId = sessionId;
    
    // 更新列表高亮
    loadSessions(window.currentKBId); 

    const chatMessages = document.getElementById('chatMessages');
    chatMessages.innerHTML = '<div style="text-align:center; padding:20px;">加载消息...</div>';
    
    // 更新标题
    const titleEl = document.getElementById('current-session-title');
    if(titleEl) titleEl.textContent = `会话 #${sessionId}`;

    fetch(`/api/chat/messages?session_id=${sessionId}`)
        .then(res => res.json())
        .then(data => {
            chatMessages.innerHTML = '';
            // 修复：API 直接返回数组，而不是对象包含 messages
            const messages = Array.isArray(data) ? data : (data.messages || []);
            
            if (messages.length > 0) {
                messages.forEach(msg => {
                    // msg.role is 'user' or 'assistant'
                    // renderMessage handles formatting
                    appendMessageToUI(msg.role, msg.content);
                });
            } else {
                 chatMessages.innerHTML = `
                    <div class="message ai">
                        <div class="message-avatar">🤖</div>
                        <div class="message-content">
                            这是一个新会话，请开始提问。
                        </div>
                    </div>`;
            }
            chatMessages.scrollTop = chatMessages.scrollHeight;
            
            // 启用输入框
            setLoading(false);
        });
}

function setLoading(isLoading) {
    const sendBtn = document.getElementById('sendBtn');
    const stopBtn = document.getElementById('stopBtn');
    const userInput = document.getElementById('userInput');

    if (isLoading) {
        sendBtn.style.display = 'none';
        stopBtn.style.display = 'block';
        userInput.disabled = true;
        userInput.placeholder = 'AI 正在思考中...';
    } else {
        sendBtn.style.display = 'block';
        stopBtn.style.display = 'none';
        userInput.disabled = false;
        userInput.placeholder = '请输入您的问题...';
        userInput.focus();
    }
}

function appendMessageToUI(role, content) {
    const chatMessages = document.getElementById('chatMessages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role === 'user' ? 'user' : 'ai'}`;
    
    const avatarDiv = document.createElement('div');
    avatarDiv.className = 'message-avatar';
    avatarDiv.textContent = role === 'user' ? '👤' : '🤖'; // 使用简单的 emoji
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    
    // 如果是 AI 消息，进行 Markdown/格式化处理
    if (role === 'assistant' || role === 'ai') {
        contentDiv.innerHTML = formatAIContent(content);
    } else {
        contentDiv.textContent = content;
    }
    
    messageDiv.appendChild(avatarDiv);
    messageDiv.appendChild(contentDiv);
    chatMessages.appendChild(messageDiv);
    
    return contentDiv; // 返回内容容器以便流式更新
}

function formatAIContent(content) {
    if (!content) return '';
    let formatted = content
        .replace(/\[思考\][：:]?/g, '<div class="thinking"><div class="thinking-header"><i>💡</i> 思考过程</div>')
        .replace(/\[回答\][：:]?/g, '</div>')
        .replace(/\n/g, '<br>');
        
    // 简单的 Markdown 表格渲染支持
    if (formatted.includes('| --- |') || formatted.includes('|---|')) {
        let tableContent = formatted.replace(/<br>/g, '\n');
        const tableRegex = /(\|.*\|\n\|[\s\-:|]+\|.*\n(\|.*\|\n)*)/g;
        
        formatted = tableContent.replace(tableRegex, (match) => {
            const rows = match.trim().split('\n');
            if (rows.length < 2) return match;

            let html = '<div class="table-responsive"><table class="chat-table">';
            rows.forEach((row, index) => {
                row = row.trim();
                if (!row) return;
                if (row.match(/^\|[\s\-:|]+\|$/)) return; 
                
                let cells = row.split('|');
                if (row.startsWith('|')) cells.shift();
                if (row.endsWith('|')) cells.pop();
                
                html += '<tr>';
                cells.forEach(cell => {
                    if (index === 0) {
                        html += `<th>${cell.trim()}</th>`;
                    } else {
                        html += `<td>${cell.trim()}</td>`;
                    }
                });
                html += '</tr>';
            });
            html += '</table></div>';
            return html;
        });
        
        formatted = formatted.replace(/\n/g, '<br>');
    }
    return formatted;
}

function sendMessage() {
    const userInput = document.getElementById('userInput');
    const message = userInput.value.trim();
    if (!message) return;

    if (!currentSessionId) {
        alert('请先选择或创建一个会话');
        return;
    }

    // 显示用户消息
    appendMessageToUI('user', message);
    userInput.value = '';
    setLoading(true);

    // 创建 AI 消息容器（流式更新用）
    const chatMessages = document.getElementById('chatMessages');
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message ai';
    const avatarDiv = document.createElement('div');
    avatarDiv.className = 'message-avatar';
    avatarDiv.textContent = '🤖';
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    messageDiv.appendChild(avatarDiv);
    messageDiv.appendChild(contentDiv);
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;

    currentAbortController = new AbortController();

    fetch('/api/chat', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
            message: message,
            session_id: currentSessionId, // 传递 session_id
            knowledgeId: window.currentKBId // 兼容旧逻辑，虽然 session 已经关联了 KB
        }),
        signal: currentAbortController.signal
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let fullContent = '';

        function read() {
            reader.read().then(({ done, value }) => {
                if (done) {
                    currentAbortController = null;
                    setLoading(false);
                    return;
                }
                const chunk = decoder.decode(value, { stream: true });
                fullContent += chunk;
                
                // 实时格式化渲染
                contentDiv.innerHTML = formatAIContent(fullContent);
                chatMessages.scrollTop = chatMessages.scrollHeight;
                
                read();
            }).catch(error => {
                if (error.name === 'AbortError') {
                    console.log('Stream aborted');
                } else {
                    console.error('Stream error:', error);
                    contentDiv.innerHTML += '<br><span style="color:red">[出错]</span>';
                    setLoading(false);
                }
            });
        }
        read();
    })
    .catch(error => {
        if (error.name === 'AbortError') return;
        console.error('Fetch error:', error);
        contentDiv.innerHTML = '请求失败，请稍后重试。';
        setLoading(false);
    });
}

// ----------------- 文件上传逻辑 -----------------

function uploadFile() {
    const fileInput = document.getElementById('fileInput');
    const uploadStatus = document.getElementById('uploadStatus');
    const file = fileInput.files[0];
    
    if (!file) return;
    if (!window.currentKBId) {
        alert('请先选择一个知识库');
        fileInput.value = '';
        return;
    }

    const formData = new FormData();
    formData.append('file', file);
    formData.append('knowledgeId', window.currentKBId);

    uploadStatus.style.display = 'block';
    uploadStatus.textContent = '正在上传并处理文档...';
    uploadStatus.style.color = '#0369a1';
    uploadStatus.style.backgroundColor = '#f0f9ff';

    fetch('/api/upload', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            uploadStatus.textContent = '上传失败: ' + data.error;
            uploadStatus.style.color = '#dc2626';
            uploadStatus.style.backgroundColor = '#fef2f2';
        } else {
            uploadStatus.textContent = `上传成功！文件: ${data.filename}, 切片数: ${data.chunks}`;
            uploadStatus.style.color = '#059669';
            uploadStatus.style.backgroundColor = '#ecfdf5';
            
            // 刷新文档列表
            if (typeof loadKnowledgeItems === 'function') {
                loadKnowledgeItems();
            }
        }
        fileInput.value = ''; // 清空文件选择
    })
    .catch(error => {
        console.error('Error:', error);
        uploadStatus.textContent = '上传出错，请查看控制台';
        uploadStatus.style.color = '#dc2626';
        uploadStatus.style.backgroundColor = '#fef2f2';
        fileInput.value = '';
    });
}

function clearKnowledgeBase() {
    if (!window.currentKBId) {
        alert('请先选择一个知识库');
        return;
    }
    
    if (confirm('确定要清除该知识库下的所有文档和向量数据吗？此操作不可恢复。')) {
        const uploadStatus = document.getElementById('uploadStatus');
        if (uploadStatus) {
            uploadStatus.style.display = 'block';
            uploadStatus.textContent = '正在清除知识库...';
        }

        // 注意：原接口是 /api/clear-knowledge，但那是清除所有。
        // 我们应该只清除当前知识库的数据。
        // 目前后端只提供了 /api/clear-knowledge (清除所有)，这里需要后端配合修改，或者暂时调用那个接口
        // 考虑到多知识库架构，清除所有是不对的。
        // 既然目前后端只有 clear-knowledge 且没有参数，我们暂时用它，但理想情况应该传 ID
        // 实际上，之前我看 app_new.py， clear_knowledge 确实是清除所有。
        // 这里为了安全，我们应该调用 deleteKBItem 或者新增接口。
        // 暂时先提示用户这个功能是全局的
        
        // 修正：实际上之前的 clear_knowledge 是清除 *所有*。
        // 用户现在是在某个知识库下操作。
        // 我们可以循环调用删除 item 接口，或者请求后端新增接口。
        // 为了快速修复，我们可以调用 /api/knowledge/delete/<id> 删除整个库再重建？不，那样太暴力。
        // 暂时实现为：清除该知识库下的所有文档。
        
        // 由于时间关系，我们先调用后端现有的 clear-knowledge 接口（如果用户接受），或者前端循环删除。
        // 为了更好的体验，我们假设后端支持 DELETE /api/knowledge/items/clear?knowledge_id=...
        // 但后端没这个接口。
        // 让我们看看 deleteKnowledgeItem 是怎么实现的。
        
        // 临时方案：前端获取列表然后逐个删除（效率低但安全）
        // 或者，我们直接调用 /api/clear-knowledge 并在后端修改它接受参数。
        // 让我们先用 fetch('/api/knowledge/clear?knowledge_id=' + window.currentKBId) 
        // 然后去后端实现它。
        
        fetch(`/api/knowledge/clear?knowledge_id=${window.currentKBId}`, {
            method: 'POST'
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                alert('清除失败: ' + data.error);
            } else {
                alert('知识库已清空');
                if (typeof loadKnowledgeItems === 'function') {
                    loadKnowledgeItems();
                }
                if (uploadStatus) uploadStatus.style.display = 'none';
            }
        })
        .catch(error => {
            alert('清除出错: ' + error.message);
        });
    }
}
