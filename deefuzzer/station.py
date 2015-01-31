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
from streamer import *
from tools import *


class Station(ThreadQueueLog):
    """a DeeFuzzer shouting station thread"""

    def __init__(self, station, lock_queue, log_queue, m3u):
        ThreadQueueLog.__init__(self, log_queue)
        
        self.new_tracks = []
        self.mediafile = ""
        self.jingle_id = 0
        self.jingles_mode = 0
        self.jingles_length = 0
        self.jingles_playlist = None
        self.next_media = 0
        self.twitter = None
        self.twitter_mode = 0
        self.rec_file = ""
        self.id = -1
        self.valid = False
        self.counter = -1
        self.delay = 0
        self.start_time = time.time()
        self.server_ping = False
        self.playlist = []
        self.source = None
        self.lp = 1
        self.player_mode = 1
        self.osc_control_mode = 0
        self.twitter_mode = 0
        self.jingles_mode = 0
        self.relay_mode = 0
        self.record_mode = 0
        self.run_mode = 1
        self.appendtype = 0
        self.feeds_json = 0
        self.feeds_rss = 1
        self.feeds_mode = 1
        self.feeds_playlist = 1
        self.feeds_showfilepath = 0
        self.feeds_showfilename = 0
        self.short_name = ''
        self.channelIsOpen = False
        self.starting_id = -1
        self.jingles_frequency = 2
        self.statusfile = ''
        self.base_directory = ''
        self.recorder = None
        self.m3u_url = ""
        self.feeds_url = ""
        self.stream = None
        self.prefix = ""
        self.title = ""
        self.artist = ""
        self.song = ""
        self.metadata_file = ""

        self.station = station
        self.q = lock_queue
        self.m3u = m3u

        self.current_media_obj = MediaBase()

        if 'station_statusfile' in self.station:
            self.statusfile = station['station_statusfile']
            try:
                if os.path.exists(self.statusfile):
                    f = open(self.statusfile, 'r')
                    self.starting_id = int(f.read())
                    f.close()
            except:
                pass

        if 'base_dir' in self.station:
            self.base_directory = self.station['base_dir'].strip()

        # Media
        if 'm3u' in self.station['media']:
            if not self.station['media']['m3u'].strip() == '':
                self.source = self._path_add_base(self.station['media']['m3u'])

        if 'dir' in self.station['media']:
            if not self.station['media']['dir'].strip() == '':
                self.source = self._path_add_base(self.station['media']['dir'])

        if 'source' in self.station['media']:
            if not self.station['media']['source'].strip() == '':
                self.source = self._path_add_base(self.station['media']['source'])

        self.media_format = self.station['media']['format']
        self.shuffle_mode = int(self.station['media']['shuffle'])
        self.bitrate = int(self.station['media']['bitrate'])
        self.ogg_quality = int(self.station['media']['ogg_quality'])
        self.samplerate = int(self.station['media']['samplerate'])
        self.voices = int(self.station['media']['voices'])

        # Server
        if 'mountpoint' in self.station['server']:
            self.mountpoint = self.station['server']['mountpoint']
        elif 'short_name' in self.station['infos']:
            self.mountpoint = self.station['infos']['short_name']
        else:
            self.mountpoint = 'default'

        self.short_name = self.mountpoint

        if 'appendtype' in self.station['server']:
            self.appendtype = int(self.station['server']['appendtype'])

        if 'type' in self.station['server']:
            self.type = self.station['server']['type']  # 'icecast' | 'stream-m'
        else:
            self.type = 'icecast'

        if 'stream-m' in self.type:
            self.channel = HTTPStreamer()
            self.channel.mount = '/publish/' + self.mountpoint
        elif 'icecast' in self.type:
            self.channel = shout.Shout()
            self.channel.mount = '/' + self.mountpoint
            if self.appendtype:
                self.channel.mount = self.channel.mount + '.' + self.media_format
        else:
            self.log_err('Not a compatible server type. Choose "stream-m" or "icecast".')
            return

        self.channel.url = self.station['infos']['url']
        self.channel.name = self.station['infos']['name']
        self.channel.genre = self.station['infos']['genre']
        self.channel.description = self.station['infos']['description']
        self.channel.format = self.media_format
        self.channel.host = self.station['server']['host']
        self.channel.port = int(self.station['server']['port'])
        self.channel.user = 'source'
        self.channel.password = self.station['server']['sourcepassword']
        self.channel.public = int(self.station['server']['public'])
        if self.channel.format == 'mp3':
            self.channel.audio_info = {'bitrate': str(self.bitrate),
                                       'samplerate': str(self.samplerate),
                                       'channels': str(self.voices), }
        else:
            self.channel.audio_info = {'bitrate': str(self.bitrate),
                                       'samplerate': str(self.samplerate),
                                       'quality': str(self.ogg_quality),
                                       'channels': str(self.voices), }

        self.server_url = 'http://' + self.channel.host + ':' + str(self.channel.port)
        self.channel_url = self.server_url + self.channel.mount

        # RSS
        if 'feeds' in self.station:
            self.station['rss'] = self.station['feeds']

        if 'rss' in self.station:
            if 'mode' in self.station['rss']:
                self.feeds_mode = int(self.station['rss']['mode'])
            self.feeds_dir = self._path_add_base(self.station['rss']['dir'])
            self.feeds_enclosure = int(self.station['rss']['enclosure'])
            if 'json' in self.station['rss']:
                self.feeds_json = int(self.station['rss']['json'])
            if 'rss' in self.station['rss']:
                self.feeds_rss = int(self.station['rss']['rss'])
            if 'playlist' in self.station['rss']:
                self.feeds_playlist = int(self.station['rss']['playlist'])
            if 'showfilename' in self.station['rss']:
                self.feeds_showfilename = int(self.station['rss']['showfilename'])
            if 'showfilepath' in self.station['rss']:
                self.feeds_showfilepath = int(self.station['rss']['showfilepath'])

            self.feeds_media_url = self.channel.url + '/media/'
            if 'media_url' in self.station['rss']:
                if not self.station['rss']['media_url'] == '':
                    self.feeds_media_url = self.station['rss']['media_url']

        self.base_name = self.feeds_dir + os.sep + self.short_name + '_' + self.channel.format
        self.feeds_current_file = self.base_name + '_current'
        self.feeds_playlist_file = self.base_name + '_playlist'

        # Logging
        self.log_info('Opening ' + self.short_name + ' - ' + self.channel.name)

        self.metadata_relative_dir = 'metadata'
        self.metadata_url = self.channel.url + '/rss/' + self.metadata_relative_dir
        self.metadata_dir = self.feeds_dir + os.sep + self.metadata_relative_dir
        if not os.path.exists(self.metadata_dir):
            os.makedirs(self.metadata_dir)

        # The station's player
        self.player = Player(self.type)

        # OSCing
        # mode = 0 means Off, mode = 1 means On
        if 'control' in self.station:
            self.osc_control_mode = int(self.station['control']['mode'])
            if self.osc_control_mode:
                self.osc_port = int(self.station['control']['port'])
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

        # Jingling between each media.
        if 'jingles' in self.station:
            if 'mode' in self.station['jingles']:
                self.jingles_mode = int(self.station['jingles']['mode'])
            if 'shuffle' in self.station['jingles']:
                self.jingles_shuffle = int(self.station['jingles']['shuffle'])
            if 'frequency' in self.station['jingles']:
                self.jingles_frequency = int(self.station['jingles']['frequency'])
            if 'dir' in self.station['jingles']:
                self.jingles_source = self._path_add_base(self.station['jingles']['dir'])
            if 'source' in self.station['jingles']:
                self.jingles_source = self._path_add_base(self.station['jingles']['source'])
            if self.jingles_mode == 1:
                self.jingles_callback('/jingles', [1])

        # Relaying
        if 'relay' in self.station:
            self.relay_mode = int(self.station['relay']['mode'])
            self.relay_url = self.station['relay']['url']
            self.relay_author = self.station['relay']['author']
            if self.relay_mode == 1:
                self.relay_callback('/media/relay', [1])

        # Twitting
        if 'twitter' in self.station:
            self.twitter_mode = int(self.station['twitter']['mode'])
            self.twitter_key = self.station['twitter']['key']
            self.twitter_secret = self.station['twitter']['secret']
            self.twitter_tags = self.station['twitter']['tags'].split(' ')
            try:
                self.twitter_messages = self.station['twitter']['message']
                if isinstance(self.twitter_messages, dict):
                    self.twitter_messages = list(self.twitter_messages)
            except:
                pass

            if self.twitter_mode:
                self.twitter_callback('/twitter', [1])

        # Recording
        if 'record' in self.station:
            self.record_mode = int(self.station['record']['mode'])
            self.record_dir = self._path_add_base(self.station['record']['dir'])
            if self.record_mode:
                self.record_callback('/record', [1])

        self.valid = True

    def log_msg_hook(self, msg):
        return 'Station %s: %s' % (str(self.channel_url), str(msg))
        
    def _path_add_base(self, a):
        self.log_debug('_path_add_base: Attempting to join "%s" and "%s"' % (self.base_directory, a))
        r = path_strip_parents(os.path.join(self.base_directory, a))
        self.log_debug('_path_add_base: Result is "%s"' % r)
        return r

    def _path_m3u_rel(self, a):
        self.log_debug('_path_m3u_rel: Attempting to join "%s" and "%s"' % (os.path.dirname(self.source), a))
        r = os.path.join(os.path.dirname(self.source), a)
        self.log_debug('_path_m3u_rel: Result is "%s"' % r)
        return r

    def init_jingles(self):
        if not self.jingles_playlist:
            self.jingles_mode = 0
            self.jingles_length = 0
            self.jingles_playlist = None
            try:
                self.jingles_playlist = self.get_playlist(self.jingles_source)
                if self.jingles_shuffle:
                    self.jingles_playlist.shuffle()
                self.jingles_length = len(self.jingles_playlist)
                self.jingles_playlist.frequency = self.jingles_frequency
            except:
                pass
            return

        if self.jingles_playlist.stale():
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
                media_file = new_media(os.path.join(self.record_dir, self.rec_file))
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
            file_list = new_playlist(source)
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

    def get_next_media(self):
        # Init playlist
        if not self.playlist:
            # Attempt to init the playlist if there isn't one already.
            self.playlist = self.get_playlist()

        if not self.playlist:
            # We still do not have a valid playlist object.  Bail immediately
            self.log_err('Error getting a playlist object!')
            self.run_mode = 0
            return None

        if not len(self.playlist):
            # We still do not have a valid playlist object.  Bail immediately
            self.log_err('There is no media to play!')
            self.run_mode = 0
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

        if self.playlist.stale():
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
        self.init_jingles()
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
                file_meta = new_media(mediapath)

                if not file_meta:
                    self.log_err('Could not get specific media type class for %s' % mediapath)
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
            self.log_err('Twitting : "' + message + '"')

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
            self.log_err('channel could not be opened')

        return False

    def channel_close(self):
        self.channelIsOpen = False
        try:
            self.channel.close()
            self.log_info('channel closed')
        except:
            self.log_err('channel could not be closed')

    def ping_server(self):
        log = True

        while not self.server_ping:
            try:
                server = urllib.urlopen(self.server_url)
                self.server_ping = True
                self.log_info('Channel available.')
            except:
                time.sleep(1)
                if log:
                    self.log_err('Could not connect the channel.  Waiting for channel to become available.')
                    log = False

    def icecastloop_nextmedia(self):
        try:
            self.mediafile = self.get_next_media()
            self.counter += 1
            self.counter = (self.counter % self.jingles_frequency) + self.jingles_frequency
            if self.relay_mode:
                self.set_relay_mode()
            elif os.path.exists(self.mediafile) and not os.sep + '.' in self.mediafile:
                if self.lp == 0:
                    self.log_err('has no media to stream !')
                    return False
                self.set_read_mode()

            return True
        except Exception, e:
            self.log_err('icecastloop_nextmedia: Error: ' + str(e))
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
            self.log_err('icecastloop_metadata: Error: ' + str(e))
        return False

    def run(self):
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
                                self.log_err('could not write the buffer to the file')

                        try:
                            # Send the chunk to the stream
                            self.channel.send(self.chunk)
                            self.channel.sync()
                        except:
                            self.log_err('could not send the buffer')
                            self.channel_close()
                            if not self.channel_open():
                                self.log_err('could not restart the channel')
                                if self.record_mode:
                                    self.recorder.close()
                                return
                            try:
                                self.channel.set_metadata({'song': self.song, 'charset': 'utf8', })
                                self.log_info('channel restarted')
                                self.channel.send(self.chunk)
                                self.channel.sync()
                            except:
                                self.log_err('could not send data after restarting the channel')
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
