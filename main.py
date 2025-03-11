#! /usr/bin/env python3
#
# PyQt5 example for VLC Python bindings
# Copyright (C) 2009-2010 the VideoLAN team
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston MA 02110-1301, USA.
#
"""
A simple example for VLC python bindings using PyQt5.

Author: Saveliy Yusufov, Columbia University, sy2685@columbia.edu
Date: 25 December 2018
"""

import platform
import os
import sys

from PyQt5 import QtWidgets, QtGui, QtCore
import vlc
from caption import get_captions, find_caption, get_template, lookup_caption, LookUpType
from caption.translate import OfflineTranslator, WordTranslation
from widget.qtool import FloatingTranslation
from widget.slider import VideoSlider, ClickableSlider

from widget.thread import QtThread


class Player(QtWidgets.QMainWindow):
    """A simple Media Player using VLC and Qt
    """

    def __init__(self, master=None):
        QtWidgets.QMainWindow.__init__(self, master)
        self.translation_threads = []
        self.setWindowTitle("SnakePlayer🐍")

        # Create a basic vlc instance
        self.instance = vlc.Instance()

        self.media = None

        # Create an empty vlc media player
        self.mediaplayer = self.instance.media_player_new()
        self.mediaplayer.audio_set_volume(50)

        self.create_ui()
        self.is_paused = False
        self.resized = False
        self.captionList = []
        self.cur_caption_seq = set()
        test_db_path = "./mdx.db"
        self.translator = OfflineTranslator(test_db_path)

    def create_ui(self):
        """Set up the user interface, signals & slots
        """
        self.widget = QtWidgets.QWidget(self)
        self.setCentralWidget(self.widget)

        # In this widget, the video will be drawn
        if platform.system() == "Darwin": # for MacOS
            self.videoframe = QtWidgets.QMacCocoaViewContainer(0)
        else:
            self.videoframe = QtWidgets.QFrame()

        self.palette = self.videoframe.palette()
        self.palette.setColor(QtGui.QPalette.Window, QtGui.QColor(0, 0, 0))
        self.videoframe.setPalette(self.palette)
        self.videoframe.setAutoFillBackground(True)
        # set size (default size)
        self.videoframe.setMinimumSize(640, 480)

        self.positionslider = ClickableSlider(QtCore.Qt.Horizontal, self)
        self.positionslider.setToolTip("Position")
        self.positionslider.setMaximum(1000)
        self.positionslider.sliderMoved.connect(self.set_position)
        self.positionslider.sliderPressed.connect(self.set_position)
        self.hbuttonbox = QtWidgets.QHBoxLayout()
        self.playbutton = QtWidgets.QPushButton("Play")
        self.hbuttonbox.addWidget(self.playbutton)
        self.playbutton.clicked.connect(self.play_pause)

        # self.stopbutton = QtWidgets.QPushButton("Stop")
        # self.hbuttonbox.addWidget(self.stopbutton)
        # self.stopbutton.clicked.connect(self.stop)

        self.hbuttonbox.addStretch(1)
        self.volumeslider = QtWidgets.QSlider(QtCore.Qt.Horizontal, self)
        self.volumeslider.setMaximum(100)
        self.volumeslider.setValue(self.mediaplayer.audio_get_volume())
        self.volumeslider.setToolTip("Volume")
        self.hbuttonbox.addWidget(self.volumeslider)
        self.volumeslider.valueChanged.connect(self.set_volume)


        # caption area
        self.caption = QtWidgets.QTextEdit("Caption")
        self.caption.setReadOnly(True)
        welcomeHtml = get_template("welcome", "subtitles will be displayed here, you can select the text and look up the meaning while watching the video")
        self.caption.setHtml(welcomeHtml)
        # register selectionChanged signal
        self.caption.mouseReleaseEvent = self.on_selection_changed
        # Create a separate layout for the caption
        self.caption_layout = QtWidgets.QVBoxLayout()
        self.caption_layout.addWidget(self.caption)

        # caption word lookup
        self.floatingWindow = FloatingTranslation(self)

        self.floatingWindow.windowClosed.connect(self.go_on_play)  # Connect signal to slot
        self.floatingWindow.captionReady.connect(self.display_translation)

        self.vboxlayout = QtWidgets.QVBoxLayout()
        self.vboxlayout.addWidget(self.videoframe)
        self.vboxlayout.addWidget(self.positionslider)
        self.vboxlayout.addLayout(self.hbuttonbox)
        self.vboxlayout.addLayout(self.caption_layout)

        self.widget.setLayout(self.vboxlayout)

        menu_bar = self.menuBar()

        # File menu
        file_menu = menu_bar.addMenu("File")
        # Caption menu
        caption_menu = menu_bar.addMenu("Caption")

        # Add actions to file menu
        open_action = QtWidgets.QAction("Load Video", self)
        open_shortcut = QtGui.QKeySequence(QtGui.QKeySequence.StandardKey.Open)
        open_action.setShortcut(open_shortcut)
        file_menu.addAction(open_action)

        # Add actions to caption menu
        caption_action = QtWidgets.QAction("Load Caption", self)
        caption_menu.addAction(caption_action)
        # Connect the caption action to a method
        caption_action.triggered.connect(self.load_caption)

        close_action = QtWidgets.QAction("Close App", self)
        close_shortcut = QtGui.QKeySequence(QtGui.QKeySequence.StandardKey.Close)
        close_action.setShortcut(close_shortcut)
        file_menu.addAction(close_action)

        open_action.triggered.connect(self.open_file)
        close_action.triggered.connect(sys.exit)

        self.timer = QtCore.QTimer(self)
        self.timer.setInterval(100)
        self.timer.timeout.connect(self.update_ui)

    def go_on_play(self, event=None):
        print('go_on_play', event)
        if not self.mediaplayer.is_playing():
            self.mediaplayer.play()
            self.playbutton.setText("Pause")
            self.timer.start()
            self.is_paused = False

    def display_translation(self, event=None):
        pos = event['pos']
        state = event['state']
        text = event['text']
        if text:
            self.floatingWindow.set_translation(text, pos, state)


    def play_pause(self):
        """Toggle play/pause status
        """
        print('play_pause')
        if self.mediaplayer.is_playing():
            self.mediaplayer.pause()
            self.playbutton.setText("Play")
            self.is_paused = True
            self.timer.stop()
        else:
            if self.mediaplayer.play() == -1:
                self.open_file()
                return

            self.mediaplayer.play()
            self.playbutton.setText("Pause")
            self.timer.start()
            self.is_paused = False
            width, height = self.mediaplayer.video_get_size(0)
            print(f"Video Size: {width}x{height}")
            # resize the window to the video size
            if not self.resized and width > 0 and height > 0:
                # self.setMinimumSize(width, height)
                self.resize(width, height)
                self.resized = True
                self.caption.resize(width, int(height/3))
                pass

    def pause(self, action):
        if self.mediaplayer.is_playing():
            self.mediaplayer.pause()
            self.playbutton.setText("Play")
            self.is_paused = True
            self.timer.stop()
            print('pause action: {}'.format(action))


    def stop(self):
        """Stop player
        """
        self.mediaplayer.stop()
        self.playbutton.setText("Play")


    def parse_video(self):
        if self.media:
            # Get audio tracks
            audio_tracks = self.mediaplayer.audio_get_track_description()
            print("Audio Tracks:")
            for track in audio_tracks:
                print(f"ID: {track[0]}, Description: {track[1]}")

            # Get subtitle tracks
            subtitle_tracks = self.mediaplayer.video_get_spu_description()
            print("Subtitle Tracks:")
            for track in subtitle_tracks:
                print(f"ID: {track[0]}, Description: {track[1]}")

    def open_file(self):
        """Open a media file in a MediaPlayer
        """

        dialog_txt = "Choose Media File"
        filename = QtWidgets.QFileDialog.getOpenFileName(self, dialog_txt, os.path.expanduser('~'))
        if not filename:
            return

        # getOpenFileName returns a tuple, so use only the actual file name
        self.media = self.instance.media_new(filename[0])
        # parse first
        self.parse_video()

        # Put the media in the media player
        self.mediaplayer.set_media(self.media)
        self.mediaplayer.set_mrl(filename[0], ":avcodec-hw=none", ":no-hw-dec", ":avcodec-threads=1")

        event_manager = self.mediaplayer.event_manager()

        def time_changed_callback(event):
            current_time = self.mediaplayer.get_time()  # 获取当前播放时间（单位：毫秒）
            if self.captionList:
                cur_caption = find_caption(current_time, self.captionList, self.cur_caption_seq)
                # print('event', event)
                # print('current_time', current_time)
                # print('cur_caption', cur_caption)
                if cur_caption and cur_caption['seq'] not in self.cur_caption_seq:
                    self.cur_caption_seq.clear()
                    text = cur_caption['caption'].text
                    text = text.replace('&nbsp;', ' ').replace('\n', ' ')
                    text = text.replace('{', '{{').replace('}', '}}')

                    self.cur_caption_seq.add(cur_caption['seq'])
                    html = get_template("caption", text)
                    QtCore.QMetaObject.invokeMethod(self.caption, "setHtml", QtCore.Qt.QueuedConnection,
                                                    QtCore.Q_ARG(str, html))

        event_manager.event_attach(vlc.EventType.MediaPlayerTimeChanged, time_changed_callback)

        # Parse the metadata of the file
        self.media.parse()
        # The media player has to be 'connected' to the QFrame (otherwise the
        # video would be displayed in it's own window). This is platform
        # specific, so we must give the ID of the QFrame (or similar object) to
        # vlc. Different platforms have different functions for this
        if platform.system() == "Linux": # for Linux using the X Server
            self.mediaplayer.set_xwindow(int(self.videoframe.winId()))
        elif platform.system() == "Windows": # for Windows
            self.mediaplayer.set_hwnd(int(self.videoframe.winId()))
        elif platform.system() == "Darwin": # for MacOS
            self.mediaplayer.set_nsobject(int(self.videoframe.winId()))
        self.play_pause()

    def set_volume(self, volume):
        """Set the volume
        """
        self.mediaplayer.audio_set_volume(volume)

    def set_position(self):
        """Set the movie position according to the position slider.
        """

        # The vlc MediaPlayer needs a float value between 0 and 1, Qt uses
        # integer variables, so you need a factor; the higher the factor, the
        # more precise are the results (1000 should suffice).

        # Set the media position to where the slider was dragged
        self.timer.stop()
        pos = self.positionslider.value()
        print('pos', pos)
        self.mediaplayer.set_position(pos / 1000.0)
        self.timer.start()

    def update_ui(self):
        """Updates the user interface"""

        # Set the slider's position to its corresponding media position
        # Note that the setValue function only takes values of type int,
        # so we must first convert the corresponding media position.
        media_pos = int(self.mediaplayer.get_position() * 1000)
        #print('set position', media_pos)
        self.positionslider.setValue(media_pos)

        # No need to call this function if nothing is played
        if not self.mediaplayer.is_playing():
            self.timer.stop()

            # After the video finished, the play button stills shows "Pause",
            # which is not the desired behavior of a media player.
            # This fixes that "bug".
            if not self.is_paused:
                self.stop()

    def load_caption(self):
        """Open a file dialog to load a caption file"""
        dialog_txt = "Choose Caption File"
        filename, _ = QtWidgets.QFileDialog.getOpenFileName(self, dialog_txt, os.path.expanduser('~'),
                                                            "webVTT (*.vtt);;srt Files (*.srt);;All Files (*)")
        if filename:
            ret = get_captions(filename)
            if len(ret) > 0:
                self.captionList = ret
                self.caption.setText("load caption {} successfully, length:{} ".format(filename, len(ret)))

    def on_selection_changed(self, event):
        cursor = self.caption.textCursor()
        if cursor.hasSelection():
            selected_text = cursor.selectedText()  # ✅ Get the selected text
            if selected_text:
                self.pause("lookup")
                cursor_rect = self.caption.cursorRect(cursor)
                pos = self.caption.mapToGlobal(cursor_rect.bottomRight())
                self.floatingWindow.captionReady.emit({
                    'text': "loading...",
                    'pos': pos,
                    "state": "loading"
                })

                def lookup_caption_task(text):
                    return self.translator.lookup(text)

                def on_result(result):
                    # emit again
                    print("result", result)
                    if isinstance(result, WordTranslation) and len(result.meanings) > 0:
                        # join all meanings
                        result = "\n".join(result.meanings)
                    else:
                        result = "No translation found"
                    self.floatingWindow.captionReady.emit({
                        'text': result,
                        'pos': pos,
                        "state": "loaded"
                    })

                # **存储多个线程，避免被覆盖**
                if not hasattr(self, "translation_threads"):
                    self.translation_threads = []  # 初始化线程列表

                thread = QtThread(lookup_caption_task, selected_text)
                thread.finished.connect(on_result)
                thread.start()

                self.translation_threads.append(thread)

                # 清理已完成的线程
                self.translation_threads = [t for t in self.translation_threads if t.isRunning()]




def main():
    """Entry point for our simple vlc player
    """
    app = QtWidgets.QApplication(sys.argv)
    player = Player()
    player.show()
    #player.resize(640, 480)
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()