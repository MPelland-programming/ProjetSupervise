import argparse
import yaml
import generalfunctions as gf
import pandas as pd
from pathlib import Path
import txtpreprocess as txtp

## Command line input ##
parser = argparse.ArgumentParser(
    description=(
        'Launches the two main steps of the parallelised part of the analysis. \n'
        'Necessitates a config file in YAML format. \n'
        '\n'
        'YAML should contain: \n'
        '   text_folder: folder for files    : where the transcript files are to be found. \n'
        '        Format: /home/files \n'
        '   transcript_folder:  \n'
        '        Format: /home/files/models \n'
        '   transcript_file : participant info doc: a .csv with column files for the file names \n'
        '        Format: model1.csv \n'
        '   preprocessing_steps: list of preprocessing steps. \n'
        '        Format: [name1,name2,name3] \n'
        ' \n'
        ' Example YAML: \n'
        '   text_folder : /home/files\n'
        '   transcript_folder : home/models \n'
        '   transcript_file : model1.csv \n'
        '   preprocessing_steps: [m01] \n'
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
parser.add_argument("--transcript_file","-t"
                    ,help = "If not specified in config file, a .csv type file with a column named 'file' containing the list of file names to score")

args = parser.parse_args()

## YAML config loading ##
with open(args.config_file) as f:
    config = yaml.safe_load(f)


## Setting up variables ##
task = args.task
text_folder = config["text_folder"]
preprocessing_steps = config["preprocessing_steps"]

if "transcript_file" in config.keys():
    if args.transcript_file:
        raise NameError("transcript_file cannot both specified in config file and as argument.")
    else:
        transcript_file = str(Path(config["transcript_folder"],config["transcript_file"]))
else:
    transcript_file = args.transcript_file

################
## Main part ##
################

#setup extra vars
extractor = txtp.TextExtraction(preprocessing_steps)

#count and allocation task
if task == "count":
    myallocator = txtp.Allocator(transcript_file,text_folder,extractor)
    myallocator.allocate(32768)
    myallocator.write_allocation(config)