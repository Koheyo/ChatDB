import unittest
from llm.query_processing import generate_query

class TestLLM(unittest.TestCase):
    def test_query_processing(self):
        query_type, query = generate_query("Show all students", db_type="sql")
        self.assertIn(query_type.upper(), ["SQL", "NOSQL"])

if __name__ == '__main__':
    unittest.main()