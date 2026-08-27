import pytest

from placement_algorithm.distance import Coordinates, haversine_km, HaversineDistanceProvider


def test_zero_distance_for_identical_points():
    p = Coordinates(-1.2921, 36.8219)
    assert haversine_km(p, p) == pytest.approx(0.0, abs=1e-9)


def test_nairobi_to_mombasa_known_distance():
    nairobi = Coordinates(-1.2921, 36.8219)
    mombasa = Coordinates(-4.0435, 39.6682)
    # Real-world great-circle distance is ~440km; allow a few km tolerance
    # for the exact coordinates chosen.
    assert haversine_km(nairobi, mombasa) == pytest.approx(440, abs=10)


def test_distance_is_symmetric():
    a = Coordinates(0.5, 35.0)
    b = Coordinates(-1.0, 36.5)
    assert haversine_km(a, b) == pytest.approx(haversine_km(b, a), rel=1e-9)


def test_provider_matches_free_function():
    a = Coordinates(0.5, 35.0)
    b = Coordinates(-1.0, 36.5)
    provider = HaversineDistanceProvider()
    assert provider.distance_km(a, b) == pytest.approx(haversine_km(a, b))


@pytest.mark.parametrize("lat,lon", [(91.0, 0.0), (-91.0, 0.0), (0.0, 181.0), (0.0, -181.0)])
def test_invalid_coordinates_rejected(lat, lon):
    with pytest.raises(ValueError):
        Coordinates(lat, lon)


def test_triangle_inequality_roughly_holds():
    # Not a strict mathematical requirement to test exhaustively, but a
    # good sanity check: going via a third point should never be shorter
    # than the direct great-circle distance.
    a = Coordinates(-1.2921, 36.8219)  # Nairobi
    b = Coordinates(-4.0435, 39.6682)  # Mombasa
    c = Coordinates(0.5143, 35.2698)   # Eldoret
    direct = haversine_km(a, b)
    via_c = haversine_km(a, c) + haversine_km(c, b)
    assert via_c >= direct - 1e-6
