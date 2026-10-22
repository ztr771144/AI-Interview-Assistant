from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from backend.services.model_router import router
from backend.schemas.report import JDMatchResult

api_router = APIRouter()

class JDRequest(BaseModel):
    resume_text: str
    jd_text: str

@api_router.post("/match", response_model=JDMatchResult, summary="JD 匹配分析")
async def match_jd(request: JDRequest):
    system_prompt = (
        "你是一个专业的职业规划师。请对比候选人的简历和目标岗位 JD。\n"
        "第一步：从 JD 中提取核心能力项。\n"
        "第二步：对照简历，计算 0-100 的匹配度。\n"
        "第三步：列出已覆盖的技能、缺失的差距，并给出具体的补齐建议。\n"
        "必须输出合法的 JSON，结构如下：\n"
        "{\"match_score\": 75, \"covered_skills\": [\"Python\"], \"gap_skills\": [\"Redis\"], \"improvement_plan\": [\"建议补充...\"]}"
    )
    user_prompt = f"简历：\n{request.resume_text}\n\n目标岗位JD：\n{request.jd_text}\n\n请输出 JSON："

    try:
        response = router.chat(
            "interview_agent", 
            messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
            response_format={"type": "json_object"}
        )
        return JDMatchResult.model_validate_json(response.choices[0].message.content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))