import asyncio
from orchestrator.context import create_context
from agents.data_retrieval import DataRetrievalAgent
from agents.performance import PerformanceAnalysisAgent
from agents.training_plan import TrainingPlanAgent

async def test():
    context = create_context(
        athlete_goals=["build endurance", "increase FTP"],
        bikes_under_consideration=["Canyon Aeroad", "Trek Madone"]
    )
    context = await DataRetrievalAgent().run(context)
    context = await PerformanceAnalysisAgent().run(context)
    context = await TrainingPlanAgent().run(context)
    plan = context["training_plan"]
    if plan:
        print("Week focus:", plan["week_focus"])
        print("TSS target:", plan["tss_target"]s)
        for day in plan["days"]:
            print(day["day"], day["workout_type"], day["intensity"], day["duration_mins"], "mins")
            print(day["description"])
        print("Coaching notes:", plan["coaching_notes"])
    print("Errors:", context["errors"])

asyncio.run(test())
