from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from backend.services.model_router import router
from backend.schemas.report import ResumeDiagnosis

api_router = APIRouter()

class ResumeRequest(BaseModel):
    resume_text: str

@api_router.post("/diagnose", response_model=ResumeDiagnosis, summary="简历诊断")
async def diagnose_resume(request: ResumeRequest):
    system_prompt = (
        "你是一个资深的 HR 和简历修改专家。请对以下简历进行诊断。\n"
        "【检查清单】\n"
        "1. 量化表达：成果是否有数字支撑？\n"
        "2. 动词弱化：是否大量使用参与/负责/协助等弱动词？\n"
        "3. 关键词对齐：是否命中求职意向的关键词？\n"
        "4. 结构问题：板块完整性、时间线、段落组织。\n"
        "5. 错别字与格式。\n"
        "必须输出合法的 JSON，结构如下：\n"
        "{\"issues\": [{\"category\": \"检查项\", \"priority\": \"高/中/低\", \"original_text\": \"原句\", \"rewritten_text\": \"改写\", \"suggestion\": \"建议\"}]}"
    )
    user_prompt = f"简历内容：\n{request.resume_text}\n\n请输出 JSON 诊断报告："

    try:
        response = router.chat(
            "interview_agent", # 暂时复用
            messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
            response_format={"type": "json_object"}
        )
        return ResumeDiagnosis.model_validate_json(response.choices[0].message.content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))