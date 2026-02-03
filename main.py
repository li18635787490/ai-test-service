"""
AI 文档检测与报告服务
主入口文件
"""
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.config import get_settings
from app.routers import documents, check, reports, requirements

# 创建应用
app = FastAPI(
    title="AI 文档检测服务",
    description="""
## 功能介绍

由 AI 驱动的智能文档检测与报告生成服务。

### 核心能力

- 📄 **多格式支持**: PDF, Word, Excel, PPT, TXT, Markdown
- 🤖 **多 AI 提供商**: OpenAI GPT, Anthropic Claude, 通义千问
- 🔍 **多维度检测**: 格式规范、内容质量、逻辑一致性、敏感信息、合规性
- 📊 **丰富报告**: HTML / Markdown / JSON 多种格式
- 📋 **需求分析**: 需求完整性、场景覆盖、描述质量检测
- 🧪 **测试用例生成**: 根据需求自动生成功能测试用例

### 使用流程

1. 上传文档 → `POST /api/v1/documents/upload`
2. 启动检测 → `POST /api/v1/check/start`
3. 查询状态 → `GET /api/v1/check/{task_id}`
4. 获取报告 → `GET /api/v1/reports/{task_id}/html`

### 需求分析流程

1. 上传需求文档 → `POST /api/v1/documents/upload`
2. 分析需求 → `POST /api/v1/requirements/analyze`
3. 生成测试用例 → `POST /api/v1/requirements/generate-testcases`
    """,
    version="1.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(documents.router, prefix="/api/v1")
app.include_router(check.router, prefix="/api/v1")
app.include_router(reports.router, prefix="/api/v1")
app.include_router(requirements.router, prefix="/api/v1")

# 静态文件服务
static_dir = Path(__file__).parent / "app" / "static"
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


@app.get("/", tags=["根"])
async def root():
    """返回 Web UI 首页"""
    return FileResponse(str(static_dir / "index.html"))


@app.get("/api", tags=["API信息"])
async def api_info():
    """API 信息"""
    return {
        "service": "AI 文档检测服务",
        "version": "1.0.0",
        "docs": "/docs",
        "status": "running"
    }


@app.get("/health", tags=["健康检查"])
async def health_check():
    """健康检查"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    settings = get_settings()
    uvicorn.run(
        "main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.debug
    )
