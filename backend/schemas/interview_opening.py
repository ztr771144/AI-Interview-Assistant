from pydantic import BaseModel, Field

# 1. 首问输出模型
class InterviewOpening(BaseModel):
    opening_question: str = Field(description="面试首问，必须引用简历/JD中的具体信息")
    followup_directions: list[str] = Field(
        min_length=3, 
        max_length=5, 
        description="3到5个追问方向，不重复、不脱离材料"
    )

# 2. 对话请求模型
class ChatRequest(BaseModel):
    history: list[dict] = Field(description="历史对话记录")
    current_answer: str = Field(description="用户刚刚输入的最新回答")

# 3. 对话响应模型
class ChatResponse(BaseModel):
    reply: str = Field(description="AI 面试官的追问内容")

# 4. 评分维度模型（刚才缺失的就是这个）
class DimensionScore(BaseModel):
    dimension: str = Field(description="评分维度名称，如：相关性、结构性、具体性、岗位匹配")
    score: int = Field(description="该维度得分，1-10分")
    evidence: list[str] = Field(description="引用候选人原话作为打分证据")

# 5. 评估报告模型（包含了交叉复核）
class InterviewEvaluation(BaseModel):
    dimensions: list[DimensionScore] = Field(description="4个维度的评分详情")
    strengths: list[str] = Field(description="做得好的2-3个亮点")
    weaknesses: list[str] = Field(description="最影响得分的2-3个短板")
    suggestions: list[str] = Field(description="下一场可直接执行的改进建议")
    cross_review: str = Field(description="交叉复核意见：由另一个 AI 复核首评后的偏差说明和最终结论")