import organizer

#Whether we are currently in a virtual environment or not.
invenv = True

source_folder = "/home/hereinlies/Downloads/Data"
organized_folder = "/home/hereinlies/Downloads/Temp"
text_folder = "/home/hereinlies/Downloads/Text"

#first step in organizing the data
mo = organizer.MainOrganizer(source_folder,organized_folder)
mo.organize()

#Extract stat model variables
me = organizer.MainExtractor(organized_folder)
me.build_participant_doc("/home/hereinlies/Downloads/Text/model.txt")

#step 2 of organizing the data
if invenv:
    print("Change flag of invenv to False or run manually outside of virtual environment")
else:
    me.cha2text(text_folder,gen_participant_doc = False)