__author__ = 'Dennis Wallace'

import os
from deefuzzer.playlistobj.playlistbase import *


class PlaylistM3U(PlaylistBase):
    """
    A playlist read from am M3U file.
    """

    def __init__(self, filepath, typefilter=""):
        PlaylistBase.__init__(self, filepath, typefilter)
        self.read_playlist()

    def get_playlist(self):
        """
        Gets the list of media file paths for the playlist.  No filtering by type should be done here.
        :return: A list of valid media file paths for this playlist
        """
        file_paths = []
        if os.path.isfile(self.filepath):
            try:
                f = open(self.filepath, 'r')
                try:
                    for path in f.readlines():
                        path = path.strip()
                        if '#' != path[0]:
                            fp = self.path_to_absolute(path)
                            if Media.isaudio(fp):
                                file_paths.append(fp)
                except:
                    f.close()
            except:
                pass

        return file_paths
