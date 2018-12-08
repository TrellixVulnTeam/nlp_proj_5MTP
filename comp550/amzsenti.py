# coding=utf-8
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import os
import tarfile
from tensor2tensor.data_generators import generator_utils
from tensor2tensor.data_generators import problem
from tensor2tensor.data_generators import text_problems
from tensor2tensor.utils import registry
from tensor2tensor.utils import restore_hook
import tensorflow as tf

flags = tf.flags
FLAGS = flags.FLAGS


@registry.register_problem
class Amzcls(text_problems.Text2ClassProblem):
    """IMDB sentiment classification."""
    URL = "http://ai.stanford.edu/~amaas/data/sentiment/aclImdb_v1.tar.gz"
    @property
    def is_generate_per_split(self):
        return True

    @property
    def dataset_splits(self):
        return [{
            "split": problem.DatasetSplit.TRAIN,
            "shards": 10,
        }, {
            "split": problem.DatasetSplit.EVAL,
            "shards": 1,
        }]

    @property
    def approx_vocab_size(self):
        return 2**15  # 8k vocab suffices for this small dataset.

    @property
    def num_classes(self):
        return 2

    def class_labels(self, data_dir):
        del data_dir
        return ["neg", "pos"]

    def doc_generator(self, imdb_dir, dataset, include_label=False):
        dirs = [(os.path.join(imdb_dir, dataset, "pos"), True), (os.path.join(
            imdb_dir, dataset, "neg"), False)]

        for d, label in dirs:
            for filename in os.listdir(d):
                with tf.gfile.Open(os.path.join(d, filename)) as imdb_f:
                    doc = imdb_f.read().strip()
                    if include_label:
                        yield doc, label
                    else:
                        yield doc

    def generate_samples(self, data_dir, tmp_dir, dataset_split):
        """Generate examples."""
        # Download and extract
        compressed_filename = os.path.basename(self.URL)
        download_path = generator_utils.maybe_download(tmp_dir, compressed_filename,
                                                       self.URL)
        imdb_dir = os.path.join(tmp_dir, "aclImdb")
        if not tf.gfile.Exists(imdb_dir):
            with tarfile.open(download_path, "r:gz") as tar:
                tar.extractall(tmp_dir)

        # Generate examples
        train = dataset_split == problem.DatasetSplit.TRAIN
        dataset = "train" if train else "test"
        for doc, label in self.doc_generator(imdb_dir, dataset, include_label=True):
            yield {
                "inputs": doc,
                "label": int(label),
            }



