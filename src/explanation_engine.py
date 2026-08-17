"""
explanation_engine.py
------------------------
Answers "Why is the system recommending it?"

The explanation is built deterministically from the already-computed
InterventionScore evidence (see src.recommendation_engine) -- template-
based, not invented. An LLM, if an API key is configured, may be used
ONLY to rephrase this already-correct structured explanation into more
natural prose for a management summary; it is never given the ability to
introduce new numbers, and if no API key is present the deterministic
text below is shown as-is.
"""

from __future__ import annotations

from src.config import settings
from src.recommendation_engine import InterventionScore


def build_explanation(score: InterventionScore, dropoff_df=None) -> str:
    parts = []

    stage_note = ""
    if dropoff_df is not None and not dropoff_df.empty:
        top_stage = dropoff_df.iloc[0]
        stage_note = (
            f" The largest abandonment stage in the reconstructed journeys is "
            f"'{top_stage['stage']}', accounting for {top_stage['share_pct']}% of non-converting sessions."
        )

    if score.causal_status == "ok" and score.causal_effect_pct is not None:
        direction = "positive" if score.causal_effect_pct > 0 else "negative"
        refute_note = ""
        if score.evidence.get("refutation_passed") is True:
            refute_note = " This estimate held up under a placebo-treatment refutation check."
        elif score.evidence.get("refutation_passed") is False:
            refute_note = " A placebo-treatment refutation check suggests this estimate should be treated with some caution."
        parts.append(
            f"The causal analysis estimates a {direction} effect of "
            f"{score.causal_effect_pct:+.2f} percentage points on conversion "
            f"associated with this change, adjusting for prior engagement as a confounder.{refute_note}"
        )
    elif score.causal_status == "insufficient_evidence":
        parts.append(
            "There was insufficient evidence for a reliable causal estimate for this "
            "intervention, so this recommendation leans more heavily on simulation results."
        )

    if score.simulated_improvement_pct is not None:
        parts.append(
            f"A discrete-event simulation of this scenario projects a "
            f"{score.simulated_improvement_pct:+.2f} percentage point change in "
            f"conversion rate relative to the current-system baseline."
        )

    parts.append(
        f"An estimated {score.affected_sessions_pct}% of sessions reach a stage "
        f"where this intervention would apply."
    )

    parts.append(
        f"Implementation complexity is rated {score.complexity} and risk is rated "
        f"{score.risk}, giving an overall confidence of {score.confidence} in this "
        f"recommendation (recommendation score: {score.recommendation_score}/10)."
    )

    explanation = " ".join(parts) + stage_note
    return explanation


def build_llm_summary(score: InterventionScore, deterministic_explanation: str) -> str | None:
    """
    Optional plain-language rewrite via an LLM. Returns None if no API
    key is configured -- callers must fall back to the deterministic
    explanation in that case. The LLM is given the ALREADY-COMPUTED
    numbers and instructed not to introduce new figures.
    """
    if not settings.anthropic_api_key and not settings.openai_api_key:
        return None

    prompt = (
        "Rewrite the following analytical explanation as a concise, plain-language "
        "summary for a non-technical manager, in 2-3 sentences. Do not invent, change, "
        "round differently, or omit any numeric figures; use only the ones given.\n\n"
        f"{deterministic_explanation}"
    )

    try:
        if settings.anthropic_api_key:
            import anthropic
            client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
            resp = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=300,
                messages=[{"role": "user", "content": prompt}],
            )
            return "".join(block.text for block in resp.content if hasattr(block, "text"))
    except Exception:
        return None
    return None
