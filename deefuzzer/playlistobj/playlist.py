__author__ = 'Dennis Wallace'

from deefuzzer.playlistobj import *


class Playlist:
    """
    Static class for interacting with playlists
    """

    def __init__(self):
        pass

    @staticmethod
    def new(filepath, typefilter=""):
        """
        Gets a playlist object that contains a file list and common useful methods for a given file or folder path.
        If the given path does not match a known playlist type, the None value is returned.
        Known types: PLS, M3U, folder
        :param filepath: The path to a folder or playlist file
        :param typefilter: The type of file to load into the playlist.  Must be a MIME type.
        :return: A playlist object for the given path, or None if no valid playlist of a known type was found.
        """
        try:
            if not os.path.exists(filepath):
                return None

            if os.path.isdir(filepath):
                return PlaylistFolder(filepath, typefilter)

            if os.path.isfile(filepath):
                root, ext = os.path.splitext(filepath)
                ext = ext.lower()
                if ext in ['m3u']:
                    return PlaylistM3U(filepath, typefilter)
                if ext in ['pls']:
                    return PlaylistPLS(filepath, typefilter)
        except:
            pass

        return None
