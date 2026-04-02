# 企业知识库RAG系统 - Vue版本

## 项目介绍

这是基于Vue 3重构的企业知识库RAG系统前端，采用Vite作为构建工具，提供现代化的开发体验和优秀的性能。

## 技术栈

- **Vue 3**: 渐进式JavaScript框架
- **Vue Router**: 路由管理
- **Vite**: 下一代前端构建工具
- **Axios**: HTTP客户端
- **ECharts**: 数据可视化

## 项目结构

```
vue-frontend/
├── src/
│   ├── views/          # 页面组件
│   │   ├── Login.vue   # 登录页面
│   │   └── Main.vue    # 主页面
│   ├── router/         # 路由配置
│   │   └── index.js
│   ├── App.vue         # 根组件
│   ├── main.js         # 入口文件
│   └── style.css       # 全局样式
├── index.html          # HTML模板
├── vite.config.js      # Vite配置
└── package.json        # 项目依赖
```

## 安装与运行

### 1. 安装依赖

```bash
cd vue-frontend
npm install
```

### 2. 开发模式

```bash
npm run dev
```

项目将在 `http://localhost:3000` 启动开发服务器。

### 3. 生产构建

```bash
npm run build
```

构建产物将输出到 `dist` 目录。

### 4. 预览生产构建

```bash
npm run preview
```

## 功能特性

### 1. 登录功能
- 用户名/密码验证
- 登录状态保存
- 错误提示

### 2. 知识库管理
- 文档上传（支持多文件）
- 知识库清除
- 上传状态提示

### 3. 智能对话
- 会话管理
- 流式响应
- 上下文保持
- 消息滚动

### 4. 响应式设计
- 侧边栏折叠/展开
- 移动端适配

## API代理

开发环境下，所有 `/api` 开头的请求都会被代理到后端服务 `http://127.0.0.1:8080`，配置在 `vite.config.js` 中。

## 注意事项

1. 确保后端服务已启动并运行在 `http://127.0.0.1:8080`
2. 登录默认账号：admin / 123456
3. 首次运行需要安装依赖

## 开发建议

1. 使用Vue 3的Composition API编写组件
2. 遵循ESLint规范（如果配置）
3. 使用Vue DevTools调试
4. 合理使用组件拆分和复用

## 后续优化

- 添加状态管理（Pinia）
- 引入TypeScript
- 添加单元测试
- 优化样式系统（使用CSS预处理器）
- 实现国际化
- 添加权限控制