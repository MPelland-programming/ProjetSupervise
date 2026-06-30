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







