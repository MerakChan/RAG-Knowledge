<template>
  <div class="app-container">
    <header class="global-topbar surface-panel">
      <div class="global-topbar__spaces">
        <button
          v-for="kb in filteredKnowledgeBases"
          :key="kb.id"
          class="global-space-item"
          :class="{ active: String(kb.id) === String(selectedKnowledgeId) }"
          type="button"
          @click="selectedKnowledgeId = String(kb.id)"
        >
          {{ kb.name }}
        </button>
        <button class="global-space-item create-btn" type="button" @click="openKnowledgeModal()">
          + 新建空间
        </button>
      </div>
    </header>
    <div class="workspace-shell layout-3-col">
      <aside class="app-sidebar surface-panel">
      <div class="sidebar-top">
        <button class="btn btn-primary compact-btn" type="button" @click="goBack" style="margin-bottom: 12px; white-space: nowrap; padding: 0 12px; min-height: 36px;">
          <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" style="width: 16px; height: 16px;">
            <path d="M19 12H5M12 19L5 12L12 5" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          内容中台
        </button>

        <div class="brand-block">
          <div class="brand-mark">SB</div>
          <div class="brand-copy">
            <strong>Second Brain</strong>
            <p>内容优先的知识工作台</p>
          </div>
        </div>

        <nav class="sidebar-nav">
          <div v-for="item in primaryNav" :key="item.key" class="sidebar-nav__item-wrapper">
            <button
              class="sidebar-nav__item"
              :class="{ active: activeView === item.key, 'has-submenu': item.key === 'assistant' }"
              type="button"
              @click="handleAgentClick(item.key)"
            >
              <span class="sidebar-nav__copy">
                <strong>{{ item.label }}</strong>
                <small>{{ item.meta }}</small>
              </span>
              <span v-if="item.key === 'assistant'" class="submenu-toggle">
                <svg :class="{ 'rotated': agentMenuOpen }" width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M9 18L15 12L9 6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
              </span>
            </button>
            
            <!-- ANote Agent 功能菜单（折叠子菜单） -->
            <div v-if="item.key === 'assistant'" class="agent-submenu" :class="{ 'is-open': agentMenuOpen }">
              <div class="submenu-content">
                <button
                  v-for="tab in agentTabs"
                  :key="tab.id"
                  class="submenu-item"
                  :class="{ active: agentActiveTab === tab.id }"
                  type="button"
                  @click="selectAgentTab(tab.id)"
                >
                  <strong>{{ tab.name }}</strong>
                  <small>{{ tab.description }}</small>
                </button>
              </div>
            </div>
          </div>
        </nav>
      </div>

      <section class="sidebar-section sidebar-metrics">
        <div class="mini-metric">
          <span>文档</span>
          <strong>{{ stats.overall.doc_count || 0 }}</strong>
        </div>
        <div class="mini-metric">
          <span>问答</span>
          <strong>{{ stats.overall.qa_count || 0 }}</strong>
        </div>
        <div class="mini-metric">
          <span>连续学习</span>
          <strong>{{ stats.workspace.learning_streak_days || 0 }} 天</strong>
        </div>
      </section>




    </aside>

    <section class="app-main">
      <header class="main-topbar surface-panel">
        <div class="main-topbar__title">
          <span class="section-label">{{ currentViewMeta.kicker }}</span>
          <h1>{{ currentViewMeta.title }}</h1>
          <p>{{ currentViewMeta.description }}</p>
        </div>



        <div class="main-topbar__actions">
          <button class="btn btn-primary compact-btn" type="button" @click="toggleAssistant">
            {{ drawerOpen ? '收起对话' : '打开对话' }}
          </button>
        </div>
      </header>

      <div v-if="notice.text" class="notice-banner" :class="notice.type">
        {{ notice.text }}
      </div>

      <main class="main-scroll scrollable-area">
        <section v-if="activeView === 'dashboard'" class="view-stack">
          <div class="hero-row">
            <div>
              <span class="section-label">工作台</span>
              <h2>你好，{{ authUser.nickname || authUser.username || '学习者' }}</h2>
              <p>把当前知识空间、近期问题和写作素材放在同一视图里，减少界面切换。</p>
            </div>

          </div>

          <div class="overview-grid">
            <article v-for="card in boardCards" :key="card.label" class="surface-panel stat-card">
              <span>{{ card.label }}</span>
              <strong>{{ card.value }}</strong>
              <small>{{ card.detail }}</small>
            </article>
          </div>

          <div class="dashboard-grid">
            <article class="surface-panel panel-card">
              <div class="panel-card__header">
                <div>
                  <span class="section-label">近期问答</span>
                  <h3>最近在问什么</h3>
                </div>
                <button class="text-btn" type="button" @click="activeView = 'assistant'">查看对话</button>
              </div>
              <div class="activity-list">
                <div v-for="item in stats.recent_qa.slice(0, 4)" :key="item.time" class="activity-item">
                  <strong>{{ item.question }}</strong>
                  <p>{{ item.kb_name || '未命名知识空间' }}</p>
                </div>
                <div v-if="!stats.recent_qa.length" class="empty-text">暂无近期问答记录</div>
              </div>
            </article>

            <article class="surface-panel panel-card">
              <div class="panel-card__header">
                <div>
                  <span class="section-label">活跃趋势</span>
                  <h3>本周使用节奏</h3>
                </div>
                <span class="soft-badge">今日提问 {{ stats.today.qa_count || 0 }}</span>
              </div>
              <div class="trend-chart">
                <div v-for="item in boardTrendBars.slice(0, 7)" :key="item.date || item.label || item.time" class="trend-bar">
                  <div class="trend-bar__value" :style="{ height: item.height }"></div>
                  <span>{{ item.label || item.date || '--' }}</span>
                </div>
                <div v-if="!boardTrendBars.length" class="empty-text">暂无趋势数据</div>
              </div>
            </article>




          </div>
        </section>



        <section v-else-if="activeView === 'knowledge'" class="view-stack">
          <div v-if="currentKnowledgeBase" class="knowledge-layout">
            <article class="surface-panel panel-card">
              <div class="panel-card__header">
                <div>
                  <span class="section-label">知识空间</span>
                  <h3>{{ currentKnowledgeBase.name }}</h3>
                  <p>{{ currentKnowledgeBase.description || '在这里管理资料、切片和来源。' }}</p>
                </div>
                <div class="row-actions">
                  <button class="btn btn-secondary compact-btn" type="button" @click="openKnowledgeModal(currentKnowledgeBase)">编辑</button>
                  <button class="btn btn-danger compact-btn" type="button" @click="removeKnowledgeBase(currentKnowledgeBase)">删除</button>
                </div>
              </div>

              <div class="overview-grid compact-grid">
                <div class="stat-card stat-card--mini">
                  <span>文档数</span>
                  <strong>{{ filteredKnowledgeItems.length }}</strong>
                  <small>当前已导入条目</small>
                </div>
                <div class="stat-card stat-card--mini">
                  <span>切片数</span>
                  <strong>{{ stats.knowledge.chunk_count || 0 }}</strong>
                  <small>用于检索的内容单元</small>
                </div>

              </div>
            </article>

            <div class="surface-panel upload-zone">
              <div>
                <strong>上传资料</strong>
                <p>支持 PDF、Word、TXT等文档和MySQL数据源。上传后自动切分并用于问答检索。</p>
              </div>
              <div class="upload-buttons">
                <button class="btn btn-primary compact-btn" type="button" @click="openImportModal('pdf')">上传数据源</button>
                <button class="btn btn-secondary compact-btn" type="button" @click="openTextModal">手动输入</button>
              </div>
            </div>

            <article class="surface-panel panel-card">
              <div class="panel-card__header">
                <div>
                  <span class="section-label">资料列表</span>
                  <h3>已导入内容</h3>
                </div>
                <button class="btn btn-secondary compact-btn" type="button" @click="clearKnowledgeBase">清空当前知识空间</button>
              </div>
              <div class="stack-list">
                <article v-for="item in filteredKnowledgeItems" :key="item.id" class="list-card">
                  <div>
                    <strong>{{ item.title || item.file_name || '未命名条目' }}</strong>
                    <p>{{ sourceLabel(item.source_type) }} · {{ item.chunk_count || 0 }} 个切片</p>
                  </div>
                  <button class="btn btn-secondary compact-btn" type="button" @click="removeKnowledgeItem(item)">移除</button>
                </article>
                <div v-if="!filteredKnowledgeItems.length" class="empty-text">当前知识空间还没有导入资料</div>
              </div>
            </article>
          </div>
          <div v-else class="empty-state surface-panel">
            <p>请先从左侧选择一个知识空间，再管理资料。</p>
          </div>
        </section>

        <section v-else-if="activeView === 'assistant'" class="view-stack">
          <!-- 主要功能区域 -->
          <article class="surface-panel panel-card">
            <div class="panel-card__header">
              <!-- 已删除重复的顶部内容 -->
            </div>
            <div style="display: flex; height: calc(100vh - 40px); overflow-y: hidden; position: relative;">
              <!-- 右侧内容区域 -->
              <div style="flex: 1; padding: 18px; overflow-y: auto;">
                <!-- 多文档联合分析 -->
                <div v-if="agentActiveTab === 'multiDoc'">
                  <div style="margin-bottom: 20px;">
                    <h4 style="margin-bottom: 8px; font-weight: 600;">多文档联合分析</h4>
                    <p style="color: var(--text-muted); font-size: 14px;">选择多个相关文档，让AI进行跨文档理解与分析。让AI具备「跨文档思考能力」，支持内容融合、观点对比、信息去重。</p>
                  </div>

                  <!-- 文档选择区域 -->
                  <div style="margin-bottom: 20px;">
                    <label class="field-label" style="margin-bottom: 8px; display: block;">选择要分析的文档</label>
                    <div style="border: 1px dashed var(--border-color); border-radius: 8px; padding: 16px; max-height: 200px; overflow-y: auto;">
                      <div v-if="knowledgeItems.length === 0" style="text-align: center; color: var(--text-muted); padding: 20px;">
                        当前知识库暂无文档
                      </div>
                      <div v-else style="display: flex; flex-direction: column; gap: 8px;">
                        <label
                          v-for="item in knowledgeItems"
                          :key="item.id"
                          style="display: flex; align-items: center; gap: 8px; padding: 8px; border-radius: 4px; cursor: pointer;"
                          :style="selectedDocuments.includes(item.id) ? 'background: var(--primary-bg);' : ''"
                        >
                          <input
                            type="checkbox"
                            :checked="selectedDocuments.includes(item.id)"
                            @change="toggleDocument(item.id)"
                          />
                          <span>{{ item.title || item.file_name || '未命名文档' }}</span>
                          <span style="margin-left: auto; color: var(--text-muted); font-size: 12px;">{{ item.source_type }}</span>
                        </label>
                      </div>
                    </div>
                  </div>

                  <!-- 模型选择 -->
                  <div style="margin-bottom: 20px;">
                    <label class="field-label" style="margin-bottom: 8px; display: block;">选择AI模型</label>
                    <select v-model="modelConfig.active_chat_model_id" class="field-select">
                      <option value="">未选择</option>
                      <option v-for="model in modelConfig.models" :key="model.id" :value="model.id">{{ model.name }}</option>
                    </select>
                  </div>

                  <!-- 分析要求输入 -->
                  <div style="margin-bottom: 20px;">
                    <label class="field-label" style="margin-bottom: 8px; display: block;">分析要求说明</label>
                    <textarea
                      v-model="multiDocAnalysis.prompt"
                      class="field-textarea"
                      rows="5"
                      placeholder="例如：帮我对比这三篇RAG论文的核心区别，或者总结这些资料中关于多模型架构的共同点..."
                    ></textarea>
                  </div>

                  <!-- 快捷示例 -->
                  <div style="margin-bottom: 20px;">
                    <label class="field-label" style="margin-bottom: 8px; display: block;">快捷示例</label>
                    <div style="display: flex; flex-wrap: wrap; gap: 8px;">
                      <button
                        class="btn btn-secondary compact-btn"
                        type="button"
                        @click="multiDocAnalysis.prompt = '请帮我对比分析这些文档的核心区别和观点差异'"
                      >
                        对比分析
                      </button>
                      <button
                        class="btn btn-secondary compact-btn"
                        type="button"
                        @click="multiDocAnalysis.prompt = '请综合总结这些文档的核心内容和关键信息'"
                      >
                        综合总结
                      </button>
                      <button
                        class="btn btn-secondary compact-btn"
                        type="button"
                        @click="multiDocAnalysis.prompt = '请归纳整理这些文档中提到的核心概念及其关系'"
                      >
                        关系归纳
                      </button>
                    </div>
                  </div>

                  <!-- 操作按钮 -->
                  <div style="display: flex; gap: 12px; margin-bottom: 20px;">
                    <button
                      class="btn btn-primary"
                      type="button"
                      :disabled="selectedDocuments.length === 0 || multiDocAnalysis.isAnalyzing"
                      @click="startMultiDocAnalysis"
                    >
                      {{ multiDocAnalysis.isAnalyzing ? '分析中...' : '开始分析' }}
                    </button>
                    <button
                      v-if="multiDocAnalysis.report"
                      class="btn btn-secondary"
                      type="button"
                      @click="exportReport"
                    >
                      导出PDF
                    </button>
                  </div>

                  <!-- 分析报告展示 -->
                  <div v-if="multiDocAnalysis.report">
                    <h5 style="margin-bottom: 12px; font-weight: 600;">分析报告</h5>
                    <div style="background: var(--bg-muted); padding: 16px; border-radius: 8px; white-space: pre-wrap;">
                      {{ multiDocAnalysis.report }}
                    </div>
                  </div>
                </div>

                <!-- 知识图谱构建 -->
                <div v-if="agentActiveTab === 'graph'">
                  <div style="margin-bottom: 20px;">
                    <h4 style="margin-bottom: 8px; font-weight: 600;">知识图谱构建</h4>
                    <p style="color: var(--text-muted); font-size: 14px;">系统自动分析知识库内容，构建结构化知识关系网络。把「碎片知识」变成「结构化知识网络」，自动提取概念、建立关系。</p>
                  </div>

                  <div style="text-align: center; padding: 40px 0;">
                    <div style="width: 120px; height: 120px; margin: 0 auto 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 50%; display: flex; align-items: center; justify-content: center;">
                      <svg style="width: 60px; height: 60px;" fill="none" stroke="white" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1"/>
                      </svg>
                    </div>
                    <p style="margin-bottom: 16px; color: var(--text-muted);">点击下方按钮，一键构建当前所有知识文档的结构化知识关系网络</p>
                    <button
                      class="btn btn-primary"
                      type="button"
                      :disabled="graphBuilding.isBuilding"
                      @click="startBuildGraph"
                    >
                      {{ graphBuilding.isBuilding ? `构建中 ${graphBuilding.progress}%` : '一键构建知识图谱' }}
                    </button>
                  </div>

                  <!-- 构建进度 -->
                  <div v-if="graphBuilding.isBuilding" style="margin-top: 30px;">
                    <div style="background: var(--bg-muted); height: 8px; border-radius: 4px; overflow: hidden;">
                      <div style="width: 0%; height: 100%; background: linear-gradient(90deg, #667eea 0%, #764ba2 100%); transition: width 0.3s;" :style="{ width: graphBuilding.progress + '%' }"></div>
                    </div>
                    <p style="text-align: center; margin-top: 8px; color: var(--text-muted); font-size: 13px;">正在分析文档，提取关键概念和关系...</p>
                  </div>

                  <!-- 图谱展示 -->
                  <div v-if="knowledgeGraph.loaded" style="margin-top: 30px;">
                    <h5 style="margin-bottom: 12px; font-weight: 600;">知识关系网络</h5>
                    
                    <!-- 节点统计 -->
                    <div style="margin-bottom: 20px; display: flex; gap: 16px; flex-wrap: wrap;">
                      <div style="padding: 12px 20px; background: var(--bg-muted); border-radius: 8px;">
                        <strong>知识源节点</strong>
                        <p style="font-size: 24px; margin: 0; color: var(--primary-color);">{{ knowledgeGraph.nodes.length }}</p>
                      </div>
                      <div style="padding: 12px 20px; background: var(--bg-muted); border-radius: 8px;">
                        <strong>关系连线</strong>
                        <p style="font-size: 24px; margin: 0; color: var(--primary-color);">{{ knowledgeGraph.edges.length }}</p>
                      </div>
                    </div>

                    <!-- 图例 -->
                    <div style="margin-bottom: 20px;">
                      <h6 style="margin-bottom: 8px;">图例</h6>
                      <div style="display: flex; gap: 16px; flex-wrap: wrap;">
                        <div style="display: flex; align-items: center; gap: 6px;">
                          <div style="width: 12px; height: 12px; background: #667eea; border-radius: 4px;"></div>
                          <span style="font-size: 13px;">知识源</span>
                        </div>
                        <div style="display: flex; align-items: center; gap: 6px;">
                          <div style="width: 30px; height: 3px; background: #ef4444; border-radius: 2px;"></div>
                          <span style="font-size: 13px;">高度相关</span>
                        </div>
                        <div style="display: flex; align-items: center; gap: 6px;">
                          <div style="width: 30px; height: 3px; background: #f59e0b; border-radius: 2px;"></div>
                          <span style="font-size: 13px;">相关</span>
                        </div>
                        <div style="display: flex; align-items: center; gap: 6px;">
                          <div style="width: 30px; height: 3px; background: #94a3b8; border-radius: 2px;"></div>
                          <span style="font-size: 13px;">弱相关</span>
                        </div>
                      </div>
                    </div>

                    <!-- 图谱可视化区域 -->
                    <div class="graph-visualization-container" ref="graphContainerRef" style="width: 100%; height: 500px; background: #f8fafc; border-radius: 12px; border: 1px solid var(--border-color); overflow: hidden;">
                      <svg ref="graphSvgRef" :width="graphSize.width" :height="graphSize.height" style="width: 100%; height: 100%; cursor: move;">
                        <!-- 定义箭头标记 -->
                        <defs>
                          <marker id="arrowhead" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto">
                            <polygon points="0 0, 10 3.5, 0 7" fill="#94a3b8" />
                          </marker>
                        </defs>
                        
                        <!-- 绘制连线 -->
                        <g class="edges">
                          <line
                            v-for="(edge, index) in knowledgeGraph.edges"
                            :key="`edge-${index}`"
                            :x1="getNodePosition(edge.source_node_id).x"
                            :y1="getNodePosition(edge.source_node_id).y"
                            :x2="getNodePosition(edge.target_node_id).x"
                            :y2="getNodePosition(edge.target_node_id).y"
                            :stroke="getEdgeColor(edge.relation_type)"
                            :stroke-width="getEdgeWidth(edge.relation_type)"
                            :stroke-opacity="0.7"
                            style="pointer-events: stroke;"
                            @click="handleEdgeClick(edge)"
                          />
                        </g>
                        
                        <!-- 绘制节点 -->
                        <g class="nodes">
                          <g
                            v-for="(node, index) in knowledgeGraph.nodes"
                            :key="`node-${node.node_id}`"
                            :transform="`translate(${getNodePosition(node.node_id).x}, ${getNodePosition(node.node_id).y})`"
                            style="cursor: pointer;"
                            @mousedown="startDrag($event, node.node_id)"
                            @click="handleNodeClick(node)"
                          >
                            <!-- 节点背景圆 -->
                            <circle
                              :r="getNodeSize(node.node_name.length)"
                              :fill="selectedNode === node.node_id ? '#4f46e5' : '#667eea'"
                              :stroke="selectedNode === node.node_id ? '#312e81' : '#4f46e5'"
                              :stroke-width="selectedNode === node.node_id ? 3 : 2"
                            />
                            <!-- 节点标签 -->
                            <text
                              :y="4"
                              text-anchor="middle"
                              :fill="selectedNode === node.node_id ? '#fff' : '#fff'"
                              font-size="11"
                              font-weight="500"
                              style="pointer-events: none;"
                            >
                              {{ truncateNodeName(node.node_name) }}
                            </text>
                          </g>
                        </g>
                      </svg>
                    </div>

                    <!-- 选中节点详情 -->
                    <div v-if="selectedNodeData" style="margin-top: 20px; padding: 16px; background: var(--bg-muted); border-radius: 12px;">
                      <h6 style="margin-bottom: 10px; font-weight: 600;">知识源详情</h6>
                      <div style="margin-bottom: 8px;">
                        <strong style="font-size: 16px;">{{ selectedNodeData.node_name }}</strong>
                      </div>
                      <div style="white-space: pre-wrap; color: var(--text-secondary); font-size: 14px; line-height: 1.6;">
                        {{ selectedNodeData.description || '暂无详情' }}
                      </div>
                    </div>
                  </div>
                  
                  <!-- 图谱预览占位（兼容旧逻辑） -->
                  <div v-else-if="graphBuilding.progress === 100 && !graphBuilding.isBuilding" style="margin-top: 30px;">
                    <h5 style="margin-bottom: 12px; font-weight: 600;">知识关系网络</h5>
                    <div style="border: 1px dashed var(--border-color); border-radius: 8px; padding: 40px; text-align: center;">
                      <p style="color: var(--text-muted);">知识图谱构建完成！</p>
                      <p style="color: var(--text-muted); font-size: 13px; margin-top: 8px;">（请点击“一键构建知识图谱”按钮重新构建）</p>
                    </div>
                  </div>
                </div>

                <!-- 知识溯源 -->
                <div v-if="agentActiveTab === 'trace'">
                  <div style="margin-bottom: 20px;">
                    <h4 style="margin-bottom: 8px; font-weight: 600;">知识溯源</h4>
                    <p style="color: var(--text-muted); font-size: 14px;">查看AI回答的来源依据，追溯到具体文档位置。所有答案都可以追溯来源，指向具体文档的chunk片段</p>
                  </div>

                  <!-- 模型选择 -->
                  <div style="margin-bottom: 20px;">
                    <label class="field-label" style="margin-bottom: 8px; display: block;">选择AI模型</label>
                    <select v-model="modelConfig.active_chat_model_id" class="field-select">
                      <option value="">未选择</option>
                      <option v-for="model in modelConfig.models" :key="model.id" :value="model.id">{{ model.name }}</option>
                    </select>
                  </div>

                  <!-- 查询输入 -->
                  <div style="margin-bottom: 20px;">
                    <label class="field-label" style="margin-bottom: 8px; display: block;">输入查询问题</label>
                    <textarea
                      v-model="knowledgeTrace.query"
                      class="field-textarea"
                      rows="4"
                      placeholder="请输入您想了解的问题，AI会基于知识库内容回答，并展示来源依据"
                    ></textarea>
                  </div>

                  <!-- 快捷示例 -->
                  <div style="margin-bottom: 20px;">
                    <label class="field-label" style="margin-bottom: 8px; display: block;">快捷示例</label>
                    <div style="display: flex; flex-wrap: wrap; gap: 8px;">
                      <button
                        class="btn btn-secondary compact-btn"
                        type="button"
                        @click="knowledgeTrace.query = '什么是RAG？'"
                      >
                        什么是RAG
                      </button>
                      <button
                        class="btn btn-secondary compact-btn"
                        type="button"
                        @click="knowledgeTrace.query = '解释一下向量检索的原理'"
                      >
                        向量检索原理
                      </button>
                      <button
                        class="btn btn-secondary compact-btn"
                        type="button"
                        @click="knowledgeTrace.query = '如何构建知识图谱？'"
                      >
                        知识图谱构建
                      </button>
                    </div>
                  </div>

                  <!-- 操作按钮 -->
                  <div style="display: flex; gap: 12px; margin-bottom: 24px;">
                    <button
                      class="btn btn-primary"
                      type="button"
                      :disabled="!knowledgeTrace.query.trim() || knowledgeTrace.isTracing"
                      @click="startKnowledgeTrace"
                    >
                      {{ knowledgeTrace.isTracing ? '溯源中...' : '开始溯源' }}
                    </button>
                  </div>

                  <!-- 溯源结果展示 -->
                  <div v-if="knowledgeTrace.answer">
                    <h5 style="margin-bottom: 12px; font-weight: 600;">AI回答</h5>
                    <div style="background: var(--bg-muted); padding: 16px; border-radius: 8px; white-space: pre-wrap; margin-bottom: 20px;">
                      <div v-html="formatAnswerWithHighlights(knowledgeTrace.answer)"></div>
                    </div>

                    <!-- 来源片段展示 -->
                    <div v-if="knowledgeTrace.sources && knowledgeTrace.sources.length > 0">
                      <h5 style="margin-bottom: 12px; font-weight: 600;">来源依据</h5>
                      <div style="display: flex; flex-direction: column; gap: 12px;">
                        <div
                          v-for="(source, index) in knowledgeTrace.sources"
                          :key="source.chunk_id"
                          style="padding: 16px; background: white; border: 1px solid var(--border-color); border-radius: 8px;"
                        >
                          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                            <strong style="font-size: 14px; color: var(--text-primary);">来源 #{{ index + 1 }}：{{ source.doc_name }}</strong>
                            <span v-if="source.score" style="font-size: 12px; color: var(--text-muted);">相关度：{{ formatScore(source.score) }}</span>
                          </div>
                          <p style="font-size: 13px; color: var(--text-secondary); line-height: 1.6; margin: 0;">{{ source.content }}</p>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </article>
        </section>



        <section v-else-if="activeView === 'models'" class="view-stack">
          <article class="surface-panel settings-panel">
            <div class="panel-card__header">
              <div>
                <span class="section-label">多模型协同</span>
                <h3>模型管理与调度</h3>
              </div>
            </div>
            
            <!-- Tab 切换 -->
            <div style="display: flex; gap: 8px; margin-bottom: 24px;">
              <button 
                class="btn" 
                :class="modelActiveTab === 'list' ? 'btn-primary' : 'btn-secondary'"
                type="button" 
                @click="modelActiveTab = 'list'"
              >
                模型列表
              </button>
              <button 
                class="btn" 
                :class="modelActiveTab === 'tasks' ? 'btn-primary' : 'btn-secondary'"
                type="button" 
                @click="modelActiveTab = 'tasks'"
              >
                任务分配
              </button>
            </div>

            <!-- 模型列表 Tab -->
            <div v-if="modelActiveTab === 'list'">
              <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
                <h4 style="margin: 0;">已添加的模型</h4>
                <button class="btn btn-primary" type="button" @click="showAddModelModal = true">
                  添加自定义模型
                </button>
              </div>

              <div style="display: flex; flex-direction: column; gap: 16px;">
                <div 
                  v-for="model in modelConfig.models" 
                  :key="model.id"
                  style="padding: 16px; background: var(--bg-muted); border-radius: 8px;"
                >
                  <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 12px;">
                    <div>
                      <div style="display: flex; gap: 8px; align-items: center; margin-bottom: 4px; flex-wrap: wrap;">
                        <strong>{{ model.name }}</strong>
                        <span 
                          class="soft-badge" 
                          :style="{
                            background: model.enabled ? '#42a5f5' : '#ef5350', 
                            color: 'white'
                          }"
                        >
                          {{ model.enabled ? '已启用' : '已停用' }}
                        </span>
                        <span class="soft-badge">{{ model.type === 'cloud' ? '云端API' : '本地模型' }}</span>
                        <span v-if="model.id === modelConfig.active_chat_model_id" class="soft-badge" style="background: var(--accent-color); color: white;">
                          主对话模型
                        </span>
                      </div>
                      <p style="margin: 0; color: var(--text-muted); font-size: 13px;">{{ model.description }}</p>
                      <p v-if="model.has_api_key" style="margin: 4px 0 0; color: var(--text-muted); font-size: 12px;">API Key: {{ model.api_key_preview }}</p>
                    </div>
                    <div style="display: flex; gap: 8px; flex-wrap: wrap;">
                      <button 
                        class="btn btn-secondary compact-btn" 
                        type="button" 
                        @click="toggleModelStatus(model)"
                      >
                        {{ model.enabled ? '停用' : '启用' }}
                      </button>
                    </div>
                  </div>
                  
                  <!-- 操作按钮区 -->
                  <div style="margin-bottom: 12px; display: flex; gap: 8px; flex-wrap: wrap;">
                    <button 
                      v-if="model.editable" 
                      class="btn btn-secondary compact-btn" 
                      type="button" 
                      @click="editModel(model)"
                    >
                      编辑
                    </button>
                    <button 
                      v-if="model.editable" 
                      class="btn btn-secondary compact-btn" 
                      type="button" 
                      style="color: var(--danger-color);"
                      @click="deleteModel(model)"
                    >
                      删除
                    </button>
                    <button 
                      v-if="model.id !== modelConfig.active_chat_model_id" 
                      class="btn btn-primary compact-btn" 
                      type="button" 
                      @click="setAsMainModel(model.id)"
                    >
                      设为主对话模型
                    </button>
                  </div>
                  
                  <!-- 标签编辑 -->
                  <div>
                    <label style="font-size: 13px; color: var(--text-muted); margin-bottom: 8px; display: block;">能力标签</label>
                    <div style="display: flex; flex-wrap: wrap; gap: 8px;">
                      <template v-for="tag in model.tags || []" :key="tag">
                        <span 
                          class="soft-badge" 
                          style="position: relative; padding-right: 24px; background: white; color: black; border: 1px solid #ccc;"
                        >
                          {{ tag }}
                          <span 
                            style="position: absolute; right: 4px; top: 50%; transform: translateY(-50%); cursor: pointer; font-size: 12px; opacity: 0.9; color: #999;"
                            @click="removeModelTag(model, tag)"
                          >×</span>
                        </span>
                      </template>
                      <template v-for="tag in model.auto_tags || []" :key="tag">
                        <span 
                          class="soft-badge" 
                          style="background: #e0e0e0; color: #616161;"
                        >
                          {{ tag }}
                        </span>
                      </template>
                      <button class="btn btn-secondary compact-btn" type="button" @click="showAddTagModal = true; currentEditModel = model">
                        + 添加标签
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- 任务分配 Tab -->
            <div v-if="modelActiveTab === 'tasks'">
              <div style="margin-bottom: 24px;">
                <h4 style="margin: 0 0 16px;">任务调度策略</h4>
                <select class="field-select" :value="taskConfig.scheduling_strategy" @change="changeSchedulingStrategy($event.target.value)">
                  <option value="fixed">固定映射 - 每个任务使用指定模型</option>
                  <option value="tag">标签匹配 - 根据任务自动选择匹配标签的模型</option>
                  <option value="fallback">多模型备选 - 主模型不可用时自动切换到备用</option>
                </select>
              </div>

              <div style="margin-bottom: 24px;">
                <h4 style="margin: 0 0 16px;">任务-模型映射</h4>
                <div style="display: flex; flex-direction: column; gap: 12px;">
                  <div v-for="task in taskTypes" :key="task.key" class="setting-item">
                    <label class="field-label">{{ task.label }}</label>
                    <select class="field-select" :value="taskConfig.task_assignments[task.key]" @change="assignTaskModel(task.key, $event.target.value)">
                      <option v-for="model in modelConfig.models.filter(m => m.enabled)" :key="model.id" :value="model.id">
                        {{ model.name }}
                      </option>
                    </select>
                  </div>
                </div>
              </div>

              <div v-if="taskConfig.scheduling_strategy === 'fallback'">
                <h4 style="margin: 0 0 16px;">备用模型配置</h4>
                <div style="display: flex; flex-direction: column; gap: 16px;">
                  <div v-for="model in modelConfig.models.filter(m => m.enabled)" :key="model.id" class="setting-item">
                    <label class="field-label">{{ model.name }} 的备用模型</label>
                    <select 
                      class="field-select" 
                      :value="(taskConfig.fallback_models[model.id] || []).join(',')" 
                      @change="setFallbackModels(model.id, $event.target.value.split(',').filter(x => x))"
                    >
                      <option value="">无备用</option>
                      <option 
                        v-for="candidate in modelConfig.models.filter(m => m.enabled && m.id !== model.id)" 
                        :key="candidate.id" 
                        :value="candidate.id"
                      >
                        {{ candidate.name }}
                      </option>
                    </select>
                  </div>
                </div>
              </div>
            </div>
          </article>

          <!-- 添加/编辑模型弹窗 -->
          <div v-if="showAddModelModal" class="overlay-shell">
            <div class="overlay-card surface-panel modal-card">
              <div class="panel-header">
                <div>
                  <span class="section-label">{{ editModelData.id ? '编辑模型' : '添加自定义模型' }}</span>
                  <h2>{{ editModelData.id ? '编辑模型配置' : '接入新模型' }}</h2>
                </div>
                <button class="modal-close" type="button" @click="showAddModelModal = false; resetEditModel()">关闭</button>
              </div>
              <form class="modal-form" @submit.prevent="saveModel">
                <div class="setting-item">
                  <label class="field-label">模型名称</label>
                  <input v-model="editModelData.name" class="field-input" type="text" placeholder="例如：我的自定义模型" required />
                </div>
                <div class="setting-item">
                  <label class="field-label">类型</label>
                  <select v-model="editModelData.type" class="field-select">
                    <option value="cloud">云端API</option>
                    <option value="local">本地模型</option>
                  </select>
                </div>
                <div class="setting-item">
                  <label class="field-label">模型标识</label>
                  <input v-model="editModelData.model_name" class="field-input" type="text" placeholder="例如：gpt-4、deepseek-chat" required />
                </div>
                <div class="setting-item">
                  <label class="field-label">Base URL</label>
                  <input v-model="editModelData.base_url" class="field-input" type="text" placeholder="例如：https://api.deepseek.com/v1/chat/completions" required />
                </div>
                <div class="setting-item">
                  <label class="field-label">API Key</label>
                  <input v-model="editModelData.api_key" class="field-input" type="password" placeholder="输入你的 API Key" />
                </div>
                <div class="setting-item">
                  <label class="field-label">描述</label>
                  <textarea v-model="editModelData.description" class="field-textarea" placeholder="描述这个模型的用途"></textarea>
                </div>
                <div class="modal-actions">
                  <button class="btn btn-secondary" type="button" @click="showAddModelModal = false; resetEditModel()">取消</button>
                  <button class="btn btn-primary" type="submit">保存</button>
                </div>
              </form>
            </div>
          </div>

          <!-- 添加标签弹窗 -->
          <div v-if="showAddTagModal" class="overlay-shell">
            <div class="overlay-card surface-panel modal-card small-modal">
              <div class="panel-header">
                <div>
                  <span class="section-label">标签管理</span>
                  <h2>添加能力标签</h2>
                </div>
                <button class="modal-close" type="button" @click="showAddTagModal = false">关闭</button>
              </div>
              <form class="modal-form" @submit.prevent="addTagToModel">
                <div class="setting-item">
                  <label class="field-label">标签名称</label>
                  <input v-model="newTag" class="field-input" type="text" placeholder="例如：推理强、代码生成" required />
                </div>
                <div style="margin-bottom: 16px;">
                  <label class="field-label" style="margin-bottom: 8px; display: block;">常用标签</label>
                  <div style="display: flex; flex-wrap: wrap; gap: 8px;">
                    <button 
                      v-for="tag in commonTags" 
                      :key="tag" 
                      class="btn btn-secondary compact-btn" 
                      type="button" 
                      @click="newTag = tag"
                    >
                      {{ tag }}
                    </button>
                  </div>
                </div>
                <div class="modal-actions">
                  <button class="btn btn-secondary" type="button" @click="showAddTagModal = false">取消</button>
                  <button class="btn btn-primary" type="submit">添加</button>
                </div>
              </form>
            </div>
          </div>
        </section>
      </main>
    </section>

    <aside class="assistant-sidebar surface-panel" :class="{ 'is-collapsed': !drawerOpen }">
      <div class="assistant-head">
        <div>
          <span class="section-label">AI 助手</span>
          <h2>对话</h2>
          <p>{{ assistantSignature }}</p>
        </div>
        <span class="soft-badge">{{ currentSessionLabel }}</span>
      </div>

      <div class="assistant-context">
        <span class="soft-badge">{{ currentKnowledgeBase?.name || '未选择知识空间' }}</span>
      </div>

      <div class="session-selector">
        <select class="field-select compact-select" v-model="selectedSessionId">
          <option v-for="session in filteredSessions" :key="session.id" :value="String(session.id)">
            {{ session.session_name || '未命名会话' }}
          </option>
        </select>
        <button class="btn btn-secondary compact-btn" type="button" @click="createSession()">新建</button>
      </div>

      <div ref="messageListRef" class="message-list scrollable-area">
        <template v-if="messages.length">
          <article v-for="message in messages" :key="message.id" class="message-card" :class="message.role">
            <div class="message-card__meta">
              <strong>{{ message.role === 'user' ? '你' : '助手' }}</strong>
            </div>
            <div class="message-card__body markdown-body" v-html="renderMessage(message.content, message.role)"></div>
          </article>
        </template>
        <div v-else class="empty-state assistant-empty">
          <p>选择知识空间后即可提问，回答会尽量基于当前资料生成。</p>
        </div>
      </div>



      <form class="assistant-composer" :class="{ generating: assistantGenerating }" @submit.prevent="sendMessage">
        <div class="composer-input-wrapper">
          <textarea
            v-model="chatInput"
            class="field-textarea composer-textarea"
            placeholder="输入问题、摘要需求或写作任务"
          ></textarea>
          <div class="composer-actions">
            <button class="btn btn-primary compact-btn send-btn" type="submit" :disabled="assistantGenerating || !chatInput.trim() || !selectedKnowledgeId">
              {{ assistantGenerating ? '生成中' : '发送' }}
            </button>
            <button v-if="assistantGenerating" class="btn btn-secondary compact-btn pause-btn" type="button" @click="isPaused = !isPaused">
              {{ isPaused ? '继续' : '暂停' }}
            </button>
          </div>
        </div>
        <div class="composer-footer">
          <span class="stream-status">{{ streamStatus || 'Enter 发送，建议问题尽量具体。' }}</span>
        </div>
      </form>
    </aside>

    <input ref="fileInputRef" type="file" class="visually-hidden" @change="handleFileChange" />
    <input ref="codeFileInputRef" type="file" class="visually-hidden" @change="handleCodeFileChange" />

    <div v-if="knowledgeModal.visible" class="overlay-shell">
      <div class="overlay-card surface-panel modal-card large-modal">
        <div class="panel-header">
          <div>
            <span class="section-label">{{ knowledgeModal.mode === 'create' ? '新建主题' : '编辑主题' }}</span>
            <h2>{{ knowledgeModal.mode === 'create' ? '创建知识空间' : '编辑知识空间' }}</h2>
          </div>
          <button class="modal-close" type="button" @click="closeKnowledgeModal">关闭</button>
        </div>
        <form class="modal-form" @submit.prevent="submitKnowledgeBase">
          <div class="modal-grid">
            <div>
              <label class="field-label">名称</label>
              <input v-model="knowledgeModal.form.name" class="field-input" type="text" placeholder="例如：毕业设计" />
            </div>
            <div>
              <label class="field-label">分类</label>
              <input v-model="knowledgeModal.form.category" class="field-input" type="text" placeholder="例如：项目研究" />
            </div>
          </div>
          <div>
            <label class="field-label">描述</label>
            <textarea v-model="knowledgeModal.form.description" class="field-textarea" placeholder="描述这个知识空间的内容边界"></textarea>
          </div>
          <div>
            <label class="field-label">背景设定（Persona）</label>
            <textarea v-model="knowledgeModal.form.persona" class="field-textarea" placeholder="例如：你是一名操作系统面试官，擅长深入追问底层原理"></textarea>
          </div>
          <div class="modal-grid">
            <div>
              <label class="field-label">思考方式（Thinking Style）</label>
              <select v-model="knowledgeModal.form.thinking_style" class="field-select">
                <option value="teaching">教学型（逐步讲解、举例）</option>
                <option value="interview">面试型（反问、追问、压力测试）</option>
                <option value="summary">总结型（精炼输出、结构化）</option>
                <option value="reasoning">推理型（多步推理、对比分析）</option>
              </select>
            </div>
            <div>
              <label class="field-label">模型策略（Model Strategy）</label>
              <input v-model="knowledgeModal.form.model_strategy" class="field-input" type="text" placeholder="例如：使用 gpt-4 进行推理，使用 gpt-3.5 进行总结" />
            </div>
          </div>
          <div>
            <label class="field-label">任务策略（Task Policy）</label>
            <input v-model="knowledgeModal.form.task_policy" class="field-input" type="text" placeholder="例如：知识查缺、问题生成（用逗号分隔）" />
          </div>
          <div>
            <label class="field-label">标签（Tags）</label>
            <input v-model="knowledgeModal.form.tags" class="field-input" type="text" placeholder="例如：计算机科学, 机器学习（用逗号分隔）" />
          </div>
          <div>
            <label class="field-label">检索模式（Retrieval Mode）</label>
            <select v-model="knowledgeModal.form.retrieval_mode" class="field-select">
              <option value="hybrid">混合检索（默认）</option>
              <option value="vector">向量检索</option>
              <option value="keyword">关键词检索</option>
            </select>
          </div>

          <div class="modal-actions">
            <button class="btn btn-secondary" type="button" @click="closeKnowledgeModal">取消</button>
            <button class="btn btn-primary" type="submit" :disabled="loading.knowledge">
              {{ loading.knowledge ? '保存中...' : '保存' }}
            </button>
          </div>
        </form>
      </div>
    </div>

    <div v-if="importModal.visible" class="overlay-shell">
      <div class="overlay-card surface-panel modal-card small-modal">
        <div class="panel-header">
          <div>
            <span class="section-label">导入来源</span>
            <h2>选择导入方式</h2>
          </div>
          <button class="modal-close" type="button" @click="importModal.visible = false">关闭</button>
        </div>
        <div class="import-grid">
          <button
            v-for="source in importSources"
            :key="`modal-${source.key}`"
            class="import-option"
            :class="{ active: importModal.source === source.key }"
            type="button"
            @click="importModal.source = source.key"
          >
            <strong>{{ source.label }}</strong>
            <p>{{ source.description }}</p>
          </button>
        </div>
        <div class="modal-actions">
          <button class="btn btn-secondary" type="button" @click="importModal.visible = false">取消</button>
          <button class="btn btn-primary" type="button" @click="confirmImport">继续</button>
        </div>
      </div>
    </div>

    <div v-if="datasourceModal.visible" class="overlay-shell">
      <div class="overlay-card surface-panel modal-card">
        <div class="panel-header">
          <div>
            <span class="section-label">添加数据源</span>
            <h2>数据库连接配置</h2>
          </div>
          <button class="modal-close" type="button" @click="datasourceModal.visible = false">关闭</button>
        </div>
        <form class="modal-form" @submit.prevent="submitDatasource">
          <div class="modal-grid">
            <div>
              <label class="field-label">数据源名称</label>
              <input v-model="datasourceForm.datasourceName" class="field-input" type="text" placeholder="例如：MySQL 数据库" required />
            </div>
            <div>
              <label class="field-label">数据库类型</label>
              <select v-model="datasourceForm.dbType" class="field-select" required>
                <option value="mysql">MySQL</option>
                <option value="postgresql">PostgreSQL</option>
                <option value="sqlserver">SQL Server</option>
              </select>
            </div>
            <div>
              <label class="field-label">主机地址</label>
              <input v-model="datasourceForm.host" class="field-input" type="text" placeholder="localhost" required />
            </div>
            <div>
              <label class="field-label">端口</label>
              <input v-model="datasourceForm.port" class="field-input" type="number" placeholder="3306" required />
            </div>
            <div>
              <label class="field-label">数据库名称</label>
              <input v-model="datasourceForm.databaseName" class="field-input" type="text" placeholder="mydb" required />
            </div>
            <div>
              <label class="field-label">用户名</label>
              <input v-model="datasourceForm.username" class="field-input" type="text" placeholder="root" required />
            </div>
            <div>
              <label class="field-label">密码</label>
              <input v-model="datasourceForm.password" class="field-input" type="password" placeholder="password" required />
            </div>
          </div>
          <div class="modal-actions">
            <button class="btn btn-secondary" type="button" @click="testDatasourceConnection">测试连接</button>
            <button class="btn btn-primary" type="submit" :disabled="loading.datasource">添加数据源</button>
          </div>
        </form>
      </div>
    </div>

    <div v-if="webModal.visible" class="overlay-shell">
      <div class="overlay-card surface-panel modal-card">
        <div class="panel-header">
          <div>
            <span class="section-label">网页解析</span>
            <h2>输入网页链接</h2>
          </div>
          <button class="modal-close" type="button" @click="webModal.visible = false">关闭</button>
        </div>
        <form class="modal-form" @submit.prevent="submitWebUrl">
          <div>
            <label class="field-label">网页链接</label>
            <input v-model="webForm.url" class="field-input" type="url" placeholder="https://example.com" required />
          </div>
          <div>
            <label class="field-label">标题（可选）</label>
            <input v-model="webForm.title" class="field-input" type="text" placeholder="自动解析网页标题" />
          </div>
          <div class="modal-actions">
            <button class="btn btn-secondary" type="button" @click="webModal.visible = false">取消</button>
            <button class="btn btn-primary" type="submit" :disabled="loading.web">解析网页</button>
          </div>
        </form>
      </div>
    </div>

    <div v-if="textModal.visible" class="overlay-shell">
      <div class="overlay-card surface-panel modal-card">
        <div class="panel-header">
          <div>
            <span class="section-label">手动输入</span>
            <h2>输入文本内容</h2>
          </div>
          <button class="modal-close" type="button" @click="textModal.visible = false">关闭</button>
        </div>
        <form class="modal-form" @submit.prevent="submitText">
          <div>
            <label class="field-label">标题</label>
            <input v-model="textForm.title" class="field-input" type="text" placeholder="输入文本标题" required />
          </div>
          <div>
            <label class="field-label">内容</label>
            <textarea v-model="textForm.content" class="field-textarea" rows="10" placeholder="输入文本内容" required></textarea>
          </div>
          <div class="modal-actions">
            <button class="btn btn-secondary" type="button" @click="textModal.visible = false">取消</button>
            <button class="btn btn-primary" type="submit" :disabled="loading.text">上传文本</button>
          </div>
        </form>
      </div>
    </div>

    <div v-if="codeModal.visible" class="overlay-shell">
      <div class="overlay-card surface-panel modal-card">
        <div class="panel-header">
          <div>
            <span class="section-label">代码文件</span>
            <h2>添加代码数据源</h2>
          </div>
          <button class="modal-close" type="button" @click="codeModal.visible = false">关闭</button>
        </div>
        <form class="modal-form" @submit.prevent="submitCode">
          <div>
            <label class="field-label">代码语言</label>
            <select v-model="codeForm.codeLanguage" class="field-select">
              <option value="java">Java</option>
              <option value="python">Python</option>
              <option value="sql">SQL</option>
              <option value="javascript">JavaScript</option>
              <option value="typescript">TypeScript</option>
              <option value="cpp">C++</option>
              <option value="csharp">C#</option>
              <option value="go">Go</option>
              <option value="rust">Rust</option>
              <option value="php">PHP</option>
              <option value="ruby">Ruby</option>
              <option value="text">其他文本</option>
            </select>
          </div>
          <div>
            <label class="field-label">输入方式</label>
            <div style="display: flex; gap: 10px; margin-bottom: 10px;">
              <button type="button" class="btn" :class="codeForm.inputMode === 'file' ? 'btn-primary' : 'btn-secondary'" @click="codeForm.inputMode = 'file'">上传文件</button>
              <button type="button" class="btn" :class="codeForm.inputMode === 'paste' ? 'btn-primary' : 'btn-secondary'" @click="codeForm.inputMode = 'paste'">手动粘贴</button>
            </div>
          </div>
          
          <!-- 文件上传模式 -->
          <div v-if="codeForm.inputMode === 'file'">
            <label class="field-label">选择文件</label>
            <div class="upload-zone" @click="triggerCodeFileSelect" style="cursor: pointer;">
              <div v-if="codeForm.selectedFile" style="margin-bottom: 8px;">
                <strong>{{ codeForm.selectedFile.name }}</strong>
                <span style="margin-left: 10px; color: var(--text-muted);">({{ (codeForm.selectedFile.size / 1024).toFixed(2) }} KB)</span>
              </div>
              <div v-else>
                <strong>点击选择代码文件</strong>
                <p style="margin-top: 8px; color: var(--text-muted);">支持 .java, .py, .sql, .js, .ts, .cpp, .go, .rs 等格式</p>
              </div>
            </div>
          </div>
          
          <!-- 手动粘贴模式 -->
          <div v-if="codeForm.inputMode === 'paste'">
            <div style="margin-bottom: 15px;">
              <label class="field-label">代码标题</label>
              <input v-model="codeForm.codeTitle" class="field-input" type="text" placeholder="例如：用户认证模块" />
            </div>
            <div>
              <label class="field-label">粘贴代码</label>
              <textarea v-model="codeForm.codeContent" class="field-textarea" rows="15" placeholder="在此粘贴您的代码内容..." style="font-family: 'Courier New', monospace; font-size: 13px;"></textarea>
            </div>
          </div>
          
          <div class="modal-actions">
            <button class="btn btn-secondary" type="button" @click="codeModal.visible = false">取消</button>
            <button class="btn btn-primary" type="submit" :disabled="loading.code || !isCodeFormValid">
              {{ loading.code ? '分析中...' : '上传并分析' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</div>
</template>


<script setup>
import axios from 'axios'
import { computed, nextTick, onMounted, reactive, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { activateModel, getModelConfig, setEmbeddingModel } from '../api/platform'
import { clearAuthSession, getAuthToken, getAuthUser } from '../utils/auth'
import { renderMarkdown } from '../utils/markdown'

const router = useRouter()
const fileInputRef = ref(null)
const codeFileInputRef = ref(null)
const messageListRef = ref(null)

const goBack = () => {
  router.push('/dashboard')
}

const authUser = reactive(getAuthUser())
const userForm = reactive({
  username: authUser.username || '',
  nickname: authUser.nickname || '',
  email: authUser.email || ''
})
const theme = ref('light')
const language = ref('zh-CN')
const activeView = ref('dashboard')
const globalSearch = ref('')
const selectedKnowledgeId = ref('')
const selectedSessionId = ref('')
const activeSourceKey = ref('')
const chatInput = ref('')
const assistantGenerating = ref(false)
const streamStatus = ref('')
const drawerOpen = ref(true)
const isPaused = ref(false)

const toggleAssistant = () => {
  drawerOpen.value = !drawerOpen.value
}

const notice = reactive({
  type: 'success',
  text: ''
})

const stats = reactive({
  overall: {
    kb_count: 0,
    doc_count: 0,
    ds_count: 0,
    qa_count: 0,
    question_count: 0
  },
  today: {
    qa_count: 0,
    doc_count: 0,
    kb_count: 0,
    ds_count: 0
  },
  knowledge: {
    chunk_count: 0,
    table_count: 0,
    column_count: 0
  },
  trend: [],
  recent_qa: [],
  workspace: {
    today_new_notes: 0,
    today_question_count: 0,
    recent_learning_topics: [],
    recent_upload_documents: [],
    recent_visited_knowledge_bases: [],
    learning_streak_days: 0,
    weekly_hot_questions: [],
    recent_summaries: []
  }
})

const loading = reactive({
  quickNote: false,
  context: false,
  upload: false,
  models: false,
  datasource: false,
  web: false,
  text: false,
  knowledge: false,
  code: false
})

const knowledgeBases = ref([])
const knowledgeItems = ref([])
const quickNotes = ref([])
const chatSessions = ref([])
const messages = ref([])
const sourceHighlights = ref([])

const knowledgeModal = reactive({
  visible: false,
  mode: 'create',
  form: {
    id: '',
    name: '',
    description: '',
    category: '通用学习',
    tags: '',
    retrieval_mode: 'hybrid',
    persona: '',
    thinking_style: 'teaching',
    task_policy: [],
    model_strategy: ''
  }
})

const importModal = reactive({
  visible: false,
  source: 'pdf'
})

const datasourceModal = reactive({
  visible: false
})

const datasourceForm = reactive({
  datasourceName: '',
  dbType: 'mysql',
  host: 'localhost',
  port: 3306,
  databaseName: '',
  username: 'root',
  password: ''
})

const webModal = reactive({
  visible: false
})

const webForm = reactive({
  url: '',
  title: ''
})

const textModal = reactive({
  visible: false
})

const textForm = reactive({
  title: '',
  content: ''
})

const codeModal = reactive({
  visible: false
})

const codeForm = reactive({
  codeLanguage: 'java',
  selectedFile: null,
  inputMode: 'file', // 'file' or 'paste'
  codeContent: '',
  codeTitle: ''
})

const modelConfig = reactive({
  active_chat_model_id: '',
  active_embedding_model: '',
  models: [],
  embedding_options: []
})

const quickNoteForm = reactive({
  title: '',
  tags: '',
  content: '',
  isPinned: false,
  isFavorite: false
})

const primaryNav = [
  { key: 'dashboard', label: '工作台', icon: '', meta: 'Overview' },
  { key: 'knowledge', label: '多源数据', icon: '', meta: 'Data' },
  { key: 'assistant', label: 'ANote Agent', icon: '', meta: 'Agent' },
  { key: 'models', label: '多模型协同', icon: '', meta: 'Models' }
]

const importSources = [
  { key: 'pdf', label: 'PDF / 文档', description: '适合课程资料、论文和项目文档。' },
  { key: 'datasource', label: '添加数据源', description: '连接数据库，自动导入结构化数据。' },
  { key: 'web', label: '网页链接', description: '自动解析网页内容，生成笔记。' },
  { key: 'code', label: '代码文件', description: '上传Java/Python/SQL等代码文件，自动分析并生成文档。' }
]

let noticeTimer = null

const boardCards = computed(() => [
  {
    label: '已存知识',
    value: stats.overall.doc_count || 0,
    detail: `${stats.knowledge.chunk_count || 0} 个知识切片`
  },
  {
    label: 'AI 调用',
    value: stats.overall.qa_count || 0,
    detail: `今日提问 ${stats.today.qa_count || 0} 次`
  },
  {
    label: '同步来源',
    value: stats.overall.ds_count || 0,
    detail: `连续活跃 ${stats.workspace.learning_streak_days || 0} 天`
  }
])

const workspaceTopics = computed(() => stats.workspace.recent_learning_topics || [])

const boardTrendBars = computed(() => {
  const items = stats.trend || []
  const max = Math.max(...items.map((item) => item.count || 0), 1)
  return items.map((item) => ({
    ...item,
    height: `${Math.max(((item.count || 0) / max) * 120, 12)}px`
  }))
})

const activeModel = computed(() => modelConfig.models.find((item) => item.id === modelConfig.active_chat_model_id) || null)
const activeModelLabel = computed(() => activeModel.value?.name || '选择模型')
const assistantSignature = computed(() => activeModel.value?.name ? `当前模型：${activeModel.value.name}` : '当前未配置可用模型')

// AnoteAgent 功能模块
const agentActiveTab = ref('multiDoc')
const agentMenuOpen = ref(false)

const handleAgentClick = (key) => {
  if (key === 'assistant') {
    // 对于ANote Agent，切换菜单展开状态
    agentMenuOpen.value = !agentMenuOpen.value
    // 只有当菜单展开时才切换视图，或者当前已是该视图时保持
    if (agentMenuOpen.value || activeView.value === 'assistant') {
      activeView.value = key
    }
  } else {
    // 其他菜单项直接切换视图
    activeView.value = key
    agentMenuOpen.value = false
  }
}

const selectAgentTab = (tabId) => {
  agentActiveTab.value = tabId
  agentMenuOpen.value = false
}
const selectedDocuments = ref([])
const multiDocAnalysis = reactive({
  prompt: '',
  isAnalyzing: false,
  report: ''
})
const graphBuilding = reactive({
  isBuilding: false,
  progress: 0
})
const knowledgeGraph = reactive({
  nodes: [],
  edges: [],
  loaded: false
})
const knowledgeTrace = reactive({
  selectedAnswer: null,
  query: '',
  isTracing: false,
  answer: '',
  sources: []
})

// 多模型相关状态
const modelActiveTab = ref('list')
const showAddModelModal = ref(false)
const showAddTagModal = ref(false)
const currentEditModel = ref(null)
const newTag = ref('')

const editModelData = reactive({
  id: '',
  name: '',
  provider: 'openai-compatible',
  model_name: '',
  base_url: '',
  api_key: '',
  description: '',
  type: 'cloud',
  enabled: true,
  tags: []
})

const taskConfig = reactive({
  task_assignments: {},
  scheduling_strategy: 'fixed',
  fallback_models: {}
})

const taskTypes = [
  { key: 'chat', label: '智能对话' },
  { key: 'rag', label: '知识库问答' },
  { key: 'summary', label: '文本总结' },
  { key: 'knowledge_graph', label: '知识图谱构建' },
  { key: 'multi_doc_analysis', label: '多文档分析' },
  { key: 'knowledge_trace', label: '知识溯源' }
]

const commonTags = [
  '推理强',
  '速度快',
  '通用对话',
  '知识库问答',
  '文本总结',
  '逻辑推理',
  '复杂分析',
  '知识图谱构建',
  '代码生成',
  '创意写作'
]

// 图谱可视化相关
const graphContainerRef = ref(null)
const graphSvgRef = ref(null)
const graphSize = reactive({
  width: 800,
  height: 500
})
const nodePositions = reactive({}) // 存储节点位置
const selectedNode = ref('')
const selectedNodeData = ref(null)
const isDragging = ref(false)
const draggedNode = ref('')
const dragOffset = reactive({ x: 0, y: 0 })

// 初始化节点位置
const initializeNodePositions = () => {
  if (!knowledgeGraph.nodes.length) return
  
  const centerX = graphSize.width / 2
  const centerY = graphSize.height / 2
  const radius = Math.min(graphSize.width, graphSize.height) / 3
  
  knowledgeGraph.nodes.forEach((node, index) => {
    if (!nodePositions[node.node_id]) {
      const angle = (2 * Math.PI * index) / knowledgeGraph.nodes.length
      nodePositions[node.node_id] = {
        x: centerX + radius * Math.cos(angle),
        y: centerY + radius * Math.sin(angle)
      }
    }
  })
}

// 获取节点位置
const getNodePosition = (nodeId) => {
  if (!nodePositions[nodeId]) {
    return { x: graphSize.width / 2, y: graphSize.height / 2 }
  }
  return nodePositions[nodeId]
}

// 获取节点大小
const getNodeSize = (nameLength) => {
  return Math.min(60, 30 + nameLength * 2)
}

// 截断节点名称
const truncateNodeName = (name) => {
  if (!name) return ''
  if (name.length <= 8) return name
  return name.substring(0, 8) + '...'
}

// 获取连线颜色
const getEdgeColor = (relationType) => {
  switch (relationType) {
    case '高度相关':
      return '#ef4444'
    case '相关':
      return '#f59e0b'
    case '弱相关':
      return '#94a3b8'
    default:
      return '#94a3b8'
  }
}

// 获取连线宽度
const getEdgeWidth = (relationType) => {
  switch (relationType) {
    case '高度相关':
      return 3
    case '相关':
      return 2
    case '弱相关':
      return 1
    default:
      return 1
  }
}

// 处理节点点击
const handleNodeClick = (node) => {
  selectedNode.value = node.node_id
  selectedNodeData.value = node
}

// 处理连线点击
const handleEdgeClick = (edge) => {
  console.log('Edge clicked:', edge)
}

// 开始拖拽
const startDrag = (event, nodeId) => {
  isDragging.value = true
  draggedNode.value = nodeId
  
  const rect = graphSvgRef.value.getBoundingClientRect()
  const nodePos = getNodePosition(nodeId)
  
  dragOffset.x = event.clientX - rect.left - nodePos.x
  dragOffset.y = event.clientY - rect.top - nodePos.y
  
  document.addEventListener('mousemove', onDrag)
  document.addEventListener('mouseup', stopDrag)
}

// 拖拽中
const onDrag = (event) => {
  if (!isDragging.value || !draggedNode.value) return
  
  const rect = graphSvgRef.value.getBoundingClientRect()
  let x = event.clientX - rect.left - dragOffset.x
  let y = event.clientY - rect.top - dragOffset.y
  
  // 限制在画布范围内
  x = Math.max(30, Math.min(graphSize.width - 30, x))
  y = Math.max(30, Math.min(graphSize.height - 30, y))
  
  nodePositions[draggedNode.value] = { x, y }
}

// 停止拖拽
const stopDrag = () => {
  isDragging.value = false
  draggedNode.value = ''
  document.removeEventListener('mousemove', onDrag)
  document.removeEventListener('mouseup', stopDrag)
}

// 调整图谱大小
const resizeGraph = () => {
  if (graphContainerRef.value) {
    graphSize.width = graphContainerRef.value.clientWidth || 800
    graphSize.height = 500
    initializeNodePositions()
  }
}

// 监听知识图谱数据变化
watch(() => [knowledgeGraph.nodes, knowledgeGraph.loaded], () => {
  if (knowledgeGraph.loaded) {
    nextTick(() => {
      resizeGraph()
      initializeNodePositions()
    })
  }
})

// 窗口大小变化时调整图谱
onMounted(() => {
  window.addEventListener('resize', resizeGraph)
})

const agentTabs = [
  {
    id: 'multiDoc', 
    name: '多文档联合分析',
    description: '跨文档理解与分析'
  },
  {
    id: 'graph',
    name: '知识图谱构建',
    description: '提取概念、建立关系'
  },
  {
    id: 'trace',
    name: '知识溯源',
    description: '追溯AI回答的来源依据'
  }
]
const currentViewMeta = computed(() => {
  const map = {
    dashboard: {
      kicker: 'Workspace',
      title: '工作台',
      description: '把知识空间、近期内容和对话入口集中在一页。'
    },
    notes: {
      kicker: 'Notes',
      title: '笔记',
      description: '在当前知识空间中写作、补充和整理你的内容。'
    },
    knowledge: {
      kicker: 'Library',
      title: '知识库',
      description: '管理资料导入、切片和当前主题的来源结构。'
    },
    assistant: {
      kicker: 'ANote Agent',
      title: '智能知识分析与管理',
      description: '多文档联合分析、知识图谱构建、知识溯源，让AI帮您深度理解和管理知识'
    },
    models: {
      kicker: 'Models',
      title: '多模型协同',
      description: '管理和配置各种AI模型。'
    }
  }
  return map[activeView.value] || map.dashboard
})

const currentKnowledgeBase = computed(() => {
  return knowledgeBases.value.find((item) => String(item.id) === String(selectedKnowledgeId.value)) || null
})

const filteredKnowledgeBases = computed(() => {
  const query = globalSearch.value.trim().toLowerCase()
  if (!query) return knowledgeBases.value
  return knowledgeBases.value.filter((item) => matchesQuery(`${item.name} ${item.category} ${item.description} ${(item.tags || []).join(' ')}`, query))
})

const filteredKnowledgeItems = computed(() => {
  const query = globalSearch.value.trim().toLowerCase()
  if (!query) return knowledgeItems.value
  return knowledgeItems.value.filter((item) => matchesQuery(`${item.title || ''} ${item.file_name || ''} ${item.source_type || ''}`, query))
})

const filteredQuickNotes = computed(() => {
  const query = globalSearch.value.trim().toLowerCase()
  if (!query) return quickNotes.value
  return quickNotes.value.filter((item) => matchesQuery(`${item.title || ''} ${item.content || ''}`, query))
})

const filteredSessions = computed(() => {
  const query = globalSearch.value.trim().toLowerCase()
  if (!query) return chatSessions.value
  return chatSessions.value.filter((item) => matchesQuery(item.session_name || '', query))
})

const currentSessionLabel = computed(() => {
  const session = chatSessions.value.find((item) => String(item.id) === String(selectedSessionId.value))
  return session?.session_name || '未开始对话'
})

const suggestionSources = computed(() => {
  const items = [
    ...knowledgeItems.value.slice(0, 4).map((item) => ({
      key: `item-${item.id}`,
      title: item.title || item.file_name || '未命名条目',
      subtitle: sourceLabel(item.source_type),
      kind: '知识',
      content: item.content || ''
    })),
    ...quickNotes.value.slice(0, 3).map((item) => ({
      key: `note-${item.id}`,
      title: item.title || '未命名笔记',
      subtitle: '快速笔记',
      kind: '笔记',
      content: item.content || ''
    }))
  ]
  return items.slice(0, 5)
})

const parseTags = (value) => {
  if (Array.isArray(value)) return value.filter(Boolean)
  if (!value) return []
  if (typeof value === 'string') {
    const text = value.trim()
    if (!text) return []
    try {
      const parsed = JSON.parse(text)
      if (Array.isArray(parsed)) return parsed.filter(Boolean)
    } catch (error) {
      return text.split(',').map((item) => item.trim()).filter(Boolean)
    }
    return []
  }
  return []
}

const normalizeKnowledgeBase = (item) => ({
  ...item,
  tags: parseTags(item.tags)
})

const sourceLabel = (type) => {
  const map = {
    file: '文件资料',
    manual: '快速笔记',
    database_schema: '数据库结构'
  }
  return map[type] || '知识条目'
}

const shortText = (value, limit = 80) => {
  const text = String(value || '').replace(/\s+/g, ' ').trim()
  if (!text) return '暂无摘要'
  return text.length > limit ? `${text.slice(0, limit)}...` : text
}

const matchesQuery = (text, query) => String(text || '').toLowerCase().includes(query)

const showNotice = (text, type = 'success') => {
  notice.text = text
  notice.type = type
  if (noticeTimer) clearTimeout(noticeTimer)
  noticeTimer = setTimeout(() => {
    notice.text = ''
  }, 2800)
}

const beautifyAssistantContent = (content = '') => {
  let text = String(content || '')
  if (!text.trim()) {
    return '### 正在整理回答\n\n请稍候，AI 正在结合知识库内容生成结果。'
  }

  text = text
    .replace(/\[思考\]：?/g, '### 思考过程\n')
    .replace(/\[回答\]：?/g, '### 回答内容\n')
    .replace(/\n{3,}/g, '\n\n')

  if (!/^#{1,3}\s/.test(text.trim())) {
    text = `### 回答内容\n\n${text.trim()}`
  }

  return text
}

const applyStats = (data = {}) => {
  Object.assign(stats.overall, data.overall || {})
  Object.assign(stats.today, data.today || {})
  Object.assign(stats.knowledge, data.knowledge || {})
  stats.trend = data.trend || []
  stats.recent_qa = data.recent_qa || []
  Object.assign(stats.workspace, {
    today_new_notes: 0,
    today_question_count: 0,
    recent_learning_topics: [],
    recent_upload_documents: [],
    recent_visited_knowledge_bases: [],
    learning_streak_days: 0,
    weekly_hot_questions: [],
    recent_summaries: [],
    ...(data.workspace || {})
  })
}

const loadDashboard = async () => {
  const { data } = await axios.get('/api/dashboard/stats')
  applyStats(data)
}

const loadKnowledgeBases = async () => {
  const { data } = await axios.get('/api/knowledge/list')
  knowledgeBases.value = (data || []).map(normalizeKnowledgeBase)

  if (!knowledgeBases.value.length) {
    selectedKnowledgeId.value = ''
    return
  }

  const exists = knowledgeBases.value.find((item) => String(item.id) === String(selectedKnowledgeId.value))
  selectedKnowledgeId.value = String((exists || knowledgeBases.value[0]).id)
}

const loadModels = async () => {
  loading.models = true
  try {
    const data = await getModelConfig()
    modelConfig.active_chat_model_id = data.active_chat_model_id || ''
    modelConfig.active_embedding_model = data.active_embedding_model || ''
    modelConfig.models = data.models || []
    modelConfig.embedding_options = data.embedding_options || []
  } finally {
    loading.models = false
  }
}

const loadKnowledgeContext = async (knowledgeId) => {
  if (!knowledgeId) {
    knowledgeItems.value = []
    quickNotes.value = []
    chatSessions.value = []
    messages.value = []
    sourceHighlights.value = []
    selectedSessionId.value = ''
    return
  }

  loading.context = true
  try {
    const [itemsRes, notesRes, sessionsRes] = await Promise.all([
      axios.get(`/api/knowledge/items/${knowledgeId}`),
      axios.get('/api/materials/quick-notes', { params: { knowledge_id: knowledgeId } }),
      axios.get('/api/chat/sessions', { params: { knowledge_id: knowledgeId } })
    ])

    knowledgeItems.value = itemsRes.data || []
    quickNotes.value = notesRes.data || []
    chatSessions.value = sessionsRes.data || []

    const existing = chatSessions.value.find((item) => String(item.id) === String(selectedSessionId.value))
    selectedSessionId.value = existing ? String(existing.id) : String(chatSessions.value[0]?.id || '')

    if (!selectedSessionId.value) {
      messages.value = []
    }

    sourceHighlights.value = suggestionSources.value.slice(0, 3)
  } finally {
    loading.context = false
  }
}

const loadMessages = async (sessionId) => {
  if (!sessionId) {
    messages.value = []
    return
  }
  const { data } = await axios.get('/api/chat/messages', { params: { session_id: sessionId } })
  messages.value = data || []
}

const loadInitialData = async () => {
  try {
    await Promise.all([loadDashboard(), loadKnowledgeBases(), loadModels()])
  } catch (error) {
    showNotice(error?.response?.data?.error || '初始化数据失败', 'error')
  }
}

const openKnowledgeModal = (item = null) => {
  knowledgeModal.visible = true
  knowledgeModal.mode = item ? 'edit' : 'create'
  knowledgeModal.form.id = item?.id || ''
  knowledgeModal.form.name = item?.name || ''
  knowledgeModal.form.description = item?.description || ''
  knowledgeModal.form.category = item?.category || '通用学习'
  knowledgeModal.form.tags = (item?.tags || []).join(', ')
  knowledgeModal.form.retrieval_mode = item?.retrieval_mode || 'hybrid'
  knowledgeModal.form.persona = item?.persona || ''
  knowledgeModal.form.thinking_style = item?.thinking_style || 'teaching'
  knowledgeModal.form.task_policy = item?.task_policy || []
  knowledgeModal.form.model_strategy = item?.model_strategy || ''
}

const closeKnowledgeModal = () => {
  knowledgeModal.visible = false
}

const submitKnowledgeBase = async () => {
  if (!knowledgeModal.form.name.trim()) {
    showNotice('请输入知识库名称', 'error')
    return
  }

  const payload = {
    id: knowledgeModal.form.id,
    name: knowledgeModal.form.name.trim(),
    description: knowledgeModal.form.description.trim(),
    category: knowledgeModal.form.category.trim(),
    tags: knowledgeModal.form.tags,
    retrieval_mode: knowledgeModal.form.retrieval_mode,
    persona: knowledgeModal.form.persona,
    thinking_style: knowledgeModal.form.thinking_style,
    task_policy: knowledgeModal.form.task_policy,
    model_strategy: knowledgeModal.form.model_strategy
  }

  loading.knowledge = true
  try {
    const response = knowledgeModal.mode === 'create'
      ? await axios.post('/api/knowledge/create', payload)
      : await axios.put('/api/knowledge/update', payload)

    closeKnowledgeModal()
    await loadKnowledgeBases()
    selectedKnowledgeId.value = String(response.data.id)
    showNotice(knowledgeModal.mode === 'create' ? '知识主题已创建' : '知识主题已更新')
    await loadDashboard()
  } catch (error) {
    showNotice(error?.response?.data?.error || '保存主题失败', 'error')
  } finally {
    loading.knowledge = false
  }
}

const removeKnowledgeBase = async (item) => {
  if (!item || !window.confirm(`确认删除知识库“${item.name}”吗？`)) return
  try {
    await axios.delete(`/api/knowledge/delete/${item.id}`)
    if (String(selectedKnowledgeId.value) === String(item.id)) {
      selectedKnowledgeId.value = ''
    }
    await loadKnowledgeBases()
    await loadDashboard()
    showNotice('知识主题已删除')
  } catch (error) {
    showNotice(error?.response?.data?.error || '删除主题失败', 'error')
  }
}

const submitQuickNote = async () => {
  if (!selectedKnowledgeId.value) {
    showNotice('请先选择一个知识库', 'error')
    return
  }
  if (!quickNoteForm.content.trim()) {
    showNotice('请先写一点内容', 'error')
    return
  }

  loading.quickNote = true
  try {
    await axios.post('/api/materials/quick-notes', {
      knowledgeId: selectedKnowledgeId.value,
      title: quickNoteForm.title,
      content: quickNoteForm.content,
      tags: quickNoteForm.tags,
      isPinned: quickNoteForm.isPinned,
      isFavorite: quickNoteForm.isFavorite
    })
    quickNoteForm.title = ''
    quickNoteForm.tags = ''
    quickNoteForm.content = ''
    quickNoteForm.isPinned = false
    quickNoteForm.isFavorite = false
    await Promise.all([loadKnowledgeContext(selectedKnowledgeId.value), loadDashboard()])
    showNotice('笔记已写入知识库')
  } catch (error) {
    showNotice(error?.response?.data?.error || '保存笔记失败', 'error')
  } finally {
    loading.quickNote = false
  }
}

const removeQuickNote = async (item) => {
  if (!window.confirm('确认删除这条笔记吗？')) return
  try {
    await axios.delete(`/api/materials/quick-notes/${item.id}`)
    await Promise.all([loadKnowledgeContext(selectedKnowledgeId.value), loadDashboard()])
    showNotice('笔记已删除')
  } catch (error) {
    showNotice(error?.response?.data?.error || '删除笔记失败', 'error')
  }
}

const removeKnowledgeItem = async (item) => {
  if (!window.confirm('确认移除这条知识条目吗？')) return
  try {
    await axios.delete(`/api/knowledge/item/${item.id}`)
    await Promise.all([loadKnowledgeContext(selectedKnowledgeId.value), loadDashboard()])
    showNotice('知识条目已移除')
  } catch (error) {
    showNotice(error?.response?.data?.error || '移除知识条目失败', 'error')
  }
}

const clearKnowledgeBase = async () => {
  if (!selectedKnowledgeId.value || !window.confirm('确认清空当前知识库中的文档和笔记吗？')) return
  try {
    await axios.post('/api/knowledge/clear', null, {
      params: { knowledge_id: selectedKnowledgeId.value }
    })
    await Promise.all([loadKnowledgeContext(selectedKnowledgeId.value), loadDashboard()])
    showNotice('当前知识库已清空')
  } catch (error) {
    showNotice(error?.response?.data?.error || '清空知识库失败', 'error')
  }
}

// AnoteAgent 相关函数
const toggleDocument = (docId) => {
  const index = selectedDocuments.value.indexOf(docId)
  if (index > -1) {
    selectedDocuments.value.splice(index, 1)
  } else {
    selectedDocuments.value.push(docId)
  }
}

const startMultiDocAnalysis = async () => {
  if (selectedDocuments.value.length === 0) {
    showNotice('请先选择要分析的文档', 'error')
    return
  }
  if (!multiDocAnalysis.prompt.trim()) {
    showNotice('请输入分析要求', 'error')
    return
  }
  if (!selectedKnowledgeId.value) {
    showNotice('请先选择一个知识空间', 'error')
    return
  }

  multiDocAnalysis.isAnalyzing = true
  try {
    const response = await axios.post('/api/agent/multi-doc-analysis', {
      knowledge_id: selectedKnowledgeId.value,
      doc_ids: selectedDocuments.value,
      query: multiDocAnalysis.prompt,
      model_id: modelConfig.active_chat_model_id
    })

    const result = response.data
    if (result.success) {
      let report = `# 多文档分析报告\n\n`
      report += `## 任务类型：${result.intent.task_type === 'compare' ? '对比分析' : result.intent.task_type === 'relation' ? '关系提取' : '总结归纳'}\n\n`
      report += `## 分析文档：\n`
      for (const [docId, title] of Object.entries(result.doc_titles)) {
        report += `- ${title}\n`
      }
      report += `\n---\n\n`
      report += result.analysis
      
      multiDocAnalysis.report = report
      showNotice('多文档分析完成！')
    } else {
      showNotice(result.error || '分析失败', 'error')
    }
  } catch (error) {
    const errorMsg = error?.response?.data?.error || error?.message || '分析失败'
    showNotice(errorMsg, 'error')
  } finally {
    multiDocAnalysis.isAnalyzing = false
  }
}

const exportReport = () => {
  if (!multiDocAnalysis.report) {
    showNotice('暂无报告可导出', 'error')
    return
  }
  showNotice('PDF导出功能开发中...')
}

const startKnowledgeTrace = async () => {
  if (!knowledgeTrace.query.trim()) {
    showNotice('请输入查询问题', 'error')
    return
  }
  if (!selectedKnowledgeId.value) {
    showNotice('请先选择一个知识空间', 'error')
    return
  }

  knowledgeTrace.isTracing = true
  try {
    const response = await axios.post('/api/agent/knowledge-trace', {
      knowledge_id: selectedKnowledgeId.value,
      query: knowledgeTrace.query,
      model_id: modelConfig.active_chat_model_id
    })

    const result = response.data
    if (result.success) {
      knowledgeTrace.answer = result.answer
      knowledgeTrace.sources = result.sources || []
      showNotice('知识溯源完成！')
    } else {
      showNotice(result.error || '溯源失败', 'error')
    }
  } catch (error) {
    const errorMsg = error?.response?.data?.error || error?.message || '溯源失败'
    showNotice(errorMsg, 'error')
  } finally {
    knowledgeTrace.isTracing = false
  }
}

const formatAnswerWithHighlights = (answer) => {
  if (!answer) return ''
  
  let formatted = answer
  // 替换[来源: xxx]为高亮样式
  formatted = formatted.replace(/\[来源:\s*([^\]]+)\]/g, '<span style="background: #dbeafe; color: #1d4ed8; padding: 2px 6px; border-radius: 4px; font-weight: 500;">[来源: $1]</span>')
  
  // 简单的Markdown处理
  formatted = formatted.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
  formatted = formatted.replace(/\*(.*?)\*/g, '<em>$1</em>')
  formatted = formatted.replace(/\n/g, '<br>')
  
  return formatted
}

const formatScore = (score) => {
  if (!score) return ''
  if (typeof score === 'number') {
    return (score * 100).toFixed(0) + '%'
  }
  return score
}

// 多模型相关函数
const loadTaskConfig = async () => {
  try {
    const response = await axios.get('/api/models/tasks')
    taskConfig.task_assignments = response.data.task_assignments || {}
    taskConfig.scheduling_strategy = response.data.scheduling_strategy || 'fixed'
    taskConfig.fallback_models = response.data.fallback_models || {}
  } catch (error) {
    console.error('加载任务配置失败', error)
  }
}

const toggleModelStatus = async (model) => {
  try {
    await axios.post('/api/models', {
      action: 'update_status',
      model_id: model.id,
      enabled: !model.enabled
    })
    await loadModels()
    showNotice(model.enabled ? '模型已停用' : '模型已启用')
  } catch (error) {
    showNotice(error?.response?.data?.error || '操作失败', 'error')
  }
}

const setAsMainModel = async (modelId) => {
  try {
    await axios.post('/api/models', {
      action: 'activate',
      model_id: modelId
    })
    await loadModels()
    showNotice('已设为主对话模型')
  } catch (error) {
    showNotice(error?.response?.data?.error || '操作失败', 'error')
  }
}

const editModel = (model) => {
  editModelData.id = model.id
  editModelData.name = model.name
  editModelData.model_name = model.model_name
  editModelData.base_url = model.base_url
  editModelData.description = model.description
  editModelData.type = model.type || 'cloud'
  editModelData.enabled = model.enabled
  editModelData.tags = [...(model.tags || [])]
  showAddModelModal.value = true
}

const resetEditModel = () => {
  editModelData.id = ''
  editModelData.name = ''
  editModelData.model_name = ''
  editModelData.base_url = ''
  editModelData.api_key = ''
  editModelData.description = ''
  editModelData.type = 'cloud'
  editModelData.enabled = true
  editModelData.tags = []
}

const saveModel = async () => {
  try {
    await axios.post('/api/models', {
      action: 'save_custom',
      ...editModelData,
      set_active: false
    })
    showAddModelModal.value = false
    resetEditModel()
    await loadModels()
    showNotice('模型保存成功')
  } catch (error) {
    showNotice(error?.response?.data?.error || '保存失败', 'error')
  }
}

const deleteModel = async (model) => {
  if (!confirm(`确定要删除模型 ${model.name} 吗？`)) return
  try {
    await axios.post('/api/models', {
      action: 'delete_custom',
      model_id: model.id
    })
    await loadModels()
    showNotice('模型已删除')
  } catch (error) {
    showNotice(error?.response?.data?.error || '删除失败', 'error')
  }
}

const addTagToModel = async () => {
  if (!newTag.value.trim() || !currentEditModel.value) return
  try {
    const tags = [...(currentEditModel.value.tags || []), newTag.value.trim()]
    await axios.post('/api/models', {
      action: 'update_tags',
      model_id: currentEditModel.value.id,
      tags: tags
    })
    showAddTagModal.value = false
    newTag.value = ''
    currentEditModel.value = null
    await loadModels()
    showNotice('标签添加成功')
  } catch (error) {
    showNotice(error?.response?.data?.error || '添加失败', 'error')
  }
}

const removeModelTag = async (model, tag) => {
  try {
    const tags = (model.tags || []).filter(t => t !== tag)
    await axios.post('/api/models', {
      action: 'update_tags',
      model_id: model.id,
      tags: tags
    })
    await loadModels()
    showNotice('标签已移除')
  } catch (error) {
    showNotice(error?.response?.data?.error || '移除失败', 'error')
  }
}

const assignTaskModel = async (taskType, modelId) => {
  try {
    await axios.post('/api/models/tasks', {
      action: 'update_task',
      task_type: taskType,
      model_id: modelId
    })
    await loadTaskConfig()
    showNotice('任务分配成功')
  } catch (error) {
    showNotice(error?.response?.data?.error || '分配失败', 'error')
  }
}

const changeSchedulingStrategy = async (strategy) => {
  try {
    await axios.post('/api/models/tasks', {
      action: 'update_strategy',
      strategy: strategy
    })
    await loadTaskConfig()
    showNotice('调度策略已更新')
  } catch (error) {
    showNotice(error?.response?.data?.error || '更新失败', 'error')
  }
}

const setFallbackModels = async (modelId, fallbackIds) => {
  try {
    await axios.post('/api/models/tasks', {
      action: 'update_fallback',
      model_id: modelId,
      fallback_ids: fallbackIds
    })
    await loadTaskConfig()
    showNotice('备用模型已更新')
  } catch (error) {
    showNotice(error?.response?.data?.error || '更新失败', 'error')
  }
}

const startBuildGraph = async () => {
  if (!selectedKnowledgeId.value) {
    showNotice('请先选择一个知识空间', 'error')
    return
  }

  graphBuilding.isBuilding = true
  graphBuilding.progress = 0

  try {
    // 模拟进度
    const progressInterval = setInterval(() => {
      if (graphBuilding.progress < 90) {
        graphBuilding.progress += 10
      }
    }, 500)

    // 调用后端API
    const response = await axios.post('/api/agent/build-knowledge-graph', {
      knowledge_id: selectedKnowledgeId.value
    })

    clearInterval(progressInterval)

    const result = response.data
    if (result.success) {
      graphBuilding.progress = 100
      
      // 更新图谱数据
      knowledgeGraph.nodes = result.graph?.nodes || []
      knowledgeGraph.edges = result.graph?.edges || []
      knowledgeGraph.loaded = true
      
      showNotice('知识图谱构建完成！')
    } else {
      showNotice(result.error || '图谱构建失败', 'error')
    }
  } catch (error) {
    const errorMsg = error?.response?.data?.error || error?.message || '图谱构建失败'
    showNotice(errorMsg, 'error')
  } finally {
    graphBuilding.isBuilding = false
  }
}

const loadKnowledgeGraph = async () => {
  if (!selectedKnowledgeId.value) return

  try {
    const response = await axios.get('/api/agent/get-knowledge-graph', {
      params: { knowledge_id: selectedKnowledgeId.value }
    })

    const result = response.data
    if (result.success) {
      knowledgeGraph.nodes = result.nodes || []
      knowledgeGraph.edges = result.edges || []
      knowledgeGraph.loaded = true
    }
  } catch (error) {
    console.error('加载知识图谱失败', error)
  }
}

const openImportModal = (source = 'pdf') => {
  importModal.visible = true
  importModal.source = source
}

const confirmImport = () => {
  importModal.visible = false
  if (!selectedKnowledgeId.value) {
    showNotice('请先选择一个知识库', 'error')
    return
  }
  if (importModal.source === 'pdf') {
    fileInputRef.value?.click()
  } else if (importModal.source === 'datasource') {
    datasourceModal.visible = true
  } else if (importModal.source === 'web') {
    webModal.visible = true
  } else if (importModal.source === 'code') {
    codeModal.visible = true
  }
}

const testDatasourceConnection = async () => {
  try {
    const response = await axios.post('/api/datasource/test', {
      dbType: datasourceForm.dbType,
      host: datasourceForm.host,
      port: datasourceForm.port,
      username: datasourceForm.username,
      password: datasourceForm.password,
      databaseName: datasourceForm.databaseName
    })
    showNotice('连接测试成功')
  } catch (error) {
    showNotice(error?.response?.data?.error || '连接测试失败', 'error')
  }
}

const submitDatasource = async () => {
  if (!selectedKnowledgeId.value) {
    showNotice('请先选择一个知识库', 'error')
    return
  }
  loading.datasource = true
  try {
    const response = await axios.post('/api/datasource/add', {
      knowledgeId: selectedKnowledgeId.value,
      datasourceName: datasourceForm.datasourceName,
      dbType: datasourceForm.dbType,
      host: datasourceForm.host,
      port: datasourceForm.port,
      username: datasourceForm.username,
      password: datasourceForm.password,
      databaseName: datasourceForm.databaseName
    })
    showNotice('数据源添加成功')
    datasourceModal.visible = false
    await loadKnowledgeContext(selectedKnowledgeId.value)
  } catch (error) {
    showNotice(error?.response?.data?.error || '添加数据源失败', 'error')
  } finally {
    loading.datasource = false
  }
}

const submitWebUrl = async () => {
  if (!selectedKnowledgeId.value) {
    showNotice('请先选择一个知识库', 'error')
    return
  }
  loading.web = true
  try {
    const response = await axios.post('/api/web/parse', {
      knowledgeId: selectedKnowledgeId.value,
      url: webForm.url,
      title: webForm.title
    })
    showNotice('网页解析成功')
    webModal.visible = false
    await loadKnowledgeContext(selectedKnowledgeId.value)
  } catch (error) {
    showNotice(error?.response?.data?.error || '网页解析失败', 'error')
  } finally {
    loading.web = false
  }
}

const openTextModal = () => {
  textForm.title = ''
  textForm.content = ''
  textModal.visible = true
}

const submitText = async () => {
  if (!selectedKnowledgeId.value) {
    showNotice('请先选择一个知识库', 'error')
    return
  }
  loading.text = true
  try {
    const response = await axios.post('/api/text/upload', {
      knowledgeId: selectedKnowledgeId.value,
      title: textForm.title,
      content: textForm.content
    })
    showNotice('文本上传成功')
    textModal.visible = false
    await loadKnowledgeContext(selectedKnowledgeId.value)
  } catch (error) {
    showNotice(error?.response?.data?.error || '文本上传失败', 'error')
  } finally {
    loading.text = false
  }
}

// 验证表单是否有效
const isCodeFormValid = computed(() => {
  if (codeForm.inputMode === 'file') {
    return codeForm.selectedFile !== null
  } else {
    return codeForm.codeTitle.trim() !== '' && codeForm.codeContent.trim() !== ''
  }
})

// 触发文件选择
const triggerCodeFileSelect = () => {
  if (codeFileInputRef.value) {
    codeFileInputRef.value.click()
  } else {
    showNotice('文件选择器未就绪', 'error')
  }
}

// 处理文件选择
const handleCodeFileChange = (event) => {
  const file = event.target.files?.[0]
  event.target.value = ''
  if (file) {
    codeForm.selectedFile = file
  }
}

// 提交代码
const submitCode = async () => {
  if (!selectedKnowledgeId.value) {
    showNotice('请先选择一个知识库', 'error')
    return
  }

  loading.code = true
  try {
    if (codeForm.inputMode === 'file') {
      // 文件上传模式
      const formData = new FormData()
      formData.append('file', codeForm.selectedFile)
      formData.append('knowledgeId', selectedKnowledgeId.value)
      formData.append('codeLanguage', codeForm.codeLanguage)

      await axios.post('/api/code/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      })
    } else {
      // 手动粘贴模式
      await axios.post('/api/code/upload', {
        knowledgeId: selectedKnowledgeId.value,
        codeLanguage: codeForm.codeLanguage,
        codeTitle: codeForm.codeTitle,
        codeContent: codeForm.codeContent
      })
    }

    showNotice('代码上传并分析成功')
    codeModal.visible = false
    // 重置表单
    codeForm.selectedFile = null
    codeForm.codeContent = ''
    codeForm.codeTitle = ''
    codeForm.inputMode = 'file'
    await Promise.all([loadKnowledgeContext(selectedKnowledgeId.value), loadDashboard()])
  } catch (error) {
    showNotice(error?.response?.data?.error || '代码上传失败', 'error')
  } finally {
    loading.code = false
  }
}

const handleFileChange = async (event) => {
  const file = event.target.files?.[0]
  event.target.value = ''
  if (!file || !selectedKnowledgeId.value) return

  loading.upload = true
  try {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('knowledgeId', selectedKnowledgeId.value)
    await axios.post('/api/upload', formData)
    await Promise.all([loadKnowledgeContext(selectedKnowledgeId.value), loadDashboard()])
    showNotice('资料导入成功')
  } catch (error) {
    showNotice(error?.response?.data?.error || '资料导入失败', 'error')
  } finally {
    loading.upload = false
  }
}

const createSession = async (silent = false) => {
  if (!selectedKnowledgeId.value) {
    if (!silent) showNotice('请先选择一个知识库', 'error')
    return ''
  }
  try {
    const { data } = await axios.post('/api/chat/session/create', {
      knowledgeId: selectedKnowledgeId.value
    })
    chatSessions.value = [data, ...chatSessions.value]
    selectedSessionId.value = String(data.id)
    if (!silent) showNotice('已创建新的对话')
    return String(data.id)
  } catch (error) {
    showNotice(error?.response?.data?.error || '创建对话失败', 'error')
    return ''
  }
}

const ensureAvailableChatModel = async () => {
  if (activeModel.value?.has_api_key) {
    return true
  }

  const fallbackModel = modelConfig.models.find((item) => item.has_api_key)
  if (fallbackModel) {
    await changeChatModel(fallbackModel.id, true)
    showNotice(`已自动切换到可用模型：${fallbackModel.name}`)
    return true
  }

  drawerOpen.value = true
  showNotice('当前没有可用的对话模型，请先在设置中配置 API Key', 'error')
  return false
}

const buildSourceHighlights = (text = '') => {
  const query = String(text || '').toLowerCase()
  const terms = query.split(/[^\p{L}\p{N}_-]+/u).filter((item) => item.length >= 2).slice(0, 12)
  const pool = [
    ...knowledgeItems.value.map((item) => ({
      key: `item-${item.id}`,
      title: item.title || item.file_name || '未命名条目',
      subtitle: `${sourceLabel(item.source_type)} · ${item.chunk_count || 0} 个切片`,
      kind: '知识',
      content: item.content || ''
    })),
    ...quickNotes.value.map((item) => ({
      key: `note-${item.id}`,
      title: item.title || '未命名笔记',
      subtitle: '快速笔记',
      kind: '笔记',
      content: item.content || ''
    }))
  ]

  return pool
    .map((item) => {
      const searchable = `${item.title} ${item.subtitle} ${item.content}`.toLowerCase()
      let score = query ? 0 : 1
      if (query && query.includes(item.title.toLowerCase())) score += 4
      for (const term of terms) {
        if (searchable.includes(term)) score += 1
      }
      return { ...item, score }
    })
    .filter((item) => item.score > 0)
    .sort((a, b) => b.score - a.score)
    .slice(0, 4)
}

const focusSource = (source) => {
  activeSourceKey.value = source.key
  const exists = sourceHighlights.value.find((item) => item.key === source.key)
  if (!exists) {
    sourceHighlights.value = [source, ...sourceHighlights.value].slice(0, 4)
  }
  activeView.value = 'knowledge'
}

const renderMessage = (content, role = 'assistant') => {
  const normalized = role === 'assistant' ? beautifyAssistantContent(content) : String(content || '')
  return renderMarkdown(normalized)
}

const scrollToBottom = async () => {
  await nextTick()
  if (messageListRef.value) {
    messageListRef.value.scrollTop = messageListRef.value.scrollHeight
  }
}

const sendMessage = async () => {
  const message = chatInput.value.trim()
  if (!message || !selectedKnowledgeId.value) return

  const modelReady = await ensureAvailableChatModel()
  if (!modelReady) return

  let sessionId = selectedSessionId.value
  if (!sessionId) {
    sessionId = await createSession(true)
    if (!sessionId) return
  }

  activeView.value = 'assistant'
  assistantGenerating.value = true
  streamStatus.value = 'AI 正在整理回答...'

  const localUserMessage = {
    id: `local-user-${Date.now()}`,
    role: 'user',
    content: message
  }
  const localAssistantMessage = {
    id: `local-ai-${Date.now()}`,
    role: 'assistant',
    content: '### 正在整理回答\n\n请稍候，AI 正在结合知识库内容生成答案。'
  }

  messages.value = [...messages.value, localUserMessage, localAssistantMessage]
  chatInput.value = ''
  await scrollToBottom()

  try {
    const response = await fetch('/api/chat', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${getAuthToken()}`
      },
      body: JSON.stringify({
        message,
        knowledgeId: selectedKnowledgeId.value,
        knowledgeIds: [Number(selectedKnowledgeId.value)],
        sessionId
      })
    })

    if (!response.ok) {
      let errorText = '对话失败'
      try {
        const data = await response.json()
        errorText = data.error || errorText
      } catch (error) {
        errorText = await response.text()
      }
      throw new Error(errorText)
    }

    const reader = response.body?.getReader()
    const decoder = new TextDecoder('utf-8')
    let answer = ''

    if (!reader) {
      answer = await response.text()
      localAssistantMessage.content = answer
      messages.value = [...messages.value.slice(0, -1), { ...localAssistantMessage }]
      await Promise.all([loadMessages(sessionId), loadKnowledgeContext(selectedKnowledgeId.value), loadDashboard()])
      showNotice('回答已生成，并同步了参考来源')
      return
    }

    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      answer += decoder.decode(value, { stream: true })
      localAssistantMessage.content = answer
      messages.value = [...messages.value.slice(0, -1), { ...localAssistantMessage }]
      await scrollToBottom()
    }
    answer += decoder.decode()

    sourceHighlights.value = buildSourceHighlights(`${message} ${answer}`)
    if (sourceHighlights.value[0]) {
      activeSourceKey.value = sourceHighlights.value[0].key
    }

    await Promise.all([loadMessages(sessionId), loadKnowledgeContext(selectedKnowledgeId.value), loadDashboard()])
    showNotice('回答已生成，并同步了参考来源')
  } catch (error) {
    messages.value = [...messages.value.slice(0, -1), {
      ...localAssistantMessage,
      content: `### 生成失败\n\n${error.message || '当前暂时无法回答这个问题。'}`
    }]
    showNotice(error.message || '对话失败', 'error')
  } finally {
    assistantGenerating.value = false
    streamStatus.value = ''
    await scrollToBottom()
  }
}

const changeChatModel = async (modelId, silent = false) => {
  try {
    const data = await activateModel(modelId)
    modelConfig.active_chat_model_id = data.active_chat_model_id || modelId
    modelConfig.models = data.models || modelConfig.models
    if (!silent) {
      showNotice('对话模型已更新')
    }
  } catch (error) {
    showNotice(error?.response?.data?.error || '切换对话模型失败', 'error')
  }
}

const changeEmbeddingModel = async (modelId) => {
  try {
    const data = await setEmbeddingModel(modelId)
    modelConfig.active_embedding_model = data.active_embedding_model || modelId
    modelConfig.embedding_options = data.embedding_options || modelConfig.embedding_options
    showNotice('向量模型已更新')
  } catch (error) {
    showNotice(error?.response?.data?.error || '切换向量模型失败', 'error')
  }
}

const logout = async () => {
  clearAuthSession()
  await router.replace('/')
}

const updateUserInfo = async () => {
  try {
    const response = await axios.post('/api/user/update', userForm)
    showNotice('账号信息修改成功')
    Object.assign(authUser, userForm)
  } catch (error) {
    showNotice(error?.response?.data?.error || '账号信息修改失败', 'error')
  }
}

const changeTheme = async (value) => {
  try {
    const response = await axios.post('/api/user/set-theme', { theme: value })
    showNotice('主题设置成功')
  } catch (error) {
    showNotice(error?.response?.data?.error || '主题设置失败', 'error')
  }
}

const changeLanguage = async (value) => {
  try {
    const response = await axios.post('/api/user/set-language', { language: value })
    showNotice('语言切换成功')
  } catch (error) {
    showNotice(error?.response?.data?.error || '语言切换失败', 'error')
  }
}

watch(selectedKnowledgeId, async (value, oldValue) => {
  if (value === oldValue) return
  try {
    await loadKnowledgeContext(value)
  } catch (error) {
    showNotice(error?.response?.data?.error || '加载知识库失败', 'error')
  }
})

watch(selectedSessionId, async (value, oldValue) => {
  if (value === oldValue) return
  try {
    await loadMessages(value)
    await scrollToBottom()
  } catch (error) {
    showNotice(error?.response?.data?.error || '加载会话失败', 'error')
  }
})

watch(activeView, (newValue) => {
  if (newValue === 'settings') {
    activeView.value = 'dashboard'
  }
})

const loadInitialDataWithQuery = async () => {
  const queryParams = new URLSearchParams(window.location.search)
  const knowledgeId = queryParams.get('knowledgeId')
  
  if (knowledgeId) {
    selectedKnowledgeId.value = knowledgeId
  }
  
  try {
    await Promise.all([loadDashboard(), loadKnowledgeBases(), loadModels(), loadTaskConfig()])
  } catch (error) {
    showNotice(error?.response?.data?.error || '初始化数据失败', 'error')
  }
}

onMounted(loadInitialDataWithQuery)
</script>

<style scoped>
.layout-3-col {
  flex: 1;
  padding: 20px;
  display: grid;
  grid-template-columns: 280px minmax(0, 1fr) auto;
  gap: 20px;
  background: var(--bg-page);
  overflow: hidden;
}

.assistant-sidebar {
  width: 570px;
  transition: width 0.3s cubic-bezier(0.4, 0, 0.2, 1), padding 0.3s cubic-bezier(0.4, 0, 0.2, 1), opacity 0.3s cubic-bezier(0.4, 0, 0.2, 1), margin 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  overflow: hidden;
}
.assistant-sidebar.is-collapsed {
  width: 0;
  padding-left: 0;
  padding-right: 0;
  opacity: 0;
  border: none;
  margin-left: -20px;
}

.surface-panel {
  background: var(--bg-strong);
  backdrop-filter: blur(24px);
  -webkit-backdrop-filter: blur(24px);
  border: 1px solid var(--line-soft);
  border-radius: 22px;
  box-shadow: var(--shadow-card);
}

.app-sidebar,
.assistant-sidebar {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 40px);
  padding: 18px;
  gap: 18px;
}

.sidebar-top {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.brand-block {
  display: flex;
  align-items: center;
  gap: 14px;
}

.brand-mark {
  width: 44px;
  height: 44px;
  display: grid;
  place-items: center;
  border-radius: 14px;
  background: #111827;
  color: #fff;
  font-size: 14px;
  font-weight: 700;
  letter-spacing: 0.08em;
}

.brand-copy strong,
.sidebar-nav__copy strong,
.space-item strong,
.mini-metric strong,
.panel-card__header h3,
.assistant-head h2,
.hero-row h2 {
  display: block;
}

.brand-copy p,
.main-topbar__title p,
.hero-row p,
.panel-card__header p,
.assistant-head p {
  margin: 6px 0 0;
  color: var(--text-secondary);
  line-height: 1.6;
}

.sidebar-nav {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.sidebar-nav__item {
  display: flex;
  align-items: center;
  gap: 12px;
  width: 100%;
  padding: 12px;
  border-radius: 16px;
  background: transparent;
  color: var(--text-secondary);
  text-align: left;
  cursor: pointer;
  transition: background 0.2s ease, color 0.2s ease, border-color 0.2s ease;
}

.sidebar-nav__item:hover,
.space-item:hover,
.note-card:hover,
.reference-item:hover,
.prompt-card:hover,
.import-option:hover,
.text-btn:hover {
  background: var(--primary-soft);
}

.sidebar-nav__item.active {
  background: #f3f6fb;
  color: var(--text-primary);
  border: 1px solid rgba(29, 78, 216, 0.12);
}

.sidebar-nav__index {
  width: 36px;
  height: 36px;
  display: grid;
  place-items: center;
  border-radius: 12px;
  background: #f3f4f6;
  color: var(--text-muted);
  font-size: 12px;
  font-weight: 700;
}

.sidebar-nav__item.active .sidebar-nav__index {
  background: rgba(37, 99, 235, 0.1);
  color: var(--primary-strong);
}

.sidebar-nav__copy {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.sidebar-nav__copy small,
.space-item span,
.space-item small,
.mini-metric span,
.stat-card span,
.stat-card small,
.activity-item p,
.reference-item p,
.list-card p,
.trend-bar span {
  color: var(--text-muted);
}

.sidebar-section {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.sidebar-section__header,
.panel-card__header,
.main-topbar,
.hero-row,
.editor-toolbar,
.row-actions,
.settings-footer,
.composer-footer,
.panel-header,
.modal-actions,
.ideas-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.section-label {
  display: inline-flex;
  align-items: center;
  min-height: 24px;
  padding: 0 10px;
  border-radius: 999px;
  background: #eef2ff;
  color: var(--primary-strong);
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.space-list,
.topic-list,
.activity-list,
.reference-list,
.stack-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.space-item,
.reference-item,
.prompt-card,
.import-option,
.note-card {
  width: 100%;
  padding: 14px;
  border-radius: 16px;
  border: 1px solid transparent;
  background: #fafafa;
  text-align: left;
  cursor: pointer;
  transition: background 0.2s ease, border-color 0.2s ease;
}

.space-item.active {
  background: #f3f6fb;
  border-color: rgba(37, 99, 235, 0.16);
}

.space-item__title {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 6px;
}

.sidebar-metrics {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
}

.mini-metric {
  padding: 12px;
  border-radius: 16px;
  background: #f8fafc;
}

.topic-item {
  padding: 10px 12px;
  border-radius: 12px;
  background: #f8fafc;
  color: var(--text-secondary);
  font-size: 13px;
}

.sidebar-footer {
  margin-top: auto;
  margin-bottom: 20px;
  padding-top: 18px;
  border-top: 1px solid var(--line-soft);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
}

.user-profile {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 0;
}

.user-avatar {
  width: 38px;
  height: 38px;
  display: grid;
  place-items: center;
  border-radius: 14px;
  background: #e8eefc;
  color: var(--primary-strong);
  font-weight: 700;
}

.user-info {
  min-width: 0;
}

.user-info span {
  display: block;
  margin-top: 3px;
  color: var(--text-muted);
  font-size: 12px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.footer-btn {
  flex-shrink: 0;
}

.main-topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24px;
  padding: 16px 24px;
}

.main-topbar__title h1 {
  margin: 6px 0 0;
  font-size: 24px;
}

.app-container {
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.global-topbar {
  position: sticky;
  top: 0;
  z-index: 100;
  padding: 12px 24px;
  background: var(--bg-soft);
  border-bottom: 1px solid var(--line-soft);
}

.global-topbar__spaces {
  display: flex;
  align-items: center;
  gap: 12px;
  overflow-x: auto;
  padding: 0;
  scrollbar-width: thin;
  scrollbar-color: var(--primary-soft) transparent;
}

.global-topbar__spaces::-webkit-scrollbar {
  height: 4px;
}

.global-topbar__spaces::-webkit-scrollbar-track {
  background: transparent;
}

.global-topbar__spaces::-webkit-scrollbar-thumb {
  background: var(--primary-soft);
  border-radius: 2px;
}

.global-topbar__spaces::-webkit-scrollbar-thumb:hover {
  background: var(--primary-strong);
}

.global-space-item {
  white-space: nowrap;
  padding: 8px 16px;
  border-radius: 999px;
  background: transparent;
  border: 1px solid var(--line-soft);
  color: var(--text-secondary);
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.global-space-item:hover {
  background: rgba(15, 23, 42, 0.04);
}

.global-space-item.active {
  background: var(--accent);
  color: #fff;
  border-color: var(--accent);
  box-shadow: 0 4px 12px rgba(15, 23, 42, 0.1);
}

.global-space-item.create-btn {
  background: var(--primary-soft);
  border-color: var(--primary);
  color: var(--primary-strong);
  font-weight: 600;
}

.topbar-space-item.create-btn:hover {
  background: var(--primary-soft);
  border-color: var(--primary-strong);
}

.main-topbar__actions {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-shrink: 0;
}

.main-scroll {
  flex: 1;
  overflow-y: auto;
  padding-bottom: 12px;
  max-height: calc(100vh - 200px);
}

.upload-zone {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 24px;
  text-align: center;
}

.upload-buttons {
  display: flex;
  gap: 10px;
  margin-top: 12px;
}

.view-stack,
.knowledge-layout {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.hero-row {
  padding: 8px 2px;
}

.hero-row__actions {
  display: flex;
  gap: 10px;
}

.overview-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 16px;
}

.compact-grid {
  margin-top: 8px;
}

.stat-card {
  padding: 18px;
  border-radius: 20px;
  background: var(--bg-strong);
  border: 1px solid var(--line-soft);
}

.stat-card strong {
  display: block;
  margin: 8px 0 4px;
  font-size: 28px;
  line-height: 1;
}

.stat-card--mini {
  background: #f8fafc;
  border-radius: 18px;
}

.stat-card--mini strong {
  font-size: 24px;
}

.dashboard-grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
  gap: 16px;
}

.panel-card {
  padding: 20px;
}

.panel-card--wide {
  grid-column: 1 / -1;
}

.panel-card__header h3 {
  margin: 8px 0 0;
  font-size: 22px;
}

.activity-item,
.list-card {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  padding: 14px 0;
  border-bottom: 1px solid var(--line-soft);
}

.activity-item:last-child,
.list-card:last-child {
  border-bottom: none;
  padding-bottom: 0;
}

.activity-item:first-child,
.list-card:first-child {
  padding-top: 0;
}

.trend-chart {
  min-height: 220px;
  display: flex;
  align-items: flex-end;
  gap: 14px;
  padding-top: 20px;
}

.trend-bar {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  min-width: 0;
}

.trend-bar__value {
  width: 100%;
  min-height: 12px;
  border-radius: 999px 999px 12px 12px;
  background: linear-gradient(180deg, rgba(37, 99, 235, 0.82), rgba(96, 165, 250, 0.42));
}

.note-grid,
.prompt-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.note-card strong,
.reference-item strong,
.prompt-card strong {
  display: block;
  margin-bottom: 6px;
}

.notes-layout {
  display: grid;
  grid-template-columns: minmax(0, 1.2fr) minmax(320px, 0.8fr);
  gap: 16px;
}

.editor-panel,
.notes-side-panel,
.settings-panel {
  padding: 20px;
}

.editor-form,
.ideas-form {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.title-input {
  font-size: 26px;
  font-weight: 700;
}

.editor-inline-fields {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 12px;
  align-items: center;
}

.checkbox-row {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  min-height: 52px;
  padding: 0 16px;
  border-radius: 16px;
  border: 1px solid var(--line-soft);
  background: #fafafa;
  color: var(--text-secondary);
}

.markdown-editor-container {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}

.markdown-textarea,
.markdown-preview {
  min-height: 460px;
}

.markdown-textarea {
  font-family: "Consolas", "SFMono-Regular", monospace;
}

.markdown-preview {
  overflow-y: auto;
  padding: 18px;
  border-radius: 18px;
  border: 1px solid var(--line-soft);
  background: #fbfbfc;
}

.editor-hint {
  color: var(--text-muted);
  font-size: 13px;
}

.upload-zone {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  width: 100%;
  padding: 28px 20px;
  border: 1px dashed rgba(37, 99, 235, 0.24);
  background: #f8fbff;
  cursor: pointer;
}

.row-actions {
  flex-wrap: wrap;
}

.ideas-panel,
.graph-panel {
  padding: 28px;
}

.quick-idea-input {
  min-height: 220px;
}

.graph-placeholder {
  position: relative;
  height: 320px;
  margin-top: 18px;
  border-radius: 20px;
  border: 1px dashed var(--line-strong);
  background:
    radial-gradient(circle at 35% 30%, rgba(37, 99, 235, 0.12), transparent 18%),
    radial-gradient(circle at 65% 60%, rgba(99, 102, 241, 0.12), transparent 16%),
    #fafafa;
}

.graph-node {
  position: absolute;
  width: 72px;
  height: 72px;
  border-radius: 50%;
  background: rgba(37, 99, 235, 0.14);
  border: 1px solid rgba(37, 99, 235, 0.18);
  top: 26%;
  left: 28%;
}

.graph-node--secondary {
  width: 54px;
  height: 54px;
  top: 54%;
  left: 58%;
}

.graph-node--small {
  width: 34px;
  height: 34px;
  top: 38%;
  left: 72%;
}

.settings-stack {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.setting-item {
  display: flex;
  flex-direction: column;
}

.assistant-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.assistant-head h2 {
  margin: 8px 0 0;
  font-size: 26px;
}

.assistant-context {
  display: flex;
  justify-content: flex-start;
}

.session-selector {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 10px;
}

.compact-select {
  min-height: 44px;
}

.message-list {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 14px;
  min-height: 0;
  overflow-y: auto;
}

.message-card {
  max-width: 100%;
  padding: 14px 16px;
  border-radius: 18px;
  border: 1px solid var(--line-soft);
  background: #fafafa;
}

.message-card.user {
  align-self: flex-end;
  max-width: 88%;
  background: #eef4ff;
  border-color: rgba(37, 99, 235, 0.16);
}

.message-card.assistant {
  align-self: stretch;
  background: #fff;
}

.message-card__meta {
  margin-bottom: 8px;
  color: var(--text-muted);
  font-size: 12px;
}

.assistant-empty {
  min-height: 160px;
  background: #fafafa;
  border-radius: 18px;
  border: 1px dashed var(--line-soft);
}

.assistant-trace {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.assistant-trace__header {
  padding: 0;
}

.source-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.source-chip {
  min-height: 34px;
  padding: 0 14px;
  border-radius: 999px;
  border: 1px solid var(--line-soft);
  background: #fafafa;
  color: var(--text-secondary);
  cursor: pointer;
}

.assistant-composer {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding-top: 8px;
  border-top: 1px solid var(--line-soft);
}

.composer-textarea {
  min-height: 120px;
}

.composer-input-wrapper {
  position: relative;
}

.composer-actions {
  position: absolute;
  top: 10px;
  right: 10px;
  display: flex;
  gap: 10px;
}

.composer-textarea {
  min-height: 120px;
  padding: 12px;
}

.composer-footer {
  align-items: center;
}

.stream-status {
  color: var(--text-muted);
  font-size: 12px;
}

.text-btn,
.icon-btn,
.modal-close {
  border: none;
  background: transparent;
  color: var(--text-secondary);
  cursor: pointer;
}

.text-btn {
  padding: 8px 10px;
  border-radius: 12px;
}

.icon-btn.subtle {
  min-height: 34px;
  padding: 0 12px;
  border-radius: 999px;
  background: #f3f4f6;
}

.visually-hidden {
  display: none;
}

.overlay-shell {
  position: fixed;
  inset: 0;
  display: grid;
  place-items: center;
  padding: 20px;
  background: rgba(15, 23, 42, 0.22);
  z-index: 100;
}

.modal-card {
  width: min(560px, 100%);
  padding: 24px;
}

.small-modal {
  width: min(520px, 100%);
}

.modal-grid,
.import-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}

.modal-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.import-option.active {
  background: #eef4ff;
  border-color: rgba(37, 99, 235, 0.18);
}

.empty-text {
  padding: 16px;
  color: var(--text-muted);
  text-align: center;
  font-size: 14px;
}

@media (max-width: 1440px) {
  .layout-3-col {
    grid-template-columns: 250px minmax(0, 1fr) 510px;
  }

  .main-topbar {
    flex-wrap: wrap;
    align-items: flex-start;
  }

  .main-topbar__search {
    order: 3;
    width: 100%;
  }
}

@media (max-width: 1180px) {
  .layout-3-col {
    grid-template-columns: 240px minmax(0, 1fr);
  }

  .assistant-sidebar {
    grid-column: 1 / -1;
    min-height: auto;
  }

  .notes-layout,
  .overview-grid,
  .dashboard-grid,
  .note-grid,
  .prompt-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 840px) {
  .layout-3-col {
    grid-template-columns: 1fr;
    padding: 12px;
  }

  .app-sidebar,
  .assistant-sidebar {
    min-height: auto;
  }

  .sidebar-metrics,
  .modal-grid,
  .import-grid,
  .markdown-editor-container,
  .editor-inline-fields,
  .session-selector {
    grid-template-columns: 1fr;
  }

  .hero-row,
  .main-topbar,
  .sidebar-footer,
  .ideas-actions,
  .composer-footer {
    flex-direction: column;
    align-items: stretch;
  }
}

.large-modal {
  width: min(720px, 100%);
}

.upload-actions {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.field-select {
  width: 100%;
  padding: 10px 14px;
  border: 1px solid var(--line-soft);
  border-radius: 12px;
  font-size: 14px;
  background: white;
  color: var(--text-primary);
}

.field-select:focus {
  outline: none;
  border-color: rgba(37, 99, 235, 0.4);
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.08);
}

.workspace-shell {
  position: relative;
  z-index: 1;
}

.app-main {
  position: relative;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 16px;
  height: 100%;
}

/* ANote Agent 子菜单样式 */
.sidebar-nav__item-wrapper {
  position: relative;
  display: flex;
  flex-direction: column;
}

.sidebar-nav__item.has-submenu {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.submenu-toggle {
  display: flex;
  align-items: center;
  transition: transform 0.3s ease;
}

.submenu-toggle svg {
  transition: transform 0.3s ease;
}

.submenu-toggle svg.rotated {
  transform: rotate(90deg);
}

.agent-submenu {
  overflow: hidden;
  max-height: 0;
  transition: max-height 0.3s ease;
}

.agent-submenu.is-open {
  max-height: 300px;
}

.submenu-content {
  display: flex;
  flex-direction: column;
  padding: 4px 0;
}

.submenu-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
  width: 100%;
  padding: 12px 16px;
  padding-left: 48px;
  text-align: left;
  border: none;
  background: transparent;
  cursor: pointer;
  transition: background 0.2s ease;
  color: var(--text-muted);
}

.submenu-item:hover {
  background: var(--bg-muted);
}

.submenu-item.active {
  color: var(--text-primary);
  background: var(--primary-bg-soft);
}

.submenu-item strong {
  font-size: 14px;
  font-weight: 600;
  display: block;
}

.submenu-item small {
  font-size: 12px;
  opacity: 0.7;
  display: block;
}
</style>
