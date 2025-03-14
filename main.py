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

from PyQt5 import QtWidgets, QtGui, QtCore
import vlc
from caption import get_captions, find_caption, get_template, lookup_caption, LookUpType, convert_srt_to_vtt
from caption.extract import get_subtitle_tracks, extract_all, get_video_dimensions, get_video_frame_as_base64
from caption.translate import OfflineTranslator, WordTranslation, OnlineTranslator
from widget.qtool import FloatingTranslation
from widget.slider import VideoSlider, ClickableSlider

from widget.thread import QtThread

# TODO only for development
BASE_DIR = os.path.abspath(".")
MODEL_PATH = "en_core_web_sm"
check_list = {
    "en_core_web_sm": False,
    "mdx": False,
}
class Player(QtWidgets.QMainWindow):
    """A simple Media Player using VLC and Qt
    """

    def __init__(self, master=None):
        QtWidgets.QMainWindow.__init__(self, master)
        self.play_triggered_times = 0
        self.sub_file_num = 0
        self.caption_menu = None
        self.subtitle_tracks = []
        self.audio_tracks = []
        self.translation_threads = []
        self.setWindowTitle("SwordPlayer🗡️")

        # Create a basic vlc instance
        self.instance = vlc.Instance()

        self.media = None

        # Create an empty vlc media player
        self.mediaplayer = self.instance.media_player_new()
        self.mediaplayer.audio_set_volume(50)


        self.is_paused = False
        self.captionList = []
        self.cur_caption_seq = set()

        mdx_path = os.path.join(BASE_DIR, "assets/mdx.db")

        # check mdx or < 1mb
        if not os.path.exists(mdx_path) or os.path.getsize(mdx_path) < 1024 * 1024:
            print("mdx.db not found, please download it from")
            check_list["mdx"] = False
        else:
            check_list["mdx"] = True
        # get size of mdx
        self.translator = OfflineTranslator(mdx_path, MODEL_PATH)
        if self.translator.nlp_ready():
            check_list["en_core_web_sm"] = True
        self.translator_online = OnlineTranslator("http://localhost:3000/api/translate")
        self.create_ui()

    def clear_cache(self):
        self.play_triggered_times = 0
        self.sub_file_num = 0
        self.subtitle_tracks = []
        self.audio_tracks = []
        if len(self.translation_threads) > 0:
            for thread in self.translation_threads:
                thread.quit()
        self.translation_threads = []
        self.captionList = []
        self.cur_caption_seq = set()
        self.update_tracks_menu()


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
        # check check_list
        error_txt = ""
        for key, value in check_list.items():
            print(key, value)
            if not value:
                error_txt += f"{key} not found, "
        if error_txt:
            errorHtml = get_template("error", error_txt)
            self.caption.setHtml(errorHtml)


        # register selectionChanged signal
        self.caption.mouseReleaseEvent = self.on_selection_changed
        # Create a separate layout for the caption
        self.caption_layout = QtWidgets.QVBoxLayout()
        self.caption_layout.addWidget(self.caption)

        # caption word lookup
        self.floatingWindow = FloatingTranslation(self)
        # caption sentence lookup window
        self.floatingWindowLong = FloatingTranslation(self, confirm=True, onlineTranslator=self.translator_online)

        self.floatingWindow.windowClosed.connect(self.go_on_play)  # Connect signal to slot
        self.floatingWindow.captionReady.connect(self.display_translation)
        self.floatingWindowLong.windowClosed.connect(self.go_on_play)  # Connect signal to slot
        self.floatingWindowLong.captionReady.connect(self.display_translation)


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

    
    def track_parsed(self, event):
        # Use invokeMethod to update UI from the main thread
        QtCore.QMetaObject.invokeMethod(self, "update_tracks_menu", 
                                      QtCore.Qt.ConnectionType.QueuedConnection)

    @QtCore.pyqtSlot()
    def update_tracks_menu(self):
        """Update the tracks menu from the main thread"""
        # Clear existing menu items
        self.caption_menu.clear()
        
        # Add caption loading action back
        caption_action = QtWidgets.QAction("Load Caption", self)
        caption_action.triggered.connect(self.load_caption)
        self.caption_menu.addAction(caption_action)
        self.caption_menu.addSeparator()
        
        # Add audio tracks submenu
        audio_menu = self.caption_menu.addMenu("Audio Tracks")
        audio_tracks = self.mediaplayer.audio_get_track_description()
        current_audio = self.mediaplayer.audio_get_track()
        
        print("Audio Tracks:")
        for track_id, track_name in audio_tracks:
            # Add checkmark emoji if this is the current track
            prefix = "✓ " if track_id == current_audio else "    "
            action = QtWidgets.QAction(f"{prefix}Audio: {track_name.decode()}", self)
            action.setData(track_id)
            action.triggered.connect(lambda checked, tid=track_id: self.set_audio_track(tid))
            audio_menu.addAction(action)

        if len(audio_tracks) > 0:
            self.audio_tracks = audio_tracks
        self.mediaplayer.video_set_spu(-1)

        subtitle_menu = self.caption_menu.addMenu("Subtitle Tracks")
        subtitle_tracks = self.subtitle_tracks
        if len(subtitle_tracks) == 0:
            return

        current_spu = 0
        print("All Subtitle Tracks: ", len(subtitle_tracks), "extract file num", self.sub_file_num)
        for track in subtitle_tracks:
            print(f"Subtitle Track: {track}")
            track_id = track[0]
            track_name = track[1]
            # Add checkmark emoji if this is the current track
            prefix = "✓ " if track_id == current_spu else "    "
            action = QtWidgets.QAction(f"{prefix}Subtitle: {track_name} {track_id}", self)
            action.setData(track_id)
            action.triggered.connect(lambda checked, tid=track_id: self.set_subtitle_track(tid))
            subtitle_menu.addAction(action)
        
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


    def go_on_play(self, event=None):
        print('go_on_play', event)
        self.play_triggered_times += 1
        if not self.mediaplayer.is_playing():
            self.mediaplayer.play()
            self.playbutton.setText("Pause")
            self.timer.start()
            self.is_paused = False
        if self.play_triggered_times < 2:
            self.track_parsed(event)

    def display_translation(self, event=None):
        pos = event['pos']
        state = event['state']
        text = event['text']
        _type = event.get('type', LookUpType.WORD)
        confirm = False
        component = self.floatingWindow
        if _type == LookUpType.SENTENCE:
            component = self.floatingWindowLong
            if state == "loading": # confirm to use ai , hide collect button
                confirm = True

        if text:
            component.set_translation(text, pos, state, confirm)


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
                #self.open_file()
                return

            self.mediaplayer.play()
            self.playbutton.setText("Pause")
            self.timer.start()
            self.is_paused = False
            width, height = self.mediaplayer.video_get_size(0)
            print(f"Video Size: {width}x{height}")

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

    def set_cover_image(self, base64_image):
        """Set a cover image on the video frame before playback starts"""
        if not base64_image:
            return
            
        # Create a QPixmap from the base64 image data
        pixmap = QtGui.QPixmap()
        pixmap.loadFromData(QtCore.QByteArray.fromBase64(base64_image.encode()))
        
        # Scale the pixmap to fit the video frame while maintaining aspect ratio
        scaled_pixmap = pixmap.scaled(
            self.videoframe.size(),
            QtCore.Qt.AspectRatioMode.KeepAspectRatio,
            QtCore.Qt.TransformationMode.SmoothTransformation
        )
        
        # Create a label to display the image
        self.cover_label = QtWidgets.QLabel(self.videoframe)
        self.cover_label.setPixmap(scaled_pixmap)
        self.cover_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.cover_label.setStyleSheet("background-color: black;")
        self.cover_label.resize(self.videoframe.size())
        self.cover_label.show()
        
        # Connect to the playing event to hide the cover
        event_manager = self.mediaplayer.event_manager()
        event_manager.event_attach(vlc.EventType.MediaPlayerPlaying, 
                                  lambda e: QtCore.QMetaObject.invokeMethod(self, 
                                                                          "hide_cover", 
                                                                          QtCore.Qt.ConnectionType.QueuedConnection))
    
    @QtCore.pyqtSlot()
    def hide_cover(self):
        """Hide and remove the cover image when playback starts"""
        if hasattr(self, 'cover_label'):
            self.cover_label.hide()
            self.cover_label.deleteLater()
            delattr(self, 'cover_label')

    def open_file(self):
        """Open a media file in a MediaPlayer"""
        self.clear_cache()
        dialog_txt = "Choose Media File"
        filename = QtWidgets.QFileDialog.getOpenFileName(self, dialog_txt, os.path.expanduser('~'))
        if not filename:
            return
        
        # Get video information
        ffmpeg_tracks = get_subtitle_tracks(filename[0])
        print(ffmpeg_tracks)
        self.caption.setText("load video {} successfully, subtitle tracks: {}".format(filename, ffmpeg_tracks))
        ffmpeg_w, ffmpeg_h = get_video_dimensions(filename[0])
        
        # Resize the video frame to match video dimensions
        if ffmpeg_w > 0 and ffmpeg_h > 0:
            # Set the initial size of the window based on video dimensions
            # You can apply a scaling factor if needed
            scaling_factor = 1.0  # Adjust this if you want the window smaller/larger than the video
            
            # Calculate new window size while preserving aspect ratio
            new_width = int(ffmpeg_w * scaling_factor)
            new_height = int(ffmpeg_h * scaling_factor)
            
            # Add extra height for controls and caption area
            # Estimate the height needed for other components
            controls_height = 150  # Approximate height for slider, buttons, and caption
            
            # Resize the main window
            self.resize(new_width, new_height + controls_height)
            
            # Set minimum size for the video frame
            self.videoframe.setMinimumSize(new_width, new_height)
            
            print(f"Resized window to match video dimensions: {new_width}x{new_height + controls_height}")

        # Get and set the first frame as cover image
        first_image = get_video_frame_as_base64(filename[0])
        self.set_cover_image(first_image)
        
        # Continue with media loading...
        self.media = self.instance.media_new(filename[0])

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
        # attack play event
        event_manager.event_attach(vlc.EventType.MediaPlayerPlaying, self.go_on_play)
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

        # disable playbutton
        self.playbutton.setEnabled(False)
        # extract all subtitles
        sub_files, langs = extract_all(filename[0])
        for i, sub_file in enumerate(sub_files):
            vtt = convert_srt_to_vtt(sub_file, True)
            sub_files[i] = vtt

        for i, lang in enumerate(langs):
            self.subtitle_tracks.append((i, lang, lang))

        self.sub_file_num = len(sub_files)
        print("x(self.sub_file_num)", self.sub_file_num)
        self.playbutton.setEnabled(True)
        if self.sub_file_num > 0:
            # choose the first subtitle track as default
            self.backend_load_caption(sub_files[0])
            print("auto load subtitle tracks", self.subtitle_tracks)


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
        self.cur_caption_seq.clear()

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
        self.backend_load_caption(filename)

    def backend_load_caption(self, filename):
        if filename:
            ret = get_captions(filename)
            if len(ret) > 0:
                self.captionList = ret
                self.caption.setText("load caption {} successfully, length:{} ".format(filename, len(ret)))

    def on_selection_changed(self, event):
        cursor = self.caption.textCursor()
        if cursor.hasSelection():
            selected_text = cursor.selectedText()  # ✅ Get the selected text
            component = self.floatingWindow
            if selected_text:
                lookup_type = LookUpType.WORD
                self.pause("lookup")
                if len(selected_text.split()) > 1:
                    lookup_type = LookUpType.SENTENCE
                    component = self.floatingWindowLong

                cursor_rect = self.caption.cursorRect(cursor)
                pos = self.caption.mapToGlobal(cursor_rect.bottomRight())

                component.captionReady.emit({
                    'text': selected_text,
                    'pos': pos,
                    "state": "loading",
                    "type": lookup_type
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
                    component.captionReady.emit({
                        'text': result,
                        'pos': pos,
                        "state": "loaded"
                    })

                # lookup for a word, if it is one single word
                if lookup_type == LookUpType.WORD:
                    print("lookup one word", selected_text)
                    # **存储多个线程，避免被覆盖**
                    if not hasattr(self, "translation_threads"):
                        self.translation_threads = []  # 初始化线程列表

                    thread = QtThread(lookup_caption_task, selected_text)
                    thread.finished.connect(on_result)
                    thread.start()

                    self.translation_threads.append(thread)

                    # 清理已完成的线程
                    self.translation_threads = [t for t in self.translation_threads if t.isRunning()]
                else:
                    print("multi words", selected_text)





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