from transformers import AutoTokenizer, MistralForCausalLM
import torch
import txtpreprocess
from pathlib import Path
import pandas as pd

class sentence_scoring:
    def __init__(self,participant_file, text_folder, extractor,folder_path:str):
        self.participant_df = pd.read_csv(participant_file)
        self.extractor = extractor
        self.text_folder = text_folder
        self.sentences = []
        self.code = []
        self.file = []


    def preprocess_sentences(self):
        temp = self.extractor.serial_clean(self.participant_df, self.text_folder)

        for ii,ll in self.participant_df.iterrows():
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