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
        self.dict_methods = { "m01": self.m01
                             ,"m02": self.m02
                             ,"m03": self.m03
                             ,"m04": self.m04
                             }
        if not (type(method_list) is list):
            raise TypeError("method_list must be a list")

        if not bool(method_list):
            print("Text processing method set to default: m01")
            self.method_list = ["m01"]
        else:
            self.method_list = method_list


    def m01(self, line:str, prevtier:str):
        """
        method 1: extract the %flo line from .cha. but append the code of the main tier.
        """
        tier, text = line.split(':',maxsplit = 1)

        if tier.startswith("*"):
                return [tier, ""]
        elif tier.startswith("%flo"):
            return ["", f"{prevtier}:{text.strip()}"]

        return ["",""]

    def m01b(self,line:str, prevtier:str, code_list:list):
        pass

    def m02(self, line:str, prevtier:str, code_list:list):
        """
        method 2: removes ELAN code at the end of lies.
        """
        match = re.search(r'[.!?](?!.*[.!?])', line)
        if match:
           return text[:match.end()].strip()
        else:
           return line.strip()

    def m03(self, line:str, prevtier:str, code_list:list):
        """
        method 3: keeps dots found in parentheses
        """
        return re.sub(r'\(([.\s]+)\)', r'\1', line)

    def m04(self, line:str, prevtier:str, code_list:list):
        """
        method 4: keep text in parentheses if they only include a mix of letters, whitespaces or punctuation.
        """
        return re.sub(r'\(([A-Za-z\s,!?;:\–—-]+)\)', r'(\1)', line)

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

        prevtier = ""
        cleaned_text = []
        numline = 0

        with open(filepath, 'r') as f:
            for line in f:
                #Loops through preprocessing steps
                for metho in method_list:
                    prevtier,line = self.dict_methods[metho](line,prevtier)
                    if not line:
                        break

                if line:
                    if task == "count":
                        tier, _ = line.split(':', maxsplit=1)
                        if tier[1:].lower() in code_list:
                            numline += 1
                    else:
                        cleaned_text.append(line)

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