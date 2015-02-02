__author__ = 'Dennis Wallace'

import re
from deefuzzer.playlistobj.playlistbase import *


class PlaylistPLS(PlaylistBase):
    def __init__(self, filepath, typefilter=""):
        PlaylistBase.__init__(self, filepath, typefilter)
        self.read_playlist()

    def get_playlist(self):
        file_paths = []
        if os.path.isfile(self.filepath):
            try:
                f = open(self.filepath, 'r')
                try:
                    opener = False
                    for line in f.readlines():
                        line = line.strip()

                        if line == "[playlist]":
                            opener = True
                            continue

                        if not opener:
                            # Wait until we have an opener line to start reading
                            continue

                        if re.match("^File[0-9]+=", line):
                            line = re.sub("^File[0-9]+=", "", line).strip()
                            fp = self.path_to_absolute(line)
                            if Media.isaudio(fp):
                                file_paths.append(fp)
                            continue
                except:
                    f.close()
            except:
                pass

        return file_paths
