import ffmpeg

def get_subtitle_tracks(video_path):
    """ 获取视频文件的字幕轨道信息 """
    metadata = ffmpeg.probe(video_path)
    subtitle_tracks = []
    
    for stream in metadata['streams']:
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

ts = get_subtitle_tracks("/home/ssx/code/youtube/test5.mkv")
for t in ts:
    print(t)
 
# 使用示例
extract_subtitles("/home/ssx/code/youtube/test5.mkv", "./output.srt", track_index=0)
