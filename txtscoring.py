from transformers import AutoTokenizer, MistralForCausalLM
import torch
import txtpreprocess
from pathlib import Path
import pandas as pd

class sentence_scoring:
    def __init__(self,participant_info:dataframe, list_preprocessing_steps:list,folder_path:str):
        self.participant_info = participant_info
        self.list_preprocessing_steps = list_preprocessing_steps
        self.preprocessor = txtpreprocess.TextExtraction()
        self.folder_path = str(Path(participant_info).parent)
        self.sentences = []
        self.code = []
        self.file = []


    def preprocess_sentences(self):
        for ii,ll in self.participant_info.iterrows():
            cc = ll["code"]
            ff = ll["file"]
            temp = self.preprocessor.get_clean_text(ff, cc, method_list = self.list_preprocessing_steps, print_warnings = True)

            tcode = []
            tsentence = []
            for tt in temp:
                tc, ts = tt.split(":", maxsplit=1)
                tcode.append(tc[1:])
                tsentence.append(ts)

            tfile = len(tcode)*ff



#modelname = "mistralai/Mistral-7B-v0.1"#### change

#model = MistralForCausalLM.from_pretrained(modelname)
#tokenizer = AutoTokenizer.from_pretrained(modelname)

#sentence = "Hello my name is"

#modelinputs = tokenizer(sentence, return_tensors="pt") #I can give it a list of list if I remove the return tensors option).

#modeloutputs = model(**modelinputs)

#logits = modeloutputs.logits #shape batch x sequence lenght x vocab size