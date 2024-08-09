import pandas as pd
import os
from manual_data_files.functions import preprocess_data,parse_noun_data,parse_verb_data,parse_adj_num_data,parse_other_data


base_dir = os.getcwd()  
data_path = os.path.join(base_dir,"manual_data_files","towards_manually_edited.tsv")

def data_preparer(output_name='manually-edited.csv', data=data_path):
    """
    This function takes a dataset and parses it
    data- the raw tsv data
    output_name- name of output (.tsv)
    """
    #creating output path
    base_dir = os.getcwd()  
    output_dir = os.path.join(base_dir,"raw")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, output_name) 

    #preprocessing data
    df = pd.read_csv(data, sep="\t", encoding="utf-8")
    df = preprocess_data(df)

    # Apply the parsing functions selectively based on the POS column
    df.loc[df["POS"] == "noun", "SINGULAR"] = df[df["POS"] == "noun"]["PARSED"].apply(parse_noun_data)
    df.loc[df["POS"] == "verb", "PARSED FORM"] = df[df["POS"] == "verb"]["PARSED"].apply(parse_verb_data)
    df.loc[df["POS"].isin(["adjective", "numeral"]), "SINGULAR"] = df[df["POS"].isin(["adjective", "numeral"])]["PARSED"].apply(parse_adj_num_data)
    df.loc[df["POS"].isin(["pronoun", "other"]), "SINGULAR"] = df[df["POS"].isin(["pronoun", "other"])]["PARSED"].apply(parse_other_data)

    print(f"\nAll data succesfully parsed\nOutput found at {output_path}\n")
    
    return df.to_csv(output_path, index=False)

if __name__ == "__main__":
    data_preparer()

