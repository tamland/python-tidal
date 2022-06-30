# -*- coding: utf-8 -*-
#
# Copyright (C) 2019-2022 morguldir
# Copyright (C) 2014 Thomas Amland
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from io import BytesIO

import pytest
import ffmpeg
from PIL import Image


def verify_image_resolution(session, url, width, height):
    """
    Verifies that the image at the specified url is the specified resolution

    :param session: The TIDAL session
    :param url: The url to the image
    :param width: The width of the image
    :param height: The height of the image
    """
    image = session.request_session.get(url).content
    assert Image.open(BytesIO(image)).size == (width, height)


def verify_image_cover(session, model, resolutions):
    """
    Verifies that the given object has an image url that supports the given resolutions

    :param session: The TIDAL session you want to use
    :param model: The object you want to test the image of
    :param resolutions: A list of resolutions that the image has.
    """
    for resolution in resolutions:
        verify_image_resolution(session, model.image(resolution), resolution, resolution)

    with pytest.raises(ValueError):
        model.image(81)

    with pytest.raises(AssertionError):
        verify_image_resolution(session, model.image(resolutions[-1]), 1270, 1270)


def verify_video_resolution(url, width, height):
    """
    Verify that the video at the specified url matches the given resolutions.

    :param url: The url to the video.
    :param width: The width of the video in pixels.
    :param height: The height of the video in pixels.
    """
    probe = ffmpeg.probe(url)
    stream = probe['streams'][-1]
    assert (stream['width'], stream['height']) == (width, height)


def verify_video_cover(model, resolutions):
    """
    Verifies that the given instance of a model has an image of all the listed resolutions.

    :param model: An instance of the model you want to check
    :param resolutions: A list of resolutions
    """
    for resolution in resolutions:
        verify_video_resolution(model.video(resolution), resolution, resolution)

    with pytest.raises(ValueError):
        model.video(81)

    with pytest.raises(AssertionError):
        verify_video_resolution(model.video(resolutions[-1]), 1270, 1270)
