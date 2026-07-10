import argparse
import yaml
from pathlib import Path
import subprocess
import txtpreprocess as txtp
import txtscoring as txtsc
import sbatchwriter as sbw
from transformers import AutoTokenizer, MistralForCausalLM
from torch import cuda

## Command line input ##
parser = argparse.ArgumentParser(
    description=(
        'Launches the two main steps of the parallelised part of the analysis. \n'
        'Necessitates a config file in YAML format. \n'
        '\n'
        'YAML should contain: \n'
        '   text_folder: folder for files    : where the transcript files are to be found. \n'
        '        Format: /home/files \n'
        '   config_folder:  \n'
        '        Format: /home/files/models \n'
        '   transcript_file_list : participant info doc: a .csv with column files for the file names \n'
        '        Format: model1.csv \n'
        '   preprocessing_steps: list of preprocessing steps. \n'
        '        Format: [name1,name2,name3] \n'
        '   measures:  list of measures to obtain from the transcripts \n'
        '        Format: [measure1,measure2,measure3] \n'
        '   output_folder: folder for output files \n'
        ' \n'
        ' Example YAML: \n'
        '   text_folder : /home/files\n'
        '   config_folder : /home/models \n'
        '   transcript_file_list : model1.csv \n'
        '   preprocessing_steps: [m01] \n'
        '   nallocate: 2048 \n'
        '   measures: [sum_entropy] \n'
        '   output_folder: /home/output\n'
        '   output_file: output.csv     only necessary when using task "score"\n'
        )
    ,epilog=(
        'Note that there are two options for providing the list of files to process. \n'
        'The first is in the command lines using --transcript_list \n'
        'The second is in adding it to the YAML file \n'
        'If both a provided, the program wont run. \n'
    )
    ,formatter_class=argparse.RawDescriptionHelpFormatter
)
parser.add_argument("config_file",type = str
                    ,help = "YAML configuration file")
parser.add_argument("task", type = str
                    ,choices = ["count","score"]
                    ,help = "Whether to count number of lines per doc or score the sentences.")
parser.add_argument("--transcript_file_list","-t"
                    ,help = "If not specified in config file, a .csv type file with a column named 'file' containing the list of file names to score")

args = parser.parse_args()

## YAML config loading ##
with open(args.config_file) as f:
    config = yaml.safe_load(f)


## Setting up variables ##
task = args.task
text_folder = config["text_folder"]
preprocessing_steps = config["preprocessing_steps"]

if "transcript_file_list" in config.keys():
    if args.transcript_file_list:
        raise NameError("transcript_file_list cannot both specified in config file and as argument.")
    else:
        transcript_file_list = str(Path(config["config_folder"],config["transcript_file_list"]))
else:
    transcript_file_list = args.transcript_file_list

################
## Main part ##
################
modelname = "/home/mpelland/links/projects/def-eporte2/mpelland/predictability/lang_models/mistral/m7Bv03/snapshots/caa1feb0e54d415e2df31207e5f4e273e33509b1/"


#setup extra vars
extractor = txtp.TextExtraction(preprocessing_steps)

#count and allocation task
if task == "count":
    myallocator = txtp.Allocator(transcript_file_list,text_folder,extractor)
    myallocator.allocate(config["nallocate"])
    num_score_jobs = myallocator.write_allocation(config)
    sbw.write_sbatch_file(num_score_jobs,config)

    sbw.launch_sbatch_job(config,"submit_scoring.sh")

if task == "score":
    tokenizer = AutoTokenizer.from_pretrained(modelname,use_fast=True, local_files_only=True)
    model = MistralForCausalLM.from_pretrained(modelname,local_files_only=True)
    #print(f"CPU RAM after load: {model.get_memory_footprint() / 1e9:.2f} GB")#####################################################
    #print(f"Model dtype: {next(model.parameters()).dtype}")#######################################################################

    device ='cuda' if cuda.is_available() else 'cpu'

    scorer = txtsc.SentenceScorer(transcript_file_list, text_folder, extractor, tokenizer)
    dataset_params = {
        "context_length": config["context_length"],
        "batch_size": config["batch_size"],
        "num_workers": config["num_workers"]
    }
    scorer.gen_dataset_and_dataloader(**dataset_params)
    scorer.score_sentences(model,device=device, write2file=True, output_file=config["output_file"])