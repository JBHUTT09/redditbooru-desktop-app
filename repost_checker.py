__author__ = 'John Huttlinger'

import os
import requests
import time
from queue import Queue


class RepostChecker(object):

    def __init__(self):
        self.base_directory = 'C:\\Users\\John\\PycharmProjects\\repost_checker\\'
        self.ext_to_content_type = {'.jpg': 'image/jpeg',
                                    '.jpeg': 'image/jpeg',
                                    '.png': 'image/png',
                                    '.gif': 'image/gif'}

        self.image_queue = Queue()
        self.posted_directory = None
        self.not_posted_directory = None
        self.subreddits = dict()
        self.user_settings = dict()

        self.load_subreddits()
        self.load_user_settings()

    # set source directory and populate image queue with directory contents
    def create_image_queue(self):
        if self.user_settings['src_dir'] is not None:
            for item in os.listdir(self.user_settings['src_dir']):
                if os.path.isfile(self.user_settings['src_dir'] + item):
                    content_type = self.get_content_type(item)
                    if content_type is not None:
                        self.image_queue.put(self.user_settings['src_dir'] + item)

    # get content type
    def get_content_type(self, image_path):
        extension = os.path.splitext(image_path)[1].lower()
        try:
            return self.ext_to_content_type[extension]
        except KeyError:
            return None

    # move image to correct directory
    def sort_image(self, image_path, posted):
        if not posted:
            destination_directory = self.not_posted_directory
        else:
            destination_directory = self.posted_directory

        if destination_directory != self.user_settings['src_dir']:
            os.rename(image_path, destination_directory + os.path.split(image_path)[1])

    # make sure all directories are valid
    def directories_set(self):
        if os.path.isdir(self.user_settings['src_dir']) and \
                os.path.isdir(self.not_posted_directory) and \
                os.path.isdir(self.posted_directory):
            return True
        return False

    # get supported subreddits from redditbooru
    def get_subreddits(self):
        response = requests.get('http://redditbooru.com/sources/')
        response = response.json()
        subreddits = dict()
        for subreddit in response:
            subreddits[subreddit['title']] = {'checked': subreddit['checked'],
                                              'value': subreddit['value'],
                                              'name': subreddit['name']}
        return subreddits

    # load user settings
    def load_user_settings(self):
        with open(self.base_directory + 'media\\user_settings.config', 'r') as file:
            for line in file:
                line = line.rstrip()
                setting = line.split(':', 1)
                self.user_settings[setting[0]] = setting[1]
        # convert NSFW value to a boolean
        self.user_settings['NSFW'] = bool(int(self.user_settings['NSFW']))

        if 'src_dir' in self.user_settings and not os.path.isdir(self.user_settings['src_dir']):
            self.user_settings['src_dir'] = None
        self.not_posted_directory = self.user_settings['src_dir']
        self.posted_directory = self.user_settings['src_dir']

    # load user subreddit settings (client side specific)
    def load_subreddits(self):
        loaded_subreddits = dict()
        with open(self.base_directory + 'media\\subreddit_settings.config', 'r') as file:
            for line in file:
                line = line.rstrip()
                setting = line.split(':')
                loaded_subreddits[setting[0]] = bool(int(setting[1]))

        self.subreddits = self.get_subreddits()
        # in case new subreddits are added
        for subreddit in loaded_subreddits:
            self.subreddits[subreddit]['checked'] = loaded_subreddits[subreddit]

    # save settings
    def save_settings(self):
        self.save_subreddits()
        self.save_user_settings()

    # save user settings (source directory and show NSFW)
    def save_user_settings(self):
        i = len(self.user_settings) - 1
        with open(self.base_directory + 'media\\user_settings.config', 'w') as file:
            newline = '\n'
            for setting in self.user_settings:
                if i <= 0:
                    newline = ''
                if setting == 'NSFW':
                    self.user_settings['NSFW'] = str(int(self.user_settings['NSFW']))
                line = setting + ':' + self.user_settings[setting] + newline
                file.write(line)
                i -= 1

    # save subreddit settings
    def save_subreddits(self):
        i = len(self.subreddits) - 1
        with open(self.base_directory + 'media\\subreddit_settings.config', 'w') as file:
            newline = '\n'
            for subreddit in self.subreddits:
                if i <= 0:
                    newline = ''
                line = subreddit + ':' + str(int(self.subreddits[subreddit]['checked'])) + newline
                file.write(line)
                i -= 1

    # post image to redditbooru and get response
    def check_image(self, image_path):
        # add subreddit get parameters
        sources = '?sources='
        for subreddit in self.subreddits:
            if self.subreddits[subreddit]['checked']:
                sources += str(self.subreddits[subreddit]['value']) + ','
            # trim final comma
        sources = sources[:-1]
        response = requests.post('http://redditbooru.com/images/' + sources,
                                 files={'upload': (os.path.split(image_path)[1],
                                                   open(image_path, 'rb'),
                                                   get_content_type(image_path))},
                                 data={'uploadId': int(time.time() * 1000)})

        return response.json()


# legacy non member functions
def check_image(image_path):
    response = requests.post('http://redditbooru.com/images/',
                             files={'upload': (os.path.split(image_path)[1],
                                               open(image_path, 'rb'),
                                               get_content_type(image_path))},
                             data={'uploadId': int(time.time() * 1000)})

    return response.json()


def get_content_type(image):
    ext_to_content_type = {'.jpg': 'image/jpeg',
                           '.jpeg': 'image/jpeg',
                           '.png': 'image/png'}
    extension = os.path.splitext(image)[1].lower()
    try:
        return ext_to_content_type[extension]
    except KeyError:
        return None





