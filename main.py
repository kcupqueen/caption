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
import sys, time
from pathlib import Path

from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QMouseEvent, QKeySequence

from PyQt5 import QtWidgets, QtGui, QtCore
import vlc
from PyQt5.QtWidgets import QShortcut

from caption import get_captions, find_caption, get_template, lookup_caption, LookUpType, convert_srt_to_vtt, \
    get_captions_from_string, CaptionType, find_captions
from caption.extract import get_subtitle_tracks, extract_all, get_video_dimensions, get_video_frame_as_base64, \
    extract_all_as_strings, extract_subtitle_as_string
from caption.online_trans import OnlineTranslator
from caption.stardict import OfflineTranslator
from widget.player_controller import resize_player, handle_selection_changed
from widget.player_event import mouse_press_event
from widget.qtool import FloatingTranslation
from widget.slider import VideoSlider, ClickableSlider
from widget.subtitle_dialog import OptionDialog

from widget.thread import QtThread
from widget.thread_pool import GLOBAL_THREAD_POOL, Worker

# TODO only for development
BASE_DIR = Path(__file__).resolve().parent
current_dir = Path.cwd()

dict_path = Path(current_dir) / "assets" / "swordword.db"
lemma_path = Path(current_dir) / "assets" / "lemma.en.txt"


class Player(QtWidgets.QMainWindow):
    """A simple Media Player using VLC and Qt
    """

    def __init__(self, master=None):
        QtWidgets.QMainWindow.__init__(self, master)

        self.caption_type = CaptionType.NORMAL
        self.play_triggered_times = 0
        self.sub_file_num = 0
        self.caption_menu = None
        self.subtitle_tracks = []
        self.embed_caption_dict = {}
        self.audio_tracks = []
        self.translation_threads = []
        self.setWindowTitle("CompreVids️")
        self.ignore_user = False

        # Create a basic vlc instance
        self.instance = vlc.Instance("--file-caching=5000", "--network-caching=5000", "--no-sub-autodetect-file", "--no-spu")

        self.media = None

        # Create an empty vlc media player
        self.mediaplayer = self.instance.media_player_new()
        self.mediaplayer.audio_set_volume(50)
        event_manager = self.mediaplayer.event_manager()
        event_manager.event_attach(vlc.EventType.MediaPlayerMediaChanged, self.media_changed)

        self.is_paused = False
        self.captionList = []
        self.cur_caption_seq = set()
        # get size of mdx
        self.translator = OfflineTranslator(dict_path, lemma_path)
        self.translator2 = OnlineTranslator(url="http://211.159.170.219:3000/api/translate")

        self.create_ui()

    def media_changed(self, event):
        print("Media Changed Event:", event)
        # Reset UI elements when media changes
        self.positionslider.setValue(0)
        self.playbutton.setText("Play")
        self.is_paused = True
        self.cur_caption_seq.clear()
        
        # Clear caption display
        welcomeHtml = get_template("welcome", 
                                  "Media changed. Subtitles will be displayed here when available.")
        self.caption.setHtml(welcomeHtml)
        
        # Hide any floating translation window if visible
        if hasattr(self, 'floatingWindow') and self.floatingWindow.isVisible():
            QtCore.QMetaObject.invokeMethod(self.floatingWindow, 
                                          "hide",
                                          QtCore.Qt.ConnectionType.QueuedConnection)


    def clear_player_cache(self):
        self.play_triggered_times = 0
        self.sub_file_num = 0
        self.subtitle_tracks = []
        self.audio_tracks = []
        # if len(self.translation_threads) > 0:
        #     for thread in self.translation_threads:
        #         thread.quit()
        # self.translation_threads = []
        self.captionList = []
        self.cur_caption_seq = set()
        self.update_tracks_menu()
        self.time_label.setText("00:00:00/??:??:??")

    def create_ui(self):
        """Set up the user interface, signals & slots
        """
        self.widget = QtWidgets.QWidget(self)
        self.setCentralWidget(self.widget)

        # In this widget, the video will be drawn
        if platform.system() == "Darwin":  # for MacOS
            self.videoframe = QtWidgets.QMacCocoaViewContainer(0)
        else:
            self.videoframe = QtWidgets.QFrame()

        self.palette = self.videoframe.palette()
        self.palette.setColor(QtGui.QPalette.Window, QtGui.QColor(0, 0, 0))
        self.videoframe.setPalette(self.palette)
        self.videoframe.setAutoFillBackground(True)
        # set size (default size)
        self.videoframe.setMinimumSize(640, 480)
        self.videoframe.mousePressEvent = self.onclick_videoframe
        # Set cursor to hand when hovering over video frame
        self.positionslider = ClickableSlider(QtCore.Qt.Horizontal, self)
        self.positionslider.setToolTip("Position")
        self.positionslider.setMaximum(1000)
        self.positionslider.sliderMoved.connect(self.set_position)
        self.positionslider.sliderPressed.connect(self.set_position)
        self.hbuttonbox = QtWidgets.QHBoxLayout()
        self.playbutton = QtWidgets.QPushButton("Play")

        space_shortcut = QShortcut(QKeySequence("Space"), self)
        space_shortcut.activated.connect(self.on_space_pressed)
        left_shortcut = QShortcut(QKeySequence("Left"), self)
        left_shortcut.activated.connect(self.on_go_back)
        right_shortcut = QShortcut(QKeySequence("Right"), self)
        right_shortcut.activated.connect(self.on_go_forward)

        self.hbuttonbox.addWidget(self.playbutton)
        self.playbutton.clicked.connect(self.play_pause)

        self.time_label = QtWidgets.QLabel(self)
        self.time_label.setText("00:00:00/??:??:??")
        self.hbuttonbox.addWidget(self.time_label)

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
        welcomeHtml = get_template("welcome",
                                   "subtitles will be displayed here, you can select the text and look up the meaning while watching the video")
        self.caption.setHtml(welcomeHtml)

        # register selectionChanged signal
        self.caption.mouseReleaseEvent = self.on_selection_changed
        # Create a separate layout for the caption
        self.caption_layout = QtWidgets.QVBoxLayout()
        self.caption_layout.addWidget(self.caption)

        # caption word lookup
        self.floatingWindow = FloatingTranslation(self, self.translator2.lookup)

        self.floatingWindow.windowClosed.connect(self.play_pause)

        # self.floatingWindow.windowClosed.connect(self.go_on_play)  # Connect signal to slot
        self.floatingWindow.captionReady.connect(self.display_translation)

        self.vboxlayout = QtWidgets.QVBoxLayout()
        self.vboxlayout.addWidget(self.videoframe, 80)  # Give videoframe a stretch factor of 80
        self.vboxlayout.addWidget(self.positionslider, 1)  # Small stretch factor
        self.vboxlayout.addLayout(self.hbuttonbox, 1)  # Small stretch factor
        self.vboxlayout.addLayout(self.caption_layout, 18)  # Give caption about 18% of remaining space

        self.widget.setLayout(self.vboxlayout)

        menu_bar = self.menuBar()

        # File menu
        file_menu = menu_bar.addMenu("File")
        # Caption menu
        caption_menu = menu_bar.addMenu("Caption&Audio")
        self.caption_menu = caption_menu

        # Add actions to file menu
        open_action = QtWidgets.QAction("Load Video", self)
        open_shortcut = QtGui.QKeySequence(QtGui.QKeySequence.StandardKey.Open)
        open_action.setShortcut(open_shortcut)
        file_menu.addAction(open_action)

        # Add actions to caption menu
        caption_action = QtWidgets.QAction("加载外挂字幕", self)
        caption_menu.addAction(caption_action)
        # Connect the caption action to a method
        caption_action.triggered.connect(self.load_caption)

        close_action = QtWidgets.QAction("Close App", self)
        close_shortcut = QtGui.QKeySequence(QtGui.QKeySequence.StandardKey.Close)
        close_action.setShortcut(close_shortcut)
        file_menu.addAction(close_action)

        open_action.triggered.connect(self.open_file)
        close_action.triggered.connect(sys.exit)

    def on_go_back(self):
        print("go back")
        back_t = 5000
        current_time = self.mediaplayer.get_time()
        if current_time > back_t:
            self.mediaplayer.set_time(current_time - back_t)
            self.cur_caption_seq.clear()

    def on_go_forward(self):
        print("go forward")
        forward_t = 5000
        current_time = self.mediaplayer.get_time()
        if current_time < self.mediaplayer.get_length() - forward_t:
            self.mediaplayer.set_time(current_time + forward_t)



    def onclick_videoframe(self, event):
        self.play_pause()


    def on_space_pressed(self):
        print("Space pressed")
        self.play_pause()

    def mousePressEvent(self, event: QMouseEvent):
        mouse_press_event(self, event)

    def track_parsed(self, event):
        # Use invokeMethod to update UI from the main thread
        QtCore.QMetaObject.invokeMethod(self, "update_tracks_menu",
                                        QtCore.Qt.ConnectionType.QueuedConnection)
        # invoke playbutton to be enabled
        QtCore.QMetaObject.invokeMethod(self.playbutton, "setEnabled",
                                        QtCore.Qt.ConnectionType.QueuedConnection,
                                        QtCore.Q_ARG(bool, True))

    @QtCore.pyqtSlot()
    def update_tracks_menu(self):
        """Update the tracks menu from the main thread"""
        # Clear existing menu items
        self.caption_menu.clear()

        # Add caption loading action back
        caption_action = QtWidgets.QAction("挂载字幕", self)
        caption_action.triggered.connect(self.load_caption)
        self.caption_menu.addAction(caption_action)
        self.caption_menu.addSeparator()

        # Add audio tracks submenu
        audio_menu = self.caption_menu.addMenu("Audio Tracks")
        audio_tracks = self.mediaplayer.audio_get_track_description()
        current_audio = self.mediaplayer.audio_get_track()

        # print("Audio Tracks:")
        for track_id, track_name in audio_tracks:
            # Add checkmark emoji if this is the current track
            prefix = "✓ " if track_id == current_audio else "    "
            action = QtWidgets.QAction(f"{prefix}Audio: {track_name.decode()}", self)
            action.setData(track_id)
            action.triggered.connect(lambda checked, tid=track_id: self.set_audio_track(tid))
            audio_menu.addAction(action)

        if len(audio_tracks) > 0:
            self.audio_tracks = audio_tracks
        # Disable subtitles more thoroughly



        print("embedded audio tracks", len(self.audio_tracks), "subtitle tracks", len(self.subtitle_tracks))

    def set_audio_track(self, track_id):
        """Set the audio track"""
        print(f"Setting audio track to {track_id}")
        self.mediaplayer.audio_set_track(track_id)
        current_track = self.mediaplayer.audio_get_track()
        print("current track is", current_track)
        self.update_tracks_menu()

    def set_subtitle_track(self, track_id):
        """Set the subtitle track"""
        print(f"Setting subtitle track to {track_id}")
        self.mediaplayer.video_set_spu(track_id)
        # Get current SPU track ID to verify
        current_spu = self.mediaplayer.video_get_spu()
        print(f"Current subtitle track is now: {current_spu}")
        self.update_tracks_menu()
        self.extract_embedded_subtitle()

    def extract_embedded_subtitle(self):
        # Try to get subtitle stats/content
        try:
            spu_stats = self.mediaplayer.spu_stats()
            if spu_stats:
                print("SPU Stats:", spu_stats)

            # Get all subtitle descriptions
            spu_desc = self.mediaplayer.video_get_spu_description()
            if spu_desc:
                print("SPU Descriptions:")
                for id, desc in spu_desc:
                    print(f"ID: {id}, Description: {desc.decode()}")

        except Exception as e:
            print("Error getting SPU content:", str(e))

    def display_translation(self, event=None):
        pos = event['pos']
        state = event['state']
        text = event['text']
        lookup_type = event.get('lookup_type', LookUpType.WORD)
        print("display_translation, type is", lookup_type)
        if text:
            self.floatingWindow.set_translation(text, pos, state)

    def play_pause(self):
        """Toggle play/pause status
        """
        #self.mediaplayer.video_set_spu(-1)
        if self.ignore_user:
            print("User input ignored")
            
            # Create and show a tooltip when user input is ignored
            dots = "." * ((int(time.time()) % 3) + 1)
            loading_html = get_template("error", f"Loading in progress{dots}<br>Please wait while processing...")
            self.caption.setHtml(loading_html)
            return

        if self.mediaplayer.is_playing():
            self.mediaplayer.pause()
            self.playbutton.setText("Play")
            self.is_paused = True
        else:
            if self.mediaplayer.play() == -1:
                print("Error: Unable to play")
                return

            self.mediaplayer.play()
            self.playbutton.setText("Pause")
            self.is_paused = False
            print("play triggered 1")
            def after_play():
                if self.mediaplayer.is_playing():
                    print("play triggered 2")
                    # hide all floating windows
                    if hasattr(self, 'floatingWindow') and self.floatingWindow.isVisible():
                        self.floatingWindow.hide()
                    print("Len=", self.mediaplayer.get_length())
                    self.refresh_time_label()

                else:
                    print("play failed")

            QTimer.singleShot(200, after_play)

    def refresh_time_label(self):
        if self.mediaplayer.get_length() > 0:
            #print("refresh time label")
            cur_time = self.mediaplayer.get_time()
            # set a valid time string to self.time_l;abel
            text = f"{time.strftime('%H:%M:%S', time.gmtime(cur_time // 1000))}/" + \
                                    f"{time.strftime('%H:%M:%S', time.gmtime(self.mediaplayer.get_length() // 1000))}"
            # queued chage text
            QtCore.QMetaObject.invokeMethod(self.time_label, "setText", QtCore.Qt.QueuedConnection,
                                            QtCore.Q_ARG(str, text))
        else:
            print("No time label")

    def pause(self, action):
        if self.mediaplayer.is_playing():
            self.mediaplayer.pause()
            self.playbutton.setText("Play")
            self.is_paused = True
            print('pause action: {}'.format(action))

    def stop(self):
        """Stop player
        """
        self.mediaplayer.stop()
        self.playbutton.setText("Play")


    def lock_screen(self):
        """Lock screen while loading, showing loading indicators"""
        # Disable play button and show loading state
        self.playbutton.hide()
        
        # Start a timer to show animated loading dots in caption
        self.loading_timer = QTimer()
        self.loading_dots = 0
        
        def update_loading_text():
            dots = "." * ((self.loading_dots % 3) + 1)
            loading_html = get_template("welcome", f"Loading{dots}")
            self.caption.setHtml(loading_html)
            self.loading_dots += 1
        
        self.loading_timer.timeout.connect(update_loading_text)
        self.loading_timer.start(500)  # Update every 500ms

    def trigger_selector(self, result=None):
        """Unlock screen after loading is complete"""
        # Enable play button and clear loading state
        options = []
        filename = ""
        if result:
            ffmpeg_tracks, ffmpeg_w, ffmpeg_h, filename = result
            self.subtitle_tracks = ffmpeg_tracks
            resize_player(self, ffmpeg_w, ffmpeg_h)
            self.update_tracks_menu()
            options = [f"{track[1]} {track[0]} {track[2]}" for track in ffmpeg_tracks]

        self.playbutton.show()
        # Stop the loading timer
        if hasattr(self, 'loading_timer'):
            self.loading_timer.stop()
            delattr(self, 'loading_timer')
            delattr(self, 'loading_dots')
            self.caption.clear()
        if len(options) > 0:
            self.show_subtitle_selector(options, filename)




    def show_subtitle_selector(self, options, filename):
        # width is 1/4 of the screen width
        # height is 1/3 of the screen height
        w = self.width() // 4
        h = self.height() // 3
        def reject():
            print("reject")
            self.ignore_user = False
        dialog = OptionDialog(options, w, h, filename, reject_func=reject, parent=self)

        dialog.option_selected.connect(self.on_subtitle_selected)


        dialog.exec_()

    def open_file(self):
        """Open a media file in a MediaPlayer"""
        # Pause any currently playing media first
        if self.mediaplayer.is_playing():
            self.mediaplayer.pause()
            self.playbutton.setText("Play")
            self.is_paused = True
            
        self.clear_player_cache()
        dialog_txt = "Choose Media File"
        filename = QtWidgets.QFileDialog.getOpenFileName(self, dialog_txt, os.path.expanduser('~'))
        if not filename or not filename[0]:
            return
        ext = os.path.splitext(filename[0])[1].lower()
        if ext not in ['.mp4', '.mkv', '.avi', '.webm', '.flv', '.mov', '.wmv', '.mpg', '.mpeg', '.m4v']:
            QtWidgets.QMessageBox.warning(self, "Error", "Unsupported file format")
            return
        if ext == ".mkv":
            # Get video information
            def ffmpeg_parse():
                self.ignore_user = True
                ffmpeg_tracks = get_subtitle_tracks(filename[0])
                ffmpeg_w, ffmpeg_h = get_video_dimensions(filename[0])
                print("result is", ffmpeg_tracks, ffmpeg_w, ffmpeg_h)
                return ffmpeg_tracks, ffmpeg_w, ffmpeg_h, filename[0]  # Return as tuple
                
            # Create worker and connect result
            GLOBAL_THREAD_POOL.start(Worker(ffmpeg_parse, on_finished=self.trigger_selector))

        # Continue with media loading...
        self.media = self.instance.media_new(filename[0])
        self.media.add_options('no-sub-autodetect-file')
        self.media.add_options('no-spu')

        # Put the media in the media player
        self.mediaplayer.set_media(self.media)
        self.mediaplayer.set_mrl(filename[0], ":avcodec-hw=none", ":no-hw-dec")
        self.media.parse()

        event_manager = self.mediaplayer.event_manager()
        event_manager.event_attach(vlc.EventType.MediaPlayerTimeChanged, self.time_changed_callback)
        # The media player has to be 'connected' to the QFrame (otherwise the
        # video would be displayed in it's own window). This is platform
        # specific, so we must give the ID of the QFrame (or similar object) to
        # vlc. Different platforms have different functions for this
        if platform.system() == "Linux":  # for Linux using the X Server
            self.mediaplayer.set_xwindow(int(self.videoframe.winId()))
        elif platform.system() == "Windows":  # for Windows
            self.mediaplayer.set_hwnd(int(self.videoframe.winId()))
        elif platform.system() == "Darwin":  # for MacOS
            self.mediaplayer.set_nsobject(int(self.videoframe.winId()))
        self.mediaplayer.video_set_spu(-1)  # Try basic disable
        self.mediaplayer.video_set_subtitle_file(None)  # Clear any subtitle file
        self.mediaplayer.video_set_spu_delay(0)  # Reset subtitle delay
        self.mediaplayer.video_set_track(-1)

        print("play triggered 3")
        self.mediaplayer.play()
        # pause after 0.1s
        QTimer.singleShot(100, self.mediaplayer.pause)



    def on_subtitle_selected(self, selected_option):
        filename = selected_option.get('filename')
        index = selected_option.get('index')
        self.embed_caption_dict.clear()
        print("selected option", selected_option)
        def extract_now():
            print("start extract subtitle")
            # mock time consuming task
            time.sleep(10)
            ret = []
            subtitle_content = extract_subtitle_as_string(filename, track_index=index)
            if subtitle_content:
                ret = get_captions_from_string(subtitle_content)
            return ret

        def on_finished(result):
            if len(result) > 0:
                self.captionList = result
                html = get_template("welcome", f"加载第{index}条内置字幕, 共{len(result)}条")
                QtCore.QMetaObject.invokeMethod(self.caption, "setHtml", QtCore.Qt.QueuedConnection,
                                                QtCore.Q_ARG(str, html))
                self.ignore_user = False

        # put in thread pool
        GLOBAL_THREAD_POOL.start(Worker(extract_now, on_finished=on_finished))

    def time_changed_callback(self, event):
        media_pos = int(self.mediaplayer.get_position() * 1000)
        # print('set position', media_pos)
        QtCore.QMetaObject.invokeMethod(self.positionslider, "setValue", QtCore.Qt.QueuedConnection,
                                        QtCore.Q_ARG(int, media_pos))
        current_time = self.mediaplayer.get_time()  # 获取当前播放时间（单位：毫秒）
        self.refresh_time_label()

        if self.captionList:
            if self.caption_type == CaptionType.NORMAL:
                cur_caption = find_caption(current_time, self.captionList, self.cur_caption_seq)
                if cur_caption and cur_caption['seq'] not in self.cur_caption_seq:
                    self.cur_caption_seq.clear()
                    text = cur_caption['caption'].text
                    text = text.replace('&nbsp;', ' ').replace('\n', ' ')
                    text = text.replace('{', '{{').replace('}', '}}')

                    self.cur_caption_seq.add(cur_caption['seq'])
                    html = get_template("caption", text)
                    QtCore.QMetaObject.invokeMethod(self.caption, "setHtml", QtCore.Qt.QueuedConnection,
                                                    QtCore.Q_ARG(str, html))
            elif self.caption_type == CaptionType.YOUTUBE_AUTO_GENERATED:
                all_text = []
                first, second = find_captions(current_time, self.captionList, self.cur_caption_seq)
                # print("first", first, "second", second, "cur", current_time)
                if first and first['seq'] in self.cur_caption_seq:
                    return
                if second and second['seq'] in self.cur_caption_seq:
                    return
                self.cur_caption_seq.clear()
                if first:
                    self.cur_caption_seq.add(first['seq'])
                    all_text.append(first['caption'].text)
                if second:
                    self.cur_caption_seq.add(second['seq'])
                    all_text.append(second['caption'].text)
                if len(all_text) > 0:
                    text = " ".join(all_text)
                    text = text.replace('&nbsp;', ' ').replace('\n', ' ')
                    text = text.replace('{', '{{').replace('}', '}}')
                    html = get_template("caption", text)
                    QtCore.QMetaObject.invokeMethod(self.caption, "setHtml", QtCore.Qt.QueuedConnection,
                                                    QtCore.Q_ARG(str, html))


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
        pos = self.positionslider.value()
        print('pos', pos)
        self.mediaplayer.set_position(pos / 1000.0)
        self.cur_caption_seq.clear()



    def load_caption(self):
        """Open a file dialog to load a caption file"""
        # only if self.mediaplayer has been set
        if self.mediaplayer.get_media():
            dialog_txt = "Choose Caption File"
            filename, _ = QtWidgets.QFileDialog.getOpenFileName(self, dialog_txt, os.path.expanduser('~'),
                                                                "webVTT (*.vtt);;srt Files (*.srt)")
            self.backend_load_caption(filename)
        else:
            QtWidgets.QMessageBox.warning(self, "Error", "Please load a video file first")

    def backend_load_caption(self, filename):
        if filename:
            def load_caption():
                if filename:
                    ret, _type = get_captions(filename)
                    self.cur_caption_seq.clear()
                    return ret, _type
                return [], None

            def on_finished(result):
                ret, _type = result
                if len(ret) > 0:
                    print("get options ok", len(ret))
                    self.captionList = ret
                    html = get_template("welcome", f"加载[En]字幕文件成功, _type: {_type}")
                    QtCore.QMetaObject.invokeMethod(self.caption, "setHtml", QtCore.Qt.QueuedConnection,
                                                    QtCore.Q_ARG(str, html))
                    self.caption_type = _type

            GLOBAL_THREAD_POOL.start(Worker(load_caption, on_finished=on_finished))


    def backend_load_caption_from_str(self, content):
        if len(content) > 0:
            ret = get_captions_from_string(content)
            if len(ret) > 0:
                print("get options ok", len(ret))
                self.captionList = ret
                html = get_template("welcome", "已发现内置[En]字幕文件")
                QtCore.QMetaObject.invokeMethod(self.caption, "setHtml", QtCore.Qt.QueuedConnection,
                                                QtCore.Q_ARG(str, html))


    def on_selection_changed(self, event):
        handle_selection_changed(self, GLOBAL_THREAD_POOL)


def main():
    """Entry point for our simple vlc player
    """
    app = QtWidgets.QApplication(sys.argv)
    player = Player()
    player.show()
    # 16:9
    player.resize(960, 640)
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
