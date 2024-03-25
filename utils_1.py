import re
import pandas as pd
import numpy as np
class NounParser:
    def __init__(self):
        self.consonants = {"b", "c", "d", "f", "g", "h", "j", "k", "l", "m", "n", "p", "r", "s", "t", "v", "w", "y", "z", "ʔ", "ɲ", "ŋ"}
        self.exceptions = ["nd", "nt", "ŋg", "ŋk", "ɲj", "mb","mp" ]
        self.vowels = {"ɛ̌", "ɔ̌", "ɛ̂", "ɔ̂", "ɛ́", "ɔ́", "ɛ̀", "ɔ̀", "ì", "í", "ǔ", "û",'ê', 'ě', 'è', 'é', 'ô', 'ò', 'ǒ', 'ó', 'ǎ', 
                        'â', 'à', 'á', 'ɛ̌', 'ɛ̂', 'ɛ́', 'ɛ̀', 'û', 'ǔ', 'ú', 'ù', 'ǐ', 'î', 'í', 'ì', ' ̀ɔ ', 'ɔ́', 'ɔ̌', 'ɔ̂',
                        "i", "e", "ɛ", "u", "o", "ɔ", "a"}
        self.replacements = {"i":"i", 'í': 'í', 'ì': 'ì', 'ǐ': 'í','î': 'ì', 
                             "e": "e", 'é': 'é', 'è': 'è','ě': 'é', 'ê': 'è',
                             'ɛ':'ɛ', 'ɛ́':'ɛ́', 'ɛ̀': 'ɛ̀', "ɛ̌":'ɛ́', 'ɛ̂': 'ɛ̀',
                             "u": "u", 'ú': 'ú', 'ù': 'ù',"ǔ":'ú', "û": 'ù',
                             "o": "o", 'ó': 'ó', 'ò': 'ò', 'ǒ': 'ó', 'ô': 'ò',
                             'ɔ': 'ɔ', 'ɔ́': 'ɔ́',' ̀ɔ ': ' ̀ɔ ', 'ɔ̌':'ɔ́', 'ɔ̂': ' ̀ɔ ', 
                             "a": "a", 'á': 'á','à':'à',  'ǎ': 'á', 'â':'à'}

    def parse_durationals(self, item):
        "Replaces durationals with the preceding vowel"
        new_word = ""
        for alphabet in item:
            if alphabet == ":":
                if item.index(alphabet) > 1 and item[item.index(alphabet)-1] in self.replacements.values():
                    new_word += self.replacements[item[item.index(alphabet)-1]]
                elif item.index(alphabet) > 2 and item[item.index(alphabet)-2] in self.replacements.values():
                    new_word += self.replacements[item[item.index(alphabet)-2]]
                else:
                    new_word += alphabet
            else:
                new_word += alphabet
        return new_word

    def cvcv_segmentation(self, word, indexes=[3, 5, 7, 9, 11]):
        """Parses syllables to follow a cvcv basic structure"""
        consonant_count = 0
        new_word = ""
        for letter in word:
            if letter in self.consonants and letter != "ⁿ":
                consonant_count += 1 #continue consonant count
                if consonant_count in indexes:
                    if word[word.index(letter)-1] != "-":
                        new_word += "-" + letter #parsing
                    else:
                        new_word += letter
                else:
                    new_word += letter
            elif letter == " ": #start recount at word boundaries
                consonant_count=0
                new_word +=letter
            else:
                new_word += letter #skipping over vowels

        for i in self.exceptions:
            with_hyphen = i[0] + "-" + i[1]
            if with_hyphen in new_word:  #cases where there is a hyphen between nasalized consonants
                idx = new_word.index(with_hyphen)
                new_word = new_word[:idx] + "-"  + i[0]+i[1] + new_word[idx + 3:]
        return new_word.replace("--", "-")

    def hyphen_space(self, word):
        """removes hyphens after morphemic boundaries indicated by a space"""
        if "-" in word and (word[word.index("-")-1]==" " or word[word.index("-") + 1] ==" "):
            word=word.replace("-", "")
        return word

    def nasalized_stops(self, word):
        """Parses 'consonant ensembles i.e. nasalized consonants'"""
        for i in self.exceptions:
            with_hyphen = i[0] + "-" + i[1]
            if with_hyphen in word:  #cases where there is a hyphen between the nasalized consonants
                idx = word.index(with_hyphen)
                if word[idx-1] != "-":
                    word = word[:idx] + "-"  + word[idx + 3:]
                    remainder = word[word.index(i) + 2:] if i in word and len(word) > idx + 3 else None
                    word = word[:word.index(i) + 2] + self.cvcv_segmentation(remainder, indexes=[1, 3, 5, 7, 9]) if remainder is not None else word

                else:
                    word = word[:idx]  + word[idx + 3:]
                    remainder = word[word.index(i) + 2:] if i in word and len(word) > idx + 3 else None
                    word = word[:word.index(i) + 2] + self.cvcv_segmentation(remainder, indexes=[1, 3, 5, 7, 9]) if remainder is not None else word
            else:                #cases where nasalized consonants have no hyphen in-between 
                if i in word:
                    idx = word.index(i)
                    word = word[:idx] + "-"  + i + word[idx + 2:]  
                    if len(word) > idx + 2:
                        remainder = word[idx + 3:]  if i in word and len(word) > idx + 3 else None
                        word = word[:idx + len(i) + 1] + self.cvcv_segmentation(remainder, indexes=[1, 3, 5, 7, 9]) if remainder is not None else word
                else:
                    word=word
        return self.hyphen_space(word.replace("--", "-"))



class VerbParser:
    def __init__(self):
        self.vowels = {
            "ɛ̌", "ɔ̌", "ɛ̂", "ɔ̂", "ɛ́", "ɔ́", "ɛ̀", "ɔ̀", "ì", "í", "ǔ", "û", 'ê', 'ě', 'è', 'é', 'ô', 'ò', 'ǒ', 'ó',
            'ǎ', 'â', 'à', 'á', 'ɛ̌', 'ɛ̂', 'ɛ́', 'ɛ̀', 'û', 'ǔ', 'ú', 'ù', 'ǐ', 'î', 'í', 'ì', ' ̀ɔ ', 'ɔ́', 'ɔ̌',
            'ɔ̂', "i", "e", "ɛ", "u", "o", "ɔ", "a"
        }
        self.consonants = {
            "b", "c", "d", "f", "g", "h", "j", "k", "l", "m", "n", "p", "r", "s", "t", "v", "w", "y", "z", "ʔ",
            "ɲ", "ŋ"
        }
        self.exceptions = ["nd", "nt", "ŋg", "ɲj", "mb"] #nasalized consonants in data

    def parse_durationals(self, item):
        """Double cases where a vowel has durataional marking"""
      
        def get_last_vowel(item):
            """Extracts the last vowel from the input string ending with ':'"""
            if item.endswith(":"):
                return item[-2]
            return None

        vowels = [get_last_vowel(item)] # extracting vowels 
        replacements = {
            "ɛ̌": "ɛ́", "ɔ̌": "ɔ́", "ɛ̂": "ɛ̀", "ɔ̂": "ɔ̀",
            "ɛ́": "ɛ́", "ɔ́": "ɔ́", "ɛ̀": "ɛ̀", "ɔ̀": "ɔ̀",
            "ì": "ì", "í": "í", "ǔ": "ú", "û": "ù"
        }# cases where vowels are not extracted

        for letter in replacements:     # Handle exceptions like 'tɔ́d-ɛ̀:' and 'nàrⁿ-ɛ́:'
            if item.endswith(letter + ':'):
                return item[:-1] + "-" + replacements[letter]

        if 'ɛ᷈:' in item:                # Handle the exceptional case 'jɛ᷈:'
            return item[:-1] + "-ɛ᷈"

        for letter in replacements:     # Handle cases of unextracted vowels
            if item.endswith(":"):
                if letter in item[1:4]:
                    return item[:-1] + "-" + replacements[letter]

        material = {                                   # Handle cases with extracted vowels 
            'ǎ': 'á', 'ê': 'è', 'ô': 'ò', 'ě': 'é',
            'ǐ': 'í', 'î': 'ì', 'ǒ': 'ó', 'â': 'à',
            'ɛ́': 'ɛ́', 'ɛ̀': 'ɛ̀', 'ǔ': 'ú', 'í': 'í',
            'ì': 'ì'
        }.get(vowels[0], vowels[0])
        return item[:-1] + "-" + material if vowels[0] else item

    def verify_exceptions(self, word):
        """verifies that consonant ensembles are not parsed as different consonants"""
        for i in self.exceptions:
            with_hyphen = i[0] + "-" + i[1]
            if with_hyphen in word:
                idx = word.index(with_hyphen)
                word = word[:idx] + i + "-" + word[idx + 3:]
        word = word.replace("--", "-")
        return word

    def vowel_tone_hyphen(self, word):
        "handles cases in which despite parse_durationals, it is difficult to extract vowels"
        if len(word) >= 4:
            if word[-1] not in self.vowels.union(self.consonants) and word[-2] == "-":
                return self.verify_exceptions(word[:-3] + "-" + word[-3] + word[-1])
        return self.verify_exceptions(word)

    def syllabic_vowels(self, word):
        "isolates syllabic vowels and parses them off"
        final_word = word

        for alphabet in self.vowels:
            if alphabet in word[2:-2]:
                try:
                    index = word.index(alphabet)
                    if word[index - 1] == "-" and word[index + 1] in self.consonants:
                        final_word = final_word.replace(word[index], f"{alphabet}-")
                except ValueError:
                    pass

        return self.vowel_tone_hyphen(final_word.rstrip('-').replace("--", "-"))

    def post_coda(self, word):
        """parses vowels sounds that occur after codas"""
        for i in range(1, len(word) - 3):
            if word[i] in self.consonants:
                if i + 1 < len(word) and word[i + 1] == "-":
                    try:
                        if i + 2 < len(word) and i + 3 < len(word) and word[i + 2] in self.vowels and word[
                            i + 3] in self.consonants:
                            material = word[:i + 2] + "-" + word[i + 2:]
                            return self.syllabic_vowels(material)
                        else:
                            return self.syllabic_vowels(word)
                    except IndexError:
                        return self.syllabic_vowels(word)
        return self.syllabic_vowels(word)

    def special_mid_forms(self, item):
        """takes words of between 3-4 alphabets long that have special characters and parses them"""
        if "-" not in item[-3:] and item[-1] not in self.consonants:
            return self.post_coda(item[:-1] + "-" + item[-1:])
        return self.post_coda(item)

    def long_words(self, word):
        """takes word of length 5 and parses them into CVC"""
        current_syllable = ''
        consonant_count = 0

        for i in range(len(word)):
            if word[i] in self.consonants:
                consonant_count += 1
                if consonant_count == 2 and i < len(word):
                    word = word[:i + 1] + '-' + word[i + 1:]
                    consonant_count = 0
        return self.post_coda(word)

    def segment_cvcs(self, item):
        """main segmentation function to be implemented after parse_durationals has been implemented"""
        if len(item) >= 5:
            return self.long_words(item) #calling long_words function
        elif 3 <= len(item) <= 4:
            return self.special_mid_forms(item) #calling special_mid_forms function
        else:
            return self.post_coda(item) #directly sending words to post_coda function for parsing
