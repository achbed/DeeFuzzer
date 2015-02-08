__author__ = 'Dennis Wallace'

from deefuzzer.playlistobj.playlistbase import *


class PlaylistFolder(PlaylistBase):
    """
    A playlist read from a folder.
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
        if os.path.isdir(self.filepath):
            try:
                for root, dirs, files in os.walk(self.filepath):
                    for fn in files:
                        fp = self.path_to_absolute(os.path.join(root, fn))
                        if Media.isaudio(fp):
                            file_paths.append(fp)
                file_paths.sort()
            except:
                pass

        return file_paths
