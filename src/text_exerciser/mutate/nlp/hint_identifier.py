# -*- coding: utf-8 -*-
import os
import logging
import json
import pickle
from src.text_exerciser.mutate.nlp import data_helper
import numpy as np
import tensorflow as tf
from src.text_exerciser.mutate.nlp.text_cnn_rnn import TextCNNRNN

# warnings.filterwarnings('ignore')
logging.getLogger().setLevel(logging.ERROR)


class HintIdentifier:
    def __init__(self, ModelPath):
        self.ModelPath = ModelPath
        # Load model has time cost
        self.params, self.words_index, self.labels, self.embedding_mat = load_trained_params(ModelPath)

    def predict_hints(self, str_list):
        x_ = []
        for d in str_list:
            x_.append(data_helper.clean_str(d).split(" "))
        x_ = data_helper.pad_sentences(x_, forced_sequence_length=self.params['sequence_length'])
        x_ = map_word_to_index(x_, self.words_index)
        x_test = np.asarray(x_)

        with tf.Graph().as_default():
            session_conf = tf.ConfigProto(allow_soft_placement=True, log_device_placement=False)
            sess = tf.Session(config=session_conf)
            with sess.as_default():
                cnn_rnn = TextCNNRNN(
                    embedding_mat=self.embedding_mat,
                    non_static=self.params['non_static'],
                    hidden_unit=self.params['hidden_unit'],
                    sequence_length=len(x_test[0]),
                    max_pool_size=self.params['max_pool_size'],
                    filter_sizes=map(int, self.params['filter_sizes'].split(",")),
                    num_filters=self.params['num_filters'],
                    num_classes=len(self.labels),
                    embedding_size=self.params['embedding_dim'],
                    l2_reg_lambda=self.params['l2_reg_lambda'])

                def real_len(batches):
                    return [np.ceil(np.argmin(batch + [0]) * 1.0 / self.params['max_pool_size']) for batch in batches]

                def predict_step(x_batch):
                    feed_dict = {
                        cnn_rnn.input_x: x_batch,
                        cnn_rnn.dropout_keep_prob: 1.0,
                        cnn_rnn.batch_size: len(x_batch),
                        cnn_rnn.pad: np.zeros([len(x_batch), 1, self.params['embedding_dim'], 1]),
                        cnn_rnn.real_len: real_len(x_batch),
                    }
                    predictions = sess.run([cnn_rnn.predictions], feed_dict)
                    return predictions

                checkpoint_file = os.path.join(self.ModelPath, 'best_model.ckpt')
                saver = tf.train.Saver(tf.all_variables())
                saver = tf.train.import_meta_graph("{}.meta".format(checkpoint_file))
                saver.restore(sess, checkpoint_file)
                batches = data_helper.batch_iter(list(x_test), self.params['batch_size'], 1, shuffle=False)
                predictions, predict_labels = [], []
                for x_batch in batches:
                    batch_predictions = predict_step(x_batch)[0]
                    for batch_prediction in batch_predictions:
                        predictions.append(batch_prediction)
                        predict_labels.append(self.labels[batch_prediction])
                return predict_labels


def load_trained_params(trained_dir):
    params = json.loads(open(os.path.join(trained_dir, 'trained_parameters.json')).read())
    words_index = json.loads(open(os.path.join(trained_dir, 'words_index.json')).read())
    labels = json.loads(open(os.path.join(trained_dir, 'labels.json')).read())

    with open(os.path.join(trained_dir, 'embeddings.pickle'), 'rb') as input_file:
        fetched_embedding = pickle.load(input_file)
        embedding_mat = np.array(fetched_embedding, dtype=np.float32)
    return params, words_index, labels, embedding_mat


def map_word_to_index(examples, words_index):
    x_ = []
    for example in examples:
        temp = []
        for word in example:
            if word in words_index:
                temp.append(words_index[word])
            else:
                temp.append(0)
        x_.append(temp)
    return x_
