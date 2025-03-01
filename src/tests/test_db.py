import unittest
from db.query_execution import execute_sql

class TestDB(unittest.TestCase):
    def test_execute_query(self):
        query_info = ("SQL", "SELECT * FROM employees")
        self.assertIsInstance(execute_sql(query_info), list)

if __name__ == '__main__':
    unittest.main()