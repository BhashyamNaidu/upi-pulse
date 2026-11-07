import pytest

import upi_pulse
from upi_pulse.config import LAYERS, load_settings


def test_package_has_version():
    assert upi_pulse.__version__


def test_defaults_to_local_lake_under_project():
    settings = load_settings({})
    assert settings.env == "local"
    assert settings.lake_root.endswith("data/lake")


def test_env_overrides_lake_root_for_cloud():
    settings = load_settings(
        {"UPI_PULSE_ENV": "cloud", "UPI_PULSE_LAKE_ROOT": "abfss://lake@acct.dfs.core.windows.net/"}
    )
    assert settings.layer_path("silver") == "abfss://lake@acct.dfs.core.windows.net/silver"


@pytest.mark.parametrize("layer", LAYERS)
def test_every_layer_resolves(layer):
    assert load_settings({}).layer_path(layer).endswith(f"/{layer}")


def test_unknown_layer_rejected():
    with pytest.raises(ValueError, match="Unknown lake layer"):
        load_settings({}).layer_path("platinum")


def test_invalid_env_rejected():
    with pytest.raises(ValueError, match="UPI_PULSE_ENV"):
        load_settings({"UPI_PULSE_ENV": "prod"})


def test_drop_dir_and_metrics_defaults_and_empty_values():
    settings = load_settings({"UPI_PULSE_DROP_DIR": "", "UPI_PULSE_LAKE_ROOT": ""})
    assert settings.drop_dir.endswith("data/manual_drop")
    assert settings.lake_root.endswith("data/lake")
    assert settings.metrics_path.endswith("metrics/run_metrics.json")
