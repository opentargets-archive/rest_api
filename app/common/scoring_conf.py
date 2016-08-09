__author__ = 'andreap'


class DataSourceScoring():

    def __init__(self, app):
        self.methods = app.config['DATASOURCE_SCORING_METHOD']

class ScoringMethods():

    SUM='sum'
    MAX='max'
    HARMONIC_SUM='harmonic-sum'

    DEFAULT = HARMONIC_SUM