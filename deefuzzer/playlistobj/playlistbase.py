__author__ = 'Dennis Wallace'

import random
from deefuzzer.tools.utils import *
from deefuzzer.mediaobj.media import *


class PlaylistBase(object):
    """
    Base playlistobj class. All playlist objects should inherit from this class
    to allow common functions to be used in core code.  See PlaylistM3U and PlaylistPLS classes
    for examples on how to configure a subclass, and playlist.py to add the new class into the autodetection
    function.
    """

    def __init__(self, filepath, typefilter=""):
        object.__init__(self)
        self.file_list = []
        self.mod = ""
        self.base = ""
        self.hash = None
        self.frequency = 0
        self.current = -1
        self.current_track = None

        self.filepath = path_strip_parents(filepath)
        self.filter = typefilter
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
        """
        Randomly shuffles the contents of the playlist.
        :return: None
        """
        random.shuffle(self.file_list)

    def sort(self, comp=None, key=None, rev=False):
        """
        Sorts the contents of the playlist in order.  See list.sorted() documentation for details on the
        available options.
        :param comp: The comparison function to use
        :param key: The key extraction function to use
        :param rev: Whether or not to reverse the order of the result
        :return: None
        """
        self.file_list.sort(comp, key, rev)

    def should_play(self, counter):
        """
        Whether a track should be played based on an internal frequency value for the playlist and the counter value
        given.  Useful for when tracks should only be played periodically (ie, a jingle or ad).
        :param counter: The counter to check
        :return: True if the track should be played, False if not.
        """
        if not len(self.file_list):
            return False

        if self.frequency < 2:
            return True

        if not self.frequency % counter:
            return True

        return False

    def next(self):
        """
        Jump to the next track in the playlist
        :return: The index value of the new track (may not match the requested index if wrap-around was required)
        """
        return self.goto(self.current + 1)

    def prev(self):
        """
        Jump to the previous track in the playlist
        :return: The index value of the new track (may not match the requested index if wrap-around was required)
        """
        return self.goto(self.current - 1)

    def goto(self, index):
        """
        Jumps to a particular index in the playlist.  Will "wrap around" if required.
        :param index: The index to jump to.
        :return: The index value of the new track (may not match the requested index if wrap-around was required)
        """
        if not len(self.file_list):
            return -1

        # Get the requested index into range
        l = len(self.file_list)
        while index < 0:
            index += l
        if index > l:
            index %= l

        self.current = l
        self.current_track = Media.new(self.file_list[self.current])
        return self.current

    def path_to_absolute(self, p):
        """
        Gets the absolute path to the requested path, based on the location of the playlist.
        :param p: The (possibly) relative path to convert to absolute.
        :return: The absolute path to the file.  If the requested path was absolute, no change should be made.
        """
        return path_strip_parents(os.path.join(self.base, p))

    def read_playlist(self):
        """
        Reads the playlist data into the internal data structures, filtering for the requested media type.  If no
        media type is given, the first valid media file is used to filter the rest of the files.
        :return: None
        """
        self.file_list = []
        for i in self.get_playlist():
            if Media.isaudio(i, self.filter):
                if not self.filter:
                    m = Media.new(i)
                    self.filter = m.mime_type
                self.file_list.append(i)
        self.hash = self.gethash(self.file_list)

    def get_playlist(self):
        """
        Gets the list of media file paths for the playlist.  No filtering by type should be done here.  This method
        must be overridden by inherited classes in order to function.
        :return: A list of media file paths for this playlist
        """
        return []

    def gethash(self, filelist):
        """
        Gets a unique hash for the playlist, incorporating enough details to detect when a media file changes
        :param filelist: The list of media paths to hash
        :return: The resulting hash value
        """
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

    def isstale(self):
        """
        Detects whether the playlist or any media files used in the playlist have been updated.
        :return: True of the list of media files is out of date, False if not.
        """
        if not self.hash:
            self.hash = self.gethash(self.get_playlist())
            return False
        newhash = self.gethash(self.get_playlist())
        return self.hash == newhash
