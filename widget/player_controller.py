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

        # Set minimum size for the video frame
        w.videoframe.setMinimumSize(new_width, new_height)

        print(f"Resized window to match video dimensions: {new_width}x{new_height + controls_height}")


