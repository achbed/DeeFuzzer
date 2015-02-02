__author__ = 'Dennis Wallace'

from deefuzzer.mediaobj import *
import mimetypes


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
    def isaudio(filepath):
        """
        Detects if the given file path is a supported audio file.
        :param filepath: The path to check
        :return: True if the file is a supported audio file type, False if not.
        """
        if not os.path.isfile(filepath):
            return False

        fileref = mutagen.File(filepath)
        if not fileref:
            return False
        mime_type = fileref.mime
        if 'audio/mpeg' in mime_type:
            return True
        if 'audio/ogg' in mime_type:
            return True
        # Add detection for more file types as needed here
        return False
