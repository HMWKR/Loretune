"""WebVTT for an immutable, approved render snapshot; never current editor drafts."""
from html import escape
from editing import srt, caption_text

def webvtt(lines, *, preserve_leading_spaces=False):
    # Share the export's millisecond rounding, while escaping VTT cue markup.
    blocks=[]
    for i,line in enumerate(lines):
        timing=srt([dict(line,text="")]).splitlines()[1].replace(",", ".")
        text=escape(caption_text(line['text']),quote=False)
        # FFmpeg's WebVTT decoder drops leading spaces without preceding markup.
        # An empty italic span leaves no formatted characters in the MP4 track.
        if preserve_leading_spaces and text.startswith(' '):text='<i></i>'+text
        blocks.append(f"{i+1}\n{timing}\n{text}")
    return ("WEBVTT\n\n"+"\n\n".join(blocks)+"\n").encode('utf-8')
