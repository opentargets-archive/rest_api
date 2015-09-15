__author__ = 'andreap'


class DataSourceScoring():

    def __init__(self, app):
        self.methods = app.config['DATASOURCE_SCORING_METHOD']
        self.weights = app.config['SCORING_WEIGHTS']

class ScoringMethods():

    SUM='sum'
    MAX='max'
    COUNT='count'
    MIN='min'
    AVG='avg'