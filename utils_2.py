import re

vowels = {"ɛ̌", "ɔ̌", "ɛ̂", "ɔ̂", "ɛ́", "ɔ́", "ɛ̀", "ɔ̀", "ì", "í", "ǔ", "û",'ê', 'ě', 'è', 'é', 'ô', 'ò', 'ǒ', 'ó', 'ǎ', 
          'â', 'à', 'á', 'ɛ̌', 'ɛ̂', 'ɛ́', 'ɛ̀', 'û', 'ǔ', 'ú', 'ù', 'ǐ', 'î', 'í', 'ì', ' ̀ɔ ', 'ɔ́', 'ɔ̌', 'ɔ̂',
           "i", "e", "ɛ", "u", "o", "ɔ", "a"}
consonants={"b", "c", "d", "f", "g", "h", "j", "k", "l", "m", "n", "p", "r", "s", "t", "v", "w", "y", "z", "ʔ", "ɲ", "ŋ"}
exceptions = ["nd", "nt", "ŋg", "ɲj", "mb"]



def parse_durationals_1(item):
    
    def get_last_vowel(item):
        """Extracts the last vowel from the input string ending with ':'"""
        if item.endswith(":"):
            return item[-2]
        return None
 
    vowels = [get_last_vowel(item)]  # extracting vowels from dataset
    replacements = {
        "ɛ̌": "ɛ́", "ɔ̌": "ɔ́", "ɛ̂": "ɛ̀", "ɔ̂": "ɔ̀",
        "ɛ́": "ɛ́", "ɔ́": "ɔ́", "ɛ̀": "ɛ̀", "ɔ̀": "ɔ̀",
        "ì": "ì", "í": "í", "ǔ": "ú", "û": "ù"
    }  # cases where vowels are not extracted
    # Handle exceptions like 'tɔ́d-ɛ̀:' and 'nàrⁿ-ɛ́:'
    for letter in replacements:
        if item.endswith(letter + ':'):
            return item[:-1] + "-" + replacements[letter]
    # Handling the exceptional case 'jɛ᷈:'
    if 'ɛ᷈:' in item:
        return item[:-1] + "-ɛ᷈"
    # Handle cases of unextracted vowels
    for letter in replacements:
        if item.endswith(":"):
            if letter in item[1:4]:
                return item[:-1] + "-" + replacements[letter]
    # Handle cases with extracted vowels 
    material = {
        'ǎ': 'á', 'ê': 'è', 'ô': 'ò', 'ě': 'é',
        'ǐ': 'í', 'î': 'ì', 'ǒ': 'ó', 'â': 'à',
        'ɛ́': 'ɛ́', 'ɛ̀': 'ɛ̀', 'ǔ': 'ú', 'í': 'í',
        'ì': 'ì'
    }.get(vowels[0], vowels[0])
    return item[:-1] + "-" + material if vowels[0] else item



def reverify_exceptions(word):
    """This function reverifies that the final word does not parse consonants ensembles"""
    
    for i in exceptions:
        with_hyphen = i[0] + "-" + i[1]
        if with_hyphen in word:
            idx = word.index(with_hyphen)
            word = word[:idx] + i + "-" + word[idx + 3:]
    word = word.replace("--", "-")
    return word




def vowel_tone_hyphen(word):
    "This function handles cases in which it is difficult to extract vowels"
    if word[-1] not in vowels.union(consonants) and word[-2] == "-":
        return reverify_exceptions(word[:-3] + "-" + word[-3] + word[-1])
    elif word[-1] in vowels and word[-2] == "-":
        return reverify_exceptions(word)
    else: 
        return reverify_exceptions(word)




def remove_final_hyphen(word):
    """This function takes a word and returns it without a final hyphen/The function also eliminates any cases of double hyphen"""
    if word.endswith("-"):
        word = word[:-1]
        return vowel_tone_hyphen(
            word[:word.index("-")] + word[word.index("-")+1:]
            if "--" in word else word
        )
    else:
        return vowel_tone_hyphen(
            word[:word.index("-")] + word[word.index("-")+1:]
            if "--" in word else word
        )
    



def syllabic_vowels(word):
    "This function isolates syllabic vowels and parses them off"

    final_word = word

    for alphabet in vowels:
        if alphabet in word[2:-2]:
            try:
                index = word.index(alphabet)
                if word[index - 1] == "-" and word[index + 1] in consonants:
                    final_word = final_word.replace(word[index], f"{alphabet}-")
            except ValueError:
                pass

    return remove_final_hyphen(final_word)




def post_coda(word):
    """This function parses vowels sounds that occur after codas"""
    
    for i in range(1, len(word)-3):
        if word[i] in consonants:
            if i + 1 < len(word) and word[i + 1] == "-":
                try:
                    if i + 2 < len(word) and i + 3 < len(word) and word[i + 2] in vowels and word[i + 3] in consonants:
                        material = word[:i + 2] + "-" + word[i + 2:]
                        return syllabic_vowels(material)
                    else:
                        return syllabic_vowels(word)
                except IndexError:
                    return syllabic_vowels(word)
    return syllabic_vowels(word)





def segment_cvcs(item):

    def find_cvc(item, vowels):
        vowel_pattern = '[' + ''.join(vowels) + ''.join(vowels).lower() + ']'
        pattern = r'([bcdfghjʔklmnŋɲpqrstvwxyzBCDFGHJKLMŊƝPQRSTVWXYZ])' \
                  r'' + vowel_pattern + r'([bcdfghjʔklmnpqrstvwxyzBCDFGHJKLMNPQRSTVWXYZ])'

        matches = re.findall(pattern, item)
        return matches

    cvc = find_cvc(item, vowels)

    for char in exceptions:
        if char in item:
            result = item.replace(char, f"{char}-") 
            if cvc:
                for i in range(len(cvc)):
                    if item[item.index(cvc[i][0])+1] not in vowels:
                        result = result.replace(item[item.index(cvc[i][0])], f"{cvc[i][0]}-")
            return post_coda(result)

    if len(cvc) >= 2 and " " not in item:
        return post_coda(item)
    elif len(cvc) == 1 and len(item) >= 4:
        if cvc[0][-2] in vowels:
            material = item[:item.index(cvc[0][-2]) + 2] + "-" + item[item.index(cvc[0][-2]) + 2:]
            return post_coda(material)
        elif "-" not in item[-2:]:
            if item[2] in consonants:
                material=item[:3] + "-" + item[3:] 
                return post_coda(material)
            else:
                material=item[:4] + "-" + item[4:] 
                return post_coda(material)
        else:
            return post_coda(item[:-1] if item[-1]=="-" else item)
    elif len(item) >= 5:
        if "-" not in item[-4:]:
            for alphabet in item[-3:]:
                if alphabet not in vowels:
                    for element in item[1:-3]:
                        if element in consonants:
                            material =  item[:1]+ item[1:-3].replace(element, f"{element}-") +item[-3:]
                            return post_coda(material)
                elif item[-3] in consonants:
                    material = item.replace(item[-3], f"{item[-3]}-")
                    return post_coda(material)

                else:
                    return post_coda(item)
            return post_coda(item[:-2] + "-" + item[-2:])
        else:
            return post_coda(item[:item.index("-")] + item[item.index("-")+1:] if "-" not in item else item)
    elif 3 <= len(item) <= 4:
        if "-" not in item[-3:] and item[-2:] not in vowels:
            return post_coda(item[:-2] + "-" + item[-1:])
        else:
            return post_coda(item)
    else:
        return post_coda(item)