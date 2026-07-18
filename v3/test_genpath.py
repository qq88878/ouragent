import asyncio
from src.core.llm import create_llm_provider
from src.core.agents.planner_agent import PlannerAgent
from src.core.utils import parse_llm_json

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
    print("Has steps:", "steps" in result)
    print("Has phases:", "phases" in result)
    print("Has error:", "error" in result)
    if "error" in result:
        print("Error:", result["error"])
    if "raw_response" in result:
        print("Raw:", result["raw_response"][:500])
    if "phases" in result:
        for p in result.get("phases", []):
            print("Phase:", p.get("phase_name"), "steps:", len(p.get("steps", [])))
    print("All keys:", list(result.keys()))

asyncio.run(test())
