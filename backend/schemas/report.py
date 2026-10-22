from pydantic import BaseModel, Field

# --- 模块 A：简历诊断 ---
class DiagnosisItem(BaseModel):
    category: str = Field(description="检查项，如：量化表达、动词弱化、结构问题等")
    priority: str = Field(description="优先级，高/中/低")
    original_text: str = Field(description="简历中的原句")
    rewritten_text: str = Field(description="优化后的改写示例")
    suggestion: str = Field(description="具体的修改建议")

class ResumeDiagnosis(BaseModel):
    issues: list[DiagnosisItem] = Field(description="按优先级排序的问题清单")

# --- 模块 B：JD 匹配 ---
class JDMatchResult(BaseModel):
    match_score: int = Field(description="匹配度评分，0-100分")
    covered_skills: list[str] = Field(description="已覆盖的能力项")
    gap_skills: list[str] = Field(description="缺失的能力项或差距")
    improvement_plan: list[str] = Field(description="针对差距的补齐建议")