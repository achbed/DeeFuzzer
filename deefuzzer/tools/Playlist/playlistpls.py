__author__ = 'Dennis Wallace'

from deefuzzer.tools.utils import *
from playlistbase import *


class PlaylistPLS(PlaylistBase):
    def __init__(self, filepath):
        PlaylistBase.__init__(self, filepath)
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
                            fp = self.path_relative(line)
                            if isaudio(fp):
                                file_paths.append(fp)
                            continue
                except:
                    f.close()
            except:
                pass

        return file_paths
