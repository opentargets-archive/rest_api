from collections import Counter
from fractions import Fraction
import logging
import pprint
from flask import current_app
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
                                                    datatypes = {}
                                                   )
                           )
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
        for score_name, score in self.scores.items():
            capped_score.update(score)
            overall_score = 0.
            datatype_scores = []

            if 'datatypes' in score:
                new_datatypes = []
                for dt in score['datatypes']:

                    """use harmonic sum"""
                    dt_computed_score = self._harmonic_sum(score['datatypes'][dt]["scores"] )
                    new_dt = {'datatype': dt,
                              score_name: self._cap_score(dt_computed_score),
                              'evidence_count': score['datatypes'][dt]['evidence_count']}
                    datatype_scores.append(dt_computed_score)
                    if 'datasources' in score['datatypes'][dt]:
                        new_datasources = []
                        for ds in score['datatypes'][dt]['datasources']:
                            """use harmonic sum"""
                            computed_score = self._harmonic_sum(score['datatypes'][dt]['datasources'][ds]["scores"] )
                            new_ds = {'datasource': ds,
                                       score_name: self._cap_score(computed_score),
                                      'evidence_count': score['datatypes'][dt]['datasources'][ds]['evidence_count']}
                            new_datasources.append(new_ds)
                        new_dt['datasources']=new_datasources
                    new_datatypes.append(new_dt)
                capped_score['datatypes'] = new_datatypes
            capped_score[score_name]=self._cap_score(self._harmonic_sum(datatype_scores))

        return capped_score


    def _cap_score(self, score):
        if score>1:
            return 1
        elif score<-1:
            return -1
        return score

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
              sortby=None,
              expand_efo = False,
              cache_key = None):
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

        calculated_scores = current_app.cache.get(cache_key)
        if not cache_key or (calculated_scores is None):

            for es_result in evs:
                counter+=1
                ev = es_result['_source']
                ev_score = ev['scores']['association_score'] * \
                           self.scoring_params.weights[ev['sourceID']]

                '''target data'''
                target = ev['target']['id']
                if target not in targets:
                    targets[target] = Score(type = Score.TARGET,
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
                    if disease != "cttv_root":
                        if disease not in diseases:
                            diseases[disease] = Score(type = Score.DISEASE,
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



