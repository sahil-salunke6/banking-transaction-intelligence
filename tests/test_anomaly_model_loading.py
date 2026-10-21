
import logging

from app.services import anomaly_service


def test_missing_model_returns_none_and_logs_warning(
    tmp_path, monkeypatch, caplog
):
    missing_path = tmp_path / "missing_model.joblib"

    monkeypatch.setattr(
        anomaly_service,
        "MODEL_PATH",
        missing_path,
    )
    monkeypatch.setattr(
        anomaly_service,
        "_MODEL_ARTIFACT",
        None,
    )

    with caplog.at_level(
        logging.WARNING,
        logger="app.services.anomaly_service",
    ):
        result = anomaly_service.load_model_artifact()

    assert result is None
    assert anomaly_service._MODEL_ARTIFACT is None
    assert "Anomaly model artifact not found" in caplog.text


def test_corrupted_model_is_handled_safely(
    tmp_path, monkeypatch, caplog
):
    fake_model_path = tmp_path / "corrupted_model.joblib"
    fake_model_path.write_bytes(b"not-a-valid-model")

    monkeypatch.setattr(
        anomaly_service,
        "MODEL_PATH",
        fake_model_path,
    )
    monkeypatch.setattr(
        anomaly_service,
        "_MODEL_ARTIFACT",
        None,
    )

    def fail_to_load(path):
        raise ValueError("Simulated model loading failure")

    monkeypatch.setattr(
        anomaly_service.joblib,
        "load",
        fail_to_load,
    )

    with caplog.at_level(
        logging.ERROR,
        logger="app.services.anomaly_service",
    ):
        result = anomaly_service.load_model_artifact()

    assert result is None
    assert anomaly_service._MODEL_ARTIFACT is None
    assert "Failed to load anomaly model artifact" in caplog.text
    assert "Simulated model loading failure" in caplog.text
