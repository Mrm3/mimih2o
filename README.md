# 自助查询工具

一个基于Python FastAPI和React的商户查询系统，支持按机构号和商户号查询，并提供数据导出功能。

## 功能特点

- 支持按机构号和商户号查询
- 支持数据导出为Excel
- 支持管理员上传数据
- 响应式设计，支持移动端访问
- 美观的用户界面

## 技术栈

- 后端：Python FastAPI
- 前端：React + TypeScript + Ant Design
- 数据库：SQLite
- 部署：Nginx + Gunicorn

## 快速开始

### 环境要求

- Python 3.8+
- Node.js 16+
- npm 8+

### 安装步骤

1. 克隆项目
```bash
git clone https://github.com/yourusername/mimih2o.git
cd mimih2o
```

2. 安装后端依赖
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows使用: venv\Scripts\activate
pip install -r requirements.txt
```

3. 安装前端依赖
```bash
cd ../frontend
npm install
```

4. 启动开发服务器

后端：
```bash
cd backend
uvicorn main:app --reload
```

前端：
```bash
cd frontend
npm start
```

访问 http://localhost:3000 即可看到应用界面。

## 部署

### 使用部署脚本

我们提供了一个便捷的部署脚本，可以快速在服务器上部署应用：

```bash
# 给脚本添加执行权限
chmod +x deploy.sh

# 运行部署脚本
sudo ./deploy.sh
```

部署脚本会自动：
1. 安装所需依赖
2. 配置Nginx
3. 设置系统服务
4. 启动应用

### 手动部署

1. 构建前端
```bash
cd frontend
npm run build
```

2. 配置Nginx
```bash
sudo nano /etc/nginx/sites-available/mimih2o
```

添加以下配置：
```nginx
server {
    listen 80;
    server_name minih2o.top;

    location / {
        root /var/www/mimih2o/frontend/build;
        try_files $uri $uri/ /index.html;
    }

    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

3. 启用站点配置
```bash
sudo ln -s /etc/nginx/sites-available/mimih2o /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

4. 启动后端服务
```bash
cd backend
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
```

## 项目结构

```
mimih2o/
├── backend/
│   ├── main.py
│   ├── requirements.txt
│   └── database.db
├── frontend/
│   ├── src/
│   ├── public/
│   └── package.json
└── README.md
```

## 贡献指南

我们欢迎各种形式的贡献，包括但不限于：

- 报告问题
- 提交功能建议
- 改进文档
- 提交代码修复
- 添加新功能

请查看我们的[贡献指南](CONTRIBUTING.md)了解更多信息。

## 行为准则

请查看我们的[行为准则](CODE_OF_CONDUCT.md)，以了解我们的社区准则。

## 版本历史

### v0.2.9 (2024-04-27)
- 在页面左上角显示数据日期
- 固定数据日期显示为"4月27日"
- 优化数据日期显示样式

### v0.2.8 (2024-04-27)
- 修改数据日期显示格式为"4月27日"
- 在后端添加data_date字段
- 设置固定数据日期值

### v0.2.7 (2024-04-27)
- 将系统名称统一修改为"自助查询工具"
- 更新所有相关文件中的系统名称
- 优化页面标题显示

### v0.2.6 (2024-04-27)
- 移除页面顶部的"自助查询工具"标题
- 优化页面布局和间距
- 改进移动端显示效果

### v0.2.5 (2024-04-27)
- 修复文件上传功能
- 优化后端文件处理逻辑
- 添加文件类型验证
- 改进错误处理机制

### v0.2.4 (2024-04-27)
- 优化数据日期显示位置
- 将数据日期移至页面顶部
- 改进日期显示样式
- 优化移动端适配

### v0.2.3 (2024-04-27)
- 优化移动端显示效果
- 改进表格响应式布局
- 调整按钮和输入框大小
- 优化页面间距

### v0.2.2 (2024-04-27)
- 优化页面布局
- 改进移动端适配
- 调整组件间距
- 优化表格显示效果

### v0.2.1 (2024-04-27)
- 优化页面布局
- 改进移动端适配
- 调整组件间距
- 优化表格显示效果

### v0.2.0 (2024-04-27)
- 优化页面布局
- 改进移动端适配
- 调整组件间距
- 优化表格显示效果

### v0.1.0 (2024-04-27)
- 初始版本发布
- 实现基本的查询功能
- 支持数据导出
- 添加管理员登录功能

## 许可证

MIT License