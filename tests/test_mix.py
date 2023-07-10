import tidalapi

from .cover import verify_image_cover


def test_mix(session):
    mixes = session.mixes()
    first = next(iter(mixes))
    assert isinstance(first, tidalapi.Mix)


def test_image(session):
    mixes = session.mixes()
    first = next(iter(mixes))
    verify_image_cover(session, first, [320, 640, 1500])
