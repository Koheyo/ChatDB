# Web interface using Streamlit
import streamlit as st
from llm.query_processing import generate_query
from db.query_execution import execute_sql


def run_ui():
    """Runs the Streamlit UI."""
    st.title("ChatDB: Natural Language to Database Query")

    db_type = st.radio("Select Database Type", ("sql", "nosql"))
    user_query = st.text_area("Enter your question about the database:")

    if st.button("Submit Query"):
        if user_query.strip():
            query_type, query = generate_query(user_query, db_type)

            if query_type.lower() == "sql":
                result = execute_sql(query)
            else:
                result = "NoSQL execution is not implemented yet."

            st.subheader("Generated Query:")
            st.code(query, language="sql")
            st.subheader("Query Result:")
            st.write(result)
        else:
            st.error("Please enter a valid query.")