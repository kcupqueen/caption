import webvtt


def get_captions(vtt_file):
    captions = []
    i = 0
    for caption in webvtt.read(vtt_file):
        x = {'caption': caption, 'seq': i}
        i += 1
        x['caption'].start_in_milliseconds = time_to_milliseconds(caption.start)
        x['caption'].end_in_milliseconds = time_to_milliseconds(caption.end)
        captions.append(x)
        print(x['caption'].start_in_milliseconds, x['caption'].end_in_milliseconds)

    return captions

def find_caption(currentTime, captionList, cur_seq):
    seq = -1
    # get max seq form set
    if cur_seq and len(cur_seq) > 0:
        seq = max(cur_seq)
    start = 0
    if seq != -1:
        start = seq
    for i in range(start, len(captionList)):
        if captionList[i]['caption'].end_in_milliseconds > currentTime:
            seq = i
            break
    if seq != -1 and seq < len(captionList):
        return captionList[seq]

    return None


def time_to_milliseconds(time_str):
    # 分割时间字符串
    hours, minutes, seconds = time_str.split(':')

    # 分割秒和毫秒部分
    seconds, milliseconds = seconds.split('.')

    # 转换为整数
    hours = int(hours)
    minutes = int(minutes)
    seconds = int(seconds)
    milliseconds = int(milliseconds)

    # 计算总毫秒数
    total_milliseconds = (hours * 3600 + minutes * 60 + seconds) * 1000 + milliseconds

    return total_milliseconds