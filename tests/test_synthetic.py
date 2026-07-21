from waterqual.synthetic import PARAMETERS, SyntheticWaterConfig, generate_synthetic_water_data


def test_synthetic_shapes_and_keys():
    data = generate_synthetic_water_data(SyntheticWaterConfig(stations=8, hours=48, seed=3))
    assert set(data) == {"plants", "stations", "readings"}
    assert len(data["stations"]) == 8
    assert data["readings"]["parameter"].nunique() == len(PARAMETERS)
    assert data["readings"].shape[0] == 8 * 48 * len(PARAMETERS)


def test_invalid_config_rejected():
    try:
        SyntheticWaterConfig(stations=4, hours=24)
    except ValueError:
        assert True
    else:
        raise AssertionError("invalid config should fail")
