#!/usr/bin/env python3
import argparse
import pprint
import random

__author__ = 'aderi'

import urllib.request
import json
import unicodedata
import re
import sys
import html

import operator

from alphabet_detector import alphabet_detector

ad = alphabet_detector.AlphabetDetector()

extra_wiki_to_lang = {'bat-smg': 'Samogitian',
                      'be-x-old': 'Old Belarusian',
                      'cbk-zam': 'Zamboanga Chavacano',
                      'eml': 'Emilian-Romagnol',
                      'fiu-vro': 'Võro',
                      'map-bms': 'Banyumasan Basa', 'mo': 'Moldovan', 'nah': 'Nahuatl',
                      'nds-nl': 'Dutch Low Saxon',
                      'roa-rup': 'Aromanian',
                      'roa-tara': 'Tarantino',
                      'simple': 'Simple English',
                      'zh-classical': 'Classical Chinese',
                     'zh-min-nan': 'Min Nan',
                     'zh-yue':'Cantonese'
}
import os.path
scriptdir = os.path.dirname(os.path.abspath(__file__))
langfile = os.path.join(scriptdir, 'wiki-languages.txt')

import iso_codes.parse_language_codes


def print_dict_sorted_by_value(x):
    sorted_x = sorted(x.items(), key=operator.itemgetter(1), reverse=True)
    pprint.pprint(sorted_x)


def strip_accents(s):
    return ''.join(c for c in unicodedata.normalize('NFD', s)
                   if unicodedata.category(c) != 'Mn')


def remove_parentheses(name):
    regex = re.compile('\(.*\)')
    name = regex.sub('', name)

    return name.rstrip()


def remove_after_comma(name):
    regex = re.compile(', .*')
    name = regex.sub('', name)

    return name.rstrip()


def remove_non_alphanumeric_english(eng_name):
    regex = re.compile('[-]')
    eng_name = regex.sub(' ', eng_name)
    eng_name = strip_accents(eng_name)
    # First parameter is the replacement, second parameter is your input string
    regex = re.compile('[^a-zA-Z ]')
    eng_name = regex.sub('', eng_name)
    return eng_name


def load_json_data(url):
    response = urllib.request.urlopen(url)
    str_response = response.readall().decode('utf-8')
    data = json.loads(str_response)
    return data


def get_wiki_to_lang_dict():
    wiki_to_lang = dict()

    with open(langfile, 'rb') as in_file:
        for line in in_file:
            line = line.decode('utf8')
            # list_of_wikis.append(line.strip().split()[3])
            line = line.strip().split()
            for i, elem in enumerate(line):
                elem = elem.replace(',', '')

                if elem.isdigit() and i != 0:
                    wikicode = line[i - 1]

                    lang_name = ' '.join(line[1:i - 1])

                    wiki_to_lang[wikicode] = lang_name

                    break

    return wiki_to_lang


def get_url_of_page_id(wikicode, page_id):
    url = 'http://{0}.wikipedia.org/w/api.php?action=query&prop=info&pageids={1}&inprop=url&format=json'.format(
        wikicode, page_id)

    data = load_json_data(url)

    # print(data)
    try:
        return data['query']['pages'][str(page_id)]['fullurl']
    except KeyError:
        return ''


def get_alphabet_of_text(text):
    alphabet = ad.detect_alphabet(text)

    if len(alphabet) == 1 and "LATIN" in alphabet:
        alphabet = "LATIN"
    elif "LATIN" in alphabet:
        alphabet = "PART_LATIN"
    else:
        alphabet = "NOT_LATIN"
    return alphabet


def get_usa_text(wikicode, num_chars, url_title):
    url = 'https://{0}.wikipedia.org/w/api.php?action=query&prop=extracts&exchars={1}&format=json&grnnamespace=0&titles={2}'.format(
        wikicode, num_chars, url_title)

    text = ''
    specific_url = ''
    # print(url)


    data = load_json_data(url)

    # print(data)
    for page_id, info_dict in data['query']['pages'].items():
        # print(page_id)
        text = info_dict['extract']
        text = re.sub(r'<[^>]*>', '', text)
        text = text.replace('\n', ' ')
        text = text.replace('\t', ' ')

        text = text.strip().strip('...')
        text = text.strip('…')
        text = text.strip()

        try:
            specific_url = get_url_of_page_id(wikicode, page_id)
        except urllib.error.URLError:
            specific_url = ''

        if text != '' and specific_url != '' and len(text) >= .25 * num_chars:
            alphabet = get_alphabet_of_text(text)

            return specific_url, text, alphabet

    if text == '' and specific_url == '':
        return 'N/A', 'N/A', 'N/A'

    alphabet = get_alphabet_of_text(text)

    return specific_url, text, alphabet


def get_random_text(wikicode, num_chars):
    url = \
        'https://{0}.wikipedia.org/w/api.php?action=query&generator=random&prop=extracts&' \
        'format=json&grnnamespace=0'.format(wikicode,)

    text = ''
    specific_url = ''

    for i in range(0, 100):
        data = load_json_data(url)
        for page_id, info_dict in data['query']['pages'].items():
            # print(page_id)
            text = html.unescape(info_dict['extract'])
            text = re.sub(r'<[^>]*>', '', text)
            text = text.replace('\n', ' ')
            text = text.replace('\t', ' ')

            text = text.strip().strip('...')
            text = text.strip('…')
            text = text.strip()
            text = text[:num_chars]

            try:
                specific_url = get_url_of_page_id(wikicode, page_id)
            except urllib.error.URLError:
                specific_url = ''

            if text != '' and specific_url != '' and len(text) >= .25 * num_chars:
                alphabet = get_alphabet_of_text(text)

                return specific_url, text, alphabet
#            else:
#                print("Retrying")

    if text == '' and specific_url == '':
        return 'N/A', 'N/A', 'N/A'

    alphabet = get_alphabet_of_text(text)
    return specific_url, text, alphabet


def get_lang_name(iso_code, wikicode):
    if iso_code in isocode_to_lang:
        lang_name = isocode_to_lang[iso_code]
        # print(iso_code, lang_name)
    elif wikicode in extra_wiki_to_lang:
        lang_name = extra_wiki_to_lang[wikicode]
    else:
        lang_name = "unknown (%s or %s)" % (iso_code, wikicode)
    return lang_name


def get_usa_page(num_chars):
    url = (
        "https://en.wikipedia.org/w/api.php?action=query&prop=langlinks&"
        "format=json&llprop=langname&llprop=url%7Cautonym&lllimit=10000&titles=" + 'United_States')
    """https://en.wikipedia.org/w/api.php?action=query&prop=langlinks&format=json&llprop=langname&llprop=url%7Cautonym&lllimit=10000&titles=United_States"""
    data = load_json_data(url)

    pages_dict = data['query']['pages']
    langlinks_list = list()
    for key in pages_dict:

        if 'langlinks' in pages_dict[key]:
            langlinks_list = pages_dict[key]['langlinks']
            break

    with open('usa-extracts.10000', 'w') as outfile:
        for langlink_dict in langlinks_list:
            wikicode = langlink_dict['lang']
            lang_translit = langlink_dict['*']
            lang_translit = '_'.join(lang_translit.split())
            # lang_translit = remove_parentheses(lang_translit)
            # lang_translit = remove_after_comma(lang_translit)
            # lang_translit = lang_translit.lower()
            # print(lang_translit)
            # lang_name = langlink_dict['langname']
            url = langlink_dict['url']
            url_title = url.split('/').pop()
            # print(wikicode, url)
            specific_url, text, alphabet = get_usa_text(wikicode, num_chars, url_title)
            iso_code = iso_codes.parse_language_codes.find_isocode_for_wikicode(wikicode)

            lang_name = get_lang_name(iso_code, wikicode)


            write_string = '{0}\t{1}\t{2}\t{3}\t{4}\n'.format(iso_code, alphabet,
                                                              lang_name,
                                                              specific_url, text)

            outfile.write(write_string)


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('--chars', action='store', type=int, help='max number of chars to extract; defaults to 500')
    parser.add_argument('--code', action='store', type=str, help='isocode if you only want a specific language')

    parser.add_argument('--extracts', action='store', type=int, help='number of extracts you want')
    parser.add_argument('--random', action='store_true')

    parser.add_argument('--usa_page', action='store_true')
    args = parser.parse_args()

    num_chars = args.chars
    isocode = args.code
    num_extracts = args.extracts
    usa_page = args.usa_page
    get_random_code_and_page = args.random

    wikicode_to_lang = get_wiki_to_lang_dict()
    isocode_to_lang = iso_codes.parse_language_codes.get_code_to_lang()

    # with open('wikicode-to-lang.table', 'wb') as outfile:
    #     for wikicode, lang in wikicode_to_lang.items():
    #         outfile.write('{0}\t{1}\n'.format(wikicode, lang).encode('utf8'))

    if num_chars is None:
        num_chars = 500

    if num_extracts is None:
        num_extracts = 1

    if usa_page:
        get_usa_page(num_chars)

    else:
        """get random code and page --> JON SEE HERE"""
        if get_random_code_and_page or isocode is not None:
            for i in range(num_extracts):
                if get_random_code_and_page:
                    wikicode = random.sample(wikicode_to_lang.keys(), 1)[0]
                else:
                    wikicode = iso_codes.parse_language_codes.find_wikicode_for_isocode(isocode)
                specific_url, text, alphabet = get_random_text(wikicode, num_chars)
                iso_code = iso_codes.parse_language_codes.find_isocode_for_wikicode(wikicode)
                lang_name = get_lang_name(iso_code, wikicode)
                sys.stdout.buffer.write((wikicode + '\t' + lang_name + '\t' + specific_url + '\t' + text + '\t'+ iso_code + '\n').encode('utf8'))
        else:
            with open('all-extracts.100.tail', 'w') as out_file:
                wikicode_to_url_set = dict()
                for wikicode in sorted(wikicode_to_lang.keys()):
                    if wikicode <= 'hy':
                        continue

                    print(wikicode)

                    if wikicode == 'hz':
                        iso_code = 'her'
                        alphabet = 'N/A'
                        specific_url = 'https://hz.wikipedia.org/wiki/Main_Page'
                        text = ''
                        write_string = '{0}\t{1}\t{2}\t{3}\t{4}\n'.format(iso_code, alphabet,
                                                                          get_lang_name(iso_code, wikicode),
                                                                          specific_url, text)
                        out_file.write(write_string)
                        continue

                    if wikicode == 'kr':
                        iso_code = 'kau'
                        alphabet = 'N/A'
                        specific_url = 'https://kr.wikipedia.org/wiki/Main_Page'
                        text = ''
                        write_string = '{0}\t{1}\t{2}\t{3}\t{4}\n'.format(iso_code, alphabet,
                                                                          get_lang_name(iso_code, wikicode),
                                                                          specific_url, text)
                        out_file.write(write_string)
                        continue

                    if wikicode == 'ii':
                        iso_code = 'iii'
                        alphabet = 'N/A'
                        specific_url = 'https://ii.wikipedia.org/wiki/%EA%80%A8%EA%8F%BE%EA%8C%A0'
                        text = ''
                        write_string = '{0}\t{1}\t{2}\t{3}\t{4}\n'.format(iso_code, alphabet,
                                                                          get_lang_name(iso_code, wikicode),
                                                                          specific_url, text)
                        out_file.write(write_string)
                        continue

                    for i in range(num_extracts):
                        iso_code = iso_codes.parse_language_codes.find_isocode_for_wikicode(wikicode)

                        specific_url, text, alphabet = get_random_text(wikicode, num_chars)

                        if wikicode not in wikicode_to_url_set or specific_url not in wikicode_to_url_set[wikicode]:
                            write_string = '{0}\t{1}\t{2}\t{3}\t{4}\n'.format(iso_code, alphabet,
                                                                              wikicode_to_lang[wikicode], specific_url,
                                                                              text)

                            out_file.write(write_string)

                            if wikicode in wikicode_to_url_set:
                                wikicode_to_url_set[wikicode].add(specific_url)
                            else:
                                wikicode_to_url_set[wikicode] = {specific_url}



