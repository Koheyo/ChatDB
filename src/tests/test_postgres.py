import unittest

from db.postgres_connector import connect_to_postgres
from llm.query_processing import generate_query, get_postgres_schema


class TestPostgreSQL(unittest.TestCase):
    def setUp(self):
        """Set up test environment."""
        self.connection = connect_to_postgres()
        
    def tearDown(self):
        """Clean up test environment."""
        if self.connection:
            self.connection.close()

    def test_get_postgres_schema(self):
        """Test if we can get PostgreSQL schema."""
        schema = get_postgres_schema()
        self.assertIsInstance(schema, dict)
        self.assertTrue(len(schema) > 0)
        # Check for some expected tables in dvdrental
        expected_tables = ['film', 'customer', 'rental', 'payment', 'inventory']
        for table in expected_tables:
            self.assertIn(table, schema)

    def test_generate_postgres_query(self):
        """Test PostgreSQL query generation."""
        # Test film queries
        query_type, query = generate_query("Show all films", "postgres")
        self.assertEqual(query_type, "POSTGRES")
        self.assertTrue(query.upper().startswith("SELECT"))
        self.assertTrue("film" in query.lower())
        
        # Test customer queries
        query_type, query = generate_query("Find customers from Canada", "postgres")
        self.assertEqual(query_type, "POSTGRES")
        self.assertTrue("customer" in query.lower())
        self.assertTrue("WHERE" in query.upper())
        
        # Test rental queries
        query_type, query = generate_query("Show rentals for customer with ID 1", "postgres")
        self.assertEqual(query_type, "POSTGRES")
        self.assertTrue("rental" in query.lower())
        self.assertTrue("customer_id" in query.lower())

    def test_execute_postgres_query(self):
        """Test executing PostgreSQL queries."""
        with self.connection.cursor() as cursor:
            # Test film query
            query_type, query = generate_query("Show all films", "postgres")
            cursor.execute(query)
            results = cursor.fetchall()
            self.assertIsInstance(results, list)
            self.assertTrue(len(results) > 0)
            
            # Test customer query
            query_type, query = generate_query("Find customers from Canada", "postgres")
            cursor.execute(query)
            results = cursor.fetchall()
            self.assertIsInstance(results, list)

    def test_complex_queries(self):
        """Test more complex PostgreSQL queries."""
        # Test film category queries
        query_type, query = generate_query("Count films by category", "postgres")
        self.assertEqual(query_type, "POSTGRES")
        self.assertTrue("COUNT" in query.upper())
        self.assertTrue("GROUP BY" in query.upper())
        self.assertTrue("category" in query.lower())
        
        # Test rental statistics
        query_type, query = generate_query("Show top 10 customers by rental count", "postgres")
        self.assertEqual(query_type, "POSTGRES")
        self.assertTrue("ORDER BY" in query.upper())
        self.assertTrue("LIMIT" in query.upper())
        self.assertTrue("COUNT" in query.upper())
        
        # Test payment queries
        query_type, query = generate_query("Find customers who paid more than average", "postgres")
        self.assertEqual(query_type, "POSTGRES")
        self.assertTrue("payment" in query.lower())
        self.assertTrue("AVG" in query.upper())
        
        # Test film inventory queries
        query_type, query = generate_query("Show films that are currently rented", "postgres")
        self.assertEqual(query_type, "POSTGRES")
        self.assertTrue("film" in query.lower())
        self.assertTrue("rental" in query.lower())
        self.assertTrue("inventory" in query.lower())

    def test_join_queries(self):
        """Test queries with joins."""
        # Test film and actor joins
        query_type, query = generate_query("Show films with their actors", "postgres")
        self.assertEqual(query_type, "POSTGRES")
        self.assertTrue("film" in query.lower())
        self.assertTrue("actor" in query.lower())
        self.assertTrue("JOIN" in query.upper())
        
        # Test customer and payment joins
        query_type, query = generate_query("Show customer payments with staff details", "postgres")
        self.assertEqual(query_type, "POSTGRES")
        self.assertTrue("customer" in query.lower())
        self.assertTrue("payment" in query.lower())
        self.assertTrue("staff" in query.lower())
        self.assertTrue("JOIN" in query.upper())

if __name__ == '__main__':
    unittest.main() 