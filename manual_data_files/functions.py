
from .utils import NounParser,VerbParser,AdjectiveNumeralParser
import pandas as pd
from segments import Tokenizer
import os


noun_parser = NounParser()
verb_parser = VerbParser()
adj_num_parser = AdjectiveNumeralParser()

def prior_forms(row):
    """
    Puts all forms that have been parsed into a single column.
    """
    if pd.isna(row["POS"]):
        return None
    elif row["POS"] in ["noun", "numeral", "adjective"]:
        form = str(row["SINGULAR"]) if isinstance(row["SINGULAR"], str) else ""
        return form
    elif row["POS"] == "verb":
        verb = row["FORM"]
        if pd.isna(verb):
            return None
        else:
            return verb
    else:
        form = str(row["SINGULAR"]) if isinstance(row["SINGULAR"], str) else ""
        return form

#getting parser-orthography profile path
base_dir = os.getcwd()  
ortho_path = os.path.join(base_dir, "manual_data_files", 'ortho_1.tsv')

def preprocess_data(df, profile=ortho_path):
    df["BEFORE_PARSE"] = df.apply(prior_forms, axis=1)
    tk = Tokenizer(profile)
    df["PARSED"] = df["BEFORE_PARSE"].apply(lambda x: tk(x, column="IPA") if isinstance(x, str) else x)  # Running orthography profile
    df["PARSED"] = df["PARSED"].apply(lambda x: x.replace(" ", "") if isinstance(x, str) else x)  # Removing spaces
    return df

def parse_noun_data(noun):
    if pd.isna(noun):
        return None
    if noun.endswith("y") or (noun.endswith("ⁿ") and noun[-2] == "y"):
        parsed_noun = noun_parser.double_last_vowels(
            noun_parser.identified_suffixes(
                noun_parser.hyphen_space(
                    noun_parser.nasalized_stops(
                        noun_parser.cvcv_segmentation(
                            noun_parser.parse_off_final_nasals(
                                noun_parser.existing_parses(
                                    adj_num_parser.y_suffixes(noun.strip("()/_")))))))))
    else:
        parsed_noun = noun_parser.double_last_vowels(
            noun_parser.identified_suffixes(
                noun_parser.hyphen_space(
                    noun_parser.nasalized_stops(
                        noun_parser.cvcv_segmentation(
                            noun_parser.parse_off_final_nasals(
                                noun_parser.existing_parses(noun.strip("()/_"))))))))
    return parsed_noun

def parse_verb_data(verb):
    if pd.isna(verb):
        return None
    parsed_verb = verb_parser.double_last_vowels(
        verb_parser.post_editing_short_strings(
            verb_parser.segment_cvcs(
                verb_parser.existing_parses(verb.strip(")(_")))))
    return parsed_verb

def parse_adj_num_data(adjective_numeral):
    if pd.isna(adjective_numeral):
        return None
    parsed_adj_num = adj_num_parser.double_last_vowels(
        adj_num_parser.miscellaneous(
            adj_num_parser.switch_hyphen_position(
                adj_num_parser.replace_hyphens_keep_last(
                    adj_num_parser.y_suffixes(
                        adj_num_parser.isolating_suffixes(
                            adj_num_parser.existing_parses(adjective_numeral.strip("()/_"))))))))
    return parsed_adj_num

def parse_other_data(form):
    return noun_parser.double_last_vowels(noun_parser.existing_parses(form))
