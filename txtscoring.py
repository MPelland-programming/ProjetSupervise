import torch
from torch.utils.data import Dataset
from torch.utils.data import DataLoader
import pandas as pd
import numpy as np
import ast


class ChildesDataset(Dataset):
    def __init__(self, files, speakers, encoded_sentences, filtidx, tokenizer, context_length=0):
        self.files = files
        self.speakers = speakers
        self.encoded_sentences = encoded_sentences
        self.filtidx = filtidx
        self.bos = tokenizer.bos_token_id
        self.context_length = context_length

    def __len__(self):
        return len(self.filtidx)

    def __getitem__(self, idx):
        """
        Get only items which are in the filtered index list.
        This is to avoid sentences which are not spoken by the speaker of interest.
        :param idx:
        :return:
            - files: the file name of the transcript
            - speakers: the speaker of the sentence
            - t_enc: dict of input_ids, attention_mask
            - stidx2score: index from which to start scoring.
        """
        tidx = self.filtidx[idx]

        if self.context_length == 0:
            ii = [self.bos]
            ii.extend(self.encoded_sentences["input_ids"][tidx])
            am = [1]
            am.extend(self.encoded_sentences["attention_mask"][tidx])

            t_enc = {"input_ids": ii, "attention_mask": am}

            out = (  self.files[tidx]
                    ,self.speakers[tidx]
                    ,t_enc
                    , 0
                    )
        else :
            pass####################################################################implementation awaiting

        return out

def collate_fn(batch):
    """
    Collate function to be used with the DataLoader.
    This function pads the input_ids and attention_mask to the maximum length in the batch.
    :param batch: list of tuples (file, speaker, t_enc, stidx2score)
    :return: dict of padded input_ids, attention_mask, and list of files and speakers
    """
    files, speakers, t_encs, stidx2scores = zip(*batch)

    max_len = max(len(t_enc["input_ids"]) for t_enc in t_encs)

    padded_input_ids = []
    padded_attention_mask = []

    for t_enc in t_encs:
        input_ids = t_enc["input_ids"]
        attention_mask = t_enc["attention_mask"]

        # Pad input_ids and attention_mask
        pad_length = max_len - len(input_ids)
        padded_input_ids.append(input_ids + [0] * pad_length)  # Assuming 0 is the padding token ID
        padded_attention_mask.append(attention_mask + [0] * pad_length)

    return {
        "files": files,
        "speakers": speakers,
        "input_ids": torch.tensor(padded_input_ids),
        "attention_mask": torch.tensor(padded_attention_mask),
        "stidx2scores": stidx2scores
    }

class SentenceScorer:
    def __init__(self,participant_file, text_folder, extractor, tokenizer):
        participant_df = pd.read_csv(participant_file)
        participant_df["code"] = participant_df['code'].apply(ast.literal_eval)
        self.participant_df = participant_df
        self.extractor = extractor
        self.tokenizer = tokenizer
        self.text_folder = text_folder

        #Automated preprocessing
        self.preprocess_sentences()
        self.order_filtidx()

    def preprocess_sentences(self, write2self=True):
        """
        Preprocesses the sentences in the text files specified in self.participant_df and self.text_folder.
        This is done automatically upon initialization of the class.
        :param write2self: whether to write the sentences to self.sentences or return them. Default is True.
        :return: if write2self is False, returns files, sentences, codes and speakers. If True, returns None.
        """
        files, speakers, sentences, codes = self.extractor.serial_clean(
                                                self.participant_df
                                                ,self.text_folder)

        filtidx = [ii for ii, (ss , cc) in enumerate(zip(fspeaker,fcode)) if ss in cc]

        if write2self:
            self.files = files
            self.speakers = speakers
            self.sentences = sentences
            self.codes = codes
            self.filtidx = filtidx
        else:
            return files, speakers, sentences, codes, filtidx

    def tokenize_sentences(self,write2self=True):
        """
        Tokenizes the sentences in self.sentences using the tokenizer specified in self.tokenizer.
        :return: a list of tokenized sentences including mask and lenght, but without special tokens.
        """
        encoded_sentences = self.tokenizer(self.sentences,add_special_tokens=False,return_length = True)

        if write2self:
            self.encoded_sentences = encoded_sentences
        else:
            return encoded_sentences

    def order_filtidx(self):
        """
        Orders the filtered dataframe by the length of the tokenized sentences.
        :return: updates filtdf
        """
        all_len = self.encoded_sentences["length"]
        slen = [all_len[ii] for ii in self.filtidx]
        order = np.argsort(slen)

        nord_idx = list(map(self.filtidx.__getitem__, order))

        self.filtidx=nord_idx

    def gen_dataset_and_dataloader(self,context_length=0,batch_size=1):
        dataset = ChildesDataset( self.files
                                      ,self.speakers
                                      ,self.encoded_sentences
                                      ,self.filtidx
                                      ,self.tokenizer
                                      ,context_length=context_length
                                       )



        dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=False)







#modeloutputs = model(**modelinputs)

#logits = modeloutputs.logits #shape batch x sequence lenght x vocab size