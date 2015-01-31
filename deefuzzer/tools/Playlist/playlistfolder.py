__author__ = 'Dennis Wallace'

from deefuzzer.tools.utils import *
from playlistbase import *


class PlaylistFolder(PlaylistBase):
    def __init__(self, filepath):
        PlaylistBase.__init__(self, filepath)
        self.read_playlist()

    def get_playlist(self):
        file_paths = []
        if os.path.isdir(self.filepath):
            try:
                for root, dirs, files in os.walk(self.filepath):
                    for fn in files:
                        fp = self.path_relative(os.path.join(root, fn))
                        if isaudio(fp):
                            file_paths.append(fp)
                file_paths.sort()
            except:
                pass

        return file_paths
