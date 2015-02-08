__author__ = 'Dennis Wallace'

from deefuzzer.playlistobj.playlistbase import *


class PlaylistEmpty(PlaylistBase):
    """
    An empty playlist object.
    """

    def __init__(self):
        PlaylistBase.__init__(self, "", "")

    def get_playlist(self):
        """
        Gets the list of media file paths for the playlist.  No filtering by type should be done here.
        :return: A list of valid media file paths for this playlist
        """
        return []
