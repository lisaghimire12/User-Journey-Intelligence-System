def simulate(
    conversion_rate,
    abandonment_rate,
    journey_length,
    intervention,
    intensity,
):
    """
    What-If simulation engine.

    The simulation starts from the actual observed metrics and
    models how a hypothetical intervention could change them.

    IMPORTANT:
    Results are simulated/estimated, not observed causal effects.
    """

    # ---------------------------------------------------------
    # BASELINE
    # ---------------------------------------------------------

    baseline_conversion = float(
        conversion_rate or 0
    )

    baseline_abandonment = float(
        abandonment_rate or 0
    )

    baseline_journey_length = float(
        journey_length or 0
    )

    intensity = max(
        0.0,
        min(1.0, float(intensity))
    )

    # ---------------------------------------------------------
    # INTERVENTION MODELS
    #
    # Each intervention represents a hypothetical change.
    #
    # The values are maximum modeled effects at intensity = 1.
    # ---------------------------------------------------------

    effects = {

        "Reduce checkout steps": {
            "conversion_gain": 15.0,
            "abandonment_reduction": 15.0,
            "journey_reduction": 2.0,
        },

        "Improve product information visibility": {
            "conversion_gain": 10.0,
            "abandonment_reduction": 10.0,
            "journey_reduction": 1.0,
        },

        "Reduce navigation friction": {
            "conversion_gain": 12.0,
            "abandonment_reduction": 12.0,
            "journey_reduction": 1.5,
        },

        "Increase product exposure": {
            "conversion_gain": 8.0,
            "abandonment_reduction": 6.0,
            "journey_reduction": 0.5,
        },

        "Add product-information intervention": {
            "conversion_gain": 10.0,
            "abandonment_reduction": 8.0,
            "journey_reduction": 1.0,
        },
    }

    effect = effects.get(
        intervention,
        {
            "conversion_gain": 0.0,
            "abandonment_reduction": 0.0,
            "journey_reduction": 0.0,
        },
    )

    # ---------------------------------------------------------
    # CALCULATE SIMULATED VALUES
    # ---------------------------------------------------------

    simulated_conversion = (
        baseline_conversion
        + effect["conversion_gain"] * intensity
    )

    simulated_abandonment = (
        baseline_abandonment
        - effect["abandonment_reduction"] * intensity
    )

    simulated_journey_length = (
        baseline_journey_length
        - effect["journey_reduction"] * intensity
    )

    # Keep values sensible.
    simulated_conversion = max(
        0.0,
        min(100.0, simulated_conversion)
    )

    simulated_abandonment = max(
        0.0,
        min(100.0, simulated_abandonment)
    )

    simulated_journey_length = max(
        1.0,
        simulated_journey_length
    )

    # ---------------------------------------------------------
    # CHANGE FROM BASELINE
    # ---------------------------------------------------------

    conversion_change = (
        simulated_conversion
        - baseline_conversion
    )

    abandonment_change = (
        simulated_abandonment
        - baseline_abandonment
    )

    journey_change = (
        simulated_journey_length
        - baseline_journey_length
    )

    # ---------------------------------------------------------
    # RETURN
    # ---------------------------------------------------------

    return {

        "intervention": intervention,

        "intensity": intensity,

        "baseline_conversion": round(
            baseline_conversion,
            2,
        ),

        "simulated_conversion": round(
            simulated_conversion,
            2,
        ),

        "conversion_change": round(
            conversion_change,
            2,
        ),

        "baseline_abandonment": round(
            baseline_abandonment,
            2,
        ),

        "simulated_abandonment": round(
            simulated_abandonment,
            2,
        ),

        "abandonment_change": round(
            abandonment_change,
            2,
        ),

        "baseline_journey_length": round(
            baseline_journey_length,
            2,
        ),

        "simulated_journey_length": round(
            simulated_journey_length,
            2,
        ),

        "journey_length_change": round(
            journey_change,
            2,
        ),

        "confidence": "Medium",

        "status": "SIMULATED",
    }