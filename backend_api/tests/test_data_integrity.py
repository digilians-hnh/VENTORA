import shutil

import pytest

from backend_api.core import data_access
from backend_api.core.config import RISK_DF_PATH


def test_verify_frozen_hashes_passes_on_untouched_repo():
    verified = data_access.verify_frozen_hashes()
    assert "data/risk_df_recommendations_FINAL.pkl" in verified
    assert "data/business_value_comparison.csv" in verified


def test_verify_frozen_hashes_detects_tampering(tmp_path, monkeypatch):
    # Copy the real ventora_app dir to a scratch location, corrupt one
    # frozen file there, and confirm verify_frozen_hashes() raises --
    # without touching the real, checked-in frozen file at all.
    from backend_api.core import config as config_module

    scratch_app_dir = tmp_path / "ventora_app"
    shutil.copytree(config_module.VENTORA_APP_DIR, scratch_app_dir)

    tampered_pkl = scratch_app_dir / "data" / "risk_df_recommendations_FINAL.pkl"
    with open(tampered_pkl, "ab") as f:
        f.write(b"\x00tamper")

    monkeypatch.setattr(config_module, "VENTORA_APP_DIR", scratch_app_dir)
    monkeypatch.setattr(config_module, "RISK_DF_PATH", scratch_app_dir / "data" / "risk_df_recommendations_FINAL.pkl")
    monkeypatch.setattr(config_module, "FROZEN_HASHES_FILE", scratch_app_dir / "FROZEN_ARTIFACT_HASHES.txt")
    monkeypatch.setattr(data_access, "VENTORA_APP_DIR", scratch_app_dir)
    monkeypatch.setattr(data_access, "FROZEN_HASHES_FILE", scratch_app_dir / "FROZEN_ARTIFACT_HASHES.txt")

    with pytest.raises(data_access.DataIntegrityError):
        data_access.verify_frozen_hashes()

    # Confirm the real, original file is untouched throughout.
    assert RISK_DF_PATH.exists()
