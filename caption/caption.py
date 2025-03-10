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

htmlTemplateCaption = '''<body>
    <style>
        h3 {{
            font-family: "Arial", sans-serif; /* Modern, clean font */
            font-size: 24px; /* Medium website-style font size */
            color: #333333; /* Dark gray text for readability */
            text-align: center; /* Center the text */
            font-weight: 600; /* Medium-bold text */
            margin-top: 20px;
        }}
    </style>

    <h3>{}</h3>
</body>
'''

htmlTemplateWelcome = '''<body>
    <style>
        h1 {{
            font-family: "Georgia", serif; /* Medium uses a serif font for article titles */
            font-size: 36px; /* Large size for article titles */
            color: #222222; /* Dark gray for contrast */
            text-align: center; /* Centered title */
            font-weight: bold; /* Strong presence */
            line-height: 1.3; /* Good readability */
            margin-top: 40px;
            margin-bottom: 20px;
        }}
    </style>

    <h1>{}</h1>
</body>
'''



def get_template(t_type, txt):
    if t_type == 'caption':
        return htmlTemplateCaption.format(txt)
    else:
        return htmlTemplateWelcome.format(txt)

# content_type enum
class LookUpType:
    WORD = 1
    SENTENCE = 2

def lookup_caption(content, content_type):
    if content_type == LookUpType.WORD:
        # mock data
        return '报复；报仇'
    elif content_type == LookUpType.SENTENCE:
        return '请问，你是如何理解哈姆雷特一直拖延为父复仇这件事的？'
    else:
        return None

