__author__ = 'Dennis Wallace'

import os
import mimetypes
from mp3 import *
from ogg import *
from webm import *


def new_media(filepath):
    try:
        if not os.path.exists(filepath):
            return None

        if os.path.isdir(filepath):
            return None

        root, ext = os.path.splitext(filepath)
        ext = ext.lower()
        mime = mimetypes.guess_type(filepath)

        if ext == 'mp3' or 'audio/mpeg' in mime:
            return Mp3(filepath)

        if ext == 'ogg' or 'audio/ogg' in mime:
            return Ogg(filepath)

        if ext == 'webm' or 'video/webm' in mime:
            return WebM(filepath)
    except:
        pass

    return None
