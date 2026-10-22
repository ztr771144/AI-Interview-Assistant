import json
from fastapi import APIRouter, HTTPException, File, UploadFile
from pydantic import BaseModel, Field

# 导入模型路由器、Schemas 和 PDF 解析器
from backend.services.model_router import router
from backend.schemas.interview_opening import (
    InterviewOpening, 
    ChatRequest, 
    ChatResponse, 
    InterviewEvaluation
)
from backend.services.parser.pdf_parser import extract_text_from_pdf

api_router = APIRouter()

# ================= 1. PDF 简历上传解析 =================
@api_router.post("/upload-resume", summary="上传并解析 PDF 简历")
async def upload_resume(file: UploadFile = File(...)):
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="目前仅支持 PDF 格式的简历")
        
    try:
        contents = await file.read()
        text = extract_text_from_pdf(contents)
        return {"text": text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ================= 2. 生成面试首问 =================
class OpeningRequest(BaseModel):
    resume_text: str = Field(..., description="求职者的简历纯文本内容")
    jd_text: str = Field(..., description="目标岗位的 JD（职位描述）文本")

@api_router.post("/opening", response_model=InterviewOpening, summary="生成面试首问")
async def generate_opening(request: OpeningRequest):
    system_prompt = (
        "你是一个专业的技术面试官。请根据提供的简历和岗位 JD，生成一个面试首问，以及 3 个追问方向。\n"
        "⚠️ 严格要求：followup_directions 数组必须且只能包含 3 个元素！绝对不能多也不能少！\n"
        "必须输出合法的 JSON 格式，不要包含 markdown 标记或多余文本。\n"
        "JSON 结构要求: {\"opening_question\": \"...\", \"followup_directions\": [\"...\", \"...\", \"...\"]}"
    )
    user_prompt = f"简历：\n{request.resume_text}\n\n岗位JD：\n{request.jd_text}\n\n请输出 JSON："
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
    try:
        response = router.chat("interview_agent", messages=messages, response_format={"type": "json_object"})
        return InterviewOpening.model_validate_json(response.choices[0].message.content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ================= 3. 多轮对话追问 =================
@api_router.post("/chat", response_model=ChatResponse, summary="面试官追问")
async def chat_with_interviewer(request: ChatRequest):
    system_prompt = (
        "你是一个专业、略带压力的技术面试官。\n"
        "你的任务是根据候选人的回答进行追问。\n"
        "【追问规则】\n"
        "1. 如果候选人回答含糊、没有数据或细节，请追问具体做法和数据。\n"
        "2. 如果候选人提到技术名词，请深挖底层原理（比如为什么用A不用B）。\n"
        "3. 如果回答很完整，请切换到简历或JD中的下一个能力点进行考察。\n"
        "4. ⚠️ 每次只能问一个问题！绝对不要一次问多个问题！\n"
        "5. 必须结合上下文，不要凭空提问。用口语化、专业的面试语气说话。"
    )

    messages = [{"role": "system", "content": system_prompt}]
    
    # 放入历史对话
    for msg in request.history:
        messages.append({"role": msg["role"], "content": msg["content"]})
        
    # 放入用户刚刚的回答
    messages.append({"role": "user", "content": request.current_answer})

    try:
        response = router.chat("interview_agent", messages=messages)
        reply = response.choices[0].message.content
        return ChatResponse(reply=reply)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ================= 4. 评估报告（含交叉复核） =================
@api_router.post("/report", response_model=InterviewEvaluation, summary="生成面试评估报告")
async def generate_report(request: ChatRequest):
    history_text = "\n".join([f"{msg['role']}: {msg['content']}" for msg in request.history])

    # 第一步：生成首评
    system_prompt = (
        "你是一个专业的面试评估专家。请根据对话记录，对候选人的表现进行打分。\n"
        "【强制要求】每个维度的打分，必须先在 evidence 数组中引用候选人的原话作为证据，再给分！如果证据不足2条，该维度得分不得高于6分！\n"
        "严格输出 JSON，结构: {\"dimensions\": [{\"dimension\": \"相关性\", \"score\": 8, \"evidence\": [\"原话1\"]}], \"strengths\": [\"...\"], \"weaknesses\": [\"...\"], \"suggestions\": [\"...\"]}"
    )
    user_prompt = f"对话记录：\n{history_text}\n\n请输出评估 JSON："

    try:
        response = router.chat(
            route_name="interview_agent", 
            messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
            response_format={"type": "json_object"} 
        )
        first_eval_text = response.choices[0].message.content
        
        # 第二步：交叉复核
        cross_system_prompt = (
            "你是一个严苛的面试复核专家。请审阅以下另一名面试官给出的评分和对话记录。\n"
            "指出其中是否有关联不紧密、主观偏见、或证据不足的问题。用 1-2 句话给出复核结论。\n"
            "严格输出 JSON，结构: {\"cross_review\": \"复核结论说明\"}"
        )
        cross_user_prompt = f"对话记录：\n{history_text}\n\n首评报告：\n{first_eval_text}\n\n请输出 JSON："

        cross_response = router.chat(
            route_name="cross_review",
            messages=[{"role": "system", "content": cross_system_prompt}, {"role": "user", "content": cross_user_prompt}],
            response_format={"type": "json_object"}
        )
        
        cross_data = json.loads(cross_response.choices[0].message.content)
        
        # 合并结果
        eval_dict = json.loads(first_eval_text)
        eval_dict["cross_review"] = cross_data.get("cross_review", "复核完成，无重大偏差。")
        
        return InterviewEvaluation.model_validate(eval_dict)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))