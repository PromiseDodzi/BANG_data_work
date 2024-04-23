import re
import pandas as pd
import numpy as np


class NounParser:
    def __init__(self):
        self.consonants = {"b", "c", "d", "f", "g", "h", "j", "k", "l", "m", "n", "p", "r", "s", "t", "v", "w", "y", "z", "ʔ", "ɲ", "ŋ", "ɣ"}
        self.exceptions = ["nd", "nt", "ŋg", "ŋk", "ɲj", "mb","mp" ]
        self.vowels = {"ɛ̌", "ɔ̌", "ɛ̂", "ɔ̂", "ɛ́", "ɔ́", "ɛ̀", "ɔ̀", "ì", "í", "ǔ", "û",'ê', 'ě', 'è', 'é', 'ô', 'ò', 'ǒ', 'ó', 'ǎ', 
                        'â', 'à', 'á', 'ɛ̌', 'ɛ̂', 'ɛ́', 'ɛ̀', 'û', 'ǔ', 'ú', 'ù', 'ǐ', 'î', 'í', 'ì', ' ̀ɔ ', 'ɔ́', 'ɔ̌', 'ɔ̂',
                        "i", "e", "ɛ", "u", "o", "ɔ", "a"}
        self.replacements = {"i":"i", 'í': 'í', 'ì': 'ì', 'ǐ': 'í','î': 'ì', "e": "e", 'é': 'é', 'è': 'è','ě': 'é', 'ê': 'è','ɛ':'ɛ', 
                             'ɛ́':'ɛ́', 'ɛ̀': 'ɛ̀', "ɛ̌":'ɛ́', 'ɛ̂': 'ɛ̀',"u": "u", 'ú': 'ú', 'ù': 'ù',"ǔ":'ú', "û": 'ù',"o": "o", 'ó': 'ó', 
                             'ò': 'ò', 'ǒ': 'ó', 'ô': 'ò','ɔ': 'ɔ', 'ɔ́': 'ɔ́','ɔ̀': 'ɔ̀', 'ɔ̌':'ɔ́', 'ɔ̂': ' ̀ɔ ', "a": "a", 'á': 'á',
                             'à':'à',  'ǎ': 'á', 'â':'à'}
        self.replacement_exceptions={'ǐ':'ì','î':'í','ě':'è','ê':'é',"ɛ̌":'ɛ̀','ɛ̂':'ɛ́',"ǔ":'ù',"û":'ú','ɔ̌':'ɔ̀','ɔ̂':'ɔ́','ǒ':'ò', 
                                     'ô':'ó','ǎ':'à','â':'á'}
        self.replacement_exceptions_1={'ǐ':'ì','î':'í','ě':'è','ê':'é',"ɛ̌":'ɛ̀','ɛ̂':'ɛ́',"ǔ":'ù',"û":'ú','ɔ̌':'ɔ̀','ɔ̂':'ɔ́','ǒ':'ò','ô':'ó','ǎ':'à','â':'á'}
        self.replacement_exceptions_2={'ǐ':'í','î':'ì','ě':'é','ê':'è',"ɛ̌":'ɛ́','ɛ̂':'ɛ̀',"ǔ":'ú',"û":'ù','ɔ̌':'ɔ́','ɔ̂':'ɔ̀','ǒ':'ó','ô':'ò','ǎ':'á','â':'à'}
        
        self.extra_material={ 'ǎ': 'á', 'ê': 'è', 'ô': 'ò', 'ě': 'é','ǐ': 'í', 'î': 'ì', 'ǒ': 'ó', 'â': 'à', 'ɛ́': 'ɛ́', 'ɛ̀': 'ɛ̀', 
                             'ǔ': 'ú', 'í': 'í','ì': 'ì'} 

    def parse_off_final_nasals(self, item):
        if item and item[-1] =="ⁿ":
            return item[:-1] + "-" + item[-1:]
        else:
            return item
        

    def existing_parses(self, word):
        """
        reparses existing parses:
        Jeff's parses: 
        hyphens in word-final syllables are eliminated.
        hyphens elsewhere indicate word boundaries

        parse from orthography profile:
        spaces are eliminated
        """
        new_word=""  #Jeff's parses
        for index, letter in enumerate(word):
            idx=len(word)-index
            if letter== "-" and idx <=4:
                new_word += ""
            elif letter== "-" and idx >3:
                new_word += " "
            else:
                new_word += str(letter)

        final_word_1="" #eliminating orthography profile spaces
        for letter in new_word:
            if letter==" ":
                final_word_1 += ""
            else:
                final_word_1 += letter

        final_word_2=""
        for letter in final_word_1:
            if letter=="#":
               final_word_2 += " "
            else:
                final_word_2 += letter
            
        return  final_word_2  

    
    
    def parse_noun_durationals(self, item):
        """
        parses durational marking in nouns
        """
        new_word = ""
        for index, letter in enumerate(item):                 #segments that preceed a durational and which have contour tones
            if (letter in self.replacement_exceptions_1.keys() and 
                index < len(item) - 1 and item[index + 1] == ":"):
                new_word += str(self.replacement_exceptions_1.get(letter, letter)) 
            elif (letter == ":" and                          #replacing durationals that are preceeded by a contour tone
                  index > 0 and 
                  item[index - 1] in self.replacement_exceptions_1.keys()):
                new_word += str(self.replacement_exceptions_2.get(item[index - 1], letter))
            elif letter ==":" and item[index-1] not in self.replacement_exceptions_1.keys():     #replacing durationals that are preceded by level tones
                new_word += str(self.replacements.get(item[index-1],f"{ item[index-2]+ item[index-1]}" ))
            else:
                new_word +=letter
        return new_word
    

    def cvcv_segmentation(self, word, indexes=[3, 5, 7, 9, 11]):
        """
        Parses syllables to follow a cvcv basic structure
        """
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
        """
        remove hyphens after morphemic boundaries indicated by a space and hyphens occuring word initially
        """
        if "-" in word and (word[word.index("-")-1]=="#" or word[word.index("-") + 1] ==" "):#eliminates hyphens after space
            word=word.replace("-", "")
        elif word.find("-")==0: #elinates hyphens that occur at the begining of a word
            word=word[1:]
        return word

    def nasalized_stops(self, word):
        """
        Parses 'consonant ensembles i.e. nasalized consonants'
        """
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

    def identified_suffixes(self, word):
        """
        This function parses suffixes that have been identified. These are the suffixes identified so far:
        'g'+ vowel
        'm'+vowel
        """
        new_word=""
        for i in range(len(word)):
            letter = word[i]
            if i >= len(word) - 3:  # Checking if the letter is within the last three alphabets
                if letter == "g" and word[i - 1] != "ŋ":#checking if "g" is not a nasalized consonant
                    new_word += f"-{letter}"
                elif letter == "m":
                    new_word += f"-{letter}"
                else:
                    new_word += letter
            else:
                new_word += letter
        
        return  self.hyphen_space(new_word.replace("--", "-"))



class VerbParser(NounParser):
    def __init__(self):
       super().__init__()
        
    def consonant_count(self, item):
        """
        counts number of consonants in words
        """
        
        if item is None:
            return 0
        
        consonant_count=0
        for letter in item:
            if letter != "ⁿ" and letter in self.consonants:
                consonant_count +=1
        return consonant_count
                      

    def parse_verb_durationals(self, item):
        """
        parses durational marking in nouns
        """
        
        if item.endswith(":"):
            new_word = ""
            for index, letter in enumerate(item):                 #segments that preceed a durational and which have contour tones
                if (letter in self.replacement_exceptions_1.keys() and 
                    index < len(item) - 1 and item[index + 1] == ":"):
                    new_word += str(self.replacement_exceptions_1.get(letter, letter)) 
                elif (letter == ":" and                          #replacing durationals that are preceeded by a contour tone
                      index > 0 and 
                      item[index - 1] in self.replacement_exceptions_1.keys()):
                    if index +1 == len(item):
                        new_word += f"-{str(self.replacement_exceptions_2.get(item[index - 1], letter))}"
                    else:
                        new_word += str(self.replacement_exceptions_2.get(item[index - 1], letter))
                elif letter ==":" and item[index-1] not in self.replacement_exceptions_1.keys():     #replacing durationals that are preceded by level tones
                    if index +1 == len(item):
                        new_word += f"-{str(self.replacements.get(item[index-1],f"{ item[index-2]+ item[index-1]}" ))}"
                    else:
                        new_word += str(self.replacements.get(item[index-1],f"{ item[index-2]+ item[index-1]}" ))
                else:
                    new_word +=letter
        else:
            new_word=self.parse_noun_durationals(item)
    
        return new_word

    def post_editing_short_strings(self, word):
        """
        post edits short words that have been "over-parsed" as a result of issues encountered with character fonts
        """
        
        if word is None:
            return None
        
        consonant_count=self.consonant_count(word)
        if consonant_count <=2 and word.count("-") >1:
            word=word.replace("-", "", 1)
        return word
        
    def hyphen_space(self, word):
        """
        special utility function to remove hyphens after morphemic boundaries indicated by a space and hyphens occurring word initially
        """
        new_word=""
        for index, letter in enumerate(word):
            if letter== "-" and index+1 < len(word) and (word[index+1]== " " or word[index-1]== " ") :
                new_word += ""
            else:
                new_word +=  letter
        return new_word

    
    def maintaining_nasality_on_segment(self, word):
        """
        ensures that nasality remains on segment that is marked for it, and also parses sounds occuring after the nasal marker  
        """
        new_word=""
        for index, letter in enumerate(word):
            if letter == "-" and index + 1 < len(word) and word[index + 1]== "ⁿ":         #zǐǐ-ⁿ zǐ-ǐⁿ can be solved from here but the fonts do not permit this
                new_word +=""
            else:
                new_word += letter
    
        word=""
        for index, letter in enumerate(new_word):
            idx=len(new_word)-index
            if letter == "ⁿ" and 3 >= idx > 1:
                if new_word[index]!= "-":
                    word += f"{letter}-"
    
            else:
                word +=letter
        
        
        if "-" not in word:
            new_word=""
            for index, letter in enumerate(word):
                if letter not in self.consonants and index+1 < len(word) and "ⁿ" in word[index: index+2]:
                    new_word += f"-{letter}"
                else:
                    new_word +=letter
            return self.hyphen_space(new_word)
        else:       
            return self.hyphen_space(word)
        

    def verify_exceptions(self, word):
        """
        verifies that consonant ensembles are not parsed as different consonants and reparses long words with consonant ensembles
        """
        for i in self.exceptions:
            with_hyphen = i[0] + "-" + i[1]
            if with_hyphen in word:
                idx = word.index(with_hyphen)
                word = word[:idx] + i + "-" + word[idx + 3:]
        word = word.replace("--", "-")
        
        return self.maintaining_nasality_on_segment(word)
            

    def vowel_tone_hyphen(self, word):
        """
        handles cases in which despite parse_durationals, it is difficult to extract vowels
        """
        if len(word) >= 4:
            if word[-1] not in self.vowels.union(self.consonants) and word[-2] == "-":
                return self.verify_exceptions(word[:-3] + "-" + word[-3] + word[-1])
        return self.verify_exceptions(word)

    def syllabic_vowels(self, word):
        """
        isolates syllabic vowels and parses them off
        """
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
        """
        parses vowels sounds that occur after codas
        """
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
        """
        takes words of between 3-4 alphabets long that have special characters and parses them
        """
        if "-" not in item[-3:] and item[-1] not in self.consonants:
            return self.post_coda(item[:-1] + "-" + item[-1:])
        return self.post_coda(item)

    def special_long_words(self, word):
        """
        takes word of length 5 and parses them into CVC: this is because of the font-recognition issues encountered
        """
        current_syllable = ''
        consonant_count = 0

        for i in range(len(word)):
            if word[i] != "ⁿ" and word[i] in self.consonants:
                consonant_count += 1
                if consonant_count == 2 and i < len(word):
                    word = word[:i + 1] + '-' + word[i + 1:]
                    consonant_count = 0
        return self.post_coda(word)
   
    
    def long_words(self, word):
        """
        parses long words according to a cvc priority structure and also takes care of idiosyncratic words
        """
        num=[2,4,6,8]
        new_word="" #word parsed according to cvc priority
        consonant_count=0
        for index, letter in enumerate(word):
            
            if letter == "#" or letter== "ⁿ":
                consonant_count=0
                new_word +=letter
                
            elif letter!= "ⁿ" and letter in self.consonants: #just to be extra sure
                consonant_count +=1
                if consonant_count in num:
                    new_word += f"{letter}-"
                elif consonant_count==3 and word[index-1] != " ":
                    new_word +=f"-{letter}"
                else:
                    new_word += letter
                    
            else:
                new_word +=letter
    
        if " "  in new_word and "-" not in new_word[new_word.index(" "):]:   #parsing words such as "gúr-ɔ́ gùrɔ́" which have second parts not responding to code above so they become "gúr-ɔ́ gùr-ɔ́"
            consonant_count=self.consonant_count(new_word[new_word.index(" "):])
            if consonant_count >=2 and new_word[-1] not in self.consonants:
                conso=[x for x in new_word[new_word.index(" "):] if x in self.consonants]
                idx=new_word.index(conso[1])
                new_word=new_word[:idx+1] + "-" + new_word[idx+1:] 
        
        new_word=new_word[:-1].replace("--", "-") if new_word[-1] == '-' else new_word.replace("--", "-")
 
        return self.verify_exceptions(new_word)


    
    def segment_cvcs(self, item):
        """
        main segmentation function to be implemented after parse_durationals has been implemented
        """
        if len(item) >= 5:
            return self.long_words(item)
        elif 3 <= len(item) <= 4:
            return self.special_mid_forms(item) #calling special_mid_forms function
        else:
            return self.post_coda(item) #directly sending words to post_coda function for parsing




class AdjectiveNumeralParser(VerbParser):
    def __init__(self):
        super().__init__()

    def isolating_suffixes(self,item):

        """
        parses suffixes of adjectives and numerals i.e. vowels and 'y'
        """
        
        consonants=self.consonant_count(item)
        if consonants >=2:
            new_word=""
            idxs=[index for index,letter in enumerate(item) if letter in self.consonants and letter != "ⁿ"] #usual cases
            for index, letter in enumerate(item):
                if index==idxs[-1] and item[index-1] != "-":
                    if  index+1 >len(item) :
                        new_word += f"-{letter}"
                    elif index+1 < len(item) and item[index+1]=="ⁿ":
                        new_word += f"-{letter}"
                    else: 
                        new_word += f"{letter}-"
                else: 
                    new_word += letter
        elif consonants <2 and len(item)>=3:
            new_word=""
            for letter in item:
                if letter in self.consonants and letter != "ⁿ" and item[-1] != letter:
                    new_word += f"{letter}-"
                else:
                    new_word+=letter
        else:
            new_word=item
            
    
        if new_word.endswith("-") and new_word.index("-")+1 < len(new_word) and new_word[new_word.index("-")-1]=="y": #the case of 'y'
            new_word=new_word[:new_word.index("-")-1] + "-" + new_word[new_word.index("-")-1:new_word.index("-")]
        elif new_word.endswith("-"):
            new_word=new_word[:-1]
        else:
            new_word=new_word
            
        return new_word
    
    def y_suffixes(self, item):
        """
        further parses y suffixes due to font instabilities
        """
        if item.endswith("y") and "-" not in item:
            return item[:item.index("y")] + "-" + item[item.index("y"):]
        else:
            return item
    
    
    def replace_hyphens_keep_last(self, item):

        """
        corrects overgeneralizations from isolating suffixes method and makes sure only suffixes are parsed
        """
        parts=item.rsplit("-",1)
        if len(parts)==2:
            first_part,last_part=parts
            if last_part[-1] in self.consonants and last_part[-1] != "y":
                return first_part.replace("-", "")+ "-" + last_part
            else:
                return first_part.replace("-", "")+ "-" + last_part
        else:
            return item
    
    def switch_hyphen_position(self, item):
        """
        corrects parses where hyphen occurs on the opposite side of expected position
        """
        if "-" in item:
            hyphen_index = item.index("-")
            if len(item) > hyphen_index + 1 and item[hyphen_index + 1] != "y" and item[hyphen_index + 1] in self.consonants:
                if len(item) > hyphen_index + 2 and item[hyphen_index+2] in self.vowels:
                    word = item[:hyphen_index] + item[hyphen_index + 1] + "-" + item[-1:]
                    return word
        return item  
    
    def miscellaneous(self, input_string):
        """
        fourre tout method to handle adhoc cases of wrong parse as a result of font instability
        """
        x = [i for i in range(len(input_string)) if i > 0 and i < len(input_string) - 3]     #handles cases such as in "núm-ɔ̀ẁ"
        if "-" in input_string and input_string.index("-") in x and input_string[-1] != "y":
            return input_string[:input_string.index("-")] + input_string[input_string.index("-") + 1:]
    
        y = [index for index, letter in enumerate(input_string) if letter == "ⁿ"]       #handles cases such as in "dííⁿ díí-wⁿ"
        if "ⁿ" in input_string[:-2] and  "-" in input_string[:y[-1]] and input_string[y[-1]-1] in self.consonants and input_string[y[-1]-1] != "y":
            return input_string[:input_string.index("-")] + input_string[input_string.index("-") + 1:]
        else:
            return input_string