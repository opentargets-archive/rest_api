from collections import Counter
import logging
import pprint
from flask import current_app
from app.common.scoring_conf import ScoringMethods
from elasticsearch import helpers


__author__ = 'andreap'


class ScoringModes():
    DISEASE = 'efo_codes'
    TARGET = 'genes'


class Score():
    '''
    Base class for score object.
    Subclasses needs populate the scores object
    '''

    DISEASE = 'disease'
    TARGET = 'target'

    def __init__(self,
                 type,
                 datatypes,
                 key='',
                 name = '',):
        """

        :param key:
        :param name:
        :param type: self.DISEASE or self.TARGET
        :return:
        """
        self.type = type
        self.datatypes = datatypes
        self.key = key
        self.name = name
        self.scores = dict(association_score = dict(association_score = 0.,
                                                    evidence_count = 0,
                                                    datatypes = {}
                                                   )
                           )


    def finalise(self):
        if self.type == self.DISEASE:
            capped_score = {"efo_code": self.key,
                            "label": self.name}
        elif self.type == self.TARGET:
            capped_score = {"gene_id": self.key,
                            "label": self.name}
        for score_name, score in self.scores.items():
            capped_score.update(score)
            capped_score[score_name]=self._cap_score(score[score_name])
            if 'datatypes' in score:
                new_datatypes = []
                for dt in score['datatypes']:
                    new_dt = {'datatype': dt,
                              score_name: self._cap_score(score['datatypes'][dt][score_name]),
                              'evidence_count': score['datatypes'][dt]['evidence_count']}
                    capped_score['datatypes'][dt][score_name]=self._cap_score(score['datatypes'][dt][score_name])
                    if 'datasources' in score['datatypes'][dt]:
                        new_datasources = []
                        for ds in score['datatypes'][dt]['datasources']:
                            new_ds = {'datasource': ds,
                                       score_name: self._cap_score(score['datatypes'][dt]['datasources'][ds][score_name]),
                                      'evidence_count': score['datatypes'][dt]['datasources'][ds]['evidence_count']}
                            new_datasources.append(new_ds)
                        new_dt['datasources']=new_datasources
                    new_datatypes.append(new_dt)
                capped_score['datatypes'] = new_datatypes

        return capped_score


    def _cap_score(self, score):
        if score>1:
            return 1
        elif score<-1:
            return -1
        return score


class ScorerResult():

    def __init__(self,
                 target_scores,
                 disease_scores,
                 datapoints,
                 disease_with_data,
                 facets = []):
        self.target_scores = target_scores
        self.disease_scores = disease_scores
        self.datapoints = datapoints
        self.disease_with_data = disease_with_data
        self.facets = facets


class Scorer():
    '''
    Base Class to calculate scores for a list of evidencestring documents
    '''


    def __init__(self, scoring_params, handler, index):

        self.available_methods=ScoringMethods()
        self.scoring_params = scoring_params
        self.default_sorting = 'association_score'
        self.handler = handler
        self.index = index

    def score(self,
              query,
              stringency,
              mode,
              datatypes,
              sortby=None,
              expand_efo = False,
              cache_key = None):
        '''
        needs to be overriden by children classes.
        :param data: data to use for the calculation
        :param stringency: stringency parameter to scale score
        :param mode: chose between target and disease using a ScoringModes object
        :param datatypes: a DataType object storing the available datatypes and datasources
        :param sortby: result sorting parameter
        :param expand_efo: expand the efo herarchy True or False
        :param cache_key: key to use for intermediate cache
        :return: ScorerResult
        '''
        raise NotImplementedError



    def apply_scoring_params(self, score_values, stringency):
        def recurse(d, score_name, stringency):
            if isinstance(d, dict):
                for k,v in d.items():
                    if (k == score_name) and (isinstance(v, float) or isinstance(v, int)):
                        d[k]=v/stringency
                    elif isinstance(v, dict):
                        recurse(v, score_name, stringency)
            return d

        for k,v in score_values.items():
            for score_name in score_values[k].scores:
                score_values[k].scores[score_name] = recurse(score_values[k].scores[score_name], score_name, stringency)
        return score_values

class ManualScore(Score):

    def add_evidence_score(self, ev_score, dt, ds):
        for score_name, score in self.scores.items():
            score[score_name]+=ev_score
            score["evidence_count"]+=1
            if dt not in score['datatypes']:
                 score['datatypes'][dt]={"datasources" : {ds : { score_name: ev_score,
                                                                 "evidence_count" : 1},
                                                          },
                                         score_name : ev_score,
                                         "evidence_count" : 1,}
            elif ds not in score['datatypes'][dt]['datasources']:
                score['datatypes'][dt]['datasources'][ds] = { score_name: ev_score,
                                                              "evidence_count" : 1}
                score['datatypes'][dt][score_name]+=ev_score
                score['datatypes'][dt]["evidence_count"]+=1
            else:
                score['datatypes'][dt]['datasources'][ds][score_name]+=ev_score
                score['datatypes'][dt]['datasources'][ds]["evidence_count"]+=1
                score['datatypes'][dt][score_name]+=ev_score
                score['datatypes'][dt]["evidence_count"]+=1



class ManualScorer(Scorer):
     ''' get all the evidence strings from elasticsearch and manually compute the score
     '''

     def score(self,
              query,
              stringency,
              mode,
              datatypes,
              sortby=None,
              expand_efo = False,
              cache_key = None):

        targets = {}
        diseases = {}
        disease_with_data = set()
        if sortby is None:
            sortby = self.default_sorting
        counter = 0

        calculated_scores = current_app.cache.get(cache_key)
        if not cache_key or (calculated_scores is None):
            evs = helpers.scan(self.handler,
                              index=self.index,
                              query=query,
                              size=10000,
                              timeout = "10m",
                               )

            for es_result in evs:
                counter+=1
                ev = es_result['_source']
                ev_score = ev['scores']['association_score'] * \
                           self.scoring_params.weights[ev['sourceID']]

                '''target data'''
                target = ev['target']['id']
                if target not in targets:
                    targets[target] = ManualScore(type = Score.TARGET,
                                                  datatypes=datatypes,
                                            key = target,
                                            name = ev['target']['gene_info']['symbol'])
                targets[target].add_evidence_score(ev_score,
                                                   ev['_private']['datatype'],
                                                   ev['sourceID'])
                '''disease data'''
                disease_with_data.add(ev['disease']['id'])
                if expand_efo:
                    linked_diseases = ev['_private']['efo_codes']
                else:
                    linked_diseases = [ev['disease']['id']]
                for disease in linked_diseases:
                    if disease not in diseases:
                        diseases[disease] = ManualScore(type = Score.DISEASE,
                                                        datatypes=datatypes,
                                                  key = disease,
                                                  name = "")
                    diseases[disease].add_evidence_score(ev_score,
                                                         ev['_private']['datatype'],
                                                         ev['sourceID'])
            current_app.cache.set(cache_key, (targets, diseases, counter, disease_with_data), timeout=current_app.config['APP_CACHE_EXPIRY_TIMEOUT'])
        else:
            targets, diseases, counter, disease_with_data = calculated_scores

        parametrized_targets = self.apply_scoring_params(targets, stringency)
        parametrized_diseases = self.apply_scoring_params(diseases, stringency)

        sorted_targets = sorted(parametrized_targets.values(),key=lambda v: v.scores[sortby][sortby], reverse=True)
        sorted_diseases = sorted(parametrized_diseases.values(),key=lambda v: v.scores[sortby][sortby], reverse=True)

        for i,score in enumerate(sorted_targets):
            sorted_targets[i] = score.finalise()
        for i,score in enumerate(sorted_diseases):
            sorted_diseases[i]=score.finalise()

        return  ScorerResult(sorted_targets, sorted_diseases, counter, list(disease_with_data))


class ESScore(Score):

    def add_score(self, bucket):

        for score_name, score in self.scores.items():
            score_data =bucket[score_name+"_mp"]['value']['scores']
            count_data =bucket[score_name+"_mp"]['value']['counts']
            score[score_name]=score_data['all']
            score["evidence_count"]=bucket['doc_count']
            for dt in self.datatypes.available_datatypes:
                if dt not in score['datatypes']:
                    score['datatypes'][dt]={"datasources" : {},
                                            score_name : score_data[dt],
                                            "evidence_count" : count_data[dt],}

                for ds in  self.datatypes.get_datasources(dt):
                    if ds not in score['datatypes'][dt]['datasources']:
                        score['datatypes'][dt]['datasources'][ds] = { score_name: score_data[ds],
                                                                      "evidence_count" : count_data[ds]}




class ESScorer(Scorer):
     '''score calculation implementation using elasticsarch scripted metric'''

     def score(self,
              query,
              stringency,
              mode,
              datatypes,
              sortby=None,
              expand_efo = False,
              cache_key = None):

        targets = {}
        diseases = {}
        disease_with_data = set()
        if sortby is None:
            sortby = self.default_sorting
        counter = 0

        calculated_scores = current_app.cache.get(cache_key)
        if not cache_key or (calculated_scores is None):

            res = self.handler.search(index=self.index,
                          body = query,
                          timeout = "10m",
                          )


            if  res['timed_out']:
                raise Exception("Association score query in elasticsearch timed out")



            for es_result in res['aggregations']['data'][mode]['buckets']:
                counter+=1
                if mode == ScoringModes.TARGET:
                    '''target data'''
                    target = es_result['key']
                    if target not in targets:
                        score = ESScore(type = Score.TARGET,
                                        datatypes=datatypes,
                                        key = target,
                                        name ='')#todo: add names here
                        score.add_score(es_result)
                        targets[target] = score

                elif mode == ScoringModes.DISEASE:
                    '''disease data'''
                    disease = es_result['key']
                    if disease not in diseases:
                        score = ESScore(type = Score.DISEASE,
                                        datatypes=datatypes,
                                        key = disease,
                                        name ='')#todo: add names here
                        score.add_score(es_result)
                        diseases[disease] = score
            current_app.cache.set(cache_key, (targets, diseases, counter, disease_with_data), timeout=current_app.config['APP_CACHE_EXPIRY_TIMEOUT'])
        else:
            targets, diseases, counter, disease_with_data = calculated_scores

        parametrized_targets = self.apply_scoring_params(targets, stringency)
        parametrized_diseases = self.apply_scoring_params(diseases, stringency)

        sorted_targets = sorted(parametrized_targets.values(),key=lambda v: v.scores[sortby][sortby], reverse=True)
        sorted_diseases = sorted(parametrized_diseases.values(),key=lambda v: v.scores[sortby][sortby], reverse=True)

        for i,score in enumerate(sorted_targets):
            sorted_targets[i] = score.finalise()
        for i,score in enumerate(sorted_diseases):
            sorted_diseases[i]=score.finalise()

        return  ScorerResult(sorted_targets, sorted_diseases, counter, list(disease_with_data))