import shutil
import os
from pathlib import Path
import pandas as pd
import re
import subprocess

from zope.interface import named

from local_main import model_folder


class MainExtractor:
    """
    This class creates a text file for each .cha file in the organized folder. The text file contains
    the raw transcript of the conversation, without any annotations.

    CLAN and the virtual environment don't work well together, can use the following lines from outside
    the virtual environment to run the code:

    import sys
    sys.path.append('/home/hereinlies/Documents/Documents/Ecole/HEC/ProjetSupervise/code/ProjetSupervise') #modify path accordingly.
    import organizer
    organized_folder = "/home/hereinlies/Downloads/Temp"
    me = organizer.MainExtractor(organized_folder)
    me.cha2text("/home/hereinlies/Downloads/Text", gen_participant_doc = False)
    """
    def __init__(self, organized_folder:str, text_folder:str, model_folder:str, chat_path = "/home/hereinlies/Documents/Programs/unix-clan/unix/bin") -> None:
        """
        :param organized_folder:
        :param chat_path: path to the CHAT program on the computer
        """
        self.temp_out = [] #list that will take input before being transformed into a dataframe and then outputted as a .txt file.
        self.file_list = [ff for ff in (Path(organized_folder)).rglob("*.cha")]
        self.organized_folder = organized_folder
        self.chat_path = chat_path
        self.text_folder = text_folder
        self.model_folder = model_folder

    def get_single_file_participant_info(self,current_file):
        ladd = self.get_participant_info(current_file)
        return(ladd)

    def format_line(self, infolist, current_file,skip = 0):
        # foramt participant info into a dictionary to add to the temp_out list.
        _,_,task,_,_,corpus,name = current_file.stem.split("_")
        lang,_,code,age,sex,_,_,role,education,_,_= infolist

        if age != "":
            yy, rest = age.split(";")
            mm, dd = rest.split(".")

            if dd == "": dd = "0"
            if mm == "": print(f"Warning: missing month information for file {current_file}")
            if yy == "": print(f"Warning: missing year information for file {current_file}")

            agem = str(12*int(yy) + int(mm) + int(dd)/30)

        else: agem = ""

        output = {   "name": f"{corpus}_{name}"
                    ,"age_months": agem
                    ,"sex": sex
                    ,"education": education
                    ,"code": code
                    ,"role": role
                    ,"task": task
                    ,"skip": skip
                    ,"file": str(current_file.stem)
                    }

        return output

    def add_participant_info(self, current_file):
        ladd = self.get_participant_info(current_file)

        self.temp_out.extend(ladd)

    #Get list of participants.
    def get_participant_info(self, current_file):
        lparticipant = []
        ltargets = []
        lparents = []


        with open(current_file, 'r') as f:
            for line in f:
                if line.startswith('@Languages'):
                    #Remove any transcript with languages other than English.
                    templang= [x.strip() for x in line[11:].split(",")]

                    if len(templang) > 1 or templang[0].lower() != 'eng':
                        print(f"Skipping file {current_file} because it contains languages other than English: {templang}")
                        infolist = "||||||||||".split("|")
                        lparticipant.append(self.format_line(infolist, current_file,skip = 1))
                        break

                if line.startswith('@Participants'):
                    #extract the participant codes and their roles (e.g., mother, father, target_child) from the @Participants line
                    temp_list = line[14:].strip()
                    temp_code_role = [x for x in [s.strip().split() for s in temp_list.split(',')] if any(e.lower() in ('mother', 'father', 'target_child') for e in x)]
                    code_list = [x[0].lower() for x in temp_code_role]
                    role_list = [x[1].lower() for x in temp_code_role]

                if line.startswith('@ID'):
                    infolist = line[4:].strip().lower().split("|")

                    if infolist[2].lower() in code_list:
                        lparticipant.append(self.format_line(infolist,current_file))

                if line.startswith('*'):
                    break

        return lparticipant

    def gen_out_dataframe(self):
        df = pd.DataFrame(self.temp_out)
        ufiles = list(set(df["file"]))

        for uf in ufiles:
            mask_has = (df["file"] == uf) & (df["age_months"] != "")
            mask_missing = (df["file"] == uf) & (df["age_months"] == "")
            tempage = df.loc[mask_has, "age_months"]
            df.loc[mask_missing, "age_months"] = tempage.values[0] if len(tempage) > 0 else ""

        #Mean value of age fro pre-k of the ehs corpus.
        mask_ages = df['file'].str.contains(r'pk_[a-zA-Z]+_ehs', na=False) & (df["age_months"] != "")
        mean_age_ehs = df.loc[mask_ages, "age_months"].astype(float).mean()

        #For corpora with missing age in transcript, but present in file or folder name
        mask_has = df[df["age_months"] == ""].index
        for ll in mask_has:
            fileparts = df.loc[ll, "file"].split("_")

            if fileparts[-2] in ("champaign", "newmanratner", "rollins"):
                df.loc[ll, "age_months"] = fileparts[3]
            elif fileparts[-2] in ("ehs"):
                if fileparts[3] =="pk":
                    df.loc[ll, "age_months"] = mean_age_ehs
                else:
                    df.loc[ll, "age_months"] = fileparts[3]

        return df

    def build_participant_doc(self, output_file="model.csv"):
        """
        Function that returns the output file
        """
        #populate temp_out by iterating through the file list.
        #then create a dataframe from temp_out and output it as a .txt file.

        for current_file in self.file_list:
            self.add_participant_info(current_file)

        output_file = str(Path(model_folder,output_file))

        df = self.gen_out_dataframe()

        df.to_csv(output_file, index=False)

        self.output_file = output_file

    def cha2text(self, output_folder="", gen_participant_doc = False, output_file = "model.csv"):
        """
        Function that creates a processed file for each .cha file in the organized folder.
        The .txt file contains the raw transcript of the conversation, without any annotations.
        By default, it also creates a participant document that contains the participant information for each file.
        """
        #make sure the output folder exists
        #os.makedirs(output_folder, exist_ok=True)

        if gen_participant_doc & (not output_file):
            raise ValueError("No name was provided for generating the participant document. ")

        if gen_participant_doc:
            self.build_participant_doc(output_file = output_file)

        if not output_folder:
            output_folder = self.text_folder

        for current_file in self.file_list:
            subprocess.run([f"{self.chat_path}/flo", "-t%", str(current_file)])

        subprocess.run(f"mv {self.organized_folder}/*.flo.cex {output_folder}/", shell=True)


class MainOrganizer:
    """
    This class is responsible for organizing the each corpus so that
    it can easily be used by the rest of the pipeline. Each corpus has its own organization method, which is stored in a dictionary.
    inputs:
        path to source folder where the raw data is located
        path to destination folder where the organized data will be stored
    """
    def __init__(self, source_folder, destination_folder):
        self.source_folder = Path(source_folder)
        self.destination_folder = Path(destination_folder)
        os.makedirs(self.destination_folder, exist_ok=True)
        self.corpora =  self.get_subfolders()
        self.dict_corpo_method = {   "Bates":       self.org_bates
                                    ,"Bernstein":   self.org_bernstein
                                    ,"Bloom":       self.org_bloom
                                    ,"Braunwald":   self.org_braunwald
                                    ,"Brown":       self.org_brown
                                    ,"Champaign":   self.org_champaign
                                    ,"Clark":       self.org_clark
                                    ,"Demetras1":   self.org_demetras1
                                    ,"Demetras2":   self.org_demetras2
                                    ,"EHS":         self.org_ehs
                                    ,"EllisWeismer":self.org_ellisweismer
                                    ,"Feldman":     self.org_feldman
                                    ,"Gleason":     self.org_gleason
                                    ,"HSLLD":       self.org_hslld
                                    ,"Kuczaj":      self.org_kuczaj
                                    ,"MacWhinney":  self.org_macwhinney
                                    ,"McCune":      self.org_mccune
                                    ,"Nelson":      self.org_nelson
                                    ,"NewEngland":  self.org_newengland
                                    ,"NewmanRatner":self.org_newmanratner
                                    ,"Peters":      self.org_peters
                                    ,"Post":        self.org_post
                                    ,"Rollins":     self.org_rollins
                                    ,"Sachs":       self.org_sachs
                                    ,"Snow":        self.org_snow
                                    ,"Suppes":      self.org_suppes
                                    ,"VanHouten":   self.org_vanhouten
                                    ,"Weist":       self.org_weist
                                    }


    def get_subfolders(self):
        return [f for f in self.source_folder.iterdir() if f.is_dir()]

    def organize(self):
        for corpus in self.corpora:
            cc = corpus.stem
            tempmethod = self.dict_corpo_method[cc]()

    def org_bates(self):
        corpus = "bates"
        _count = 0

        for file in (self.source_folder / "Bates").rglob("*.cha"):
            task = file.parent.name

            if task == "Free20":
                _time = "20"
                _task = "toyplay"
                _other = "0"
                _name = file.stem.lower()
                fname = f"{corpus}_{str(_count)}_{_task}_{_time}_{_other}_{corpus}_{_name}.cha"

                shutil.copy(file, self.destination_folder / fname)

            if task == "Free28":
                _time = "28"
                _task = "toyplay"
                _other = "0"
                _name = file.stem.lower()[:-2]
                fname = f"{corpus}_{str(_count)}_{_task}_{_time}_{_other}_{corpus}_{_name}.cha"

                shutil.copy(file, self.destination_folder / fname)

            if task == "Snack28":
                _time = "28"
                _task = "meal"
                _other = "0"
                _name = file.stem.lower()
                fname = f"{corpus}_{str(_count)}_{_task}_{_time}_{_other}_{corpus}_{_name}.cha"

                shutil.copy(file, self.destination_folder / fname)

            if task == "Story28":
                _time = "28"
                _task = "book"
                _other = "0"
                _name = file.stem.lower()[:-2]
                fname = f"{corpus}_{str(_count)}_{_task}_{_time}_{_other}_{corpus}_{_name}.cha"

                shutil.copy(file, self.destination_folder / fname)

            _count += 1

    def org_bernstein(self):
        corpus = "bernstein"
        _count = 0

        for file in (self.source_folder / "Bernstein").rglob("*.cha"):
            _name = file.parent.name
            _time = "0"
            _task = "toyplay"
            _other = "0"
            fname = f"{corpus}_{str(_count)}_{_task}_{_time}_{_other}_{corpus}_{_name}.cha"

            shutil.copy(file, self.destination_folder / fname)

            _count += 1

    def org_bloom(self):
        corpus = "bloom"
        _count = 0

        for file in (self.source_folder / "Bloom").rglob("*.cha"):
            _name = file.parent.name
            _time = "0"
            _task = "everyday"
            _other = "0"
            fname = f"{corpus}_{str(_count)}_{_task}_{_time}_{_other}_{corpus}_{_name}.cha"

            shutil.copy(file, self.destination_folder / fname)

            _count += 1

    def org_braunwald(self):
        corpus = "braunwald"
        _count = 0

        for file in (self.source_folder / "Braunwald").rglob("*.cha"):
            _name = "L"
            _time = "0"
            _task = "everyday"
            _other = "0"
            fname = f"{corpus}_{str(_count)}_{_task}_{_time}_{_other}_{corpus}_{_name}.cha"

            shutil.copy(file, self.destination_folder / fname)

            _count += 1

    def org_brown(self):
        corpus = "brown"
        _count = 0

        for file in (self.source_folder / "Brown").rglob("*.cha"):
            _name = file.parent.name.lower()
            _time = "0"
            _task = "everyday"
            _other = "0"
            fname = f"{corpus}_{str(_count)}_{_task}_{_time}_{_other}_{corpus}_{_name}.cha"

            shutil.copy(file, self.destination_folder / fname)

            _count += 1

    def org_champaign(self):
        corpus = "champaign"
        _count = 0

        for file in (self.source_folder / "Champaign").rglob("*.cha"):
            _name = file.stem.lower()
            _time = file.parent.name[0:2]
            _task = "toyplay"
            _other = "0"
            fname = f"{corpus}_{str(_count)}_{_task}_{_time}_{_other}_{corpus}_{_name}.cha"

            shutil.copy(file, self.destination_folder / fname)

            _count += 1

    def org_clark(self):
        corpus = "clark"
        _count = 0

        for file in (self.source_folder / "Clark").rglob("*.cha"):
            _name = "Shem"
            _time = "0"
            _task = "everyday"
            _other = "0"
            fname = f"{corpus}_{str(_count)}_{_task}_{_time}_{_other}_{corpus}_{_name}.cha"

            shutil.copy(file, self.destination_folder / fname)

            _count += 1

    def org_demetras1(self):
        corpus = "demetras1"
        _count = 0

        for file in (self.source_folder / "Demetras1").rglob("*.cha"):
            _name = "trevor"
            _time = "0"
            _task = "toyplay"
            _other = "0"
            fname = f"{corpus}_{str(_count)}_{_task}_{_time}_{_other}_{corpus}_{_name}.cha"

            shutil.copy(file, self.destination_folder / fname)

            _count += 1

    def org_demetras2(self):
        corpus = "demetras2"
        _count = 0

        for file in (self.source_folder / "Demetras2").rglob("*.cha"):
            _name = file.parent.parent.stem.lower()
            _time = "0"
            _task = "discussion"
            _other = file.parent.stem
            fname = f"{corpus}_{str(_count)}_{_task}_{_time}_{_other}_{corpus}_{_name}.cha"

            shutil.copy(file, self.destination_folder / fname)

            _count += 1

    def org_ehs(self):
        corpus = "ehs"
        _count = 0

        time_dict = {
            "14-mot":["14", "mot"]
            ,"24-mot":["24", "mot"]
            ,"36-mot":["36", "mot"]
            ,"pre-k-book":["pk", "book"]
            ,"pre-K-fat":["pk", "fat"]
            ,"pre-K-mot":["pk", "mot"]
        }

        for file in (self.source_folder / "EHS").rglob("*.cha"):
            _name = file.stem.lower()
            _time = time_dict[file.parent.stem][0]
            _task = "multi"
            _other = time_dict[file.parent.stem][1]
            fname = f"{corpus}_{str(_count)}_{_task}_{_time}_{_other}_{corpus}_{_name}.cha"

            shutil.copy(file, self.destination_folder / fname)

            _count += 1

    def org_ellisweismer(self):
        corpus = "ellisweismer"
        _count = 0

        task_dict = {"ec":"toyplay", "pc":"toyplay","int":"interview","conv":"interview"}

        for file in (self.source_folder / "EllisWeismer").rglob("*.cha"):
            _name = file.stem.lower()
            _time = file.parent.stem[:2].lower()
            _task = "everyday"
            _other = task_dict[file.parent.stem[2:]]
            fname = f"{corpus}_{str(_count)}_{_task}_{_time}_{_other}_{corpus}_{_name}.cha"

            shutil.copy(file, self.destination_folder / fname)

            _count += 1

    def org_feldman(self):
        corpus = "feldman"
        _count = 0

        for file in (self.source_folder / "Feldman").rglob("*.cha"):
            _name = "steven"
            _time = "0"
            _task = "everyday"
            _other = "0"
            fname = f"{corpus}_{str(_count)}_{_task}_{_time}_{_other}_{corpus}_{_name}.cha"

            shutil.copy(file, self.destination_folder / fname)

            _count += 1

    def org_gleason(self):
        corpus = "gleason"
        _count = 0

        task_dict = {"Dinner": "meal", "Father": "toyplay", "Mother": "toyplay"}

        for file in (self.source_folder / "Gleason").rglob("*.cha"):
            _name = file.stem.lower()
            _time = "0"
            _task = task_dict[file.parent.stem].lower()
            _other = "0"
            fname = f"{corpus}_{str(_count)}_{_task}_{_time}_{_other}_{corpus}_{_name}.cha"

            shutil.copy(file, self.destination_folder / fname)

            _count += 1

    def org_hslld(self):
        corpus = "hslld"
        _count = 0

        task_dict = {"BR":"book","ER":"retell", "MT":"meal", "TP":"toyplay", "ET":"tests", "RE":"book", "LW":"writing", "MD":"other"}

        for file in (self.source_folder / "HSLLD").rglob(".cha*"):
            _name = file.stem.lower()[:3]
            _time = file.parent.parent.stem.lower()
            _task = task_dict[file.parent.stem].lower()
            _other = "0"
            fname = f"{corpus}_{str(_count)}_{_task}_{_time}_{_other}_{corpus}_{_name}.cha"

            shutil.copy(file, self.destination_folder / fname)

            _count += 1

    def org_kuczaj(self):
        corpus = "kuczaj"
        _count = 0

        for file in (self.source_folder / "Kuczaj").rglob("*.cha"):
            _name = "abe"
            _time = "0"
            _task = "everyday"
            _other = "0"
            fname = f"{corpus}_{str(_count)}_{_task}_{_time}_{_other}_{corpus}_{_name}.cha"

            shutil.copy(file, self.destination_folder / fname)

            _count += 1

    def org_post(self):
        corpus = "post"
        _count = 0

        for file in (self.source_folder / "Post").rglob("*.cha"):
            _name = file.parent.stem.lower()
            _time = "0"
            _task = "toyplay"
            _other = "0"
            fname = f"{corpus}_{str(_count)}_{_task}_{_time}_{_other}_{corpus}_{_name}.cha"

            shutil.copy(file, self.destination_folder / fname)

            _count += 1

    def org_mccune(self):
        corpus = "mccune"
        _count = 0

        for file in (self.source_folder / "McCune").rglob("*.cha"):
            _name = file.parent.stem.lower()
            _time = "0"
            _task = "toyplay"
            _other = "0"
            fname = f"{corpus}_{str(_count)}_{_task}_{_time}_{_other}_{corpus}_{_name}.cha"

            shutil.copy(file, self.destination_folder / fname)

            _count += 1

    def org_macwhinney(self):
        corpus = "macwhinney"
        _count = 0

        for file in (self.source_folder / "MacWhinney").rglob("*.cha"):
            _name = "rossmark"
            _time = "0"
            _task = "everyday"
            _other = "0"
            fname = f"{corpus}_{str(_count)}_{_task}_{_time}_{_other}_{corpus}_{_name}.cha"

            shutil.copy(file, self.destination_folder / fname)

            _count += 1

    def org_nelson(self):
        pass

    def org_newengland(self):
        corpus = "newengland"
        _count = 0

        for file in (self.source_folder / "NewEngland").rglob("*.cha"):
            _name = file.stem.lower()
            _time = file.parent.stem.lower()
            _task = "multi"
            _other = "0"
            fname = f"{corpus}_{str(_count)}_{_task}_{_time}_{_other}_{corpus}_{_name}.cha"

            shutil.copy(file, self.destination_folder / fname)

            _count += 1

    def org_newmanratner(self):
        corpus = "newmanratner"
        _count = 0

        for file in (self.source_folder / "NewmanRatner").rglob("*.cha"):
            _name = file.stem.lower()
            _time = file.parent.stem.lower()
            _task = "toyplay"
            _other = "0"
            fname = f"{corpus}_{str(_count)}_{_task}_{_time}_{_other}_{corpus}_{_name}.cha"

            shutil.copy(file, self.destination_folder / fname)

            _count += 1

    def org_peters(self):
        corpus = "peters"
        _count = 0

        for file in (self.source_folder / "Peters").rglob("*.cha"):
            _name = "seth"
            _time = "0"
            _task = "everyday"
            _other = "0"
            fname = f"{corpus}_{str(_count)}_{_task}_{_time}_{_other}_{corpus}_{_name}.cha"

            shutil.copy(file, self.destination_folder / fname)

            _count += 1

    def org_rollins(self):
        corpus = "rollins"
        _count = 0

        for file in (self.source_folder / "Rollins").rglob("*.cha"):
            if file.stem.lower()[0:4] == "jw12": continue #skipping these because it is unclear whether it is the same kid.

            _name = file.stem.lower()[0:2]
            _time = file.stem.lower()[2:4]
            _task = "toyplay"
            _other = "0"
            fname = f"{corpus}_{str(_count)}_{_task}_{_time}_{_other}_{corpus}_{_name}.cha"

            shutil.copy(file, self.destination_folder / fname)

            _count += 1

    def org_sachs(self):
        corpus = "sachs"
        _count = 0

        for file in (self.source_folder / "Sachs").rglob("*.cha"):
            _name = "naomi"
            _time = "0"
            _task = "everyday"
            _other = "0"
            fname = f"{corpus}_{str(_count)}_{_task}_{_time}_{_other}_{corpus}_{_name}.cha"

            shutil.copy(file, self.destination_folder / fname)

            _count += 1

    def org_snow(self):
        pass

    def org_suppes(self):
        corpus = "suppes"
        _count = 0

        for file in (self.source_folder / "Suppes").rglob("*.cha"):
            _name = "nina"
            _time = "0"
            _task = "everyday"
            _other = "0"
            fname = f"{corpus}_{str(_count)}_{_task}_{_time}_{_other}_{corpus}_{_name}.cha"

            shutil.copy(file, self.destination_folder / fname)

            _count += 1

    def org_vanhouten(self):
        corpus = "vanhouten"
        _count = 0

        task_dict = {"teaching":"tests", "lunch":"meal", "freeplay":"toyplay"}

        for file in (self.source_folder / "VanHouten").rglob("*.cha"):
            _name = file.stem.lower()[:-1]
            _time = file.parent.parent.stem.lower()
            _task = task_dict[file.parent.stem].lower()
            _other = "0"
            fname = f"{corpus}_{str(_count)}_{_task}_{_time}_{_other}_{corpus}_{_name}.cha"

            shutil.copy(file, self.destination_folder / fname)

            _count += 1

    def org_weist(self):
        corpus = "weist"
        _count = 0

        for file in (self.source_folder / "Weist").rglob("*.cha"):
            _name = file.parent.stem.lower()
            _time = "0"
            _task = "everyday"
            _other = "0"
            fname = f"{corpus}_{str(_count)}_{_task}_{_time}_{_other}_{corpus}_{_name}.cha"

            shutil.copy(file, self.destination_folder / fname)

            _count += 1