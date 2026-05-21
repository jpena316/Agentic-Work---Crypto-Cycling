import asyncio
from orchestrator.context import create_context
from agents.data_retrieval import DataRetrievalAgent
from agents.performance import PerformanceAnalysisAgent
from agents.training_plan import TrainingPlanAgent
from agents.bike_recommender import BikeRecommenderAgent

async def test():
    context = create_context(
        athlete_goals=["build endurance", "increase FTP"],
        bikes_under_consideration=[
            "Trek Madone SLR7", "Cervelo Caledonia", "Cervelo Soloist",
            "Specialized Tarmac SL8", "Canyon Aeroad CF SLX8",
            "Canyon Endurace CF SLX8", "Canyon Endurace CF SLX7",
            "Factor Monza"
        ]
    )

    print("Running Agent 1 - Data Retrieval...")
    context = await DataRetrievalAgent().run(context)

    print("Running Agent 2 - Performance Analysis...")
    context = await PerformanceAnalysisAgent().run(context)

    print("Running Agent 3 - Training Plan...")
    context = await TrainingPlanAgent().run(context)

    print("Running Agent 4 - Bike Recommendation...")
    context = await BikeRecommenderAgent().run(context)

    print()
    print("=== RIDER SIGNATURE ===")
    sig = context["rider_signature"]
    if sig:
        for k, v in sig.items():
            print(k + ":", v)

    print()
    print("=== BIKE RECOMMENDATIONS ===")
    recs = context["bike_recommendations"]
    if recs:
        print("Best overall:", recs["best_overall"])
        print()
        print("Ranked:")
        for i, bike in enumerate(recs["ranked"], 1):
            print(str(i) + ".", bike)
            print("   ", recs["rationale"].get(bike, ""))
        print()
        print("Summary:", recs["summary"])

    print()
    print("Errors:", context["errors"])

asyncio.run(test())
