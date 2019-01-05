from functools import lru_cache
from fuzzy import Soundex
from collections import defaultdict
import time
import sys
import pickle
import editdistance

from utils import levenshtein, lcs, singleton, ngrams_match, generate_ngrams
from constants import TOP_RESULT_COUNT, MATCH_ALGO, N__GRAM, MIN_CHARS

@singleton
class WordMatching:
    def __init__(self, corpus_name):
        self.file_name = corpus_name
        self.soundex = Soundex(N__GRAM)  # for phonetic similarity
        self.algo_ref = {
            'levenshtein': levenshtein,
            'c_levenshtein': editdistance.eval,
            'lcs': lcs,
            'ngrams': ngrams_match
        }
        self.load_corpus()

    def load_corpus(self):
        start_time = time.time()
        try:
            # loading index from pickled file if available.
            with open(f'{self.file_name.split(".")[0]}_index.pickle', 'rb') as handle:
                (gram_size, self.corpus_map, self.soundex_map,
                 self.ngrams_map) = pickle.load(handle)
        except:
            # map to store words based on their soundex value
            self.soundex_map = defaultdict(set)
            self.ngrams_map = defaultdict(set)       # map to store 3-grams:word pairs
            self.corpus_map = {}                     # map to store word: freq pairs
            with open(self.file_name) as f:
                for line in f:
                    word, freq = line.strip(" \n").split("\t")
                    self.corpus_map[word] = int(freq)
                    self.soundex_map[self.soundex(word)[:N__GRAM]].add(word)
                    ngrams = generate_ngrams(word)
                    for gram in ngrams:
                        self.ngrams_map[gram].add(word)
            # writing the index to a pickle file
            with open(f'{self.file_name.split(".")[0]}_index.pickle', 'wb') as handle:
                pickle.dump(
                    (N__GRAM, self.corpus_map, self.soundex_map, self.ngrams_map),
                    handle,
                    protocol=pickle.HIGHEST_PROTOCOL)


    @lru_cache(maxsize=64)
    def top_matches(
            self, match_string, count=TOP_RESULT_COUNT):
        result_map = {}
        # match_string = match_string[:8]       # can be used to optimize long string assuming
                                                # long strings will have errors only till
                                                # first k(8) characters
        soundex_match = self.soundex_map[self.soundex(match_string)]
        match_string = f"  {match_string}  "
        if len(match_string) < MIN_CHARS:
            word_ngram = [gram for gram in self.ngrams_map if match_string in gram]
        else:
            word_ngram = [match_string[x:x + N__GRAM]
                          for x in range(len(match_string) - (N__GRAM-1))]
        final_word_list = set(
            [word for ngram in word_ngram for word in self.ngrams_map[ngram]]
        ).union(soundex_match)
        for word in final_word_list:
            result_map[word] = (
                self.corpus_map[word], self.algo_ref[MATCH_ALGO](match_string, word))
        # sorting by match score, word length and term frequency .
        return (
            sorted(result_map.items(), key=lambda x: (
                x[1][1], len(x[0]), -x[1][0]))[:count]                                      # assuming word length has more weight than freq count
        )


if __name__ == "__main__":
    wm = WordMatching("word_search.tsv")

