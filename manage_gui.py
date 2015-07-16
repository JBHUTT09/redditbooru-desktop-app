__author__ = 'John Huttlinger'

import repost_checker
import os
from PyQt4 import QtCore, QtGui
import urllib.request
import threading
from bs4 import BeautifulSoup


class CheckerWidget(QtGui.QWidget):
    # constructor
    def __init__(self, image_path=None):

        super(CheckerWidget, self).__init__()
        self.checker = repost_checker.RepostChecker()

        self.resize(1570, 600)
        self.center()
        self.setAcceptDrops(True)
        self.setWindowTitle('redditbooru - Repost Checker')
        self.setWindowIcon(QtGui.QIcon(self.checker.base_directory + 'media\\redditbooru.jpg'))

        with open(self.checker.base_directory + 'media\\stylesheet.css', 'r') as file:
            stylesheet = file.read()
        self.setStyleSheet(stylesheet)

        self.mission_gothic_thin_small = None
        self.mission_gothic_thin_xsmall = None
        self.mission_gothic_thin_large = None

        # QWidget definitions
        # labels
        self.your_image_label = None
        self.original_image_label = None
        self.loading_text_label = None
        self.loading_label = None
        self.drag_and_drop_label = None
        self.posted_directory_label = None
        self.not_posted_directory_label = None
        self.source_directory_label = None
        self.subreddits_label = None
        self.similar_label = None
        # checkboxes
        self.nsfw_checkbox = None
        self.subreddit_checkboxes = dict()
        # buttons
        self.set_source_directory_button = None
        self.set_not_posted_directory_button = None
        self.set_not_posted_directory_button = None

        # create tab view
        self.tab_widget = QtGui.QTabWidget(self)

        self.single_search_tab = QtGui.QWidget()
        self.bulk_search_tab = QtGui.QWidget()
        self.album_tab = QtGui.QWidget()
        self.options_tab = QtGui.QWidget()

        tab_layout = QtGui.QVBoxLayout()

        self.single_search_tab.setLayout(tab_layout)
        self.bulk_search_tab.setLayout(tab_layout)
        self.album_tab.setLayout(tab_layout)
        self.options_tab.setLayout(tab_layout)

        self.tab_widget.addTab(self.single_search_tab, 'Search for Repost')
        self.tab_widget.addTab(self.bulk_search_tab, 'Bulk Search')
        self.tab_widget.addTab(self.album_tab, 'Build Album')
        self.tab_widget.addTab(self.options_tab, 'Options')

        main_layout = QtGui.QVBoxLayout()
        main_layout.addWidget(self.tab_widget)
        self.setLayout(main_layout)

        self.transparent_black = QtGui.QColor(0, 0, 0, alpha=170)
        self.nsfw_blur = QtGui.QGraphicsBlurEffect()
        self.nsfw_blur.setBlurRadius(100)
        self.set_fonts()
        self.overlay_label_palette = None
        self.set_palettes()

        self.set_initial_objects(image_path)
        # if program was opened on an image
        if image_path is not None:
            self.single_search(image_path)

        self.sort_images_button = QtGui.QPushButton('Sort Images', self.bulk_search_tab)
        self.sort_images_button.setGeometry(10, 150, 100, 25)
        self.sort_images_button.setEnabled(False)

    def create_push_button(self, x_pos, y_pos, width, height, text, parent):
        new_button = QtGui.QPushButton(text, parent)
        new_button.setGeometry(x_pos, y_pos, width, height)
        return new_button

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        for url in event.mimeData().urls():
            image_path = url.toLocalFile()
            if os.path.isfile(image_path):
                self.single_search(image_path)

    def single_search(self, image_path):
        checker_thread = CheckerThread(self, image_path, self.checker)
        self.connect(checker_thread, QtCore.SIGNAL("Finished ( PyQt_PyObject ) "), self.done_checking)
        checker_thread.start()
        if repost_checker.get_content_type(image_path) == 'image/gif':
            self.original_image_label = self.create_gif_label(10, 70, 300, 300, image_path, self.single_search_tab)
        else:
            self.original_image_label = self.create_image_label(10, 70, 300, 300, image_path, self.single_search_tab)
        self.original_image_label.show()
        self.your_image_label.show()
        self.loading_text_label.setText('Searching...')
        self.loading_text_label.show()
        self.loading_label.show()

    # wrapper function to handle directory selection call from a button
    def make_choose_directory(self, directory_type):

        # inner function that opens a directory selection dialog, sets the directory, and updates the directory label
        def choose_directory():
            if directory_type == 'source':
                temp_directory = \
                    QtGui.QFileDialog.getExistingDirectory(parent=self,
                                                           caption='Choose source directory',
                                                           directory=self.checker.user_settings['src_dir'],
                                                           options=QtGui.QFileDialog.ShowDirsOnly)
                if temp_directory != '':
                    self.checker.user_settings['src_dir'] = temp_directory
                self.source_directory_label.setText(self.checker.user_settings['src_dir'])

            elif directory_type == 'not_posted':
                temp_directory = \
                    QtGui.QFileDialog.getExistingDirectory(parent=self,
                                                           caption='Choose destination directory for not posted images',
                                                           directory=self.checker.user_settings['src_dir'],
                                                           options=QtGui.QFileDialog.ShowDirsOnly)
                if temp_directory != '':
                    self.checker.not_posted_directory = temp_directory
                self.not_posted_directory_label.setText(self.checker.not_posted_directory)

            else:
                temp_directory = \
                    QtGui.QFileDialog.getExistingDirectory(parent=self,
                                                           caption='Choose destination directory for posted images',
                                                           directory=self.checker.user_settings['src_dir'],
                                                           options=QtGui.QFileDialog.ShowDirsOnly)
                if temp_directory != '':
                    self.checker.posted_directory = temp_directory
                self.posted_directory_label.setText(self.checker.posted_directory)

        return choose_directory

    def make_update_subreddits(self, subreddit):
        def update_subreddits():
            self.checker.subreddits[subreddit]['checked'] = not self.checker.subreddits[subreddit]['checked']
        return update_subreddits

    # creates the labels displayed on construction
    def set_initial_labels(self, image_path):

        self.your_image_label = self.create_text_label(10, 5, 300, 60, 'Your Image', self.single_search_tab)
        self.your_image_label.setFont(self.mission_gothic_thin_large)
        self.your_image_label.hide()

        self.loading_text_label = self.create_text_label(45, 375, 200, 30, "Searching...", self.single_search_tab)
        self.loading_text_label.setFont(self.mission_gothic_thin_small)
        self.loading_text_label.hide()

        self.loading_label = self.create_gif_label(10, 375, 30, 30,
                                                   self.checker.base_directory +
                                                   'media\\loading.gif',
                                                   self.single_search_tab)
        self.loading_label.hide()

        self.similar_label = self.create_text_label(330, 5, 300, 60, 'Similar images', self.single_search_tab)
        self.similar_label.setFont(self.mission_gothic_thin_large)
        self.similar_label.hide()

        # create labels for 'Bulk Search' tab
        self.source_directory_label = self.create_text_label(220, 10, 520, 25, '', self.bulk_search_tab)
        self.source_directory_label.setFont(self.mission_gothic_thin_small)

        self.not_posted_directory_label = self.create_text_label(220, 40, 520, 25, '', self.bulk_search_tab)
        self.not_posted_directory_label.setFont(self.mission_gothic_thin_small)

        self.posted_directory_label = self.create_text_label(220, 70, 520, 25, '', self.bulk_search_tab)
        self.posted_directory_label.setFont(self.mission_gothic_thin_small)

        self.subreddits_label = self.create_text_label(10, 10, 300, 25, 'Subreddits', self.options_tab)
        self.subreddits_label.setFont(self.mission_gothic_thin_small)

    def create_checkbox(self, x_pos, y_pos, width, height, text, font, parent):
        new_checkbox = QtGui.QCheckBox(text, parent)
        new_checkbox.setGeometry(x_pos, y_pos, width, height)
        new_checkbox.setFont(font)
        return new_checkbox

    def set_initial_objects(self, image_path):
        self.set_initial_labels(image_path)
        self.set_initial_buttons()
        self.set_initial_checkboxes()

    def set_initial_buttons(self):
        self.set_source_directory_button = self.create_push_button(10, 10, 200, 25,
                                                                   'Select Source Directory',
                                                                   self.bulk_search_tab)
        self.set_source_directory_button.clicked.connect(self.make_choose_directory('source'))

        self.set_not_posted_directory_button = self.create_push_button(10, 40, 200, 25,
                                                                       'Select Not Posted Directory',
                                                                       self.bulk_search_tab)
        self.set_not_posted_directory_button.clicked.connect(self.make_choose_directory('not_posted'))

        self.set_posted_directory_button = QtGui.QPushButton('Select Posted Directory', self.bulk_search_tab)
        self.set_posted_directory_button.setGeometry(10, 70, 200, 25)
        self.set_posted_directory_button.clicked.connect(self.make_choose_directory('posted'))

    def set_initial_checkboxes(self):
        self.nsfw_checkbox = self.create_checkbox(340, 10, 300, 20,
                                                  'Show NSFW',
                                                  self.mission_gothic_thin_xsmall,
                                                  self.options_tab)
        self.nsfw_checkbox.stateChanged.connect(self.make_update_nsfw)
        self.nsfw_checkbox.setChecked(self.checker.user_settings['NSFW'])
        self.set_subreddit_checkboxes()

    def make_update_nsfw(self):
        def update_nsfw():
            self.checker.user_settings['NSFW'] = not self.checker.user_settings['NSFW']
        return update_nsfw()

    def set_subreddit_checkboxes(self):
        i = 0
        y_pos = 45
        """
        sorted_keys = []
        sorted_temp = sorted(self.checker.subreddits.items(), key=lambda item: item[1]['value'])
        for item in sorted_temp:
            sorted_keys.append(item[0])
        """
        sorted_keys = sorted(self.checker.subreddits.keys(), key=lambda key: key.lower())
        for subreddit in sorted_keys:
            x_pos = 10
            if i % 2:
                x_pos = 210
                y_pos -= 30
            self.subreddit_checkboxes[subreddit] = \
                self.create_checkbox(x_pos, y_pos, 200, 20,
                                     subreddit,
                                     self.mission_gothic_thin_xsmall,
                                     self.options_tab)
            self.subreddit_checkboxes[subreddit].setChecked(self.checker.subreddits[subreddit]['checked'])

            self.subreddit_checkboxes[subreddit].stateChanged.\
                connect(self.make_update_subreddits(subreddit))

            y_pos += 30
            i += 1

    # sets palette objects
    def set_palettes(self):
        self.overlay_label_palette = self.palette()
        self.overlay_label_palette.setColor(self.overlay_label_palette.Background, self.transparent_black)
        self.overlay_label_palette.setColor(self.overlay_label_palette.Foreground, QtCore.Qt.white)

    # centers window
    def center(self):
        qr = self.frameGeometry()
        cp = QtGui.QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    # creates the fonts
    def set_fonts(self):
        self.mission_gothic_thin_large = QtGui.QFont('Mission Gothic Thin')
        self.mission_gothic_thin_large.setPixelSize(50)

        self.mission_gothic_thin_small = QtGui.QFont('Mission Gothic Light')
        self.mission_gothic_thin_small.setPixelSize(20)

        self.mission_gothic_thin_xsmall = QtGui.QFont('Mission Gothic Light')
        self.mission_gothic_thin_xsmall.setPixelSize(14)

    # sets background color
    def set_background(self):
        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setColor(self.backgroundRole(), QtCore.Qt.white)
        self.setPalette(palette)

    # creates a label that holds an animated gif
    def create_gif_label(self, x_pos, y_pos, width, height, gif, parent):
        new_label = self.create_label(x_pos, y_pos, width, height, parent)
        movie = QtGui.QMovie(gif)
        movie.setScaledSize(QtCore.QSize(width, height))
        new_label.setMovie(movie)
        movie.start()
        return new_label

    # creates a label that holds text
    def create_text_label(self, x_pos, y_pos, width, height, text, parent):
        new_label = self.create_label(x_pos, y_pos, width, height, parent)
        new_label.setText(text)
        return new_label

    # creates a label that holds an image
    def create_image_label(self, x_pos, y_pos, width, height, image, parent):
        new_label = self.create_label(x_pos, y_pos, width, height, parent)
        new_label.setPixmap(QtGui.QPixmap(image)
                            .scaled(new_label.size(),
                                    QtCore.Qt.KeepAspectRatioByExpanding,
                                    QtCore.Qt.SmoothTransformation))
        return new_label

    # creates a label. used by all label creation functions
    def create_label(self, x_pos, y_pos, width, height, parent):
        new_label = QtGui.QLabel(parent)
        new_label.setGeometry(x_pos, y_pos, width, height)
        return new_label

    # executes on completion of checker_thread
    def done_checking(self, response):
        results = []
        for result in response['results']:
            if result['sourceName'] is not None:
                if self.checker.subreddits[result['sourceName']]['checked']:
                    results.append(result)
        self.loading_text_label.setText('Loading similar images...')
        preview_creation_thread = PreviewCreator(self, results)
        self.connect(preview_creation_thread,
                     QtCore.SIGNAL("Finished ( PyQt_PyObject ) "),
                     self.display_results)
        preview_creation_thread.start()

    # translates time in seconds to approximate time in English
    # returns string: '<time> ago'
    def format_age(self, age):
        if age >= 31536000:
            years = int(age / 31536000)
            if years == 1:
                formatted = str(years) + ' year ago'
            else:
                formatted = str(years) + ' years ago'

        elif age >= 2592000:
            months = int(age / 2592000)
            if months == 1:
                formatted = str(months) + ' month ago'
            else:
                formatted = str(months) + ' months ago'

        elif age >= 604800:
            weeks = int(age / 604800)
            if weeks == 1:
                formatted = str(weeks) + ' week ago'
            else:
                formatted = str(weeks) + ' weeks ago'

        elif age >= 86400:
            days = int(age / 86400)
            if days == 1:
                formatted = str(days) + ' day ago'
            else:
                formatted = str(days) + ' days ago'

        elif age >= 3600:
            hours = int(age / 3600)
            if hours == 1:
                formatted = str(hours) + ' hour ago'
            else:
                formatted = str(hours) + ' hours ago'

        elif age >= 60:
            minutes = int(age / 60)
            if minutes == 1:
                formatted = str(minutes) + ' minute ago'
            else:
                formatted = str(minutes) + ' minutes ago'

        else:
            if age == 1:
                formatted = str(age) + ' second ago'
            else:
                formatted = str(age) + ' seconds ago'

        return formatted

    # executes on completion of preview_creation_thread
    def display_results(self, results):
        self.loading_label.hide()
        self.loading_text_label.hide()
        self.similar_label.show()

        x_pos = 330
        for result in results:
            image = QtGui.QImage()
            image.loadFromData(result['preview'])

            preview_label = self.create_image_label(x_pos, 70, 300, 300,
                                                    image,
                                                    self.single_search_tab)
            if not self.checker.user_settings['NSFW'] and result['nsfw']:
                preview_label.setGraphicsEffect(self.nsfw_blur)
            preview_label.show()

            title_label = self.create_text_label(x_pos, 70, 300, 28,
                                                 result['title'],
                                                 self.single_search_tab)
            title_label.setFont(self.mission_gothic_thin_small)
            title_label.setAutoFillBackground(True)
            title_label.setPalette(self.overlay_label_palette)
            title_label.show()

            subreddit_label = self.create_text_label(x_pos, 342, 150, 28,
                                                     result['subreddit'],
                                                     self.single_search_tab)
            subreddit_label.setFont(self.mission_gothic_thin_small)
            subreddit_label.setAutoFillBackground(True)
            subreddit_label.setPalette(self.overlay_label_palette)
            subreddit_label.show()

            age_label = self.create_text_label(x_pos + 150, 342, 150, 28,
                                               self.format_age(result['age']),
                                               self.single_search_tab)
            age_label.setFont(self.mission_gothic_thin_small)
            age_label.setAlignment(QtCore.Qt.AlignRight)
            age_label.setAutoFillBackground(True)
            age_label.setPalette(self.overlay_label_palette)
            age_label.show()

            x_pos += 310

    def sort_images(self):
        def checker(checker_num):
            while True:
                image_path = self.checker.image_queue.get()


        for i in range(5):
            t = threading.Thread(target=checker, args=i)
            t.setDaemon(True)
            t.start()

        self.checker.create_image_dict()
        self.images_left = self.checker.image_queue.qsize()

        self.checker.image_queue.join()

    def sort_image(self, image_path):
        posted = repost_checker.check_image(image_path, True)
        self.checker.sort_image(image_path, posted)
        return posted

    def closeEvent(self, event):
        self.checker.save_settings()


class CheckerThread(QtCore.QThread):
    def __init__(self, parent=None, image_path=None, checker=None):
        QtCore.QThread.__init__(self, parent)
        self.image_path = image_path
        self.checker = checker

    def run(self):
        results = self.checker.check_image(self.image_path)
        self.emit(QtCore.SIGNAL("Finished ( PyQt_PyObject )"), results)


class PreviewCreator(QtCore.QThread):
    def __init__(self, parent=None, results=None):
        QtCore.QThread.__init__(self, parent)
        self.results = results
        self.redditbooru = 'http://redditbooru.com'
        self.details = []

    def run(self):
        i = 0
        for result in self.results:
            preview_url = self.redditbooru + result['thumb'] + '_300_300.jpg'
            data = urllib.request.urlopen(preview_url).read()
            result_details = {'age': result['age'],
                              'user': result['userName'],
                              'nsfw': result['nsfw'],
                              'score': result['score'],
                              'title': result['title'],
                              'identical': False,
                              'preview': data,
                              'subreddit': result['sourceName']}
            if 'identical' in result:
                result_details['identical'] = True

            self.details.append(result_details)

            i += 1
            if i > 3:
                break

        self.emit(QtCore.SIGNAL("Finished ( PyQt_PyObject )"), self.details)