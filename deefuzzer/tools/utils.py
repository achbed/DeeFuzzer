#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2007-2009 Guillaume Pellerin <yomguy@parisson.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution. The terms
# are also available at http://svn.parisson.org/deefuzz/wiki/DefuzzLicense.
#
# Author: Guillaume Pellerin <yomguy@parisson.com>

import os
import mimetypes
import re
import string
from itertools import *
from deefuzzer.tools.xmltodict import *

mimetypes.add_type('application/x-yaml', '.yaml')


def path_strip_parents(path):
    """
    Strips all parent directory requests from a path.  Prevents attacks like ../../../../etc/passwd
    :param path: The path to check
    :return: The cleaned path
    """
    newpath = None
    base = path
    while base:
        base, tail = os.path.split(base)
        if tail:
            if tail not in [".", ".."]:
                if newpath:
                    newpath = os.path.join(tail, newpath)
                else:
                    newpath = tail

    return newpath


def clean_word(word):
    """
    Cleans a string to remove excess whitespace and certain characters that may cause issues with export functions
    Specifically, replaces any instances of &[];"*:, with an underscore, and strips all characters that do not match
    the regex definition of a word (\w).
    :param word: The word to clean
    :return: The cleaned word
    """
    word = re.sub("^[^\w]+", "", word)  # trim the beginning
    word = re.sub("[^\w]+$", "", word)  # trim the end
    word = re.sub("_+", "_", word)  # squeeze continuous _ to one _
    # word = re.sub("^[^\w]+", "", word)  # trim the beginning _
    # word = string.replace(word,' ','_')
    # word = string.capitalize(word)
    conv_dict = '&[];"*:,'
    for letter in conv_dict:
        word = string.replace(word, letter, '_')
    return word


def get_file_info(filepath):
    """
    Returns the filename (name + extension), filetitle (name only) and extension as three-part return value. Uses
    the os.path functions to provide cross-platform support
    :param filepath:
    :return: (filename, filetitle, extension)
    """
    (folder, file_name) = os.path.split(filepath)
    (file_title, file_ext) = os.path.splitext(file_name)
    return file_name, file_title, file_ext


def merge_dict(replacement_keys, original_keys):
    """
    Combines all keys for two dict objects.  Recursively scans all sub-dicts (if present) for replacements as well.
    :param replacement_keys: The dict containing keys to overwrite into the base
    :param original_keys: The dict to use as a base
    :return: A newly combined dict object
    """
    combined = {}
    for key in set(chain(replacement_keys, original_keys)):
        if key in replacement_keys:
            if key in original_keys:
                if isinstance(replacement_keys[key], dict) and isinstance(original_keys[key], dict):
                    combined[key] = merge_dict(replacement_keys[key], original_keys[key])
                else:
                    combined[key] = replacement_keys[key]
            else:
                combined[key] = replacement_keys[key]
        else:
            combined[key] = original_keys[key]
    return combined


def replace_all(source, repl, tags=None):
    """
    Performs a search and replace on a given object, using a dict of possible replacements.  If a list or dict
    if given, then all values within the list or dict are scanned for strings to perform replacement on.
    :param source: The object to search
    :param repl: A dict continaing search and replace data.  Keys will be used to match, values will be the replacements
    :param tags: A dict containing "open" and "close" tags to use during the search.  Defaults are open:"[", close:"]"
    :return: A new object with replacements performed
    """
    if not tags:
        tags = {}
    if "open" not in tags:
        tags["open"] = "["
    if "close" not in tags:
        tags["close"] = "]"

    output = source

    if isinstance(output, list):
        r = []
        for i in output:
            r.append(replace_all(i, repl))
        return r
    elif isinstance(output, dict):
        r = {}
        for key in output.keys():
            r[key] = replace_all(output[key], repl)
        return r
    elif isinstance(output, str):
        r = output
        for key in repl.keys():
            f = ("%s%s%s" % (tags["open"], key, tags["close"]))
            r = r.replace(f, repl[key])
        return r
    return output


def get_conf_dict(filepath):
    """
    Gets a dict object containing a configuration file
    :param filepath: The full path to the configuration file to load
    :return: A dict object with the configuration file contents
    """
    mime_type = mimetypes.guess_type(filepath)[0]

    # Do the type check first, so we don't load huge files that won't be used
    if 'xml' in mime_type:
        confile = open(filepath, 'r')
        data = confile.read()
        confile.close()
        return xmltodict(data, 'utf-8')
    elif 'yaml' in mime_type:
        import yaml

        def custom_str_constructor(loader, node):
            return loader.construct_scalar(node).encode('utf-8')

        yaml.add_constructor(u'tag:yaml.org,2002:str', custom_str_constructor)
        confile = open(filepath, 'r')
        data = confile.read()
        confile.close()
        return yaml.load(data)
    elif 'json' in mime_type:
        import json

        confile = open(filepath, 'r')
        data = confile.read()
        confile.close()
        return json.loads(data)

    return False


def get_md5(word):
    """
    Returns an MD5 hash using the best available hashing method.  Uses hashlib if available, with fallback to md5
    :param word: The string to hash
    :return: The hexdigest hash value
    """
    try:
        import hashlib
        return hashlib.md5(word).hexdigest()
    except:
        pass

    try:
        import md5
        a = md5.new()
        a.update(word)
        return a.hexdigest()
    except:
        pass

    return ""

def ping_url(url, timeout_connect=5, timeout_read=10):
    import pycurl

    c = pycurl.Curl()
    c.setopt(c.URL, url)
    c.setopt(c.CONNECTTIMEOUT, int(timeout_connect))
    c.setopt(c.TIMEOUT, int(timeout_read))
    c.setopt(c.FAILONERROR, True)
    try:
        c.perform()
    except:
        return False

    return True
