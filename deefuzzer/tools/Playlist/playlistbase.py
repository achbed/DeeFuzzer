__author__ = 'Dennis Wallace'

import random
from deefuzzer.tools.utils import *
from deefuzzer.tools.Media.media import *


class PlaylistBase(object):
    """
    Base Playlist class. All playlist objects should inherit from this class
    to allow common functions to be used in core code.  See PlaylistM3U and PlaylistPLS classes
    for examples on how to configure a subclass, and playlist.py to add the new class into the autodetection
    function.
    """

    def __init__(self, filepath):
        object.__init__(self)
        self.file_list = []
        self.mod = ""
        self.base = ""
        self.hash = None
        self.frequency = 0
        self.current = -1
        self.current_track = None

        self.filepath = path_strip_parents(filepath)
        if os.path.exists(self.filepath):
            self.mod = str(os.path.getmtime(self.filepath))
            self.base = os.path.dirname(self.filepath)

        if os.path.isdir(self.filepath):
            self.base = self.filepath

        self.read_playlist()

    def __hash__(self):
        if not self.hash:
            self.hash = self.gethash(self.file_list)
        return self.hash

    def __len__(self):
        return len(self.file_list)

    def shuffle(self):
        random.shuffle(self.file_list)

    def should_play(self, counter):
        if not len(self.file_list):
            return False

        if self.frequency < 2:
            return True

        if not self.frequency % counter:
            return True

        return False

    def next(self):
        return self.goto(self.current + 1)

    def prev(self):
        return self.goto(self.current - 1)

    def goto(self, index):
        if not len(self.file_list):
            return -1

        # Get the requested index into range
        l = len(self.file_list)
        while index < 0:
            index += l
        if index > l:
            index %= l

        self.current = l
        self.current_track = new_media(self.file_list[self.current])
        return self.current

    def path_relative(self, p):
        return path_strip_parents(os.path.join(self.base, p))

    def read_playlist(self):
        self.file_list = self.get_playlist()
        self.hash = self.gethash(self.file_list)

    def get_playlist(self):
        return []

    def gethash(self, filelist):
        hash_source = self.filepath
        if os.path.exists(self.filepath):
            hash_source += str(os.path.getmtime(self.filepath))
            if os.path.isfile(self.filepath):
                hash_source += str(os.path.getsize(self.filepath))
        for i in filelist:
            hash_source += i
            if os.path.exists(i):
                hash_source += str(os.path.getmtime(i))
                if os.path.isfile(i):
                    hash_source += str(os.path.getsize(i))

        return get_md5(hash_source)

    def stale(self):
        if not self.hash:
            self.hash = self.gethash(self.get_playlist())
            return False
        newhash = self.gethash(self.get_playlist())
        return self.hash == newhash
