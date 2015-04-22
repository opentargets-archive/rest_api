__author__ = 'andreap'


class ScoringMethods():

    SUM='sum'
    MAX='max'
    COUNT='count'
    MIN='min'
    AVG='avg'



class DataSourceScoring():

    def __init__(self, app):
        self.scoring_method = app.config['DATASOURCE_SCORING_METHOD']



