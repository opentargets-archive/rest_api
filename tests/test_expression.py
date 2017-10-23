import unittest, json
from tests import GenericTestCase
import pytest
from config import Config
pytestmark = pytest.mark.skipif(
    not Config.ELASTICSEARCH_URL,
    reason="needs ES, pass url as ENV var: ELASTICSEARCH_URL"
)

class ExpressionTestCase(GenericTestCase):


    def testGetExpression(self):
        target_id = 'ENSG00000198947'
        response = self._make_request('/platform/private/target/expression?gene=%s'%target_id, token=self._AUTO_GET_TOKEN)
        self.assertTrue(response.status_code == 200)
        json_response = json.loads(response.data.decode('utf-8'))




if __name__ == "__main__":
     unittest.main()