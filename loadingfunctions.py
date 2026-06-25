import pandas as pd
from pathlib import Path

def get_file_and_pcodes(participant_doc,ext = ".flo.cex"):
    folder = Path(participant_doc).parent

    partdf = pd.read_csv(participant_doc,sep="\t")
    filtdf = partdf[partdf['skip'] == 0]

    aggdf = filtdf.groupby('file')['code'].apply(list).reset_index()

    return aggdf

    #for ii in range(len(aggdf)):
    #    tname = aggdf["file"].iloc[ii]
    #    newfname = str(Path(folder, tname).with_suffix(ext))

    #    aggdf["file"].iloc[ii] = newfname

    #    with open(newfname, 'rb') as f:
    #        flenght.append(sum(1 for _ in f)/2)

    #return

