# 贡献指南

感谢您对自助查询工具项目的关注！我们欢迎各种形式的贡献，包括但不限于报告问题、提交功能建议、改进文档、提交代码修复和添加新功能。

## 如何贡献

### 报告问题

1. 在提交问题之前，请先搜索是否已经存在类似的问题
2. 使用清晰、具体的标题描述问题
3. 详细描述问题的复现步骤
4. 提供相关的错误信息或日志
5. 如果可能，提供截图或录屏

### 提交功能建议

1. 清晰描述您想要的功能
2. 解释这个功能如何帮助用户
3. 提供可能的实现方案
4. 如果有类似功能的参考，请提供链接

### 改进文档

1. 修正文档中的错误
2. 改进文档的清晰度和可读性
3. 添加缺失的信息
4. 更新过时的内容

### 提交代码

1. Fork 项目仓库
2. 创建新的分支：`git checkout -b feature/your-feature-name`
3. 提交您的修改：`git commit -m 'Add some feature'`
4. 推送到分支：`git push origin feature/your-feature-name`
5. 提交 Pull Request

### 代码规范

1. 遵循项目的代码风格
2. 添加必要的注释
3. 确保代码通过所有测试
4. 更新相关文档

## 开发环境设置

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

## 提交规范

### 提交信息格式

```
<类型>: <描述>

[可选的详细描述]

[可选的关闭问题引用]
```

### 类型

- feat: 新功能
- fix: 修复问题
- docs: 文档修改
- style: 代码格式修改
- refactor: 代码重构
- test: 测试用例修改
- chore: 其他修改

### 示例

```
feat: 添加用户登录功能

- 实现用户名密码登录
- 添加登录状态管理
- 添加登录页面样式

Closes #123
```

## 行为准则

请查看我们的[行为准则](CODE_OF_CONDUCT.md)，以了解我们的社区准则。

## 许可证

通过提交代码，您同意您的贡献将根据项目的 MIT 许可证进行许可。 