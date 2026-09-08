import re

def m01(tier: str, line: str):
    """
    method 1: extract the %flo line from .cha. but append the code of the main tier.
    """
    curr_tier, text = line.split(':', maxsplit=1)

    if curr_tier.startswith("*"):
        return [curr_tier, ""]
    elif curr_tier.startswith("%flo"):
        return [tier, text.strip()]

    return ["", ""]

def m01b(tier: str, line: str):
    """
    method 1b: extract the * line from .cha also removes the tab at the beginning of the line.
    """
    if line.startswith("*"):
        tier, text = line.split(':', maxsplit=1)
        return [tier, text.strip()]
    else:
        return ["", ""]

def m02(tier: str, line: str):
    """
    method 2: removes ELAN code at the end of lies.
    """
    match = re.search(r'[.!?](?!.*[.!?])', line)
    if match:
        return [tier, line[:match.end()].strip()]
    else:
        return [tier, line.strip()]

def m03(tier: str, line: str): pass

def m04a(tier: str, line: str):
    """
    method 4a: keep text in parentheses if they only include a mix of letters, whitespaces or punctuation.
    Example: (be)cause to because
    """
    line = re.sub(r'\(([A-Za-z\s,!?;:\–—-]+)\)', r'\1', line)
    return [tier, line]

def m04b(tier: str, line: str):
    """
    method 4b: remove parentheses (and their contents) if they only include a mix of letters, whitespaces or punctuation.
    Example: (be)cause to cause
    """
    line = re.sub(r'\([A-Za-z\s,!?;:\–—-]+\)', '', line)
    return [tier, line]

def m05(tier: str, line: str):
    """
    method 5: remove special form markers: from @ to next whitespace, including punctuation
    Example @baby to baby
    """
    line = re.sub(r'@\w*', '', line)
    return [tier, line]

def m06(tier: str, line: str):
    """
    method 6: replace www with nothing.
    """
    line = re.sub(r'www', '', line)
    return [tier, line]

def m07(tier: str, line: str):
    """
    method 7: replace xxx with single . .
    """
    line = re.sub(r'xxx', '.', line)
    return [tier, line]

def m08(tier: str, line: str):
    """
    method 8: replace yyy with single . .
    """
    line = re.sub(r'yyy', '.', line)
    return [tier, line]

def m09(tier: str, line: str):
    """
    method 09: remove audio and video time marks
    Example: ·0_1073·
            ·%pic: cat.jpg·
            ·%txt: cat.txt·
    """
    line = re.sub(r'[-]*\d+_\d+', '', line)
    line = re.sub(r'%pic: ?[\w]+\.[\w]+', '', line)
    line = re.sub(r'%text: ?[\w]+\.[\w]+', '', line)
    return [tier, line]

def m10(tier: str, line: str):
    """
    method 10: remove words that were missing but still inserted by transcriber.
    Example : say that 0word to say that
    """
    line = re.sub(r'\b0\w+', '', line)
    return [tier, line]

def m11(tier: str, line: str):
    """
    method 11: underscore removal
    """

    def merge_singles(match):
        return match.group(0).replace('_', '')

    line = re.sub(r'\b[A-Za-z0-9](?:_[A-Za-z0-9])+\b', merge_singles, line)
    line = line.replace('_', ' ')

    return [tier, line]

def m12b(tier: str, line: str):
    """
    method 12b: remove brackets (and their contents) if they only include a mix of letters, whitespaces or punctuation.
    """
    line = re.sub(r'[\(\[][A-Za-z\s,!?;:\–—-]+[\)\]]', '', line)
    return [tier, line]

def m13(tier: str, line: str):
    """
    method 13: : used to denote long vowels.
    Example: ba:by to baby
    """
    line = re.sub(r'(?<=[a-z]):(?=[a-z])', '', line)
    return [tier, line]

def m14(tier: str, line: str):
    """
    method 14: remove satellite markers
    Removes: ‡
    """
    line = re.sub(r'[‡]|,,', '', line)
    return [tier, line]

def m15(tier: str, line: str):
    """
    method 15: remove tonal direction markers
    Removes ↑,↓,-!,-?'
    """
    line = re.sub(r'↑|↓|-!|-\?', '', line)
    if not line.strip().endswith(('.', '?', '!')):
        line = line.strip() + ' .'
    return [tier, line]

def m16(tier: str, line: str):
    """
    method 16: remove stress
    Example: baby want baˈna:nas to baby want bananas
    """
    line = re.sub(r'[\u02C8\u02CC^]', '', line)
    return [tier, line]

def m17(tier, line): pass

def m18(tier, line): pass

def m19(tier: str, line: str):
    """
    method 19: replace time of pauses with pauses
    Example: (0.5) to (.)
    """
    line = re.sub(r'\([\d:.]+\)', '(.)', line)
    return [tier, line]

def m20a(tier: str, line: str):
    """
    method 20a: keep pauses but remove parentheses around them (any parentheses with only a dot or whitespace inside)
    Example (.) to .
    """
    line = re.sub(r'\(([.\s]+)\)', r'\1', line)
    return [tier, line]

def m20b(tier: str, line: str):
    """
    method 20b: remove pauses (any parentheses with only a dot or whitespace inside)
    Example (.) to
    """
    line = re.sub(r'\(([.\s]+)\)', '', line)
    return [tier, line]

def m21(tier: str, line: str):
    """
    method 21: remove actions
    Example: don't &=shakehead:action do that to don't do that
    """
    line = re.sub(r'&=\S+:\S+', '', line)
    line = re.sub(r'&=', '', line)
    return [tier, line]

def m22(tier: str, line: str): pass

def m23(tier: str, line: str):
    """
    method 23: remove insertion by other speakers
    Example I think *MOT:mhm I like it to I think I like it.
    """
    line = re.sub(r'&\*\S*', '', line)
    return [tier, line]

def m24a(tier: str, line: str):
    """
    method 24a keep long vocal events (laughter)
    Example: say &{l=laughing goodbye &}n=laughing to say laughing goodbye laughing
    """
    line = re.sub(r'\&[\{\}]+l=(\S*)', r'\1', line)
    return [tier, line]

def m24b(tier: str, line: str):
    """
    method 24b remove long vocal events (laughter)
    Example: say &{l=laughing goodbye &}n=laughing to say goodbye
    """
    line = re.sub(r'\&[\{\}]+l=(\S*)', '', line)
    return [tier, line]

def m25a(tier: str, line: str):
    """
    method 25a keep long nonvocal events (waving)
    Example: say &{n=waving goodbye &}n=waving to say waving goodbye waving
    """
    line = re.sub(r'\&[\{\}]+n=(\S*)', r'\1', line)
    return [tier, line]

def m25b(tier: str, line: str):
    """
    method 25b remove long nonvocal events (waving)
    Example: say &{n=waving goodbye &}n=waving to say goodbye
    """
    line = re.sub(r'\&[\{\}]+n=(\S*)', '', line)
    return [tier, line]

def m26(): pass

def m27(tier: str, line: str):
    """
    method 27: remove indications for fragments, fillers, and non-words, keeping the actual items.
    Example: &-uh, &+r-r-r-r (disfluency), &~biblu (non-word)
    """
    line = re.sub(r'&\+|&-|&~|&', '', line)
    return [tier, line]

def m28a(tier: str, line: str):
    """
    method 28a: keep trailing off
    Example +... or +..? to ... or ..?
    """
    line = re.sub(r'\+\.\.\.', '...', line)
    line = re.sub(r'\+\.\.\?', '..?', line)
    return [tier, line]

def m28b(tier: str, line: str):
    """
    method 28b: remove trailing off
    Example +... or +..?
    """
    line = re.sub(r'\+\.\.\.', '', line)
    line = re.sub(r'\+\.\.\?', '', line)
    return [tier, line]

def m29a(tier: str, line: str):
    """
    method 29a: keep exclamation question
    Example +!? to !?
    """
    line = re.sub(r'\+!\?', '!?', line)
    return [tier, line]

def m29b(tier: str, line: str):
    """
    method 29b: remove exclamation question
    Example +!? to nothing
    """
    line = re.sub(r'\+!\?', '?', line)
    return [tier, line]

def m30(tier: str, line: str):
    """
    method 30: remove interuptions
    Example
        *MOT: what did you +/.
        *SAR: Mommy.
        *MOT: +, with your spoon.

        Here, the +/. and +, are removed, leaving "what did you" and "with your spoon."
    """
    line = re.sub(r'\+//|\+/|\+,', '', line)
    line = re.sub(r'\+\.', '.', line)
    return [tier, line]

def m31(tier: str, line: str):
    """
    method 31: remove quotes
    Example +"/ or +"
    """
    line = re.sub(r'\+"/|\+"', '', line)
    return [tier, line]

def m32(tier: str, line: str):
    """
    method 32: remove quick uptake
    Example +^ when someone speaks immediately after another speaker.
    """
    line = re.sub(r'\+\^', '', line)
    return [tier, line]

def m33(tier: str, line: str):
    """
    method 33: remove completion
    Example +, or ++ when someone completes their own sentence.
    """
    line = re.sub(r'\+,|\+\+', '', line)
    return [tier, line]

def m34a(tier: str, line: str):
    """
    method 34: keep paralinguistic material
    Example: <blah blah> [=! cries] to blah blah cries
    """
    line = re.sub(r'<([^>]*)> \[=! ([^\]]*)\]', r'\1 \2', line)
    line = re.sub(r'\[=! ([^\]]*)\]', r'\1', line)
    return [tier, line]

def m34b(tier: str, line: str):
    """
    method 34: removes paralinguistic material
    Example: <blah blah> [=! cries] to blah blah
    """
    line = re.sub(r'<([^>]*)> \[=! ([^\]]*)\]', r'\1', line)
    line = re.sub(r'\[=! [^\]]*\]', r'', line)
    return [tier, line]

def m35a(tier: str, line: str):
    """
    method 35a: keep stressing, essentially an exclamation mark.
    Example: <blah blah> [!] to blah blah !
    """
    line = re.sub(r'<([^>]*)> \[!\]', r'\1 !', line)
    line = re.sub(r'\[(!!)\]|\[(!)\]', '!', line)
    return [tier, line]

def m35b(tier: str, line: str):
    """
    method 35a: remove stressing, essentially an exclamation mark.
    Example: <blah blah> [!] to blah blah
    """
    line = re.sub(r'<([^>]*)> \[!\]', r'\1', line)
    line = re.sub(r'\[!!\]|\[!\]', '', line)
    return [tier, line]

def m36(tier: str, line: str):
    """
    method 36: remove target words (when people read and make a mistake)
    Example: <blah blah> [= target] to blah blah
    """
    line = re.sub(r'\[= [^\]]*\]', '', line)
    return [tier, line]

def m37a(tier: str, line: str):
    """
    method 37a: replace word (don't to do not)
    Example: don't [: do not] to do not
    """
    line = re.sub(r' [\w]* \[: ([^\]]*)\]', r'\1', line)
    return [tier, line]

def m37b(tier: str, line: str):
    """
    method 37b: remove replacement word (don't to do not), keep original
    Example: don't [: do not] to don't
    """
    line = re.sub(r'\[: [^\]]*\]', '', line)
    return [tier, line]

def m38(tier: str, line: str):
    """
    method 38: remove error notation [*]
    Example: man when men should have been read.
    """
    line = re.sub(r'\[\*\]', '', line)
    return [tier, line]

def m39(tier: str, line: str):
    """
    method 39: remove alternative transcription
    Example: <blah blah> [=? alternative] to blah blah
    """
    line = re.sub(r'<([^>]*)> \[=\? [^\]]*\]', r'\1', line)
    return [tier, line]

def m40(tier: str, line: str):
    """
    method 40: remove inline comments
    Example: blah blah [=% comment] to blah blah
    """
    line = re.sub(r'\[=% [^\]]*\]', r'', line)
    return [tier, line]

def m41(tier: str, line: str):
    """
    method 41: remove overlapping notation <blah blah> [<] and  <blah blah> [>]
    Example:
        *SAR:and the <doggy was> [>1] really cute and it <had to go> [>2] into bed.
        *MOT:<why don't you> [<1] ?
        *MOT:<maybe we could> [<2].
    """
    line = re.sub(r'<([^>]*)> \[\d*>\]', r'\1', line)
    line = re.sub(r'<([^>]*)> \[\d*<\]', r'\1', line)
    line = re.sub(r'\+<', r'', line)
    return [tier, line]

def m42(tier: str, line: str):
    """
    method 42: removal of repetition notation <blah blah> [/], reformulation , retracing, etc.
    Examples: <I wanted> [/] I wanted to I wanted I wanted
              <I wanted> [//] &-uh I thought I wanted to
              and others with [///], [e], [/-]
    """
    line = re.sub(r'<([^>]*)> \[/\]', r'\1', line)
    line = re.sub(r'<([^>]*)> \[//\]', r'\1', line)
    line = re.sub(r'<([^>]*)> \[///\]', r'\1', line)
    line = re.sub(r'<([^>]*)> \[e\]', r'\1', line)
    line = re.sub(r'\[/\]', '', line)
    line = re.sub(r'\[/-\]', '', line)
    return [tier, line]

def m43(tier: str, line: str):
    """
    method 43: removal of postcodes (added code at the end of lines
    """
    line = re.sub(r'\[+ [^\]]*/\]', r'', line)
    return [tier, line]

def m99a(tier: str, line: str):
    """
    method 99a: replace any set of more than 1 subsequent whitespace with a single whitespace.
    """
    line = re.sub(r'\s{2,}', ' ', line)
    return [tier, line]

def m99z(tier: str, line: str):
    """
    method 99b: remove any text that consist solely of a single . , any number of whitspaces  and the tier
    """
    # if line.strip()[]
    line = re.sub(r'^\s*\.\s*$', '', line)
    return [tier, line]


#Leave at end
main_dict = {}
main_dict["default"] ={ "m01": m01 ,"m01b": m01b ,"m02": m02
                        ,"m03": m03 ,"m04a": m04a,"m04b": m04b
                        ,"m05": m05,"m06": m06, "m07": m07
                        ,"m08": m08,"m09": m09,"m10": m10
                        ,"m11": m11,"m12b": m12b,"m13": m13
                        ,"m14": m14,"m15": m15,"m16": m16
                        ,"m17": m17,"m18": m18,"m19": m19
                        ,"m20a": m20a,"m20b": m20b,"m21": m21
                        ,"m22": m22,"m23": m23,"m24a": m24a
                        ,"m24b": m24b,"m25a": m25a,"m25b": m25b
                        ,"m26": m26,"m27": m27,"m28a": m28a
                        ,"m28b": m28b,"m29a": m29a,"m29b": m29b
                        ,"m30": m30,"m31": m31,"m32": m32
                        ,"m33": m33,"m34a": m34a,"m34b": m34b
                        ,"m35a": m35a,"m35b": m35b,"m36": m36
                        ,"m37a": m37a,"m37b": m37b,"m38": m38
                        ,"m39": m39,"m40": m40,"m41": m41
                        ,"m42": m42,"m43": m43,"m99a": m99a
                        ,"m99z": m99z
                        }
def return_fx_dict(dict_name: str):
    return main_dict[dict_name]