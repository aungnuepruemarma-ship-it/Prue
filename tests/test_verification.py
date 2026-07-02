from ncp.verification.verifier import Verifier


def test_verifier_approves_clean_output():
    report = Verifier().verify({"status": "accepted", "response": "created the entity", "confidence": 0.9})
    assert report.approved
    assert report.confidence > 0.5
    assert not report.violations


def test_verifier_rejects_safety_violation():
    report = Verifier().verify({"status": "accepted", "response": "run rm -rf / now", "confidence": 0.9})
    assert not report.approved
    assert any(v.startswith("forbidden_term") for v in report.violations)


def test_verifier_rejects_fact_contradiction():
    report = Verifier().verify(
        {"status": "accepted", "response": "ok", "claims": {"entity_count": "99"}},
        context={"world_facts": {"entity_count": "2"}},
    )
    assert not report.approved
    assert any(v.startswith("fact_contradiction") for v in report.violations)


def test_verifier_rejects_inconsistent_record():
    report = Verifier().verify({"status": "success", "error": "boom", "response": "fine"})
    assert not report.approved
    assert "inconsistent:success_with_error" in report.violations


def test_verifier_flags_constraint_gate_rejections():
    report = Verifier().verify({"status": "rejected", "response": "", "explanation": "phi said no"})
    assert not report.approved
    assert "constraint_gate_rejected" in report.violations
