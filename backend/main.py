from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.api.interview import api_router
from backend.api.interview import api_router as interview_router
from backend.api.resume import api_router as resume_router
from backend.api.jd import api_router as jd_router

app = FastAPI(
    title="AI 模拟面试助手 API",
    description="🎯 面向高校学生的 AI 求职练习助手后端。",
    version="0.1.0"
)

# 👇 新增：配置允许跨域请求（开发阶段允许所有）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境请改为具体的前端域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/interview", tags=["模拟面试"])

@app.get("/health", tags=["系统管理"], summary="服务健康检查")
def health_check():
    return {"status": "ok"}

app.include_router(interview_router, prefix="/api/interview", tags=["模拟面试"])
app.include_router(resume_router, prefix="/api/resume", tags=["简历诊断"])
app.include_router(jd_router, prefix="/api/jd", tags=["JD匹配"])