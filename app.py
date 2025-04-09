import streamlit as st
import pandas as pd
from src.llm import generate_query, get_nosql_schema, extract_sql_from_response
from src.db import execute_sql, execute_nosql, validate_sql

def main():
    st.title("Natural Language to SQL/NoSQL Query")

    # Select the type of database
    db_choice = st.radio("Select Database Type", ("SQL", "NoSQL"))

    # Input the natural language query
    user_query = st.text_area("Enter your query in natural language")

    # Initialize session state for storing the generated query
    if "generated_query" not in st.session_state:
        st.session_state.generated_query = None

    # Generate Query Button
    if st.button("Generate Query"):
        if user_query:
            db_type = "sql" if db_choice == "SQL" else "nosql"
            
            # Generate and store query
            query_type, sql_query = generate_query(user_query, db_type)
            sql_query = extract_sql_from_response(sql_query)  # 提取 SQL 语句

            st.session_state.generated_query = sql_query  # 只存储 SQL 语句
            #st.session_state.generated_query = generate_query(user_query, db_type)

    # Display the generated query **only if it exists**
    if st.session_state.generated_query:
        st.write("### Generated Query:")
        st.code(st.session_state.generated_query, language="sql" if db_choice == "SQL" else "json")

        # Execute Query Button
        if st.button("Execute Query"):
            if db_choice == "SQL":
                if validate_sql(st.session_state.generated_query):
                    try:
                        result_df = execute_sql(st.session_state.generated_query)

                        # Display results
                        if isinstance(result_df, pd.DataFrame):
                            st.dataframe(result_df)
                        else:
                            st.write(result_df)  # Display error/message if no DataFrame

                        # Download button for CSV
                        if isinstance(result_df, pd.DataFrame):
                            csv = result_df.to_csv(index=False).encode('utf-8')
                            st.download_button("Download Results", csv, "results.csv", "text/csv")
                    except Exception as e:
                        st.write(f"Error: {str(e)}")
                else:
                    st.write("Invalid SQL query. Please try again.")
            else:
                # Execute NoSQL Query
                collection = list(get_nosql_schema().keys())[0]
                filter_query = {}  
                result_df = execute_nosql(collection, filter_query)

                # Display results
                if isinstance(result_df, pd.DataFrame):
                    st.dataframe(result_df)
                else:
                    st.write(result_df)

                # Download button for NoSQL results
                if isinstance(result_df, pd.DataFrame):
                    csv = result_df.to_csv(index=False).encode('utf-8')
                    st.download_button("Download Results", csv, "results.csv", "text/csv")

if __name__ == "__main__":
    main()
