import os

os.environ['CUDA_VISIBLE_DEVICES'] = '-1'
import tensorflow as tf
import tensorflow_hub as hub
import numpy as np
from spacy.lang.en import English  # updated
import pickle

try:
    tf.config.set_visible_devices([], 'GPU')  # disable GPU, required when served in docker
except:
    pass

def encode_text_for_bert(
    texts,
    tokenizer_for_bert,
    max_len
):
    ''' This function is to encode data for inputting into BERT model
    Parameters:
    texts - List of texts to encode
    tokenizer_for_bert - Tokenizer to be used to convert text into tokens
    max_len - Maximum length of text. It can have maximum value as 512
    Return: Tupple of 3 numpy arrays
    1) Token Ids padded with 0s to make length as max_len.
    2) Array where we have 1 for actual tokens and 0 for padding tokens
    3) Array of 0s to indicate that token belongs to 1st sentence (chunk of text). There is no 2nd sentence here.
    '''
    all_token_ids = []
    all_masks = []
    all_segments = []

    for text in texts:
        tokens = tokenizer_for_bert.tokenize(text)  # Tokenizing using Bert tokenizer
        tokens = tokens[
                 :max_len - 2]  # Truncating number of tokens to max_len -2, Reduced extra 2 to add special tokens
        input_sequence = ["[CLS]"] + tokens + [
            "[SEP]"]  # [CLS] and [SEP] are special tokens to be added into input text
        pad_len = max_len - len(input_sequence)  # Spaces to fill with 0s to make each sequence equal to max_len
        token_ids = tokenizer_for_bert.convert_tokens_to_ids(input_sequence)  # Converting tokens to token ids
        token_ids += [0] * pad_len  # Padding token ids with 0s
        pad_masks = [1] * len(input_sequence) + [0] * pad_len  # 1 where we have sentence tokens and 0 otherwise
        segment_ids = [
                          0] * max_len  # Segment ids are all 0 to indicate it is part of sentence 1. There is no sentence 2 here
        all_token_ids.append(token_ids)
        all_masks.append(pad_masks)
        all_segments.append(segment_ids)

    return [tf.convert_to_tensor(all_token_ids, tf.int32, name="input_word_ids"),
            tf.convert_to_tensor(all_masks, tf.int32, name="input_mask"),
            tf.convert_to_tensor(all_segments, tf.int32, name="segment_ids")]

def split_sentences(
    text
):
    nlp = English()
    #         nlp.add_pipe(nlp.create_pipe('sentencizer'))  # updated
    nlp.add_pipe('sentencizer')
    doc = nlp(text)
    sentences = [sent.text for sent in doc.sents]
    return sentences

class SPTBertModel(object):

    def __init__(self):
        """
        Load Model Parameters
        """
        self.loaded = False
        self._max_len = 300

    def load(self):
        """
        Load Tensorflow Model
        """
        self._model = tf.keras.models.load_model("model_final_aug3.h5",
                                                 custom_objects={'KerasLayer': hub.KerasLayer}
                                                 )
        with open('tokenizer.pkl', 'rb') as fp:
            self._tokenizer = pickle.load(fp)

        self.loaded = True

    def predict(self, X, feature_names=None, meta=None):
        """
        Return a Prediction
        """
        if not self.loaded:
            self.load()
        sentences = split_sentences(X)
        input = encode_text_for_bert(sentences, self._tokenizer, self._max_len)
        return np.round(self._model(input)).T
