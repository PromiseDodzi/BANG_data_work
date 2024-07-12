import argparse
import pandas as pd
import numpy as np

from segments.tokenizer import Tokenizer
from functions import prior_forms, preprocess_data,parse_noun_data,parse_verb_data,parse_adj_num_data,parse_other_data

def data_preparer(output_name="manually-edited.csv", data="data.tsv"):
    """
    This function takes a dataset and parses it
    data- the raw tsv data
    output_name- name of output (.tsv)
    """
    df = pd.read_csv(data, sep="\t", encoding="utf-8")

    df = preprocess_data(df)

    # Apply the parsing functions selectively based on the POS column
    df.loc[df["POS"] == "noun", "SINGULAR"] = df[df["POS"] == "noun"]["PARSED"].apply(parse_noun_data)
    df.loc[df["POS"] == "verb", "PARSED FORM"] = df[df["POS"] == "verb"]["PARSED"].apply(parse_verb_data)
    df.loc[df["POS"].isin(["adjective", "numeral"]), "SINGULAR"] = df[df["POS"].isin(["adjective", "numeral"])]["PARSED"].apply(parse_adj_num_data)
    df.loc[df["POS"].isin(["pronoun", "other"]), "SINGULAR"] = df[df["POS"].isin(["pronoun", "other"])]["PARSED"].apply(parse_other_data)
    
    return df.to_csv(output_name, index=False)

if __name__ == "__main__":
    data_preparer()

