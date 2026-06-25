import organizer
import loadingfunctions as lf
import txtpreprocess
import txtpreprocess as tp

#Flags
invenv = True           #whether we are in a virtual environmnent
task_organize = False    #whether to organize the raw data
task_score = False

source_folder = "/home/hereinlies/Downloads/Data"
organized_folder = "/home/hereinlies/Downloads/Temp"
text_folder = "/home/hereinlies/Downloads/Text"
preprocessing_step_list = ["m01"]                                #Sets the list of text prepocessing steps
#participant_doc = text_folder+"/model.txt"  #This should be in the same director as text_folder

if task_organize:
    #first step in organizing the data
    mo = organizer.MainOrganizer(source_folder,organized_folder)
    mo.organize()

    #Extract stat model variables
    me = organizer.MainExtractor(organized_folder,text_folder)
    me.build_participant_doc()

    #step 2 of organizing the data
    if invenv:
        print("Change flag of invenv to False or run manually outside of virtual environment")
    else:
        me.cha2text(text_folder,gen_participant_doc = False)

if task_score:
    preprocessor = tp.TextExtraction(method_list=preprocessing_step_list)
    file_code = lf.get_file_and_pcodes(participant_doc)
