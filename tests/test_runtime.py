from ncp.core.runtime import Runtime, build_default_universe

def test_runtime_step_accepts_some_candidate():
    runtime = Runtime(build_default_universe())
    result = runtime.step("create a new concept")
    assert result.status in {"accepted", "rejected", "no_candidates"}
    assert runtime.history.events
