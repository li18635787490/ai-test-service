# AI 文档检测与报告服务

由外部 AI 驱动的智能文档检测与报告生成系统。

## ✨ 功能特性

- 📄 **多格式文档支持**: PDF, Word (.docx), Excel (.xlsx), PPT (.pptx), TXT, Markdown
- 🤖 **多 AI 提供商**: OpenAI GPT-4, Anthropic Claude, 阿里通义千问
- 🔍 **多维度检测**:
  - 格式规范检测
  - 内容质量检测
  - 逻辑一致性检测
  - 敏感信息检测
  - 合规性检测
- 📊 **多格式报告**: HTML (可视化) / Markdown / JSON

## 🚀 快速开始

### 1. 安装依赖

```bash
# 创建虚拟环境（推荐）
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
# 复制配置文件
copy .env.example .env

# 编辑 .env 文件，填入你的 AI API Key
# OPENAI_API_KEY=sk-your-key
# 或
# ANTHROPIC_API_KEY=sk-your-key
# 或
# QWEN_API_KEY=sk-your-key
```

### 3. 启动服务

```bash
python main.py

# 或使用 uvicorn
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 4. 访问 API 文档

打开浏览器访问: http://localhost:8000/docs

## 📖 API 使用示例

### 上传文档

```bash
curl -X POST "http://localhost:8000/api/v1/documents/upload" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@your-document.pdf"
```

响应:
```json
{
  "id": "abc123...",
  "filename": "your-document.pdf",
  "file_type": "pdf",
  "file_size": 102400,
  "upload_time": "2024-01-01T10:00:00"
}
```

### 启动检测

```bash
curl -X POST "http://localhost:8000/api/v1/check/start" \
  -H "Content-Type: application/json" \
  -d '{
    "document_id": "abc123...",
    "dimensions": ["format", "content", "logic"],
    "ai_provider": "openai"
  }'
```

响应:
```json
{
  "task_id": "task-xyz...",
  "message": "检测任务已创建，正在处理中"
}
```

### 查询状态

```bash
curl "http://localhost:8000/api/v1/check/task-xyz..."
```

### 获取 HTML 报告

```bash
curl "http://localhost:8000/api/v1/reports/task-xyz.../html"
```

## 📁 项目结构

```
ai-test-service/
├── app/
│   ├── __init__.py
│   ├── config.py              # 配置管理
│   ├── models.py              # 数据模型
│   ├── routers/
│   │   ├── documents.py       # 文档上传接口
│   │   ├── check.py           # 检测任务接口
│   │   └── reports.py         # 报告获取接口
│   ├── services/
│   │   ├── ai_providers.py    # AI 提供商适配层
│   │   ├── document_parser.py # 文档解析服务
│   │   ├── check_service.py   # 检测核心服务
│   │   └── report_generator.py# 报告生成服务
│   └── templates/
│       └── report.html        # HTML 报告模板
├── main.py                    # 应用入口
├── requirements.txt           # Python 依赖
├── .env.example              # 环境变量示例
└── README.md
```

## 🔧 配置说明

| 环境变量 | 说明 | 默认值 |
|---------|------|-------|
| `DEFAULT_AI_PROVIDER` | 默认 AI 提供商 | openai |
| `OPENAI_API_KEY` | OpenAI API Key | - |
| `OPENAI_MODEL` | OpenAI 模型 | gpt-4-turbo-preview |
| `ANTHROPIC_API_KEY` | Claude API Key | - |
| `QWEN_API_KEY` | 通义千问 API Key | - |
| `APP_PORT` | 服务端口 | 8000 |

## 🎯 检测维度说明

系统默认使用**智能检测模式**，自动检测所有维度。如需自定义，可切换到"自定义维度"模式。

| 维度 | 标识 | 检测内容 |
|-----|------|---------|
| 格式规范 | `format` | 标题层级、段落结构、标点符号、编号格式 |
| 内容质量 | `content` | 语法错误、表述清晰度、专业术语、错别字 |
| 逻辑一致性 | `logic` | 前后矛盾、数据一致性、论证合理性 |
| 敏感信息 | `sensitive` | 个人信息、财务信息、机密泄露风险 |
| 合规检查 | `compliance` | 行业规范、法律法规、引用规范 |

## 📋 需求分析功能

从**业务视角**对需求文档进行深度分析，重点关注：
- 业务流程完整性（用户旅程、业务闭环）
- 业务规则清晰度（计算逻辑、状态流转）
- 异常场景覆盖（业务异常、操作冲突）
- 用户体验考量（操作反馈、错误引导）
- 运营支撑能力（数据统计、人工干预）

## 🧪 测试用例生成

根据需求文档自动生成测试用例，包括：
- 正向测试用例（主流程）
- 反向测试用例（异常场景）
- 边界测试用例（极限值）
- 异常测试用例（系统错误）

## 📝 License

MIT
