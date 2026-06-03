import childespy
import pandas

cpytransc = childespy.get_transcripts(collection = "Eng-NA")
onltransc = pandas.read_excel("/home/hereinlies/Documents/Documents/Ecole/HEC/ProjetSupervise/data/EngNaOnlyMod.ods",engine ="odf",dtype="str").fillna("null")

onltransc["corpora"] = onltransc["path"].str.split("/").str[2]
cpytransc["corpora"] = cpytransc["filename"].str.split("/").str[1]

onltransc["path"] = onltransc["path"].astype(str)+".xml"
cpytransc["path"] = "childes/"+cpytransc["filename"]

cpytransc["pid"] = cpytransc["pid"].astype(str)
onltransc["pid"] = onltransc["pid"].astype(str)

transc = cpytransc.join(onltransc,on = "pid",how="inner")