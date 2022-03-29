import re
import spacy
from spacy.lang.en import English
from collections import defaultdict
import numpy as np
from flask import request
import logging
import sys
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

nlp = spacy.load('en_core_web_sm')

dic = ['carbon monoxide', 'suicide vest', 'gas stove', 'gas oven']
dic1 = ['noose', 'exhaust', 'seppuku']

dic2 = ['railway', 'bridge', 'cord', 'ligature',
        'opioid', 'arsenic', 'amphetamine', 'methadone', 'benzodiazepine', 'methamphetamine', 'mdma',
        'pregabalin', 'poison', 'smoke', 'helium',
        'oxycontin', 'gabapentin', 'buprenorphine']

def split_sentences(text):
    nlp = English()
    # nlp.add_pipe(nlp.create_pipe('sentencizer'))  # updated
    nlp.add_pipe('sentencizer')
    doc = nlp(text)
    sentences = [sent.text for sent in doc.sents]
    return sentences

def def_value():
    return "Not Present"

def get_tag_dic(text):
    tag_dic = defaultdict(def_value)
    text_doc = nlp(text)
    for token in text_doc:
        tag_dic[str(token).lower()] = [token.tag_, token.dep_]

    return tag_dic

def has_sensitive_vocab(text, tag_dic):
    for word in dic:
        if (re.search(word, text, re.IGNORECASE)):
            return 1

    for word in dic1:
        if (re.search(word, text, re.IGNORECASE) and tag_dic[word][0] == 'NN'):
            return 1

    for word in dic2:
        if (refer_to_suicide(text) and re.search(word, text, re.IGNORECASE) and tag_dic[word][0] == 'NN'):
            return 1
    return 0

def hanging_suicide(text):
    if (re.search('\W(hang|hung)', text, re.IGNORECASE)):
        text = re.sub(r'(hang|hung)(ed|ing)? (up|out|onto|over)', '', text)
        text = re.sub(r'hang on', '', text)

        if ((not re.search('sentenced to', text, re.IGNORECASE)) and (
                re.search('suicide.*\Whanging', text, re.IGNORECASE) or
                re.search('\W(hung|(hang(ed|ing|s)?)) ((him|her|my)self|themselves)', text, re.IGNORECASE) or
                re.search('\Whanging death', text, re.IGNORECASE) or
                re.search('(death|died|body|him|her).{1,15}hang', text, re.IGNORECASE) or
                re.search('hang.{1,15}(death|died|dead)', text, re.IGNORECASE) or
                re.search('\W(found|discovered).* ((hang(ed|ing))|hung)', text, re.IGNORECASE)
                or (refer_to_suicide(text) and re.search('hung|hang', text, re.IGNORECASE)))
        ):
            return 1

    if (re.search(' strangle.{0,50} ((him|her|my)self|themselves)', text, re.IGNORECASE) or
            re.search(' self.{0,30}(strangulation|suffocation|asphyxiation|immolation)', text, re.IGNORECASE) or
            re.search(
                '(suicide|(took (her|his|their) life)|(killed (him|her)self)).{0,50} by (strangulation|suffocation|asphyxiation|immolation|drowning|throwing|jumping|drinking|ingesting|taking)',
                text, re.IGNORECASE)):
        return 1

    return 0

def gun_suicide(text):
    if (re.search('( pistol| gun| rifle | firearm| sword| knife| shotgun| bullet| handgun| revolver)', text,
                  re.IGNORECASE)):
        if (re.search('self-inflicted', text, re.IGNORECASE) or
                re.search('\W(his|him|her) (body|head|mouth|chest|hand|heart)', text, re.IGNORECASE) or
                re.search('\W(him|her)self', text, re.IGNORECASE) or
                refer_to_suicide_shot(text) or refer_to_suicide(text)):
            return 1
    return 0

def jumping_suicide(text):
    if (re.search('(jump(ing|s|ed)?|leap)', text, re.IGNORECASE)):
        if (re.search('(jump(ing|s|ed)?|leap(ing|s|ed|t)?).{0,20}(from|out|off).{0,50}window', text, re.IGNORECASE)
                and (re.search('escape', text))):
            return 0
        if (
                #             refer_to_suicide(text) or
                re.search('(jumped|leapt) to.{0,15} death', text, re.IGNORECASE) or
                re.search(
                    '(jump(ing|s|ed)?|leap(ing|s|ed|t)?).{0,20}(from|out|off|over).{0,50}( window| bridge| roof| balcony| building| apartment| (floor of)| hotel)',
                    text, re.IGNORECASE)
                or re.search(
            '(jump(ing|s|ed)?|leap(ing|s|ed|t)?) (into|in).{0,20}( gorges| water| river| pool| sea| gulf)', text,
            re.IGNORECASE)
                or re.search('(jump(ing|s|ed)?|leap(ing|s|ed|t)?) (in front of).{0,20}( car| bus| taxi)', text,
                             re.IGNORECASE)
        ):
            return 1

    if (re.search('(throw|threw)', text, re.IGNORECASE)):
        if (re.search('((him|her|my)self|themselves) (from|out|off)', text, re.IGNORECASE)
                and re.search('( window| bridge| roof| floor| building| apartment| cliff|  highrise)', text,
                              re.IGNORECASE)):
            return 1
    if (re.search(
            '(throw|threw).* (him|her|my)self (in|into|off).* (window|cliff|bridge|water|river|sea|pool|volcano|lava|path)',
            text, re.IGNORECASE)):
        return 1
    return 0

def refer_to_suicide(text):
    if (re.search('(comit|committed|attempted|(died by)|ruled a) suicide', text, re.IGNORECASE)
            or re.search('suicide (attempt|note)', text, re.IGNORECASE)
            or re.search('\Wkill(ed|s|ing)? ((him|her|my)self|themselves)', text, re.IGNORECASE)
            or re.search('\W(took|take) (his|her|my) (own )?life', text, re.IGNORECASE)
            or re.search('\Wend(ed|ing|s)? (his|her|my) (own )?life', text, re.IGNORECASE)
            or re.search('\Wfound dead', text, re.IGNORECASE)
            or re.search('apparent suicide', text, re.IGNORECASE)
            or (re.search('cause of death', text, re.IGNORECASE) and (re.search('suicide', text, re.IGNORECASE)))
    ):
        return 1


def refer_to_suicide_shot(text):
    if (re.search('(shot|shooting|shoot(s)?) (and killed )?((him|her|my)self|themselves)', text, re.IGNORECASE)
            or re.search('gunshot suicides', text, re.IGNORECASE)):
        return 1
    return  0

def drug_suicide(text):
    if (re.search('(drug(s)?|alcohol|tablet(s)?|pill(s)?)( |[.,;?!])', text, re.IGNORECASE)):
        if (re.search(
                '(suicide attempt |((attempted|committed) suicide)|(end (his|her) life)|(kill(ed)? (him|her)self).{0,15}(by|with).{0,15}(drugs|alcohol|pills|tablets))',
                text)
                or re.search(
                    'used.*(drugs|alcohol|pills|tablets).*(suicide|(kill(ed)? (him|her)self)|((end|take) (his|her) (own)? life))',
                    text)
                or re.search('^(?!no) (drugs|alcohol) in (him|her) (blood|veins|system|body)', text,
                             re.IGNORECASE)):
            return 1
    return 0

def train_suicide(text, suicide_related_article):
    if (re.search('\Wtrain\W', text, re.IGNORECASE)):
        tag_dic = get_tag_dic(text)
        if (tag_dic['train'][0] == 'NN'):
            if (re.search('(jump|walk|stepped|went|ran|stand).*(\Wfront of\W|\Wunder\W)', text, re.IGNORECASE)
                    or re.search('(threw|throw|put)(ing)? ((him|her|my)self|themselves).*(\Wfront\W|\Wunder\W)',
                                 text, re.IGNORECASE)
                    or re.search('(jump|threw|throw|walk|went|ran|step|laid|lying|run|stand).* on .*(track|rail)',
                                 text, re.IGNORECASE)
                    or (suicide_related_article and re.search('hit|struck', text, re.IGNORECASE))
                    or (suicide_related_article and re.search('\W(found|discovered).* (train|track|railway)', text,
                                                              re.IGNORECASE))):
                return 1
    return 0

def poison_suicide(text, suicide_related_article):
    if (re.search(' poison|pesticide|barbiturate(s)?|cyanide', text, re.IGNORECASE)):
        if (re.search('( consum| eat| took| tak| ate| ingest| swallow| overdose).* ', text, re.IGNORECASE)
                or (re.search('(poison(ed|ing|s)?|kill(ed|ing|s)?).*(him|her|my)self', text, re.IGNORECASE))
        ):
            return 1
    if (suicide_related_article and re.search('( by ingesting)|(ingestion of)', text, re.IGNORECASE)):
        return 1
    return 0

def fire_suicide(text):
    if ( re.search('\Wset(ting)? ((him|her|my)self|themselves) (on fire|ablaze)', text, re.IGNORECASE) or
        re.search('\Wsuicide.{0,20}by fire', text, re.IGNORECASE) or
        re.search('\Wburn(ing)? ((him|her|my)self|themselves)', text, re.IGNORECASE) or
        re.search('\W(asphyxiat|immolat|suffocat|starv|starve)(ed|ing)? ((him|her|my)self|themselves)', text,
                  re.IGNORECASE)):
        return 1
    return 0

def cut_suicide(text, suicide_related_article):
    if (re.search('\W(slit(ting|s)?|cut(s|ing)?) (his|her|their|my) .*(wrists|throat|veins)', text, re.IGNORECASE) or
        re.search('\W(slash(ed|ing|es)|(drown(ed|ing))) ((him|her|my)self|themselves)', text, re.IGNORECASE) or
        (refer_to_suicide(text) and re.search('\W(slit(ting|s)?\W|\Wcut(s|ing)?\W)', text, re.IGNORECASE)) ):
        return 1
    if (re.search('\W(stab|slash)', text, re.IGNORECASE)):
        if (re.search('\W(him|her|my)self', text, re.IGNORECASE) or
            (re.search(' (his|her|my|their) (wrist|throat)', text, re.IGNORECASE))):
            return 1
    if (suicide_related_article and re.search('\W(wrists|veins|throat)', text, re.IGNORECASE)):
        if (re.search('\W(knife|sword|cut|slit)', text, re.IGNORECASE)):
            return 1
    return 0

def overdose_suicide(text):
    if (re.search(' overdose', text, re.IGNORECASE)):

        if (refer_to_suicide(text) and re.search('overdose', text, re.IGNORECASE)):
            return 1
        if (re.search('(took|died|taken|take| intentional| delibrate| aparent).{0,20}overdose', text, re.IGNORECASE)
                or re.search('overdosed|(overdose of)', text, re.IGNORECASE)):
            return 1
        if (re.search('(attempted|committed|died by) suicide ', text, re.IGNORECASE)):
            return 1
    return 0

def other_suicide_method(text, suicide_related_article, tag_dic):
    if (re.search('committed suicide.{0,30} by (?!the)', text, re.IGNORECASE)):
        return 1
    if (re.search('\Wsuicide by (?!the)', text, re.IGNORECASE)):
        if (tag_dic['by'][1] != 'agent'):
            return 1
    if ((suicide_related_article and re.search('plastic bag.{1,30}head', text, re.IGNORECASE) )
        or (suicide_related_article and has_sensitive_vocab(text, tag_dic))):
        return 1

    if (re.search('\Wneck\W', text, re.IGNORECASE)):
        if ((refer_to_suicide(text) and re.search('\Waround (his|her) neck', text, re.IGNORECASE))
                or re.search('\W(rope |cord|cut|slit|slash|noose)', text, re.IGNORECASE)):
            return 1

    return 0

def detect_methods(text, suicide_related_article=True):

    tag_dic = get_tag_dic(text)

    if ( refer_to_suicide_shot(text)
        | jumping_suicide(text)| drug_suicide(text)| gun_suicide(text)
        | overdose_suicide(text) | fire_suicide(text) | cut_suicide(text, suicide_related_article) |
        train_suicide(text, suicide_related_article) | hanging_suicide(text) | poison_suicide(text, suicide_related_article)
        | other_suicide_method(text, suicide_related_article, tag_dic)):
            return 1
    return 0

class SPTRuleBasedModel(object):

    def predict(self, X, feature_names=None, meta=None):
        """
        Return a Prediction
        """
        sentences = split_sentences(X)
        logging.info('These are the request headers')
        logging.info(request.headers)
        return np.array([list(map(detect_methods, sentences))])
