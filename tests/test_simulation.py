from src.simulation_engine import SimulationParams, run_simulation


def test_run_simulation_returns_valid_rate():
    params = SimulationParams(n_sessions=300, seed=1)
    result = run_simulation(params)
    assert 0.0 <= result["conversion_rate"] <= 100.0
    assert result["n_sessions"] == 300
    total_outcomes = (
        result["converted"] + result["registration_exit"]
        + result["checkout_exit"] + result["browse_exit"]
    )
    assert total_outcomes == 300


def test_lower_friction_improves_conversion_on_average():
    high_friction = run_simulation(SimulationParams(registration_friction=90, checkout_friction=90, n_sessions=800, seed=2))
    low_friction = run_simulation(SimulationParams(registration_friction=10, checkout_friction=10, n_sessions=800, seed=2))
    assert low_friction["conversion_rate"] > high_friction["conversion_rate"]
