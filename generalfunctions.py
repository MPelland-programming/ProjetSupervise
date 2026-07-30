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
    Iterate through a subfolder to concatenat all files of .csv format, then left join the concatenated files to the main one
    based on the column filename.
    :param main_file:
    :param sub_folder:
    :return: uptdated main file saved in the subfolder
    """
    main_df = pd.read_csv(main_file)

    # Concatenate all CSVs into a single DataFrame
    df_list = []
    for file in Path(sub_folder).glob("*.csv"):
        df = pd.read_csv(file)
        df_list.append(df)

    concatenated_df = pd.concat(df_list, ignore_index=True)

    updated_main_file = main_df.merge(
        concatenated_df,
        left_on=["file", "code"],
        right_on=["file", "speaker"],
        how="left"
    )

    # Save updated main file back into the subfolder
    updated_main_file.to_csv(Path(sub_folder,Path(main_file).name),index=False)






