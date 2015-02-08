#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2006-2011 Guillaume Pellerin

# <yomguy@parisson.com>

# This software is a computer program whose purpose is to stream audio
# and video data through icecast2 servers.

# This software is governed by the CeCILL license under French law and
# abiding by the rules of distribution of free software. You can use,
# modify and/ or redistribute the software under the terms of the CeCILL
# license as circulated by CEA, CNRS and INRIA at the following URL
# "http://www.cecill.info".

# As a counterpart to the access to the source code and  rights to copy,
# modify and redistribute granted by the license, users are provided only
# with a limited warranty and the software's author, the holder of the
# economic rights, and the successive licensors have only limited
# liability.

# In this respect, the user's attention is drawn to the risks associated
# with loading, using,  modifying and/or developing or reproducing the
# software by the user in light of its specific status of free software,
# that may mean that it is complicated to manipulate, and that also
# therefore means that it is reserved for developers and  experienced
# professionals having in-depth computer knowledge. Users are therefore
# encouraged to load and test the software's suitability as regards their
# requirements in conditions enabling the security of their systems and/or
# data to be ensured and, more generally, to use and operate it in the
# same conditions as regards security.

# The fact that you are presently reading this means that you have had
# knowledge of the CeCILL license and that you accept its terms.

# Author: Guillaume Pellerin <yomguy@parisson.com>

import os
import sys
import time
import datetime
import string
import random
import shout
import urllib
import mimetypes
import json

from threading import Thread
from player import *
from recorder import *
from relay import *
from tools import *
from playlistobj import *
from mediaobj import *
from streamer import *


class Station(Thread, LogCommon, ConfigReader):
    """a DeeFuzzer shouting station thread"""

    def log_msg_hook(self, msg):
        """
        Implement this in child classes to alter the log message before output.  Useful to prepend a class name
        or identifier for code tracing.
        :param msg: The message to alter
        :return: The message to log
        """
        return 'Station %s: %s' % (self.short_name, str(msg))

    def __init__(self, station, lock_queue, log_queue, m3u):
        """
        Initialization for the station instance.
        :param station: The configuration for this station.  Must be a dict object.
        :param lock_queue: A Queue used for locking when file writes occurr
        :param log_queue: A Queue used to send messages to the main log
        :param m3u: The path to an output M3U file for this station
        :return:
        """
        Thread.__init__(self)
        LogCommon.__init__(self)
        ConfigReader.__init__(self, station)
        
        self.logqueue = log_queue
        self.q = lock_queue
        self.m3u = m3u

        self.log_debug("Starting station init")

        self.__valid_types = ['icecast', 'stream-m']

        self.statusfile = ''
        self.base_directory = ''

        self.source = ''
        self.typefilter = ''
        self.media_format = ''

        self.shuffle_mode = 0
        self.bitrate = 0
        self.ogg_quality = 0
        self.samplerate = 0
        self.voices = 2

        self.mountpoint = 'default'
        self.short_name = ''
        self.appendtype = 0
        self.type = 'icecast'

        self.chan_url = ''
        self.chan_name = ''
        self.chan_genre = ''
        self.chan_description = ''
        self.chan_host = ''
        self.chan_port = 80
        self.chan_user = 'source'
        self.chan_pass = ''
        self.chan_public = 0

        self.new_tracks = []
        self.mediafile = ""
        self.jingle_id = 0
        self.jingles_mode = 0
        self.jingles_length = 0
        self.jingles_source = ''
        self.jingles_playlist = None

        self.feeds_mode = 1
        self.feeds_dir = ''
        self.feeds_enclosure = 0
        self.feeds_json = 0
        self.feeds_rss = 1
        self.feeds_playlist = 1
        self.feeds_showfilepath = 0
        self.feeds_showfilename = 0
        self.feeds_media_url = ''
        self.feeds_current_file = ''
        self.feeds_playlist_file = ''

        self.metadata_relative_dir = 'metadata'
        self.metadata_url = ''
        self.metadata_dir = ''

        self.osc_controller = None
        self.osc_control_mode = 0
        self.osc_port = 16001

        self.relay_mode = 0
        self.relay_url = ''
        self.relay_author = ''

        self.player = None

        self.twitter = None
        self.twitter_mode = 0
        self.twitter_key = ''
        self.twitter_secret = ''
        self.twitter_tags = ''
        self.twitter_messages = []

        self.next_media = 0
        self.rec_file = ""
        self.id = -1
        self.valid = False
        self.counter = -1
        self.delay = 0
        self.start_time = time.time()
        self.server_ping = False
        self.playlist = PlaylistEmpty()
        self.lp = 1
        self.player_mode = 1

        self.record_mode = 0
        self.run_mode = 1
        self.channelIsOpen = False
        self.starting_id = -1
        self.jingles_frequency = 10
        self.statusfile = ''
        self.recorder = None
        self.m3u_url = ""
        self.feeds_url = ""
        self.stream = None
        self.prefix = ""
        self.title = ""
        self.artist = ""
        self.song = ""
        self.metadata_file = ""
        self.channel_delay = 0
        self.current_media_obj = None
        self.channel = None

        self.setup()

    def setup(self):
        """
        Loads the values from the configuration into the correct places
        :return:
        """
        # Start with the status file
        self.log_debug("Init: Getting station_statusfile")
        self.statusfile = self.option(['station_statusfile'], self.statusfile)
        try:
            if os.path.exists(self.statusfile):
                f = open(self.statusfile, 'r')
                self.starting_id = int(f.read())
                f.close()
        except:
            pass

        # Base directory up front (so we can use it with other settings)
        self.log_debug("Init: Getting base_dir")
        self.base_directory = self.option(['base_dir'], self.base_directory)

        # Media Source
        self.log_debug("Init: Getting source")
        c = self.option(['media', 'm3u'], self.source)
        c = self.option(['media', 'dir'], c)
        c = self.option(['media', 'source'], c)
        if c:
            self.source = self._path_add_base(c)

        # Media Format
        self.log_debug("Init: Getting media format")
        if 'format' in self.station['media']:
            self.typefilter = Media.get_mimetype(self.option(['media', 'format'], self.typefilter))

        self.log_debug("Init: Getting media settings")
        self.shuffle_mode = int(self.option(['media', 'shuffle'], self.shuffle_mode))
        self.bitrate = int(self.option(['media', 'bitrate'], self.bitrate))
        self.ogg_quality = int(self.option(['media', 'ogg_quality'], self.ogg_quality))
        self.samplerate = int(self.option(['media', 'samplerate'], self.samplerate))
        self.voices = int(self.option(['media', 'voices'], self.voices))

        # Mountpoint info and naming
        self.log_debug("Init: Getting mountpoint")
        self.mountpoint = self.option(['infos', 'short_name'], self.mountpoint)
        self.mountpoint = self.option(['server', 'mountpoint'], self.mountpoint)

        self.short_name = self.mountpoint
        self.short_name = self.option(['infos', 'short_name'], self.short_name)

        self.appendtype = int(self.option(['server', 'appendtype'], self.appendtype))

        c = str(self.option(['server', 'type'], self.type)).lower()
        if c in self.__valid_types:
            self.type = c

        # Jingling between each media.
        self.log_debug("Init: Getting jingles")
        self.jingles_mode = int(self.option(['jingles', 'mode'], self.jingles_mode))
        self.jingles_source = int(self.option(['jingles', 'dir'], self.jingles_source))
        self.jingles_source = int(self.option(['jingles', 'source'], self.jingles_source))
        c = int(self.option(['jingles', 'frequency'], self.jingles_frequency))
        if c > 1:
            self.jingles_frequency = c

        if self.jingles_mode == 1:
            self.jingles_callback('/jingles', [1])

        self.chan_url = self.option(['infos', 'url'], self.chan_url)
        self.chan_name = self.option(['infos', 'name'], self.chan_name)
        self.chan_genre = self.option(['infos', 'genre'], self.chan_genre)
        self.chan_description = self.option(['infos', 'description'], self.chan_description)
        self.chan_host = self.option(['infos', 'host'], self.chan_host)
        self.chan_port = int(self.option(['infos', 'port'], self.chan_port))
        self.chan_user = self.option(['infos', 'sourceusername'], self.chan_user)
        self.chan_pass = self.option(['infos', 'sourcepassword'], self.chan_pass)
        self.chan_public = self.option(['infos', 'public'], self.chan_public)

        # RSS
        self.feeds_mode = int(self.option([['feeds', 'rss'], 'mode'], self.feeds_mode))

        self.feeds_dir = self.option([['feeds', 'rss'], 'dir'], self.feeds_mode)
        self.feeds_dir = self._path_add_base(self.feeds_dir)

        self.feeds_enclosure = int(self.option([['feeds', 'rss'], 'enclosure'], self.feeds_enclosure))
        self.feeds_json = int(self.option([['feeds', 'rss'], 'json'], self.feeds_json))
        self.feeds_rss = int(self.option([['feeds', 'rss'], 'rss'], self.feeds_rss))
        self.feeds_playlist = int(self.option([['feeds', 'rss'], 'playlist'], self.feeds_playlist))
        self.feeds_showfilename = int(self.option([['feeds', 'rss'], 'showfilename'], self.feeds_showfilename))
        self.feeds_showfilepath = int(self.option([['feeds', 'rss'], 'showfilepath'], self.feeds_showfilepath))
        self.feeds_media_url = '%s/media/' % self.channel_url()
        self.feeds_media_url = self.option([['feeds', 'rss'], 'media_url'], self.feeds_media_url)

        self.osc_control_mode = int(self.option(['control', 'mode'], self.osc_control_mode))
        self.osc_port = int(self.option(['control', 'port'], self.osc_port))

        self.relay_mode = int(self.option(['relay', 'mode'], self.relay_mode))
        self.relay_url = self.option(['relay', 'url'], self.relay_url)
        self.relay_author = self.option(['relay', 'author'], self.relay_author)

        self.twitter_mode = int(self.option(['twitter', 'mode'], self.twitter_mode))
        self.twitter_key = self.option(['twitter', 'key'], self.twitter_key)
        self.twitter_secret = self.option(['twitter', 'secret'], self.twitter_secret)
        c = self.option(['twitter', 'tags'], self.twitter_tags)
        self.twitter_tags = c.split(' ')
        c = self.option(['twitter', 'message'], self.twitter_messages)
        if isinstance(c, dict) or isinstance(c, list):
            self.twitter_messages = list(c)
        else:
            self.twitter_messages = [c]

        self.valid = True

    def init_objects(self):
        """
        Initializes the internal objects.  Should be called after the thread is started.
        :return: Nothing
        """
        # Initialize the playlists now
        self.init_playlists()

        # The station's player
        self.player = Player(self.type)

        # Set these AFTER we've loaded the playlist (so we get the correct data)
        self.media_format = Media.get_mediatype(self.typefilter)
        feeds_base_name = os.path.join(self.feeds_dir, (self.short_name + '_' + self.media_format))
        self.feeds_current_file = feeds_base_name + '_current'
        self.feeds_playlist_file = feeds_base_name + '_playlist'

        # Initialize the channel object, and bail if we encounter an issue
        if not self.channel_init():
            self.valid = False
            return

        self.metadata_url = '%s/rss/%s' % (self.channel_url(), self.metadata_relative_dir)
        self.metadata_dir = os.path.join(self.feeds_dir, self.metadata_relative_dir)
        if not os.path.exists(self.metadata_dir):
            os.makedirs(self.metadata_dir)

        # OSCing
        # mode = 0 means Off, mode = 1 means On
        if self.osc_control_mode:
            self.osc_controller = OSCController(self.osc_port)
            # OSC paths and callbacks
            self.osc_controller.add_method('/media/next', 'i', self.media_next_callback)
            self.osc_controller.add_method('/media/prev', 'i', self.media_prev_callback)
            self.osc_controller.add_method('/media/relay', 'i', self.relay_callback)
            self.osc_controller.add_method('/twitter', 'i', self.twitter_callback)
            self.osc_controller.add_method('/jingles', 'i', self.jingles_callback)
            self.osc_controller.add_method('/record', 'i', self.record_callback)
            self.osc_controller.add_method('/player', 'i', self.player_callback)
            self.osc_controller.add_method('/run', 'i', self.run_callback)
            self.osc_controller.start()

        # Relaying
        if self.relay_mode:
            self.relay_callback('/media/relay', [1])

        # Twitting
        if self.twitter_mode:
            self.twitter_callback('/twitter', [1])

        # Recording
        if self.record_mode:
            self.record_callback('/record', [1])

    def server_url(self):
        r = '%s://%s' % (self.chan_method, self.chan_host)
        if self.chan_port <> 80:
            r += (':%d' % self.chan_port)
        return r

    def channel_url(self):
        return self.server_url() + '/' + self.get_mountpoint()

    def get_mountpoint(self):
        if 'stream-m' in self.type:
            return '/publish/' + self.mountpoint
        if 'icecast' in self.type:
            if self.appendtype and self.media_format:
                return '/' + self.mountpoint + '.' + self.media_format
            return '/' + self.mountpoint
        return ''

    def channel_init(self):
        if 'stream-m' in self.type:
            self.channel = HTTPStreamer()
        elif 'icecast' in self.type:
            self.channel = shout.Shout()
        else:
            self.log_error('Not a compatible server type. Choose "stream-m" or "icecast".')
            return False

        self.channel.mount = self.get_mountpoint()

        self.channel.url = self.chan_url
        self.channel.name = self.chan_name
        self.channel.genre = self.chan_genre
        self.channel.description = self.chan_description
        self.channel.host = self.chan_host
        self.channel.port = self.chan_port
        self.channel.user = self.chan_user
        self.channel.password = self.chan_pass
        self.channel.public = self.chan_public

        self.channel.format = self.media_format
        self.channel.audio_info = {'bitrate': str(self.bitrate),
                                   'samplerate': str(self.samplerate),
                                   'channels': str(self.voices), }
        if self.channel.format == 'ogg':
            self.channel.audio_info['quality'] = str(self.ogg_quality)

        return True

    def _path_add_base(self, a):
        r = path_strip_parents(os.path.join(self.base_directory, a))
        return r

    def _path_m3u_rel(self, a):
        r = os.path.join(os.path.dirname(self.source), a)
        return r

    def init_jingles(self):
        self.log_debug("Init: Initializing jingles")
        if not self.jingles_playlist:
            self.jingles_length = 0
            self.jingles_playlist = None
            try:
                self.jingles_playlist = self.get_playlist(self.jingles_source)
                if not self.jingles_playlist:
                    self.jingles_mode = 0
                    return

                if self.jingles_shuffle:
                    self.jingles_playlist.shuffle()
                self.jingles_length = len(self.jingles_playlist)
                self.jingles_playlist.frequency = self.jingles_frequency
            except:
                self.jingles_mode = 0
            return

        if self.jingles_playlist.isstale():
            self.jingles_playlist.read_playlist()
            if self.jingles_shuffle:
                self.jingles_playlist.shuffle()
            self.jingles_length = len(self.jingles_playlist)
            self.jingles_playlist.frequency = self.jingles_frequency

    def run_callback(self, path, value):
        value = value[0]
        self.run_mode = value
        message = "received OSC message '%s' with arguments '%d'" % (path, value)
        self.log_info(message)

    def media_prev_callback(self, path, value):
        if not self.relay_mode:
            self.next_media = -1
        message = "received OSC message '%s' with arguments '%d'" % (path, value)
        self.log_info(message)

    def media_next_callback(self, path, value):
        if not self.relay_mode:
            self.next_media = 1
        message = "received OSC message '%s' with arguments '%d'" % (path, value)
        self.log_info(message)

    def relay_callback(self, path, value):
        value = value[0]
        if value:
            self.relay_mode = 1
            if self.type == 'icecast':
                self.player.start_relay(self.relay_url)
        else:
            self.relay_mode = 0
            if self.type == 'icecast':
                self.player.stop_relay()

        self.id = 0
        self.next_media = 1
        message = "received OSC message '%s' with arguments '%d'" % (path, value)
        self.log_info(message)
        message = "relaying : %s" % self.relay_url
        self.log_info(message)

    def twitter_callback(self, path, value):
        value = value[0]
        self.twitter = Twitter(self.twitter_key, self.twitter_secret)
        self.twitter_mode = value
        message = "received OSC message '%s' with arguments '%d'" % (path, value)

        # IMPROVEMENT: The URL paths should be configurable because they're 
        # server-implementation specific
        self.m3u_url = self.channel.url + '/m3u/' + self.m3u.split(os.sep)[-1]
        self.feeds_url = self.channel.url + '/rss/' + self.feeds_playlist_file.split(os.sep)[-1]
        self.log_info(message)

    def jingles_callback(self, path, value):
        value = value[0]
        self.init_jingles()
        self.jingles_mode = value
        message = "received OSC message '%s' with arguments '%d'" % (path, value)
        self.log_info(message)

    def record_callback(self, path, value):
        value = value[0]
        if value:
            if not os.path.exists(self.record_dir):
                os.makedirs(self.record_dir)
            self.rec_file = self.short_name.replace('/', '_') + '-'
            self.rec_file += datetime.datetime.now().strftime("%x-%X").replace('/', '_')
            self.rec_file += '.' + self.channel.format
            self.recorder = Recorder(self.record_dir)
            self.recorder.open(self.rec_file)
        else:
            try:
                self.recorder.recording = False
                self.recorder.close()
            except:
                pass

            if self.type == 'icecast':
                date = datetime.datetime.now().strftime("%Y")
                media_file = Media.new(os.path.join(self.record_dir, self.rec_file))
                if media_file:
                    media_file.metadata = {'artist': self.artist.encode('utf-8'),
                                           'title': self.title.encode('utf-8'),
                                           'album': self.short_name.encode('utf-8'),
                                           'genre': self.channel.genre.encode('utf-8'),
                                           'date': date.encode('utf-8'), }
                    media_file.write_tags()

        self.record_mode = value
        message = "received OSC message '%s' with arguments '%d'" % (path, value)
        self.log_info(message)

    def player_callback(self, path, value):
        value = value[0]
        self.player_mode = value
        message = "received OSC message '%s' with arguments '%d'" % (path, value)
        self.log_info(message)

    def get_playlist(self, source=None):
        file_list = None
        if not source:
            source = self.source

        self.q.get(1)
        try:
            file_list = Playlist.new(source, self.typefilter)

            # If we didn't start with a filter, get what the playlist just used apply that
            if not self.typefilter and file_list:
                self.typefilter = file_list.filter
        except:
            pass
        self.q.task_done()

        return file_list

    def tweet(self):
        if len(self.new_tracks):
            new_tracks_objs = self.media_to_objs(self.new_tracks)
            for media_obj in new_tracks_objs:
                title, artist, song = self.get_songmeta(media_obj)

                artist_names = artist.split(' ')
                artist_tags = ' #'.join(list(set(artist_names) - {'&', '-'}))
                message = '#NEWTRACK ! %s %s on #%s' % \
                          (song, artist_tags.strip(), self.short_name)
                message = message[:113] + self.feeds_url
                self.update_twitter(message)

    def init_playlists(self):
        self.log_debug("Init: Initializing playlists")
        # Init playlist
        if not self.playlist:
            # Attempt to init the playlist if there isn't one already.
            self.playlist = self.get_playlist()

        if not self.playlist:
            # We still do not have a valid playlist object.  Bail immediately
            self.log_error('Error getting a playlist object!')
            self.run_mode = 0
            return False

        if not len(self.playlist):
            # We still do not have a valid playlist object.  Bail immediately
            self.log_error('There is no media to play!')
            self.run_mode = 0
            return False

        # Initialize the jingle playlist now too
        self.init_jingles()

        self.log_debug("Init: Finished playlist initialization")
        return True

    def get_next_media(self):
        if not self.init_playlists():
            return None

        if self.counter < 0:
            # We don't have a counter value, so we haven't started yet.
            self.id = 0
            self.lp = len(self.playlist)
            if -1 < self.starting_id < self.lp:
                self.id = self.starting_id

            # Shake it, Fuzz it !
            if self.shuffle_mode:
                self.playlist.shuffle()

            self.log_info('Generated playlist (%d tracks)' % self.lp)

        self.new_tracks = []

        if self.playlist.isstale():
            # Twitting new tracks
            playlist_set = self.playlist.file_list
            self.playlist.read_playlist()
            new_playlist_set = self.playlist.file_list
            new_tracks = new_playlist_set - playlist_set
            self.new_tracks = list(new_tracks.copy())

            if self.twitter_mode == 1 and self.counter:
                self.tweet()

            # Get the new playlist length
            self.lp = len(self.playlist)

            # Update the playlist feed
            if self.feeds_playlist:
                self.update_feeds(self.media_to_objs(self.playlist.file_list), self.feeds_playlist_file, '(playlist)')

            # Shake it, Fuzz it !
            if self.shuffle_mode:
                self.playlist.shuffle()

            # Play new tracks first - NEED NEW IMPLEMENTATION OF THIS
            # for track in self.new_tracks:
            #     playlist.insert(0, track)

            self.log_info('Updated playlist (%d tracks)' % self.lp)

        # Do the checks to see if we should Jingle!
        if self.jingles_playlist:
            should_jingle = self.jingles_playlist.should_play(self.counter)
            if not self.jingles_mode:
                should_jingle = False

            if should_jingle:
                self.jingle_id = self.jingles_playlist.next()
                self.__save_state()
                self.current_media_obj = self.jingles_playlist.current_track
                return self.jingles_playlist.file_list[self.jingle_id]

        if self.next_media > 0:
            self.id = self.playlist.next()
        if self.next_media < 0:
            self.id = self.playlist.prev()
        self.next_media = 0
        self.__save_state()
        self.current_media_obj = self.playlist.current_track
        return self.playlist.file_list[self.id]

    def __save_state(self):
        self.q.get(1)
        try:
            f = open(self.statusfile, 'w')
            f.write(str(self.id))
            f.close()
        except:
            pass
        self.q.task_done()

    def media_to_objs(self, media_list):
        media_objs = []
        self.q.get(1)
        try:
            for mediapath in media_list:
                file_meta = Media.new(mediapath)

                if not file_meta:
                    self.log_error('Could not get specific media type class for %s' % mediapath)
                    continue

                media_objs.append(file_meta)
        except:
            pass
        self.q.task_done()

        return media_objs

    def update_feeds(self, media_list, rss_file, sub_title):
        if not self.feeds_mode:
            return

        rss_item_list = []
        if not os.path.exists(self.feeds_dir):
            os.makedirs(self.feeds_dir)
        channel_subtitle = self.channel.name + ' ' + sub_title
        _date_now = datetime.datetime.now()
        date_now = str(_date_now)
        media_absolute_playtime = _date_now
        json_data = []

        for media_file in media_list:
            json_item = {}
            media_stats = os.stat(media_file.media)
            media_date = time.localtime(media_stats[8])
            media_date = time.strftime("%a, %d %b %Y %H:%M:%S +0200", media_date)
            media_file.metadata['Duration'] = str(media_file.length).split('.')[0]
            media_file.metadata['Bitrate'] = str(media_file.bitrate) + ' kbps'
            media_file.metadata['Next play'] = str(media_absolute_playtime).split('.')[0]

            media_description = '<table>'
            media_description_item = '<tr><td>%s:   </td><td><b>%s</b></td></tr>'

            for key in media_file.metadata.keys():
                if media_file.metadata[key] != '':
                    if key == 'filepath' and not self.feeds_showfilepath:
                        continue
                    if key == 'filename' and not self.feeds_showfilename:
                        continue
                    media_description += media_description_item % (key.capitalize(),
                                                                   media_file.metadata[key])
                    json_item[key] = media_file.metadata[key]
            if self.feeds_showfilepath:
                media_description += media_description_item % ('Filepath', media_file.media)
                json_item['filepath'] = media_file.media
            if self.feeds_showfilename:
                media_description += media_description_item % ('Filename', media_file.file_name)
                json_item['filename'] = media_file.file_name
            media_description += '</table>'

            title, artist, song = self.get_songmeta(media_file)
            media_absolute_playtime += media_file.length

            if self.feeds_enclosure == '1':
                media_link = self.feeds_media_url + media_file.file_name
                media_link = media_link.decode('utf-8')
                rss_item_list.append(RSSItem(
                    title=song,
                    link=media_link,
                    description=media_description,
                    enclosure=Enclosure(media_link, str(media_file.size), 'audio/mpeg'),
                    guid=Guid(media_link),
                    pubDate=media_date, )
                )
            else:
                media_link = self.metadata_url + '/' + media_file.file_name + '.xml'
                try:
                    media_link = media_link.decode('utf-8')
                except:
                    continue
                rss_item_list.append(RSSItem(
                    title=song,
                    link=media_link,
                    description=media_description,
                    guid=Guid(media_link),
                    pubDate=media_date, )
                )
            json_data.append(json_item)

        rss = RSS2(title=channel_subtitle,
                   link=self.channel.url,
                   description=self.channel.description.decode('utf-8'),
                   lastBuildDate=date_now,
                   items=rss_item_list, )
        self.q.get(1)
        try:
            if self.feeds_rss:
                f = open(rss_file + '.xml', 'w')
                rss.write_xml(f, 'utf-8')
                f.close()
        except:
            pass

        try:
            if self.feeds_json:
                f = open(rss_file + '.json', 'w')
                f.write(json.dumps(json_data, separators=(',', ':')))
                f.close()
        except:
            pass
        self.q.task_done()

    def update_twitter(self, message):
        try:
            self.twitter.post(message.decode('utf8'))
            self.log_info('Twitting : "' + message + '"')
        except:
            self.log_error('Twitting : "' + message + '"')

    def set_relay_mode(self):
        self.prefix = '#nowplaying #LIVE'
        self.get_songmeta()

        if self.type == 'stream-m':
            relay = URLReader(self.relay_url)
            self.channel.set_callback(relay.read_callback)
            if self.record_mode:
                relay.set_recorder(self.recorder)
        else:
            self.stream = self.player.relay_read()

    def get_songmeta(self, mediaobj=None):
        selfmode = False
        if not mediaobj:
            mediaobj = self.current_media_obj
            selfmode = True

        title = ""
        artist = ""
        song = ""

        try:
            title = mediaobj.get_title()
            artist = mediaobj.get_artist()
            song = mediaobj.get_song(True)
        except:
            pass

        if selfmode:
            self.title = title
            self.artist = artist
            self.song = song

        return title, artist, song

    def set_read_mode(self):
        self.prefix = '#nowplaying'
        
        try:
            self.get_songmeta()
            fn = self.current_media_obj.file_name
            if fn:
                self.metadata_file = os.path.join(self.metadata_dir, (fn + '.xml'))
            self.update_feeds([self.current_media_obj], self.feeds_current_file, '(currently playing)')
            if fn:
                self.log_info('DeeFuzzing:  id = %s, name = %s' % (self.id, fn))
        except:
            pass
        self.player.set_media(self.mediafile)

        self.q.get(1)
        try:
            if self.player_mode:
                self.stream = self.player.file_read_slow()
            else:
                self.stream = self.player.file_read_fast()
        except:
            pass
        self.q.task_done()

    def set_webm_read_mode(self):
        self.channel.set_callback(FileReader(self.mediafile).read_callback)

    def update_twitter_current(self):
        if not self.__twitter_should_update():
            return
        message = '%s %s on #%s' % (self.prefix, self.song, self.short_name)
        tags = '#' + ' #'.join(self.twitter_tags)
        message = message + ' ' + tags
        message = message[:108] + ' M3U: ' + self.m3u_url
        self.update_twitter(message)

    def channel_open(self):
        if self.channelIsOpen:
            return True

        try:
            self.channel.open()
            self.channel_delay = self.channel.delay
            self.log_info('channel connected')
            self.channelIsOpen = True
            return True
        except:
            self.log_error('channel could not be opened')

        return False

    def channel_close(self):
        self.channelIsOpen = False
        try:
            self.channel.close()
            self.log_info('channel closed')
        except:
            self.log_error('channel could not be closed')

    def ping_server(self, maxtries=-1, reset=False):
        log = True

        if reset:
            self.server_ping = False

        this_try = maxtries
        while not self.server_ping and this_try != 0:
            try:
                this_try -= 1
                self.server_ping = ping_url(self.server_url())
            except:
                time.sleep(1)
                if log:
                    self.log_error('Could not connect the channel.  Waiting for channel to become available.')
                    log = False

        if self.server_ping:
            self.log_info('Channel available.')
        return self.server_ping

    def icecastloop_nextmedia(self):
        try:
            self.mediafile = self.get_next_media()
            self.counter += 1
            self.counter = (self.counter % self.jingles_frequency) + self.jingles_frequency
            if self.relay_mode:
                self.set_relay_mode()
            elif os.path.exists(self.mediafile) and not os.sep + '.' in self.mediafile:
                if self.lp == 0:
                    self.log_error('has no media to stream !')
                    return False
                self.set_read_mode()

            return True
        except Exception, e:
            self.log_error('icecastloop_nextmedia: Error: ' + str(e))
        return False

    def __twitter_should_update(self):
        """Returns whether or not an update should be sent to Twitter"""
        if not self.twitter_mode:
            # Twitter posting disabled.  Return false.
            return False

        if self.relay_mode:
            # We are in relay mode. Return true.
            return True

        if self.jingles_mode and (self.counter % self.jingles_frequency):
            # We should be playing a jingle, and we don't send jingles to Twitter.
            return False
        return True

    def icecastloop_metadata(self):
        try:
            self.update_twitter_current()
            self.channel.set_metadata({'song': self.song, 'charset': 'utf-8'})
            return True
        except Exception, e:
            self.log_error('icecastloop_metadata: Error: ' + str(e))
        return False

    def run(self):
        self.init_objects()
        self.ping_server()

        if self.type == 'stream-m':
            if self.relay_mode:
                self.set_relay_mode()
            else:
                self.mediafile = self.get_next_media()
                self.set_webm_read_mode()
            if not self.channel_open():
                return
            self.channel.start()

        if self.type == 'icecast':
            while True:  # Do this so that the handlers will still restart the stream
                while self.run_mode:
                    if not self.channel_open():
                        return

                    if not self.icecastloop_nextmedia():
                        self.log_info('Something wrong happened in icecastloop_nextmedia.  Ending.')
                        self.channel_close()
                        return

                    self.icecastloop_metadata()

                    # TEST MODE: Jump thru only the first chunk of each file
                    # first = True
                    for self.chunk in self.stream:
                        # if first:
                            # first = False
                        # else:
                            # break

                        if self.next_media or not self.run_mode:
                            break

                        if self.record_mode:
                            try:
                                # Record the chunk
                                self.recorder.write(self.chunk)
                            except:
                                self.log_error('could not write the buffer to the file')

                        try:
                            # Send the chunk to the stream
                            self.channel.send(self.chunk)
                            self.channel.sync()
                        except:
                            self.log_error('could not send the buffer')
                            self.channel_close()
                            if not self.channel_open():
                                self.log_error('could not restart the channel')
                                if self.record_mode:
                                    self.recorder.close()
                                return
                            try:
                                self.channel.set_metadata({'song': self.song, 'charset': 'utf8', })
                                self.log_info('channel restarted')
                                self.channel.send(self.chunk)
                                self.channel.sync()
                            except:
                                self.log_error('could not send data after restarting the channel')
                                self.channel_close()
                                if self.record_mode:
                                    self.recorder.close()
                                return

                                # send chunk loop end
                # while run_mode loop end

                self.log_info("Play mode ended. Stopping stream.")

                if self.record_mode:
                    self.recorder.close()

                self.channel_close()
                time.sleep(1)
