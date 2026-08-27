import re
import generalfunctions as gf
from pathlib import Path
import pandas as pd
import numpy as np
import yaml
import ast

def get_file_and_pcodes(participant_doc):
    """
    :param participant_doc: a doc containing file names and codes
    :return: a dataframe containing the same info as the doc, but with codes aggrecated across files.
    """

    partdf = pd.read_csv(participant_doc)

    filtdf = partdf[partdf['skip'] == 0]

    aggdf = filtdf.groupby('file')['code'].apply(list).reset_index()

    return aggdf

class TextExtraction:
    """
    stores methods to preprocess text.
    Input: a file with text (.flo.cex)
    Output: a list containing each list. The nested lists each contain one utterance.
    """
    def __init__(self,method_list=[]):
        self.dict_methods = {  "m01": self.m01
                                ,"m01b": self.m01b
                                ,"m02": self.m02
                                ,"m03": self.m03
                                ,"m04a": self.m04a
                                ,"m04b": self.m04b
                                ,"m05": self.m05
                                ,"m06": self.m06
                                ,"m07": self.m07
                               ,"m08": self.m08
                               ,"m09": self.m09
                               ,"m10": self.m10
                               ,"m11": self.m11
                               ,"m12b": self.m12b
                               ,"m13": self.m13
                               ,"m14": self.m14
                               ,"m15": self.m15
                               ,"m16": self.m16
                               ,"m17": self.m17
                               ,"m18": self.m18
                               ,"m19": self.m19
                               ,"m20a": self.m20a
                               ,"m20b": self.m20b
                               ,"m21": self.m21
                               ,"m22": self.m22
                               ,"m23": self.m23
                               ,"m24a": self.m24a
                               ,"m24b": self.m24b
                               ,"m25a": self.m25a
                               ,"m25b": self.m25b
                               ,"m26": self.m26
                               ,"m27": self.m27
                               ,"m28a": self.m28a
                               ,"m28b": self.m28b
                               ,"m29a": self.m29a
                               ,"m29b": self.m29b
                               ,"m30": self.m30
                               ,"m31": self.m31
                               ,"m32": self.m32
                               ,"m33": self.m33
                               ,"m34a": self.m34a
                               ,"m34b": self.m34b
                               ,"m35a": self.m35a
                               ,"m35b": self.m35b
                               ,"m36": self.m36
                               ,"m37a": self.m37a
                               ,"m37b": self.m37b
                               ,"m38": self.m38
                               ,"m39": self.m39
                               ,"m40": self.m40
                               ,"m41": self.m41
                               ,"m42": self.m42
                               ,"m43": self.m43
                               ,"m99a": self.m99a
                               ,"m99z": self.m99z
                             }
        if not (type(method_list) is list):
            raise TypeError("method_list must be a list")

        if not bool(method_list):
            print("Text processing method set to default: m01")
            self.method_list = ["m01"]
        else:
            self.method_list = method_list


    def m01(self, prevtier:str, line:str):
        """
        method 1: extract the %flo line from .cha. but append the code of the main tier.
        """
        tier, text = line.split(':',maxsplit = 1)

        if tier.startswith("*"):
                return [tier, ""]
        elif tier.startswith("%flo"):
            return [tier, text.strip()]

        return ["",""]

    def m01b(self,prevtier:str, line:str):
        """
        method 1b: extract the * line from .cha also removes the tab at the beginning of the line.
        """
        if line.startswith("*"):
            tier, text = line.split(':', maxsplit=1)
            return [tier, text.strip()]
        else:
            return ["", ""]

    def m02(self, prevtier:str, line:str):
        """
        method 2: removes ELAN code at the end of lies.
        """
        match = re.search(r'[.!?](?!.*[.!?])', line)
        if match:
           return [prevtier,line[:match.end()].strip()]
        else:
           return [prevtier,line.strip()]

    def m03(self, prevtier:str, line:str): pass

    def m04a(self, prevtier:str, line:str):
        """
        method 4a: keep text in parentheses if they only include a mix of letters, whitespaces or punctuation.
        """
        line = re.sub(r'\(([A-Za-z\s,!?;:\–—-]+)\)', r'\1', line)
        return [prevtier, line]

    def m04b(self, prevtier: str, line: str):
        """
        method 4b: remove parentheses (and their contents) if they only include a mix of letters, whitespaces or punctuation.
        """
        line = re.sub(r'\([A-Za-z\s,!?;:\–—-]+\)', '', line)
        return [prevtier, line]

    def m05(self, prevtier:str, line:str):
        """
        method 5: remove special form markers: from @ to next whitespace, including punctuation
        """
        line = re.sub(r'@\w*', '', line)
        return [prevtier, line]

    def m06(self, prevtier:str, line:str):
        """
        method 6: replace www with nothing.
        """
        line = re.sub(r'www', '', line)
        return [prevtier, line]

    def m07(self, prevtier:str, line:str):
        """
        method 7: replace xxx with single . .
        """
        line = re.sub(r'xxx', '.', line)
        return [prevtier, line]

    def m08(self, prevtier:str, line:str):
        """
        method 8: replace yyy with single . .
        """
        line = re.sub(r'yyy', '.', line)
        return [prevtier, line]

    def m09(self, prevtier: str, line: str):
        """
        method 09: audio and video time marks
        """
        line = re.sub(r'[-]*\d+_\d+', '', line)
        line = re.sub(r'%pic: ?[\w]+\.[\w]+', '', line)
        line = re.sub(r'%text: ?[\w]+\.[\w]+', '', line)
        return [prevtier, line]

    def m10(self, prevtier:str, line:str):
        """
        method 10: remove words that were missing but still inserted by transcriber.
        """
        line = re.sub(r'\b0\w+', '', line)
        return [prevtier, line]

    def m11(self, prevtier:str, line:str):
        """
        method 11: underscore removal
        """
        def merge_singles(match):
            return match.group(0).replace('_', '')
        line = re.sub(r'\b[A-Za-z0-9](?:_[A-Za-z0-9])+\b', merge_singles, line)
        line = line.replace('_', ' ')

        return [prevtier, line]

    def m12b(self, prevtier: str, line: str):
        """
        method 12b: remove brackets (and their contents) if they only include a mix of letters, whitespaces or punctuation.
        """
        line = re.sub(r'[\(\[][A-Za-z\s,!?;:\–—-]+[\)\]]', '', line)
        return [prevtier, line]

    def m13(self, prevtier: str, line: str):
        """
        method 13: : used to denote long vowels.
        """
        line = re.sub(r'(?<=[a-z]):(?=[a-z])', '', line)
        return [prevtier, line]

    def m14(self, prevtier:str, line:str):
        """
        method 14: remove satellite markers
        """
        line = re.sub(r'[‡]|,,', '', line)
        return [prevtier, line]

    def m15(self, prevtier:str, line:str):
        """
        method 15: remove tonal direction markers
        """
        line = re.sub(r'↑|↓|-!|-\?', '', line)
        if not line.strip().endswith(('.','?','!')):
            line = line.strip() + ' .'
        return [prevtier, line]

    def m16(self, prevtier:str, line:str):
        """
        method 16: remove stress
        """
        line = re.sub(r'[\u02C8\u02CC^]', '', line)
        return [prevtier, line]

    def m17(self):pass

    def m18(self):pass

    def m19(self, prevtier:str, line:str):
        """
        method 19: replace time of pauses with pauses
        """
        line = re.sub(r'\([\d:.]+\)', '(.)', line)
        return [prevtier, line]

    def m20a(self, prevtier:str, line:str):
        """
        method 20a: keep pauses but remove parentheses around them (any parentheses with only a dot or whitespace inside)
        """
        line = re.sub(r'\(([.\s]+)\)', r'\1', line)
        return [prevtier, line]

    def m20b(self, prevtier:str, line:str):
        """
        method 20b: remove pauses (any parentheses with only a dot or whitespace inside)
        """
        line = re.sub(r'\(([.\s]+)\)', '', line)
        return [prevtier, line]

    def m21(self, prevtier:str, line:str):
        """
        method 21: remove actions
        """
        line = re.sub(r'&=\S+:\S+', '', line)
        line = re.sub(r'&=', '', line)
        return [prevtier, line]

    def m22(self, prevtier:str, line:str): pass

    def m23(self, prevtier:str, line:str):
        """
        method 23: remove insertion by other speakers
        """
        line = re.sub(r'\*&\S*', '', line)
        return [prevtier, line]

    def m24a(self, prevtier:str, line:str):
        """
        method 24a keep long vocal events (laughter)
        """
        line = re.sub(r'\&[\{\}]+l=(\S*)', r'\1', line)
        return [prevtier, line]

    def m24b(self, prevtier:str, line:str):
        """
        method 24b remove long vocal events (laughter)
        """
        line = re.sub(r'\&[\{\}]+l=(\S*)', '', line)
        return [prevtier, line]

    def m25a(self, prevtier: str, line: str):
        """
        method 25a keep long nonvocal events (waving)
        """
        line = re.sub(r'\&[\{\}]+n=(\S*)', r'\1', line)
        return [prevtier, line]

    def m25b(self, prevtier: str, line: str):
        """
        method 25b remove long nonvocal events (waving)
        """
        line = re.sub(r'\&[\{\}]+n=(\S*)', '', line)
        return [prevtier, line]

    def m26(self):pass

    def m27(self, prevtier: str, line: str):
        """
        method 27: remove indications for fragments, fillers, and non-words, keeping the actual items.
        """
        line = re.sub(r'&\+|&-|&~|&', '', line)
        return [prevtier, line]

    def m28a(self, prevtier: str, line: str):
        """
        method 28a: keep trailing off
        """
        line = re.sub(r'\+\.\.\.', '...', line)
        line = re.sub(r'\+\.\.\?', '..?', line)
        return [prevtier, line]

    def m28b(self, prevtier: str, line: str):
        """
        method 28b: remove trailing off
        """
        line = re.sub(r'\+\.\.\.', '', line)
        line = re.sub(r'\+\.\.\?', '', line)
        return [prevtier, line]

    def m29a(self, prevtier: str, line: str):
        """
        method 29a: keep exclamation question
        """
        line = re.sub(r'\+!\?', '!?', line)
        return [prevtier, line]

    def m29b(self, prevtier: str, line: str):
        """
        method 29b: remove exclamation question
        """
        line = re.sub(r'\+!\?', '?', line)
        return [prevtier, line]

    def m30(self, prevtier: str, line: str):
        """
        method 30: remove interuptions
        """
        line = re.sub(r'\+//|\+/|\+,', '', line)
        line = re.sub(r'\+\.', '.', line)
        return [prevtier, line]

    def m31(self, prevtier: str, line: str):
        """
        method 31: remove quotes
        """
        line = re.sub(r'\+"/|\+"', '', line)
        return [prevtier, line]

    def m32(self, prevtier: str, line: str):
        """
        method 32: remove quick uptake
        """
        line = re.sub(r'\+\^', '', line)
        return [prevtier, line]

    def m33(self, prevtier: str, line: str):
        """
        method 33: remove completion
        """
        line = re.sub(r'\+,|\+\+', '', line)
        return [prevtier, line]

    def m34a(self, prevtier: str, line: str):
        """
        method 34: keep paralinguistic material
        """
        line = re.sub(r'<([^>]*)> \[=! ([^\]]*)\]', r'\1 \2', line)
        line = re.sub(r'\[=! ([^\]]*)\]', r'\1', line)
        return [prevtier, line]

    def m34b(self, prevtier: str, line: str):
        """
        method 34: removes paralinguistic material
        """
        line = re.sub(r'<([^>]*)> \[=! ([^\]]*)\]', r'\1', line)
        line = re.sub(r'\[=! [^\]]*\]', r'', line)
        return [prevtier, line]

    def m35a(self, prevtier: str, line: str):
        """
        method 35a: keep stressing, essentially an exclamation mark.
        """
        line = re.sub(r'<([^>]*)> \[!\]', r'\1 !', line)
        line = re.sub(r'\[(!!)\]|\[(!)\]', '!', line)
        return [prevtier, line]

    def m35b(self, prevtier: str, line: str):
        """
        method 35a: remove stressing, essentially an exclamation mark.
        """
        line = re.sub(r'<([^>]*)> \[!\]', r'\1', line)
        line = re.sub(r'\[!!\]|\[!\]', '', line)
        return [prevtier, line]

    def m36(self, prevtier: str, line: str):
        """
        method 36: remove target words (when people read and make a mistake)
        """
        line = re.sub(r'\[= [^\]]*\]', '', line)
        return [prevtier, line]

    def m37a(self, prevtier: str, line: str):
        """
        method 37a: replace word (don't to do not)
        """
        line = re.sub(r' [\w]* \[: ([^\]]*)\]', r'\1', line)
        return [prevtier, line]

    def m37b(self, prevtier: str, line: str):
        """
        method 37b: remove replacement word (don't to do not), keep original
        """
        line = re.sub(r'\[: [^\]]*\]', '', line)
        return [prevtier, line]

    def m38(self, prevtier: str, line: str):
        """
        method 38: remove error notation [*]
        """
        line = re.sub(r'\[\*\]', '', line)
        return [prevtier, line]

    def m39(self, prevtier: str, line: str):
        """
        method 39: remove alternative transcription
        """
        line = re.sub(r'<([^>]*)> \[=\? [^\]]*\]', r'\1', line)
        return [prevtier, line]

    def m40(self, prevtier: str, line: str):
        """
        method 40: remove inline comments
        """
        line = re.sub(r'\[=% [^\]]*\]', r'', line)
        return [prevtier, line]

    def m41(self, prevtier: str, line: str):
        """
        method 41: remove overlapping notation <blah blah> [<] and  <blah blah> [>]
        """
        line = re.sub(r'<([^>]*)> \[\d*>\]', r'\1', line)
        line = re.sub(r'<([^>]*)> \[\d*<\]', r'\1', line)
        line = re.sub(r'\+<', r'', line)
        return [prevtier, line]

    def m42(self, prevtier: str, line: str):
        """
        method 42: removal of repetition notation <blah blah> [/], reformulation , retracing, etc.
        """
        line = re.sub(r'<([^>]*)> \[/\]', r'\1', line)
        line = re.sub(r'<([^>]*)> \[//\]', r'\1', line)
        line = re.sub(r'<([^>]*)> \[///\]', r'\1', line)
        line = re.sub(r'<([^>]*)> \[e\]', r'\1', line)
        line = re.sub(r'\[/\]', '', line)
        line = re.sub(r'\[/-\]', '', line)
        return [prevtier, line]

    def m43(self, prevtier: str, line: str):
        """
        method 43: removal of postcodes (added code at the end of lines
        """
        line = re.sub(r'\[+ [^\]]*/\]', r'', line)
        return [prevtier, line]

    def m99a(self, prevtier:str, line:str):
        """
        method 99a: replace any set of more than 1 subsequent whitespace with a single whitespace.
        """
        line = re.sub(r'\s{2,}', ' ', line)
        return [prevtier, line]

    def m99z(self, prevtier: str, line: str):
        """
        method 99b: remove any text that consist solely of a single . , any number of whitspaces  and the tier
        """
        #if line.strip()[]
        line = re.sub(r'^\s*\.\s*$', '', line)
        return [prevtier, line]

    def single_preprocess(self, task:str, filepath:str, code_list:list, method_list = None, print_warnings = True):
        """
        processes text based on specified method and either output the cleaned text or the number of lines in the text.
        :param filepath:
        :param code_list: list of speaker codes to extract. must be in caps, like in the files.
        :param method:
                    m1 - extract the %flo line from .cha. but append the code of the main tier.
        :param task: "clean" or "count" whether to extract cleaned text or to count the number of lines of cleaned text.
        :return:
        """
        if task not in ["clean", "count"]:
            raise ValueError("Invalid task: expected 'clean' or 'count'")

        if method_list is None:
            method_list = self.method_list

        if print_warnings:
            if method_list != sorted(method_list):
                print("methods are not listed in ascending order, this may cause issue or inefficiency. Analyses are still carried out, but consider changing the order of the methods.")

        tier = ""
        cleaned_text = []
        numline = 0

        with open(filepath, 'r') as f:
            for line in f:
                #Loops through preprocessing steps
                for metho in method_list:
                    tier,line = self.dict_methods[metho](prevtier,line)
                    if not line:
                        break

                if line:
                    nline = f"{tier}:{line}"
                    if task == "count":
                        if tier[1:].lower() in code_list:
                            numline += 1
                    else:
                        cleaned_text.append(nline)

        if task == "count":
            return numline
        elif task=="clean":
            return cleaned_text

    def serial_count(self, participant_df, text_folder):
        """
        :param task:
        :param participant_df: a dataframe containing a column "file" with filenames and "code" with all codes of interest.
        :return:
        """
        self.participant_df = participant_df

        tfile = participant_df["file"].iloc[0]
        fext = ''.join(list(Path(text_folder).glob(f"{tfile}.*"))[0].suffixes) #get the suffix

        out_list = []

        for pp,code_list in zip(participant_df["file"], participant_df["code"]):
            filepath = str(Path(text_folder,pp).with_suffix(fext))

            out_list.append(self.single_preprocess("count",filepath,code_list))

        return out_list

    def serial_clean(self, participant_df, text_folder):
        """
        :param task:
        :param participant_df: a dataframe containing a column "file" with filenames and "code" with all codes of interest.
        :return:
        """
        self.participant_df = participant_df

        tfile = participant_df["file"].iloc[0]
        fext = ''.join(list(Path(text_folder).glob(f"{tfile}.*"))[0].suffixes) #get the suffix

        ffile = []
        fspeaker = []
        fsentence = []
        fcode = []


        for pp,code_list in zip(participant_df["file"], participant_df["code"]):
            filepath = str(Path(text_folder,pp).with_suffix(fext))

            temp = self.single_preprocess("clean",filepath,code_list)

            tspeaker = []
            tsentence = []

            for tt in temp:
                tc, ts = tt.split(":", maxsplit=1)
                tspeaker.append(tc[1:].lower())
                tsentence.append(ts)

            tfile = [pp] *len(tsentence)
            tcode = [code_list for _ in range(len(tsentence))]

            ffile.extend(tfile)
            fspeaker.extend(tspeaker)
            fsentence.extend(tsentence)
            fcode.extend(tcode)

        return ffile, fspeaker, fsentence, fcode

class Allocator():
    def __init__(self, participant_df, text_folder, extractor):
        """
        :param participant_df : dataframe with columns "file" and "code"
        :param extractor: TextExtraction class
        """
        self.participant_df = get_file_and_pcodes(participant_df)
        self.text_folder = text_folder
        self.extractor = extractor
        self.allocation_info = {}

    def allocate(self, binmax:int, save2self = True):
        """
        Solve the Bin Packing Problem using the Best Fit (I think) method
        Essentially: add task to the bin with the closest amount of space to allow it.
        Any file with an empty number of lines is filtered in the process.
        :param fillist : list of file names
        :param weilist: list of weights of tasks for each file name
        :param binmax: the maximum number of tasks to allow in each core
        :output: either a tuple of nbin, bincontents, binweight
                or save the tuple into a dictionary in self.allocation_info
        """
        filelist = list(self.participant_df["file"])
        weilist = self.extractor.serial_count(self.participant_df,self.text_folder)

        order = np.argsort(weilist)[::-1]
        filelist = np.array(filelist)[order]
        weilist = np.array(weilist)[order]
        nbin = 1
        bincontents = [[]]
        binweight = [0]

        for ff,ww in zip(filelist,weilist):
            if ww == 0: continue

            for bb in range(len(binweight)):
                if binweight[bb] + ww <= binmax:
                    binweight[bb]+= ww
                    bincontents[bb].append(ff)

                    #resort binweighte and content
                    binweight, bincontents = gf.oneway_bubble_sort(binweight, bincontents)

                    break

                if bb == len(binweight)-1:
                    bincontents.append([ff])
                    binweight.append(ww)
                    nbin += 1

                    binweight, bincontents = gf.oneway_bubble_sort(binweight, bincontents)

        if save2self:
            self.allocation_info["nbin"] = nbin
            self.allocation_info["bincontents"] = bincontents
            self.allocation_info["binweight"] = binweight
        else:
            return nbin, bincontents, binweight

    def write_allocation(self,baseconfig):
        if not self.allocation_info:
            raise ValueError("No allocation_info found. Please run allocate() first.")

        for ii,tcontent in enumerate(self.allocation_info["bincontents"]):

            # write transcript file
            csvfname = f"files_block_{ii}.csv"

            tempdf = pd.DataFrame(tcontent,columns=['file'])
            tempdf = tempdf.merge(self.participant_df[['file', 'code']], on='file', how='left')

            tempdf.to_csv(str(Path(baseconfig["config_folder"], csvfname)), index=False)

            #write yaml
            baseconfig["transcript_file_list"] = csvfname
            baseconfig["output_file"] = str(Path(baseconfig["output_folder"],f"output_block_{ii}.csv"))
            yamlfname = str(Path(baseconfig["config_folder"], f"config_block_{ii}").with_suffix(".yaml"))

            with open(yamlfname, 'w') as outfile:
                yaml.dump(baseconfig, outfile, default_flow_style=False, sort_keys=False)

        return ii