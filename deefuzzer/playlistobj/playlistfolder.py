__author__ = 'Dennis Wallace'

from deefuzzer.playlistobj.playlistbase import *


class PlaylistFolder(PlaylistBase):
    def __init__(self, filepath, typefilter=""):
        PlaylistBase.__init__(self, filepath, typefilter)
        self.read_playlist()

    def get_playlist(self):
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
