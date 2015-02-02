__author__ = 'Dennis Wallace'

from deefuzzer.playlistobj.playlistbase import *


class PlaylistM3U(PlaylistBase):
    def __init__(self, filepath, typefilter=""):
        PlaylistBase.__init__(self, filepath, typefilter)
        self.read_playlist()

    def get_playlist(self):
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
