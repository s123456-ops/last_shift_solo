import pytest

from view.camera_motion import HeadBob, approach_angle


def biggest_offset(bob, seconds, moving, running):
    biggest = 0.0
    for _ in range(int(seconds * 60)):
        vertical, _ = bob.update(1 / 60, moving, running)
        biggest = max(biggest, abs(vertical))
    return biggest


def test_standing_still_does_not_bob():
    assert biggest_offset(HeadBob(), 2, moving=False, running=False) == 0


def test_running_bobs_more_than_walking():
    walking = biggest_offset(HeadBob(), 2, moving=True, running=False)
    running = biggest_offset(HeadBob(), 2, moving=True, running=True)
    assert running > walking > 0


def test_bob_fades_out_after_stopping():
    bob = HeadBob()
    biggest_offset(bob, 2, moving=True, running=True)
    biggest_offset(bob, 1, moving=False, running=False)  # une seconde d'arrêt
    assert biggest_offset(bob, 1, moving=False, running=False) < 0.001


@pytest.mark.parametrize(
    ("current", "target", "expected"),
    [(0, 90, 45), (350, 10, 0), (10, 350, 0), (-170, 170, -180)],
)
def test_approach_angle_takes_the_short_way(current, target, expected):
    result = approach_angle(current, target, 0.5)
    assert result % 360 == pytest.approx(expected % 360)  # 360° et 0°, même direction


def test_approach_angle_never_overshoots():
    assert approach_angle(0, 90, 5) == 90
