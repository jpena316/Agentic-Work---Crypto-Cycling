"""Orchestrator: coordinates all four cycling-coach agents in sequence."""

import logging
import time

from agents.bike_recommender import BikeRecommenderAgent
from agents.data_retrieval import DataRetrievalAgent
from agents.performance import PerformanceAnalysisAgent
from agents.training_plan import TrainingPlanAgent
from orchestrator.context import create_context

logger = logging.getLogger(__name__)


class CyclingCoachOrchestrator:
    """Runs the four-agent pipeline and assembles the final coaching report.

    Each agent enriches the shared context dict in sequence.  Failures are
    isolated: a critical failure in Agent 1 aborts the pipeline early, while
    failures in later agents degrade the output to a partial report rather
    than stopping execution.
    """

    async def run(
        self,
        athlete_goals: list[str],
        bikes_under_consideration: list[str],
    ) -> dict:
        """Execute the full pipeline and return an assembled coaching report.

        Args:
            athlete_goals: Free-text goal strings from the user
                (e.g. ``["complete first century", "lose 5 kg"]``).
            bikes_under_consideration: Bike model names to evaluate
                (e.g. ``["Canyon Aeroad CF SLX 8", "Trek Madone SLR 7"]``).

        Returns:
            Report dict produced by :meth:`_assemble_report`.
        """
        context = create_context(athlete_goals, bikes_under_consideration)
        pipeline_start = time.perf_counter()
        run_id = context["metadata"]["run_id"]
        logger.info("Pipeline started — run_id=%s", run_id)

        # ------------------------------------------------------------------
        # Agent 1: Data Retrieval
        # ------------------------------------------------------------------
        context = await self._run_agent(DataRetrievalAgent(), context, agent_num=1)

        if context.get("computed_metrics") is None:
            logger.error(
                "Agent 1 critical failure: computed_metrics is None — aborting pipeline."
            )
            context["errors"].append("Pipeline aborted: computed_metrics unavailable.")
            return self._assemble_report(context)

        # ------------------------------------------------------------------
        # Agent 2: Performance Analysis
        # ------------------------------------------------------------------
        context = await self._run_agent(PerformanceAnalysisAgent(), context, agent_num=2)

        skip_training_plan = context.get("performance_analysis") is None
        if skip_training_plan:
            logger.warning(
                "Agent 2 produced no performance_analysis — skipping Agent 3 (training plan)."
            )

        # ------------------------------------------------------------------
        # Agent 3: Training Plan (skipped if Agent 2 produced nothing)
        # ------------------------------------------------------------------
        if not skip_training_plan:
            context = await self._run_agent(TrainingPlanAgent(), context, agent_num=3)

        if context.get("training_plan") is None:
            logger.warning(
                "training_plan is None — continuing to Agent 4 (bike recommendations)."
            )

        # ------------------------------------------------------------------
        # Agent 4: Bike Recommender
        # ------------------------------------------------------------------
        context = await self._run_agent(BikeRecommenderAgent(), context, agent_num=4)

        elapsed = time.perf_counter() - pipeline_start
        logger.info("Pipeline complete — run_id=%s, elapsed=%.2fs", run_id, elapsed)
        context["metadata"]["elapsed_seconds"] = round(elapsed, 3)

        return self._assemble_report(context)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _run_agent(self, agent, context: dict, *, agent_num: int) -> dict:
        """Run a single agent with timing, logging, and exception isolation.

        Any unhandled exception is caught, appended to ``context["errors"]``,
        and logged — execution continues with the next agent.

        Args:
            agent: Instantiated agent object with an async ``run`` method.
            context: Shared pipeline state.
            agent_num: 1-based agent number used in log messages.

        Returns:
            Updated context dict (same object, mutated in-place by the agent).
        """
        name = type(agent).__name__
        logger.info("--- Agent %d: %s starting ---", agent_num, name)
        t0 = time.perf_counter()
        try:
            context = await agent.run(context)
        except Exception as exc:
            msg = f"Agent {agent_num} ({name}) raised an unhandled exception: {exc}"
            logger.exception(msg)
            context["errors"].append(msg)
        elapsed = time.perf_counter() - t0
        logger.info("--- Agent %d: %s done (%.2fs) ---", agent_num, name, elapsed)
        return context

    def _assemble_report(self, context: dict) -> dict:
        """Build the final output dict from the completed context.

        Status rules:
        - ``"success"`` — no errors recorded during the run.
        - ``"partial"`` — errors present but at least one key output exists.
        - ``"failed"`` — errors present and no meaningful output was produced.

        Args:
            context: Completed shared pipeline state.

        Returns:
            Structured report dict with status, all agent outputs, and metadata.
        """
        errors = context.get("errors") or []

        has_data = any([
            context.get("performance_analysis"),
            context.get("training_plan"),
            context.get("bike_recommendations"),
        ])

        if not errors:
            status = "success"
        elif has_data:
            status = "partial"
        else:
            status = "failed"

        return {
            "status": status,
            "athlete": context.get("athlete_profile"),
            "performance_analysis": context.get("performance_analysis"),
            "training_plan": context.get("training_plan"),
            "bike_recommendations": context.get("bike_recommendations"),
            "rider_signature": context.get("rider_signature"),
            "errors": errors,
            "metadata": context.get("metadata", {}),
        }
