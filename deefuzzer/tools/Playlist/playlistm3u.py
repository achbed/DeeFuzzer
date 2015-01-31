__author__ = 'Dennis Wallace'

from deefuzzer.tools.utils import *


class PlaylistM3U(PlaylistBase):
    def __init__(self, filepath):
        PlaylistBase.__init__(self, filepath)
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
                            fp = self.path_relative(path)
                            if isaudio(fp):
                                file_paths.append(fp)
                except:
                    f.close()
            except:
                pass

        return file_paths
