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
        self.context_length = context_length
        self.dtype = encoded_sentences["input_ids"][0].dtype
        self.bos = torch.tensor([tokenizer.bos_token_id],dtype=self.dtype)

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
            input_ids = torch.cat((self.bos, self.encoded_sentences["input_ids"][tidx]))
        else :
            pass####################################################################implementation awaiting

        out = (self.files[tidx]
                   , self.speakers[tidx]
                   , input_ids
                   , self.context_length
               )

        return out

def collate_fn(batch):
    """
    Collate function to be used with the DataLoader.
    This function pads the input_ids and attention_mask to the maximum length in the batch.
    :param batch: list of tuples (file, speaker, t_enc, stidx2score)
    :return: dict of padded input_ids, attention_mask, and list of files and speakers
    """
    files, speakers, raw_ids, stidx2scores = zip(*batch)

    rawlen = [len(xx) for xx in raw_ids]
    maxlen = max(rawlen)
    dtype = raw_ids[0].dtype

    input_ids = torch.zeros(len(raw_ids), maxlen, dtype=dtype)
    attention_mask = torch.zeros(input_ids.shape, dtype=torch.int8)

    for ii,rlen,renc in zip(range(0,len(raw_ids)),rawlen,raw_ids):
        # Pad input_ids and attention_mask
        pad_len = maxlen - rlen

        input_ids[ii,:] = torch.cat((renc, torch.zeros(pad_len,dtype=torch.int64)))
        attention_mask[ii,:] = torch.cat((torch.ones(rlen,dtype=torch.int8), torch.zeros(pad_len,dtype=torch.int8)))


    return {
        "files": files,
        "speakers": speakers,
        "input_ids": input_ids,
        "attention_mask": attention_mask,
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

        filtidx = [ii for ii, (ss , cc) in enumerate(zip(speakers,codes)) if ss in cc]

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
        list_encoded_sentences = self.tokenizer(self.sentences,add_special_tokens=False,return_length = True, return_attention_mask=False)

        encoded_sentences = {}
        encoded_sentences["input_ids"] = [torch.tensor(les,dtype=torch.int64) for les in list_encoded_sentences["input_ids"]]
        encoded_sentences["length"] = list_encoded_sentences["length"]

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

    def gen_dataset_and_dataloader(self,context_length=0,batch_size=1,write2self=True):
        sentence_dataset = ChildesDataset( self.files
                                      ,self.speakers
                                      ,self.encoded_sentences
                                      ,self.filtidx
                                      ,self.tokenizer
                                      ,context_length=context_length
                                       )
        sentence_loader = DataLoader(sentence_dataset, batch_size=batch_size, shuffle=False, collate_fn=collate_fn)
        if write2self:
            self.sentence_loader = sentence_loader
        else:
            return sentence_loader

    def score_sentences(self, model, device):
        """
        Scores the sentences in self.sentence_loader using the model specified in model.
        :param model: the model to use for scoring
        :param device: the device to use for scoring
        :return: a list of scores for each sentence in self.sentences
        """
        model.to(device)
        model.eval()

        scores = []
        with torch.no_grad():
            for batch in self.sentence_loader:
                input_ids = batch["input_ids"].to(device)
                attention_mask = batch["attention_mask"].to(device)

                modelinputs = {
                    "input_ids": input_ids,
                    "attention_mask": attention_mask
                }






#modeloutputs = model(**modelinputs)

#logits = modeloutputs.logits #shape batch x sequence lenght x vocab size