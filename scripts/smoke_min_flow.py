import sys
import os

# 将项目根目录加入系统路径，确保能 import backend 包
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.services.model_router import router
from backend.schemas.interview_opening import InterviewOpening

def main():
    print("⏳ 正在读取素材...")
    try:
        with open("data/resume1.txt", "r", encoding="utf-8") as f:
            resume = f.read()
        with open("data/jd1.txt", "r", encoding="utf-8") as f:
            jd = f.read()
    except FileNotFoundError as e:
        print(f"❌ 找不到素材文件，请检查路径: {e}")
        return

    # 构造 Prompt
    system_prompt = (
       "你是一个专业的技术面试官。请根据提供的简历和岗位 JD，生成一个面试首问，以及 3 个追问方向。\n"
        "⚠️ 严格要求：followup_directions 数组必须且只能包含 3 个元素！绝对不能多也不能少！\n"
        "必须输出合法的 JSON 格式，不要包含 markdown 标记或多余文本。\n"
        "JSON 结构要求: {\"opening_question\": \"...\", \"followup_directions\": [\"...\", \"...\", \"...\"]}"
    )
    user_prompt = f"简历：\n{resume}\n\n岗位JD：\n{jd}\n\n请输出 JSON："

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]

    print("🚀 正在请求模型生成面试首问...")
    try:
        # 调用路由器，并强制 JSON 格式
        response = router.chat(
            route_name="interview_agent", 
            messages=messages,
            response_format={"type": "json_object"} 
        )
        
        raw_content = response.choices[0].message.content
        print("\n--- 模型原始返回 ---")
        print(raw_content)
        
        print("\n🔍 正在用 Pydantic 校验...")
        # 使用 Pydantic 解析并校验 JSON
        opening = InterviewOpening.model_validate_json(raw_content)
        
        print("\n✅ 校验成功！")
        print(f"【首问】 {opening.opening_question}")
        print("【3个追问方向】")
        for i, direction in enumerate(opening.followup_directions, 1):
            print(f"  {i}. {direction}")
            
    except Exception as e:
        print(f"\n❌ 失败，错误信息：{e}")

if __name__ == "__main__":
    main()