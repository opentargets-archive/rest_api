from collections import Counter
import logging
import pprint
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
              expand_efo = False):
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
            ev_score = ev['scores']['association_score'] * \
                       self.scoring_params.weights[ev['sourceID']] / \
                       stringency
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
                if disease not in diseases:
                    diseases[disease] = Score(type = Score.DISEASE,
                                              key = disease,
                                              name = "")
                diseases[disease].add_evidence_score(ev_score,
                                                     ev['_private']['datatype'],
                                                     ev['sourceID'])


        sorted_targets = sorted(targets.values(),key=lambda v: v.scores[sortby][sortby], reverse=True)
        sorted_diseases = sorted(diseases.values(),key=lambda v: v.scores[sortby][sortby], reverse=True)

        for i,score in enumerate(sorted_targets):
            sorted_targets[i] = score.finalise()
        for i,score in enumerate(sorted_diseases):
            sorted_diseases[i]=score.finalise()

        return sorted_targets, sorted_diseases, counter, list(disease_with_data)



