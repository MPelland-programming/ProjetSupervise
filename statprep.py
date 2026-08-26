#function for setting up the dataset for statistical analyses
import pandas as pd
import numpy as np

def weighted_average(df):
    wm = lambda x: np.average(x, weights=df.loc[x.index, "count"])
    return wm

def aggregate_time_duplicates(model_df,agg_func=None):
    if agg_func is None:
        agg_func = {
            "sum_entropy": "wmean",
            #"sum_surprisal": "wmean",
            "ntokens": "wmean",       # also fixes the "wmeans" typo
            "lencontext": "wmean",
            "propspeaker": "wmean",
        }
    else:
        agg_func = agg_func.copy()   # don't mutate the caller's dict either

    for kk in agg_func.keys():
        if agg_func[kk] == "wmean":
            agg_func[kk] = weighted_average(model_df)

    agg_func["role"] = "first"
    agg_func["file"] = "first"
    agg_func["count"] = "sum"

    grouped = model_df.groupby(["name", "code","age_months"]).agg(agg_func).reset_index()

    return grouped[grouped["count"]>0].reset_index()

def aggregate_parents(model_df,agg_func=None):
    if agg_func is None:
        agg_func = {
            "sum_entropy": "wmean",
            #"sum_surprisal": "wmean",
            "ntokens": "wmean",       # also fixes the "wmeans" typo
            "lencontext": "wmean",
            "propspeaker": "wmean",
        }
    else:
        agg_func = agg_func.copy()   # don't mutate the caller's dict either

    for kk in agg_func.keys():
        if agg_func[kk] == "wmean":
            agg_func[kk] = weighted_average(model_df)

    agg_func["role"] = "first"
    agg_func["file"] = "first"
    agg_func["count"] = "sum"

    model_df.loc[model_df["role"].isin(["mother", "father"]), "role"] = "parent"

    return model_df.groupby(["name", "code", "age_months"]).agg(agg_func).reset_index()

def dependent_var_setup(model_df,min_age_gap=2,test=False):
    children = model_df[model_df["role"] == "target_child"].copy()
    parents  = model_df[model_df["role"] == "parent"].copy()

    # create an adjusted key: "child age minus the minimum gap"
    children["age_months_adj"] = children["age_months"] - min_age_gap

    children = children.sort_values("age_months_adj")
    parents = parents.sort_values("age_months")

    merged = pd.merge_asof(
        children,
        parents,
        left_on="age_months_adj",
        right_on="age_months",
        by="name",
        direction="backward",
        suffixes=("_child", "_parent"),
        allow_exact_matches=False
    )

    if test:
        return merged
    else:
        # drop rows with NaN values in the role_parent column
        merged = merged.dropna(subset=["role_parent"]).reset_index(drop=True).copy()
        merged["name"] = merged["name"]+merged["code_child"]
        merged.drop(["code_child","code_parent","age_months_adj","role_child","role_parent"], axis=1, inplace=True)
        merged["age_diff"] = merged["age_months_child"] - merged["age_months_parent"]
        merged = merged.rename(columns={"age_months_child": "age_months_t2", "age_months_parent": "age_months_t1"})

        study_name = []

        for tt in merged["name"]:
            sn, _ = tt.split("_", maxsplit=1)
            study_name.append(sn.lower())

        study_df = pd.DataFrame({'study': study_name})

        merged = pd.concat([merged, study_df], axis=1)

        return merged

def gmm_setup(model_file,time_agg="wmean",parent_agg="wmean",min_age_gap=3):
    """

    :param model_file:
    :return:
    """
    df = pd.read_csv(model_file)
    grouped_df = aggregate_time_duplicates(df)
    grouped_df = aggregate_parents(grouped_df)

    return dependent_var_setup(grouped_df,min_age_gap=min_age_gap)