"""WebVTT for an immutable, approved render snapshot; never current editor drafts."""
from html import escape
from editing import srt

def webvtt(lines):
    # Share the export's millisecond rounding, while escaping VTT cue markup.
    blocks=[]
    for i,line in enumerate(lines):
        timing=srt([dict(line,text="")]).splitlines()[1].replace(",", ".")
        text=escape(line['text'],quote=False).replace("\r\n","\n").replace("\r","\n")
        # A blank line ends a VTT cue. NBSP preserves intentional empty text lines.
        text="\n".join(part if part else "\u00a0" for part in text.split("\n"))
        blocks.append(f"{i+1}\n{timing}\n{text}")
    return ("WEBVTT\n\n"+"\n\n".join(blocks)+"\n").encode('utf-8')
