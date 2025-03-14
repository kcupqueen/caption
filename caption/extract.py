import os

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
            raise ValueError("No video stream found")

    except ffmpeg.Error as e:
        print("FFmpeg error:", e.stderr.decode())
        return None




def get_subtitle_tracks(video_path):
    """ 获取视频文件的字幕轨道信息 """
    metadata = ffmpeg.probe(video_path)
    subtitle_tracks = []
    
    for stream in metadata['streams']:
        print(stream)
        if stream['codec_type'] == 'subtitle':
            track_index = stream['index']
            codec_name = stream.get('codec_name', 'unknown')
            language = stream['tags'].get('language', 'unknown') if 'tags' in stream else 'unknown'
            subtitle_tracks.append((track_index, codec_name, language))
    
    return subtitle_tracks

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
    i = 0
    for track in tracks:
        print(f"extract track {i} ({track})...")
        try:
            t_index = track[0]
            print("extract index=", i)
            subtitle_name = f"{os.path.splitext(video_path)[0]}_{t_index}.srt"
            extract_subtitles(video_path, subtitle_name, track_index=i)
            paths.append(subtitle_name)
            langs.append(track[2])

        except Exception as e:
            print(f"提取字幕轨道 {i} ({track}) 时出错:", e)
        finally:
            i += 1
    return paths,langs

#extract_all("/home/ssx/code/youtube/test5.mkv")
#extract_subtitles("/home/ssx/code/youtube/test5.mkv", "/home/ssx/code/youtube/test5.srt", track_index=0)

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
