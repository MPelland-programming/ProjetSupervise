import re

class TextExtraction:
    """
    stores methods to preprocess text.
    Input: a file with text (.flo.cex)
    Output: a list containing each list. The nested lists each contain one utterance.
    """
    def __init__(self,method_list=[]):
        self.dict_methods = { "m01": self.m01
                             ,"m02": self.m02
                             ,"m03": self.m03
                             ,"m04": self.m04
                             }
        if not (type(method_list) is list):
            raise TypeError("method_list must be a list")

        if not bool(method_list):
            print("Text processing method set to default: m01")
            self.method_list = ["m01"]
        else:
            self.method_list = method_list


    def m01(self, line:str, prevtier:str, code_list:list):
        """
        method 1: extract the %flo line from .cha. but append the code of the main tier.
        """
        tier, text = line.split(':',maxsplit = 1)

        if tier.startswith("*"):
            if tier[1:] in code_list:
                return [tier, ""]
            else :
                return ["",""]
        elif tier.startswith("%flo") and prevtier[1:] in code_list:
            return ["", f"{prevtier}:{text.strip()}"]

        return ["",""]

    def m01b(self,line:str, prevtier:str, code_list:list):
        pass

    def m02(self, line:str, prevtier:str, code_list:list):
        """
        method 2: removes ELAN code at the end of lies.
        """
        match = re.search(r'[.!?](?!.*[.!?])', line)
        if match:
           return text[:match.end()].strip()
        else:
           return line.strip()

    def m03(self, line:str, prevtier:str, code_list:list):
        """
        method 3: keeps dots found in parentheses
        """
        return re.sub(r'\(([.\s]+)\)', r'\1', line)

    def m04(self, line:str, prevtier:str, code_list:list):
        """
        method 4: keep text in parentheses if they only include a mix of letters, whitespaces or punctuation.
        """
        return re.sub(r'\(([A-Za-z\s,!?;:\–—-]+)\)', r'(\1)', line)

    def get_clean_text(self, task:str, filepath:str, code_list:list, method_list = self.method_list, print_warnings = True):
        """
        processes text based on specified method and either output the cleaned text or the number of lines in the text.
        :param filepath:
        :param code_list: list of speaker codes to extract. must be in caps, like in the files.
        :param method:
                    m1 - extract the %flo line from .cha. but append the code of the main tier.
        :param task: "clean" or "count" whether to extract cleaned text or to count the number of lines of cleaned text.
        :return:
        """
        if print_warnings:
            if method_list != sorted(method_list):
                print("methods are not listed in ascending order, this may cause issue or inefficiency. Analyses are still carried out, but consider changing the order of the methods.")

        if task not in ["clean", "count"]:
            raise ValueError(f"Invalid task {mode!r}: expected 'clean' or 'count'")

        prevtier = ""
        cleaned_text = []
        numline = 0

        with open(filepath, 'r') as f:
            for line in f:
                #Loops through preprocessing steps
                for metho in method_list:
                    prevtier,line = self.dict_methods[metho](line,prevtier,code_list)
                    print(prevtier)
                    print(line)
                    if not line:
                        break

                if line:
                    if task == "count":
                        numline += 1
                    else:
                        cleaned_text.append(line)
        if task == "count":
            return numline
        else:
            return cleaned_text




