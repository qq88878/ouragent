import asyncio
from src.core.llm import create_llm_provider
from src.core.agents.planner_agent import PlannerAgent

async def test():
    llm = create_llm_provider()
    agent = PlannerAgent(llm)
    result = await agent.generate_path(
        student_profile={"learning_style": "VISUAL", "grade_level": "BEGINNER"},
        course_title="数据库系统概论",
        course_description="基于王珊、萨师煊《数据库系统概论（第5版）》，涵盖关系模型、SQL、数据库设计、规范化理论",
        course_knowledge=[],
        goal="系统掌握数据库核心理论与应用",
    )
    print("Title:", result.get("title"))
    print("Steps:", len(result.get("steps", [])))
    for s in result.get("steps", [])[:8]:
        print(f"  - {s.get('title')}")

asyncio.run(test())
