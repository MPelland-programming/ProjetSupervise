import torch
from torch.utils.data import Dataset
from torch.utils.data import DataLoader
import pandas as pd
import numpy as np
import ast


def order_idx_by_size(idx, lengths):
    """
    Orders the filtered list of idx based on lengths.
    :return: updates filtdf
    """
    order = torch.argsort(torch.tensor(lengths),descending=True).tolist()

    ord_idx = [idx[ii] for ii in order]
    ord_len = [lengths[ii] for ii in order]

    return ord_idx, ord_len

def select_and_order_idx(files, filtidx, lengths, context_length=0, turn=True):
    """
    further carries idx selection and order them by size, which includes the context.
    -filtidx list of idx filter by code
    """

    if context_length == 0:
        filt_len = [lengths[ii] for ii in filtidx]
        new_filtidx = filtidx

    elif turn:
        new_filtidx = []
        filt_len = []

        for tidx in filtidx:
            if (tidx - context_length >= 0) and (files[tidx] == files[tidx-context_length]):
                tlen = 0
                for ii in range(tidx - context_length, tidx + 1):
                    tlen += lengths[ii]

                new_filtidx.append(tidx)
                filt_len.append(tlen)

    else:
        raise NotImplementedError("Context length > 0 token based is not implemented yet.")

    ord_idx,ord_len = order_idx_by_size(new_filtidx, filt_len)
    print(ord_len[0:20])
    print(ord_len[-1])
    print(len(ord_idx), len(ord_len))
    raise NameError('HiThere')
    return ord_idx,ord_len

def vectorized_selected_ids(var4measures,target_var):
    """
    :return:
        -selected_logits N (between B and BxL)
        -batch_dix       N (between B and BxL)
    """
    target_tensor = var4measures[target_var]
    tsiz = target_tensor.shape
    B,L = tsiz[0], tsiz[1]
    device = target_tensor.device
    context_lengths = var4measures["con_len"]+1 #finally accounts for BOS
    target_lengths = var4measures["utt_len"]

    positions = torch.arange(L, dtype=torch.int32, device=device).unsqueeze(0)          # (1, L)
    start = context_lengths.unsqueeze(1)                             # (B, 1)
    end   = (context_lengths + target_lengths).unsqueeze(1)          # (B, 1)
    mask  = (positions >= start) & (positions < end)                 # (B, L)

    batch_idx = torch.arange(B, dtype=torch.int64, device=device).unsqueeze(1).expand(-1, L)[mask]  # (N,)
    selected_elements = target_tensor[mask]

    var_name = "selected_"+target_var
    var4measures[var_name] = selected_elements
    var4measures["batch_idx"] = batch_idx

    return var4measures

class ChildesDataset(Dataset):
    def __init__(self, files, speakers, encoded_sentences, filtidx, tokenizer, context_length=0,turn=True):
        self.files = files
        self.speakers = speakers
        self.encoded_sentences = encoded_sentences #includes
        self.filtidx = filtidx
        self.context_length = context_length
        self.turn = turn
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
            A tuple for single target utterance.
                -file name
                -Name of speaker of target utterance
                -ids including context and BOS
                -length of target utterance
                -lenght of context linked to utterance
                -proportion of the utterances coming from target speaker.
               )
        """
        tidx = self.filtidx[idx]

        #No context
        if self.context_length == 0:
            t_ids = self.encoded_sentences["input_ids"][tidx]
            input_ids = torch.cat((self.bos, t_ids))
            context_len = 0
            proportion_speaker = 1

        #Context
        else :
            #turn based
            if self.turn:
                list_utt_ids = [self.bos]
                context_len = 0 #for bos token

                es_ids = self.encoded_sentences["input_ids"][tidx-self.context_length:tidx+1]
                es_len = self.encoded_sentences["length"][tidx - self.context_length:tidx + 1]

                for ii,le in zip(es_ids,es_len):
                    list_utt_ids.append(ii)
                    context_len += le

                input_ids = torch.cat(list_utt_ids)
                context_len -= le  #remove last length since it is the target utterance.

                target_speaker = self.speakers[tidx]
                proportion_speaker =  sum([target_speaker in ss for ss in self.speakers[tidx-self.context_length:tidx]])/self.context_length

            else:
                raise NotImplementedError("Context length > 0 token based is not implemented yet.")


        out = (self.files[tidx]
                   , self.speakers[tidx]
                   , input_ids
                   , self.encoded_sentences["length"][tidx]
                   , context_len
                   , proportion_speaker
               )

        return out

def collate_fn(batch):
    """
    Collate function to be used with the DataLoader.
    This function pads the input_ids and attention_mask to the maximum length in the batch.
    :param batch: list of tuples (file, speaker, ids, lenght of target utterance, lenght of context, proportion of speaker)
    :return:
        Dictionary of lists or tensors, contains:
        -files:             list of file name
        -speakers:          list of speaker of target utterance
        -input_ids:         tensor      (B x max context+utterance lenght of batch)
        -attention_mask:    tensor      (B x max context+utterance lenght of batch)
        -utterance_len:     list of lenght of target utterance
        -context_len:       list of lenght of context
        -proportion_speaker:list of prop_speaker
    """

    files, speakers, raw_ids, utterance_len, context_len, prop_speaker = zip(*batch)

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

    #outputs are
    return {
        "files": files,
        "speakers": speakers,
        "input_ids": input_ids,
        "attention_mask": attention_mask,
        "utterance_len":utterance_len,
        "context_len": context_len,
        "proportion_speaker": prop_speaker
    }

class TokenBasedSampler(torch.utils.data.Sampler):
    """
    Takes in indices for data which are sorted in descending lenght
    and selects indices in a way that yields batches of relatively equal sizes.
    """
    def __init__(self,idx,lengths,batch_size):
        #Amount of memory allocated to input and output size.
        maxsize = batch_size#np.floor(2**(np.log2(batch_size)+30-19)) #(number of gbs * size of gb)/proportion of memory dedicated to data and size of logits for one token.

        batch_list = []
        start_idx = 0
        curr_idx = 0

        while curr_idx < len(idx):
            idx_list = []
            width = lengths[curr_idx]
            print(width)

            while ((curr_idx-start_idx+1)*(width**2) < maxsize) and (curr_idx < len(idx)):
                idx_list.append(curr_idx)
                curr_idx += 1

            batch_list.append(idx_list)
            start_idx = curr_idx

        self.batch_list = batch_list

    def __len__(self) -> int:
        return len(self.batch_list)

    def __iter__(self):
        yield from self.batch_list

class SentenceScorer:
    def __init__(self,participant_file, text_folder, extractor, tokenizer,automated_preprocessing=True):
        participant_df = pd.read_csv(participant_file)
        participant_df["code"] = participant_df['code'].apply(ast.literal_eval)

        self.measure_list ={"sum_entropy":self.sum_entropy
                            ,"sum_surprisal":self.sum_surprisal
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

        else:
            self.files = None
            self.speakers = None
            self.sentences = None
            self.codes = None
            self.filtidx = None

    def sum_entropy(self,var4measures):
        """
        Computes the entropy of the probs.
        :var4measures: dict with keys "selected_probs", "batch_idx", anb "batch_size"
        :return: the entropy of the logits size B
        """
        probs = var4measures["selected_probs"]
        batch_idx = var4measures["batch_idx"]
        B = var4measures["batch_size"]
        device = probs.device

        entropy = torch.special.entr(probs).sum(dim=-1)

        result = torch.zeros(B, device=device,dtype=probs.dtype)
        result.scatter_add_(0, batch_idx, entropy)

        return result

    def sum_surprisal(self,var4measures):
        """
        Computes the surprisal of the probs
        :var4measures: dict with keys "selected_probs", "batch_idx", anb "batch_size"
        :return: the entropy of the logits size B
        """
        probs = var4measures["selected_probs"]      #N (1 to ntokens) x V
        ids = var4measures["selected_shifted_ids"]  #N (1 to ntokens)
        batch_idx = var4measures["batch_idx"]
        B = var4measures["batch_size"]
        device = probs.device

        target_ids_probs = torch.gather(probs, dim=1, index=ids.unsqueeze(-1)).squeeze()
        surprisal = -torch.log(target_ids_probs)

        result = torch.zeros(B, device=device, dtype=probs.dtype)
        result.scatter_add_(0, batch_idx, surprisal)

        return result

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

    def gen_dataset_and_dataloader(self,context_length=0,turn=True,batch_size=1, batch_type="nlines", num_workers=0,update_self=True):
        """
        :param context_length: int,  number of tokens or speaking turns
        :param turn:           bool, True if using speaking turns for context lenght
        :param batch_size:     int,  number of lines or tokens to analyse per batch
        :param batch_type:     str of "nlines" or "ntokens, see batch_size for more details
        :param num_workers:    int, number of workers to use for data loading
        :param update_self:    bool, whethr to retunr the dataloader or update the object.
        :return:
            a Dataloader object or updates self with it.
        """
        #update filtidx
        selected_filtidx,selected_lengths = select_and_order_idx(self.files, self.filtidx, self.encoded_sentences["length"], context_length=context_length,
                                            turn=turn)  # selection base on whether a line has enough context.

        sentence_dataset = ChildesDataset( self.files
                                      ,self.speakers
                                      ,self.encoded_sentences
                                      ,selected_filtidx
                                      ,self.tokenizer
                                      ,context_length=context_length
                                      ,turn=turn
                                       )

        if batch_type == "nlines":
            sentence_loader = DataLoader(sentence_dataset
                                         , batch_size=batch_size
                                         , shuffle=False
                                         , num_workers =num_workers
                                         , collate_fn=collate_fn
                                         , pin_memory=True)

        elif batch_type == "ntokens":
            batch_sampler = TokenBasedSampler(selected_filtidx, selected_lengths, batch_size)

            sentence_loader = DataLoader(sentence_dataset
                                         , batch_sampler=batch_sampler
                                         , num_workers =num_workers
                                         , collate_fn=collate_fn
                                         , pin_memory=True)

        if update_self:
            self.sentence_loader = sentence_loader
        else:
            return sentence_loader

    def format_scores(self, df_out, aggmethod = "mean", output_file="", write2file=False):
        """
        Formats the output dataframe and writes it to a csv file.
        :param df_out: the output dataframe
        :param output_file: the output file name
        :return: None
        """
        tcols = [x for x in df_out.columns if x not in ['file','speaker']]
        aggmethod_dict = {cc: aggmethod for cc in tcols}
        aggmethod_dict[tcols[-1]] = [aggmethod,"count"]
        col_names = ["file","speaker"]
        col_names.extend(tcols)
        col_names.append("count")

        grouped = df_out.groupby(["file", "speaker"]).agg(aggmethod_dict).reset_index()
        grouped.columns = grouped.columns.droplevel()
        grouped.columns = col_names

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
        #torch.cuda.synchronize()
        #print(f"GPU allocated after model.to(device): {torch.cuda.memory_allocated() / 1e9:.2f} GB")
        #print(f"GPU reserved after model.to(device): {torch.cuda.memory_reserved() / 1e9:.2f} GB")

        model.eval()

        nmeasures = len(measures)
        scores = [[] for _ in range(nmeasures)]
        file, speaker, utterance_len, context_len, prop_speaker = [], [], [], [], []


        with torch.no_grad():
            for batch in self.sentence_loader:

                input_ids = batch["input_ids"].to(device, non_blocking=True)
                attention_mask = batch["attention_mask"].to(device, non_blocking=True)
                con_len = torch.tensor(batch["context_len"],dtype=torch.int64).to(device, non_blocking=True)
                utt_len = torch.tensor(batch["utterance_len"],dtype=torch.int64).to(device, non_blocking=True)
                batch_size = batch["input_ids"].shape[0]

                modelinputs = {"input_ids": input_ids,"attention_mask": attention_mask}

                var4measures={"con_len": con_len,"utt_len": utt_len,"batch_size":batch_size
                              ,"shifted_ids": torch.roll(input_ids,-1,1)        #shape: b x tokens, shifter, x vocab
                              ,"logits": model(**modelinputs).logits            #shape: b x tokens x vocab
                              }

                #Get only indices of interest and apply softmax to each.
                var4measures = vectorized_selected_ids(var4measures,"logits")
                var4measures["selected_probs"] = torch.softmax(var4measures["selected_logits"], dim=-1)

                var4measures = vectorized_selected_ids(var4measures, "shifted_ids")

                #extract measures
                for ii, me in enumerate(measures):
                    scores[ii].append(self.measure_list[me](var4measures).detach().cpu())

                file.extend(batch["files"])
                speaker.extend(batch["speakers"])
                utterance_len.extend(batch["utterance_len"])
                context_len.extend(batch["context_len"])
                prop_speaker.extend(batch["proportion_speaker"])

                #torch.cuda.synchronize()
                #print(f"GPU allocated : {torch.cuda.memory_allocated() / 1e9:.2f} GB")
                #print(f"GPU reserved  : {torch.cuda.memory_reserved() / 1e9:.2f} GB")

        dict_out = {
            "file": file
            ,"speaker": speaker
            ,"ntokens": utterance_len
            ,"lencontext": context_len
            ,"propspeaker": prop_speaker
            }

        for ii,ms in enumerate(measures):
            dict_out[ms] = torch.cat(scores[ii]).float().numpy()

        df_out = pd.DataFrame(dict_out)

        if write2file:
            self.format_scores(df_out,aggmethod=aggmethod, output_file=output_file,write2file=True)
        else:
            return df_out


#https://docs.pytorch.org/tutorials/intermediate/pinmem_nonblock.html
#https://docs.pytorch.org/tutorials/intermediate/intermediate_data_loading_tutorial.html


