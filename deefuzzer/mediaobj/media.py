__author__ = 'Dennis Wallace'

from deefuzzer.mediaobj import *
import mutagen
import mimetypes
import os


class Media:
    """
    Static class for interacting with media
    """

    def __init__(self):
        pass

    @staticmethod
    def new(filepath):
        """
        Gets a media object that contains a file reference, metadata, and common useful methods for a given file .
        If the given path does not match a known media type, the None value is returned.  Known types: MP3, OOG, WebM

        :param filepath: The path to a folder or playlist file
        :return: The media object for the given path, or None if no valid media of a known type was found.
        """
        try:
            if not os.path.exists(filepath):
                return None

            if os.path.isdir(filepath):
                return None

            root, ext = os.path.splitext(filepath)
            ext = ext.lower()
            mime = mimetypes.guess_type(filepath)

            if ext == 'mp3' or 'audio/mpeg' in mime:
                return Mp3(filepath)

            if ext == 'ogg' or 'audio/ogg' in mime:
                return Ogg(filepath)

            if ext == 'webm' or 'video/webm' in mime:
                return WebM(filepath)
        except:
            pass

        return None

    @staticmethod
    def folder_contains_audio(folder):
        """
        Checks a path for any audio files.
        :param folder: Path to check for audio files
        :return: True if any supported audio files are found in the folder, False if not.
        """
        files = os.listdir(folder)
        for fn in files:
            filepath = os.path.join(folder, fn)
            if Media.isaudio(filepath):
                return True
        return False

    @staticmethod
    def isaudio(filepath, mimetype=""):
        """
        Detects if the given file path is a supported audio file, or
        :param filepath: The path to check
        :param mimetype: An optional mimetype to match.
        :return: True if the file is a supported audio file type (or matches the mimetype if given), False if not.
        """
        if not os.path.isfile(filepath):
            return False

        fileref = mutagen.File(filepath)
        if not fileref:
            return False
        filetype = fileref.mime

        if mimetype:
            return mimetype in filetype

        if 'audio/mpeg' in filetype:
            return True
        if 'audio/ogg' in filetype:
            return True
        # Add detection for more file types as needed here
        return False

    @staticmethod
    def get_mimetype(ext):
        """
        Returns the mime type to use as a filter in the Playlist.new method, given a filename extension or mime type.
        :param ext: The name to look up
        :return: The mime type to use
        """
        types = {mp3: "mpeg/audio", ogg: "audio/ogg", webm: "video/webm"}
        if ext in types:
            return types[ext]

        types = ["mpeg/audio", "audio/ogg", "video/webm"]
        if ext in types:
            return types[ext]

        return ""

    @staticmethod
    def get_mediatype(mime):
        """
        Returns the media type, given a mime type or filename extension.
        :param mime: The type to look up
        :return: The media type to use
        """
        types = {"mpeg/audio": "mp3", "audio/ogg": "ogg", "video/webm": "webm"}
        if mime in types:
            return types[mime]

        types = ["mp3", "ogg", "webm"]
        if mime in types:
            return types[mime]

        return ""
