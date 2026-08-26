#First set up the environment.

import generalfunctions as gf
from pathlib import Path
import os
import statprep as sp

sub_folder = Path(os.getcwd())
main_file = Path(sub_folder.parent,"model.csv")
out_file = Path(sub_folder,"model.csv")
write_file = Path(sub_folder,"new_model.csv")

gf.multi_join(main_file,sub_folder)

out_df = sp.gmm_setup(out_file,time_agg="wmean",parent_agg="wmean",min_age_gap=3)

out_df.to_csv(write_file)