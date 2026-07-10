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

        t_ids = self.encoded_sentences["input_ids"][tidx]


        if self.context_length == 0:
            input_ids = torch.cat((self.bos, t_ids))
        else :
            raise NotImplementedError("Context length > 0 is not implemented yet.")

        out = (self.files[tidx]
                   , self.speakers[tidx]
                   , input_ids
                   , self.encoded_sentences["length"][tidx]
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
    files, speakers, raw_ids, ntokens, lencontext = zip(*batch)

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
        "ntokens":ntokens,
        "lencontext": lencontext
    }

class SentenceScorer:
    def __init__(self,participant_file, text_folder, extractor, tokenizer,automated_preprocessing=True):
        participant_df = pd.read_csv(participant_file)
        participant_df["code"] = participant_df['code'].apply(ast.literal_eval)

        self.measure_list ={"sum_entropy":self.sum_entropy
                            }

        self.participant_df = participant_df
        self.extractor = extractor
        self.tokenizer = tokenizer
        self.text_folder = text_folder

        self.sentence_loader = None

        if automated_preprocessing:
            (      self.files
                 , self.speakers
                 , self.sentences
                 , self.codes
                 , self.filtidx) = self.preprocess_sentences()

            self.encoded_sentences = self.tokenize_sentences()
            self.filtidx = self.order_filtidx()

        else:
            self.files = None
            self.speakers = None
            self.sentences = None
            self.codes = None
            self.filtidx = None

    def sum_entropy(self,var4measures):
        """
        Computes the entropy of the logits.
        :var4measures: dict with keys "logits" and "mask"
        :return: the entropy of the logits
        """
        logits = var4measures["logits"]
        sm = torch.nn.Softmax(dim=-1)
        lsm = torch.nn.LogSoftmax(dim=-1)
        entropy = -(sm(logits)*lsm(logits)).sum(dim=-1)
        entropy = entropy*(var4measures["mask"])

        return entropy.sum(dim=-1)

    def preprocess_sentences(self, update_self=False):
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

        if update_self:
            self.files = files
            self.speakers = speakers
            self.sentences = sentences
            self.codes = codes
            self.filtidx = filtidx
        else:
            return files, speakers, sentences, codes, filtidx

    def tokenize_sentences(self,update_self=False):
        """
        Tokenizes the sentences in self.sentences using the tokenizer specified in self.tokenizer.
        :return: a list of tokenized sentences including mask and lenght, but without special tokens.
        """
        list_encoded_sentences = self.tokenizer(self.sentences,add_special_tokens=False,return_length = True, return_attention_mask=False)

        encoded_sentences = {
                            "input_ids": [torch.tensor(les,dtype=torch.int64) for les in list_encoded_sentences["input_ids"]]
                            ,"length": list_encoded_sentences["length"]
                            }

        if update_self:
            self.encoded_sentences = encoded_sentences
        else:
            return encoded_sentences

    def order_filtidx(self, update_self=False):
        """
        Orders the filtered dataframe by the length of the tokenized sentences.
        :return: updates filtdf
        """
        all_len = self.encoded_sentences["length"]
        slen = [all_len[ii] for ii in self.filtidx]
        order = np.argsort(slen)

        nord_idx = list(map(self.filtidx.__getitem__, order))

        if update_self:
            self.filtidx=nord_idx
        else:
            return nord_idx

    def gen_dataset_and_dataloader(self,context_length=0,batch_size=1, num_workers=0,update_self=True):
        sentence_dataset = ChildesDataset( self.files
                                      ,self.speakers
                                      ,self.encoded_sentences
                                      ,self.filtidx
                                      ,self.tokenizer
                                      ,context_length=context_length
                                       )
        sentence_loader = DataLoader(sentence_dataset
                                     , batch_size=batch_size
                                     , shuffle=False
                                     , num_workers =num_workers
                                     , collate_fn=collate_fn
                                     , pin_memory=True)
        if update_self:
            self.sentence_loader = sentence_loader
        else:
            return sentence_loader

    def format_scores(self, df_out, aggmethod = "median", output_file="", write2file=False):
        """
        Formats the output dataframe and writes it to a csv file.
        :param df_out: the output dataframe
        :param output_file: the output file name
        :return: None
        """
        grouped = df_out.groupby(["file", "speaker"]).agg(aggmethod).reset_index()

        grouped.to_csv(output_file, index=False)

    def score_sentences(self, model, device, aggmethod ="median", measures=["sum_entropy"],write2file=False,output_file=""):
        """
        Scores the sentences in self.sentence_loader using the model specified in model.
        :param model: the model to use for scoring
        :param device: the device to use for scoring
        :return: a list of scores for each sentence in self.sentences
        """

        #return from dataloader: {"files", "speakers","input_ids", "attention_mask","ntokens","stidx2scores"}
        model.to(device)
        torch.cuda.synchronize()
        print(f"GPU allocated after model.to(device): {torch.cuda.memory_allocated() / 1e9:.2f} GB")
        print(f"GPU reserved after model.to(device): {torch.cuda.memory_reserved() / 1e9:.2f} GB")

        model.eval()

        nmeasures = len(measures)
        scores = [[] for _ in range(nmeasures)]
        var4measures = {}
        file, speaker, ntokens = [], [], []



        with torch.no_grad():
            for batch in self.sentence_loader:

                torch.cuda.synchronize()
                print(f"GPU allocated loop start: {torch.cuda.memory_allocated() / 1e9:.2f} GB")
                print(f"GPU reserved  loop start: {torch.cuda.memory_reserved() / 1e9:.2f} GB")



                input_ids = batch["input_ids"].to(device, non_blocking=True)
                attention_mask = batch["attention_mask"].to(device, non_blocking=True)
                stidx2score = batch["lencontext"][0]+1 #+1 because of the bos token

                torch.cuda.synchronize()
                print(f"GPU allocated in to device: {torch.cuda.memory_allocated() / 1e9:.2f} GB")
                print(f"GPU reserved  in to device: {torch.cuda.memory_reserved() / 1e9:.2f} GB")

                modelinputs = {
                    "input_ids": input_ids,
                    "attention_mask": attention_mask
                }

                var4measures["logits"] = model(**modelinputs).logits[:,stidx2score:,]
                var4measures["mask"] = attention_mask[:,stidx2score:]

                for ii, me in enumerate(measures):
                    scores[ii].append(self.measure_list[me](var4measures).detach().cpu())

                torch.cuda.synchronize()
                print(f"GPU allocated after detach: {torch.cuda.memory_allocated() / 1e9:.2f} GB")
                print(f"GPU reserved  after detach: {torch.cuda.memory_reserved() / 1e9:.2f} GB")

                file.extend(batch["files"])
                speaker.extend(batch["speakers"])
                ntokens.extend(batch["ntokens"])

        dict_out = {}
        dict_out["file"] = file
        dict_out["speaker"] = speaker
        dict_out["ntokens"] = ntokens
        dict_out["lencontext"] = stidx2score-1 #remove the +1 because of the bos token

        for ii,ms in enumerate(measures):
            dict_out[ms] = torch.cat(scores[ii]).float().numpy()

        df_out = pd.DataFrame(dict_out)

        if write2file:
            self.format_scores(df_out,aggmethod=aggmethod, output_file=output_file,write2file=True)
        else:
            return df_out


#https://docs.pytorch.org/tutorials/intermediate/pinmem_nonblock.html
#https://docs.pytorch.org/tutorials/intermediate/intermediate_data_loading_tutorial.html


