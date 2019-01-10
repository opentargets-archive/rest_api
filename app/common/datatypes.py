__author__ = 'andreap'


class DataType():

    def __init__(self, name, datasources = []):
        self.name = name
        self.datasources = datasources


class DataSource():

     def __init__(self, name, datatypes = []):
        self.name = name
        self.datatypes = datatypes



class DataTypes():
    ''' Singleton representing all the known datatypes with associated datasources
    '''

    def __init__(self, app):
        self.datatypes = {}
        self.datasources = {}
        self.available_datatypes = app.config['DATATYPE_ORDERED']
        for datatype_name,datasources in app.config['DATATYPES'].items():
            self.datatypes[datatype_name] = DataType(datatype_name, datasources)
            for datasource_name in datasources:
                if datasource_name not in self.datasources:
                    self.datasources[datasource_name] = DataSource(datasource_name,[datatype_name])
                else:
                    self.datasources[datasource_name].datatypes.append(datatype_name)


    def get_datasources(self, datatype):
        try:
            return self.datatypes[datatype].datasources
        except KeyError:
            return []

    def is_datasources_in_datatype(self, datasource, datatype):
        return datasource in  self.datatypes[datatype].datasources


