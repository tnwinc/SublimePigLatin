import sublime_plugin
import sublime
import re


def translate_word(word):

    VOWELS = "AEIOUaeiou"
    start_punc, consonants, end_punc = '', '', ''

    # if no alphabet characters
    if not re.search('[A-Za-z]', word):
        return word

    # hyphenated words
    if re.search('[A-Za-z]\-[A-Za-z]', word):
        return '-'.join(map(translate_word, word.split('-')))

    # filter out leading and trailing punctuation marks
    while not word[0].isalpha():
        start_punc += word[0]
        word = word[1:]

    while not word[-1].isalpha():
        end_punc = word[-1] + end_punc
        word = word[:-1]

    suffix = 'way' if word[0] in VOWELS else 'ay'

    # flag for all caps
    all_caps = word.isupper() and len(word) > 1

    # handle first vowel being a y
    y_matched = False
    if word[0] not in VOWELS:
        y_match = re.search('(y)', word)
        if y_match:
            y_start = y_match.start(1)
            if y_start > 0 and y_start < 4:
                consonants = y_match.string[0:y_start]
                word = word[y_start:]
                y_matched = True

    # handle qu
    if word[:2].lower() == 'qu':
        consonants = 'qu'
        word = word[2:]

    # grab the consonants
    if not y_matched:
        while word[0] not in VOWELS:
            consonants += word[0]
            word = word[1:]

    # handle capitalization
    if all_caps:
        suffix = suffix.upper()
    else:
        if len(consonants) > 0 and not consonants[0].islower():
            consonants = consonants.lower()
            word = word.capitalize()

    return ''.join((start_punc, word, consonants, suffix, end_punc))


def translate_sentence(sentence):
    words = sentence.split(' ')
    translated_words = map(translate_word, words)
    return ' '.join(translated_words)


def select_between_quotes(view, sel):
    d_quotes = map(lambda x: x.begin(), view.find_all('"'))
    s_quotes = map(lambda x: x.begin(), view.find_all("'"))

    def contains_line_break(start, end):
        text = view.substr(sublime.Region(start, end))
        return re.search("\n", text)

    def search_for_quotes(q_type, quotes):
        q_size, before, after = False, False, False

        if len(quotes) - view.substr(sel).count('"') >= 2:
            all_before = filter(lambda x: x < sel.begin(), quotes)
            all_after = filter(lambda x: x >= sel.end(), quotes)

            if all_before:
                before = all_before[-1]
            if all_after:
                after = all_after[0] + 1

            if all_before and all_after and not contains_line_break(before, after):
                q_size = after - before - 1

        return q_size, before, after

    d_size, d_before, d_after = search_for_quotes('"', d_quotes)
    s_size, s_before, s_after = search_for_quotes("'", s_quotes)

    def get_new_region(start, end):
        if sel.size() < end - start - 2:
            start += 1
            end -= 1

        view.sel().subtract(sel)
        view.sel().add(sublime.Region(start, end))

        return sublime.Region(start, end)

    if d_size and (not s_size or d_size < s_size):
        return get_new_region(d_before, d_after)
    elif s_size and (not d_size or s_size < d_size):
        return get_new_region(s_before, s_after)
    else:
        return False


class PigLatinCommand(sublime_plugin.TextCommand):

    def run(self, edit):

        for region in reversed(self.view.sel()):
            # if the user didn't select anything, use text between quotes
            if region.empty():
                region = select_between_quotes(self.view, region)

            # if we failed to select between quotes, use the current word
            if not region:
                region = self.view.word(region)

            text = self.view.substr(region)

            self.view.replace(edit, region, translate_sentence(text))
