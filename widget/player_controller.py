from PyQt5 import QtCore, QtWidgets

from caption import LookUpType
from widget.thread_pool import Worker


def resize_player(w, ffmpeg_w, ffmpeg_h):
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
        w.resize(new_width, new_height + controls_height)

        # Set a reasonable minimum size that maintains aspect ratio
        # Allow scaling down to 30% of original size
        min_scale = 0.3
        min_width = max(320, int(ffmpeg_w * min_scale))
        min_height = max(240, int(ffmpeg_h * min_scale))
        w.videoframe.setMinimumSize(min_width, min_height)
        
        # Set preferred size for the video frame using sizeHint
        size_policy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        w.videoframe.setSizePolicy(size_policy)
        w.videoframe.updateGeometry()
        
        # Store original video dimensions for scaling operations
        w.original_video_width = ffmpeg_w
        w.original_video_height = ffmpeg_h

        print(f"Resized window to match video dimensions: {new_width}x{new_height + controls_height}")


def handle_selection_changed(window, thread_pool):
    cursor = window.caption.textCursor()
    if cursor.hasSelection():
        cursor_rect = window.caption.cursorRect(cursor)
        pos = window.caption.mapToGlobal(cursor_rect.bottomRight())

        selected_text = cursor.selectedText()  # ✅ Get the selected text
        if not selected_text:
            return

        def lookup_caption_task(text):
            return window.translator.query(text)

        def on_result(result):
            # emit again
            window.floatingWindow.captionReady.emit({
                'text': result,
                'pos': pos,
                "state": "loaded"

            })
        # check if selected text is a single word
        if len(selected_text.split()) == 1:
            lookup_type = LookUpType.WORD
        else:
            lookup_type = LookUpType.SENTENCE
        if lookup_type == LookUpType.WORD:
            window.pause("lookup")
            window.floatingWindow.captionReady.emit({
                'text': "loading...",
                'pos': pos,
                "state": "loading",
                "lookup_type": lookup_type,
            })

            thread_pool.start(Worker(lookup_caption_task, selected_text, on_finished=on_result))
        elif lookup_type == LookUpType.SENTENCE:
            window.pause("lookup")
            window.floatingWindow.captionReady.emit({
                'text': selected_text,
                'pos': None,
                "state": "loaded",
                "lookup_type": lookup_type,
            })
            thread_pool.start(Worker(lookup_caption_task, selected_text, on_finished=on_result))



