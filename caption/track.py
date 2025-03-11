import ffmpeg

def get_tracks(file_path):
    probe = ffmpeg.probe(file_path)

    audio_tracks = []
    subtitle_tracks = []

    for stream in probe["streams"]:
        lang = stream.get("tags", {}).get("language", "Unknown")  # 获取语言信息
        if stream["codec_type"] == "audio":
            audio_tracks.append({
                "index": stream["index"],
                "codec": stream["codec_name"],
                "channels": stream.get("channels", "N/A"),
                "language": lang
            })
        elif stream["codec_type"] == "subtitle":
            subtitle_tracks.append({
                "index": stream["index"],
                "codec": stream["codec_name"],
                "language": lang
            })

    # 输出音轨信息
    print("\n🎵 Audio Tracks:")
    for track in audio_tracks:
        print(
            f"  - Index: {track['index']}, Codec: {track['codec']}, Channels: {track['channels']}, Language: {track['language']}")

    # 输出字幕轨信息
    print("\n📜 Subtitle Tracks:")
    for track in subtitle_tracks:
        print(f"  - Index: {track['index']}, Codec: {track['codec']}, Language: {track['language']}")


get_tracks("/home/ssx/code/youtube/test5.mkv")
