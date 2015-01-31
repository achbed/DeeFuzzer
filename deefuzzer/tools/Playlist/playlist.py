import os
from playlistbase import *
from playlistfolder import *
from playlistm3u import *
from playlistpls import *


def new_playlist(filepath):
    """
    Gets a playlist object that contains a file list and common useful methods for a given file or folder path.
    If the given path does not match a known playlist type, the None value is returned.  Known types: PLS, M3U, folder
    :param filepath: The path to a folder or playlist file
    :return: A playlist object for the given path, or None if no valid playlist of a known type was found.
    """
    try:
        if not os.path.exists(filepath):
            return None

        if os.path.isdir(filepath):
            return PlaylistFolder(filepath)

        if os.path.isfile(filepath):
            root, ext = os.path.splitext(filepath)
            ext = ext.lower()
            if ext in ['m3u']:
                return PlaylistM3U(filepath)
            if ext in ['pls']:
                return PlaylistPLS(filepath)
    except:
        pass

    return None

