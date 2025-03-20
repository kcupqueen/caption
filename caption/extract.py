import os
import subprocess
import sys

import ffmpeg
import base64


def get_video_dimensions(video_path):
    try:
        probe = ffmpeg.probe(video_path)
        video_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'video'), None)

        if video_stream:
            width = video_stream['width']
            height = video_stream['height']
            return width, height
        else:
            raise ValueError(f"No video stream found {video_path}")

    except ffmpeg.Error as e:
        print("FFmpeg error:", e.stderr.decode())
        return None


def get_subtitle_tracks(video_path):
    """ 获取视频文件的字幕轨道信息，并计算相对索引 """
    metadata = ffmpeg.probe(video_path)
    subtitle_tracks = []
    lang_dict = {
        "eng": "English",
        "chi": "Chinese",
        "zho": "Chinese",
    }

    # **找出所有字幕流的索引**
    subtitle_streams = [
        stream for stream in metadata['streams'] if stream['codec_type'] == 'subtitle'
    ]

    for sub_index, stream in enumerate(subtitle_streams):
        # track_index = stream['index']  # FFmpeg 内部的索引（所有流中的索引）
        codec_name = stream.get('codec_name', 'unknown')
        language = stream['tags'].get('language', 'unknown') if 'tags' in stream else 'unknown'

        subtitle_tracks.append((sub_index, codec_name, language))  # 这里返回的是相对索引 sub_index
    return subtitle_tracks

def get_subtitle_tracks_v2(video_path):
    """
    Get subtitle tracks from video file using mkvinfo
    Returns: list of dicts with track info {index, language}
    """
    import subprocess
    
    try:
        # Run mkvinfo command
        result = subprocess.run(['mkvinfo', video_path], capture_output=True, text=True)
        
        tracks = []
        current_items = {}
        for line in result.stdout.split('\n'):
            line = line.strip()
            if line.startswith("| + Track"):
                if current_items.get('index') and current_items.get('type', '') == 'subtitles':
                    if current_items.get('language') is None:
                        current_items['language'] = 'eng'
                    tracks.append(current_items)

                current_items = {}
            else:
                if line.startswith("|  + Track number: "):
                    # Track number: 1 (track ID for mkvmerge & mkvextract: 0)
                    # use regext to get 1 and 0
                    index0 = int(line.split(":")[1].split("(")[0].strip())
                    index1 = int(line.split(":")[2].split(")")[0].strip())
                    current_items['index'] = (index0, index1)
                elif line.startswith("|  + Language:"):
                    current_items['language'] = line.split(":")[1].strip()
                elif line.startswith("|  + Track type:"):
                    current_items['type'] = line.split(":")[1].strip()
        return tracks
    except subprocess.CalledProcessError:
        return []

def extract_subtitles(video_path, output_srt="output.srt", track_index=0):
    """
    使用 ffmpeg-python 提取视频中的字幕轨道，并转换为 .srt 格式
    :param video_path: 输入视频文件路径
    :param output_srt: 输出的字幕文件路径
    :param track_index: 要提取的字幕轨道索引 default=0
    """
    try:
        (
            ffmpeg
            .input(video_path)  # 输入视频文件
            .output(output_srt, map=f"0:s:{track_index}")  # 选择字幕轨道
            .run(overwrite_output=True)  # 运行并允许覆盖输出文件
        )
        print(f"字幕已提取到 {output_srt}")

    except ffmpeg.Error as e:
        print("提取字幕时出错:", e)


# "/home/ssx/code/youtube/test5.mkv"
def extract_all(video_path):
    """ 提取视频中的所有字幕轨道 """
    tracks = get_subtitle_tracks(video_path)
    paths = []
    langs = []

    for track in tracks:

        try:
            t_index = track[0]
            print("extract index=", t_index)
            subtitle_name = f"{os.path.splitext(video_path)[0]}_{t_index}.srt"
            extract_subtitles(video_path, subtitle_name, track_index=t_index)
            paths.append(subtitle_name)
            langs.append(track[2])

        except Exception as e:
            print(f"提取字幕轨道  ({track}) 时出错:", e)
        finally:
            pass

    return paths, langs


# extract_all("/home/ssx/code/youtube/test5.mkv")
# extract_subtitles("/home/ssx/code/youtube/test5.mkv", "/home/ssx/code/youtube/test5.srt", track_index=0)

# Example usage:
# video_path = "/home/ssx/code/youtube/test5.mkv"
# width, height = get_video_dimensions(video_path)
# print(f"Width: {width}, Height: {height}")


def get_video_frame_as_base64(video_path, time="00:00:01"):
    """
    Extracts a frame from a video and returns it as a base64-encoded string.

    :param video_path: Path to the video file.
    :param time: Timestamp (HH:MM:SS) to capture the frame.
    :return: Base64-encoded image string.
    """
    try:
        # Run ffmpeg and capture the output in memory
        out, _ = (
            ffmpeg
            .input(video_path, ss=time)  # Seek to the given timestamp
            .output("pipe:", format="image2", vframes=1)  # Output image to stdout
            .run(capture_stdout=True, capture_stderr=True)
        )

        # Convert the image to base64
        base64_str = base64.b64encode(out).decode("utf-8")
        return base64_str

    except ffmpeg.Error as e:
        print("FFmpeg error:", e.stderr.decode())
        return None

# Example usage:
# video_path = "/home/ssx/code/youtube/test5.mkv"
# image_base64 = get_video_frame_as_base64(video_path)
# print(image_base64[:100] + "...")  # Print first 100 chars for preview

GLOBAL_EMBEDDING_RAW_CAPTION = {

}


def extract_subtitle_as_string(video_path, track_index=0):
    """
    Extract subtitle track as string using ffmpeg without showing a black window.

    :param video_path: Input video file path
    :param track_index: Subtitle track index to extract
    :return: Subtitle content as string
    """
    try:
        # Use pipe output to get subtitle content directly
        ffmpeg_cmd = (
            ffmpeg.input(video_path)
            .output('pipe:', map=f'0:s:{track_index}', format='srt')
            .compile()
        )

        # Platform-specific settings
        startupinfo = None
        creationflags = 0

        if sys.platform == "win32":  # Windows: Hide black console window
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            creationflags = subprocess.CREATE_NO_WINDOW
        else:  # macOS & Linux: Redirect output to prevent terminal popups
            creationflags = 0

        process = subprocess.Popen(
            ffmpeg_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            startupinfo=startupinfo,
            creationflags=creationflags
        )

        out, _ = process.communicate()
        return out.decode('utf-8')

    except ffmpeg.Error as e:
        print("Error extracting subtitle:", e)
        return None

def extract_all_as_strings(video_path):
    """ Extract all subtitle tracks as strings """
    tracks = get_subtitle_tracks(video_path)
    subtitles = []
    langs = []

    for track in tracks:
        try:
            t_index = track[0]
            print("extracting subtitle index=", t_index)
            subtitle_content = extract_subtitle_as_string(video_path, track_index=t_index)
            if subtitle_content:
                subtitles.append(subtitle_content)
                langs.append(track[2])
        except Exception as e:
            print(f"Error extracting subtitle track {track}:", e)

    return subtitles, langs

if __name__ == "__main__":
    video_path = "/home/ssx/code/youtube/test5.mkv"
    tracks = get_subtitle_tracks_v2(video_path)
    for track in tracks:
        print(track)