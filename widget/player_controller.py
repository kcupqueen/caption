from PyQt5 import QtCore, QtWidgets


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


