import tidalapi
from tidalapi import Quality

session = tidalapi.Session()
# Will run until you visit the printed url and link your account
session.login_oauth_simple()
# Override the required playback quality, if necessary
# Note: Set the quality according to your subscription.
# Normal: Quality.low_320k
# HiFi: Quality.high_lossless
# HiFi+ Quality.hi_res_lossless
session.audio_quality = Quality.low_320k

album = session.album(66236918)
tracks = album.tracks()
for track in tracks:
    print(track.name)
    for artist in track.artists:
        print(' by: ', artist.name)