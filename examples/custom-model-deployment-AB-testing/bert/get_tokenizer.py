from bert import bert_tokenization
import tensorflow_hub as hub
import pickle

def get_bert_tokenizer(do_lower_case = True, trainable=True):
    bert_layer = hub.KerasLayer("https://tfhub.dev/tensorflow/bert_en_uncased_L-12_H-768_A-12/1",
                                trainable=trainable,
                                name='keras_bert_layer'
                                )
    vocab_file = bert_layer.resolved_object.vocab_file.asset_path.numpy()
    tokenizer_for_bert = bert_tokenization.FullTokenizer(vocab_file, do_lower_case) #Tokenizer to tokenize input text
    print ( '\nLength of vocab in our tokenizer : ' , len(tokenizer_for_bert.vocab))

    with open('tokenizer.pkl', 'wb') as fp:
        pickle.dump(tokenizer_for_bert, fp)

if __name__ == '__main__':
    get_bert_tokenizer()