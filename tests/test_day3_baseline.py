from app.agent import classify_incident


def test_vpn_issue_is_classified_as_network():
    result = classify_incident("I cannot connect to the VPN")

    assert result["category"] == "Network"


def test_password_issue_is_classified_as_identity():
    result = classify_incident("I need a password reset")

    assert result["category"] == "Identity"


def test_unknown_issue_does_not_crash():
    result = classify_incident("I have an unusual technical problem")

    assert isinstance(result, dict)
    assert "category" in result