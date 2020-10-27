# -*- coding: utf-8 -*-
"""
Created on Tue Oct 20 20:20:20 2020
@author: Amal Htait and Leif Azzopardi
"""

import scipy
from sentence_transformers import SentenceTransformer
import operator
from aggregator import SumSentimentIntensityAggregator, AvgSentimentIntensityAggregator, MaxSentimentIntensityAggregator
from similarity_measure import ScipySimilarity
from scorer import SentimentIntensityScorer


DEFAULT_SEED_SIZE =500
DEFAULT_AGGREGATOR ='avg'
DEFAULT_LEXICON = 'vader'
DEFAULT_LANGUAGE_MODEL = 'bert-base-nli-mean-tokens'
DEFAULT_SIMILARITY_METHOD = 'scipy'
DEFAULT_SIMILARITY_MEASURE = 'cosine'
DEFAULT_WEIGHTED = False


class SentimentIntensityScorerBuilder:

   def __init__(self, aggregation_method_name, language_model_name, similarity_method_name=DEFAULT_SIMILARITY_METHOD, similarity_measure_name=DEFAULT_SIMILARITY_MEASURE, seed_size=DEFAULT_SEED_SIZE, weighted=DEFAULT_WEIGHTED):
      self.aggregator_method_name = aggregation_method_name
      self.language_model_name = language_model_name
      self.similarity_method_name = similarity_method_name
      self.seed_size=seed_size
      self.weighted=weighted
      self.lexicon_name=None
      self.aggregator = self._create_aggregator(aggregation_method_name)
      self.similarity_method, self.similarity_measure = self._choose_similarity(similarity_method_name, similarity_measure_name)
      self.language_model  = self._create_language_model(language_model_name)
      #self.builder_name  ='{}-{}'.format(self.aggregator_method_name, self.language_model_name)


   def build_scorer_from_lexicon_file(self, lexicon_file, seed_size=DEFAULT_SEED_SIZE):
       scorer = None
       lexicon_list, lexicon_dict = self._load_lexicon_from_file(lexicon_file)
       pos_seeds_embeddings, neg_seeds_embeddings = self._make_seed_lists(lexicon_list, self.language_model, self.seed_size)
       builder_name  ='{}|{}|{}'.format(self.aggregator_method_name, self.language_model_name,self.lexicon_name)
       scorer = SentimentIntensityScorer(pos_seeds_embeddings, neg_seeds_embeddings, self.aggregator, self.language_model, self.similarity_method, self.similarity_measure, self.weighted, lexicon_list, lexicon_dict, builder_name)

       return scorer


   def build_scorer_from_prebuilt_lexicon(self, lexicon, seed_size=DEFAULT_SEED_SIZE):
      """
      :param lexicon: the name of a prebuilt lexicon (string)
      :param seed_size: the number of positive and negative seed terms to use given the lexicon
      :return: SentimentIntensityScorer
      """
      self.lexicon_name = lexicon

      lexicons = ['vader',
                  'labmt']

      if lexicon not in lexicons:
         lexicon = DEFAULT_LEXICON

      lexicon_file  =  'lexicon/{}.txt'.format(lexicon)
      #lexicon_file  =  'lexicon/{}.lex'.format(lexicon) => we'll need to change our lexicon files to .lex

      return self.build_scorer_from_lexicon_file(lexicon_file, seed_size)


   def _load_lexicon_from_file(self, lexicon_file):
      """
      :param lexicon_file: the name of the file containing seed terms and their sentiment intensity score (tab separated file)
      :return: the list of lexicon terms, and a dictionary of terms (key) and SI scores (value)
      """
      lexicon_dict = {}
      seeds = open(lexicon_file, 'r', encoding='utf-8-sig').readlines()
      for i in range(len(seeds)):
         line = seeds[i].split('\t')
         lexicon_dict[line[0].strip()] = line[1].strip()
         lexicon_dict = dict( sorted( lexicon_dict.items(), key=operator.itemgetter(1), reverse=True ) )

      return list(lexicon_dict.keys()), lexicon_dict


   def _create_aggregator(self, aggregation_method):
      """

      :param aggregation_method:
      :return:
      """

      aggregators={
         'sum': SumSentimentIntensityAggregator,
         'avg': AvgSentimentIntensityAggregator,
         'max': MaxSentimentIntensityAggregator
        }

      am = aggregation_method.lower()
      if am in aggregators:
         aggregator = aggregators[am]
      else:
         aggregator=aggregators[DEFAULT_AGGREGATOR]
         self.aggregator_method_name = DEFAULT_AGGREGATOR

      return aggregator


   def _create_language_model(self, language_model_name):
      """

      :param language_model_name: 
      :return: the embedder created using the language model, 
               that will be used to create the embedding representation of text.
      """

      models_name = [
         'bert-base-nli-mean-tokens', #fast
         'bert-large-nli-mean-tokens', 
         'bert-base-nli-stsb-mean-tokens', 
         'bert-large-nli-stsb-mean-tokens',
         #'roberta-base-nli-stsb-mean-tokens', #TypeError: __init__() got an unexpected keyword argument 'do_lower_case'
         'roberta-large-nli-stsb-mean-tokens',
         'distilbert-base-nli-stsb-mean-tokens',
         'xlm-r-100langs-bert-base-nli-stsb-mean-tokens',
         'xlm-r-100langs-bert-base-nli-mean-tokens'
      ]

      if language_model_name in models_name:
         language_model_embedder = SentenceTransformer(language_model_name)
      else:
         language_model_embedder = SentenceTransformer(DEFAULT_LANGUAGE_MODEL)
         self.language_model_name = DEFAULT_LANGUAGE_MODEL


      return language_model_embedder


   def _make_seed_lists(self, lexicon_list, language_model_embedder, seed_size):
      """

      :param lexicon_list:
      :param language_model_embedder:
      :param seed_size:
      :return:
      """

      max_seed_size = len(lexicon_list)/2
      if seed_size > max_seed_size:
         seed_size=max_seed_size

      pos_seeds=lexicon_list[:int(seed_size)]
      neg_seeds=lexicon_list[-int(seed_size):]

      pos_seeds_embeddings=language_model_embedder.encode(pos_seeds)
      neg_seeds_embeddings=language_model_embedder.encode(neg_seeds)

      return pos_seeds_embeddings, neg_seeds_embeddings


   def _choose_similarity(self, similarity_method, similarity_measure):
      """

      :param similarity_method: We're using scipy model
      :param similarity_measure: scipy offers several measures ex: cosine, jaccard, etc
      :return:
      """



      similarity_methodes={
         'scipy': ScipySimilarity
         }
      sim_method = similarity_method.lower()
      if sim_method in similarity_methodes:
         similarity_method = similarity_methodes[sim_method]
      else:
         similarity_method = similarity_methodes[DEFAULT_SIMILARITY_METHOD]
         self.similarity_method_name = DEFAULT_SIMILARITY_METHOD


      sim_measure = similarity_measure.lower()
      similarity_measures=[
         'braycurtis', 
         'canberra', 
         'chebyshev', 
         'cityblock', 
         'correlation', 
         'cosine', 
         'dice', 
         'euclidean', 
         'hamming', 
         'jaccard', 
         'jensenshannon', 
         'kulsinski', 
         'mahalanobis', 
         'matching', 
         'minkowski', 
         'rogerstanimoto', 
         'russellrao', 
         'seuclidean', 
         'sokalmichener', 
         'sokalsneath', 
         'sqeuclidean', 
         'wminkowski', 
         'yule'
         ]
      if sim_measure in similarity_measures:
         similarity_measure = sim_measure
      else:
         similarity_measure=DEFAULT_SIMILARITY_MEASURE


      return similarity_method, similarity_measure



