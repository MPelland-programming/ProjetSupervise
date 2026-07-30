import pandas as pd
from pathlib import Path

def oneway_bubble_sort(mainlist:list,sublist:list):
    """
    bubble sort meant for one pass allowing for quick sorting of almost sorted list.
    :param mainlist: values to use for sorting
    :param sublist:  secondary list to follow first list
    :return: updated main and sub lists.
    """
    llength = len(mainlist)

    for ii in range(llength-1,0,-1):
        if mainlist[ii] > mainlist[ii-1]:
            mainlist[ii-1], mainlist[ii] = mainlist[ii], mainlist[ii-1]
            sublist[ii-1], sublist[ii] = sublist[ii], sublist[ii-1]

    return mainlist,sublist

def multi_join(main_file,sub_folder):
    """
    Takes a main file and iterates through a subfolder to join all files of .csv format.
    :param main_file:
    :param sub_folder:
    :return: uptdated main file saved in the subfolder
    """
    main_df = pd.read_csv(main_file)

    for sub_file in Path(sub_folder).glob("*.csv"):
        if sub_file != Path(main_file):
            sub_df = pd.read_csv(sub_file)
            main_df = pd.concat([main_df,sub_df],ignore_index=True)

    main_file_name = Path(main_file).name
    main_df.to_csv(Path(sub_folder,main_file_name),index=False)





