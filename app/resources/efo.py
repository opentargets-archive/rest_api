__author__ = 'andreap'
from flask import current_app
from flask.ext import restful
from flask.ext.restful import abort
from flask_restful_swagger import swagger




class EfoLabelFromCode(restful.Resource):

    @swagger.operation(
        notes='''get an EFO Information from a code''',)
    def get(self, code ):
        es = current_app.extensions['esquery']
        res = es.get_efo_label_from_code(code)
        if res:
            return res
        else:
            abort(404, message="EFO code %s cannot be found"%code)

class EfoIDFromLabel(restful.Resource):

    @swagger.operation(
        notes='''get an EFO ID from a label''',)
    def get(self, label ):
        es = current_app.extensions['esquery']
        res = es.get_efo_code_from_label(label)
        if res:
            return res
        else:
            abort(404, message="EFO label %s cannot be found"%label)