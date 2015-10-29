from collections import Counter
from fractions import Fraction
import logging
import pprint
from flask import current_app
from app import DataTypes
from app.common.scoring_conf import ScoringMethods


__author__ = 'andreap'





class Score():

    DISEASE = 'disease'
    TARGET = 'target'

    def __init__(self, type, key='', name = '',):
        """

        :param key:
        :param name:
        :param type: self.DISEASE or self.TARGET
        :return:
        """
        self.type = type
        self.key = key
        self.name = name
        self.scores = dict(association_score = dict(association_score = 0.,
                                                    evidence_count = 0,
                                                    datatypes = []
                                                   )
                           )

    def add_precomputed_score(self, precomp, datatypes):
        for score_name, score in self.scores.items():

            score[score_name] = precomp['overall']
            score['evidence_count'] = precomp['evidence_count']
            for dt in precomp['datatypes']:
                if precomp['datatype_evidence_count'][dt]:
                    datasources = []
                    for ds in datatypes.datatypes[dt].datasources:
                        if  precomp['datasource_evidence_count'][ds]:
                            datasources.append({ 'datasource': ds,
                                                 score_name:  precomp['datasources'][ds],
                                                 "evidence_count" : precomp['datasource_evidence_count'][ds]}
                                                 )

                    score['datatypes'].append( {"datatype":dt,
                                                "datasources" : datasources,
                                                 score_name : precomp['datatypes'][dt],
                                                 "evidence_count" : precomp['datatype_evidence_count'][dt]
                                                })


        return



    def add_evidence_score(self, ev_score, dt, ds):
        for score_name, score in self.scores.items():
            score[score_name]+=ev_score
            score["evidence_count"]+=1
            if dt not in score['datatypes']:
                 score['datatypes'][dt]={"datasources" : {ds : { score_name: ev_score,
                                                                 "scores" : [ev_score],
                                                                 "evidence_count" : 1},
                                                          },
                                         score_name : ev_score,
                                         "scores" : [ev_score],
                                         "evidence_count" : 1,}
            elif ds not in score['datatypes'][dt]['datasources']:
                score['datatypes'][dt]['datasources'][ds] = { score_name: ev_score,
                                                              "scores" : [ev_score],
                                                              "evidence_count" : 1}
                score['datatypes'][dt][score_name]+=ev_score
                score['datatypes'][dt]["evidence_count"]+=1
            else:
                score['datatypes'][dt]['datasources'][ds][score_name]+=ev_score
                score['datatypes'][dt]['datasources'][ds]["scores"].append(ev_score)
                score['datatypes'][dt]['datasources'][ds]["evidence_count"]+=1
                score['datatypes'][dt][score_name]+=ev_score
                score['datatypes'][dt]["evidence_count"]+=1
                score['datatypes'][dt]["scores"].append(ev_score)




    def finalise(self):
        if self.type == self.DISEASE:
            capped_score = {"efo_code": self.key,
                            "label": self.name}
        elif self.type == self.TARGET:
            capped_score = {"gene_id": self.key,
                            "label": self.name}
        score_name = 'association_score'
        score = self.scores[score_name]
        capped_score.update(score)

        final_score =  self._cap_all(capped_score, score_name)
        return final_score





    @staticmethod
    def _cap_score(score):
        if score>1:
            return 1
        elif score<-1:
            return -1
        return score

    def _cap_all(self, score_values, score_name):
        def recurse(d, score_name):
            if isinstance(d, dict):
                for k,v in d.items():
                    if (k == score_name) and (isinstance(v, float) or isinstance(v, int)):
                        d[k]=self._cap_score(v)
                    elif isinstance(v, list):
                        for i in v:
                            recurse(i, score_name)
            return d


        return recurse(score_values, score_name)


    def _harmonic_sum(self,scores, max_elements = 100 ):
        if max_elements <=0:
            max_elements=len(scores)
        scores.sort(reverse=True)
        return sum(s/(i+1) for i,s in enumerate(scores[:max_elements]))




class Scorer():
    '''
    Calculate scores for a list of evidencestring documents
    '''


    def __init__(self, scoring_params):

        self.available_methods=ScoringMethods()
        self.scoring_params = scoring_params
        self.default_sorting = 'association_score'

    def score(self,
              evs,
              stringency,
              datatypes,
              sortby=None,
              expand_efo = False,
              cache_key = None
              ):
        '''
        :param evs: an iterator returning the evidencestring documents form an elasticsearch query
        :return: a score object
        '''
        targets = {}
        diseases = {}
        disease_with_data = set()
        if sortby is None:
            sortby = self.default_sorting
        counter = 0



        for es_result in evs:
            counter+=1
            ev = es_result['_source']

            ev_score = ev['harmonic-sum']

            '''target data'''
            target = ev['target']['id']
            if target not in targets:
                targets[target] = Score(type = Score.TARGET,
                                        key = target,
                                        name = "")
            targets[target].add_precomputed_score(ev_score, datatypes)
            '''disease data'''
            disease = ev['disease']['id']
            if disease != "cttv_root":
                if expand_efo:
                    disease_with_data.add(disease)
                else:
                    if ev['is_direct']:
                        disease_with_data.add(disease)

                diseases[disease] = Score(type = Score.DISEASE,
                                              key = disease,
                                              name = "")
                diseases[disease].add_precomputed_score(ev_score, datatypes)


        parametrized_targets = self.apply_scoring_params(targets, stringency)
        parametrized_diseases = self.apply_scoring_params(diseases, stringency)

        sorted_targets = sorted(parametrized_targets.values(),key=lambda v: v.scores[sortby][sortby], reverse=True)
        sorted_diseases = sorted(parametrized_diseases.values(),key=lambda v: v.scores[sortby][sortby], reverse=True)

        for i,score in enumerate(sorted_targets):
            sorted_targets[i] = score.finalise()
        for i,score in enumerate(sorted_diseases):
            sorted_diseases[i]=score.finalise()

        return sorted_targets, sorted_diseases, counter, list(disease_with_data)

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



