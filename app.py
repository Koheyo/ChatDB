import pandas as pd
import streamlit as st
from bson import ObjectId

from src.db import (connect_to_postgres, execute_nosql, execute_postgres,
                    execute_sql, validate_sql)
from src.llm import (extract_sql_from_response, generate_query,
                     get_nosql_schema, get_postgres_schema, get_sql_schema)


def clean_mongodb_data(data):
    """Clean MongoDB data by converting special types to strings."""
    if isinstance(data, dict):
        return {k: clean_mongodb_data(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [clean_mongodb_data(item) for item in data]
    elif isinstance(data, ObjectId):
        return str(data)
    elif isinstance(data, (pd.Timestamp, pd.DatetimeTZDtype)):
        return str(data)
    return data


def main():
    st.title("Natural Language to SQL/NoSQL Query")

    # Select the type of database
    db_choice = st.radio("Select Database Type", ("MySQL", "PostgreSQL", "MongoDB"))

    # Display database schema
    st.write("### Database Schema")
    if db_choice == "MySQL":
        schema = get_sql_schema()
        st.json(schema)
    elif db_choice == "PostgreSQL":
        schema = get_postgres_schema()
        st.json(schema)
    else:
        schema = get_nosql_schema()
        st.json(schema)

    # Input the natural language query
    user_query = st.text_area("Enter your query in natural language")

    # Initialize session state for storing the generated query
    if "generated_query" not in st.session_state:
        st.session_state.generated_query = None

    # Generate Query Button
    if st.button("Generate Query"):
        if user_query:
            # Convert database choice to the expected format
            db_type_map = {
                "MySQL": "mysql",
                "PostgreSQL": "postgres",
                "MongoDB": "mongodb"
            }
            db_type = db_type_map[db_choice]
            
            # Generate and store query
            query_type, generated_query = generate_query(user_query, db_type)
            st.session_state.generated_query = generated_query

    # Display the generated query **only if it exists**
    if st.session_state.generated_query:
        st.write("### Generated Query:")
        st.code(st.session_state.generated_query, language="sql" if db_choice in ["MySQL", "PostgreSQL"] else "json")

        # Execute Query Button
        if st.button("Execute Query"):
            try:
                if db_choice == "MySQL":
                    if validate_sql(st.session_state.generated_query):
                        result = execute_sql(st.session_state.generated_query)
                    else:
                        st.error("Invalid MySQL query. Please try again.")
                        return
                elif db_choice == "PostgreSQL":
                    result = execute_postgres(st.session_state.generated_query)
                else:  # MongoDB
                    result = execute_nosql(st.session_state.generated_query)
                    # Clean MongoDB result
                    if isinstance(result, list):
                        result = [clean_mongodb_data(item) for item in result]
                    else:
                        result = clean_mongodb_data(result)
                
                # Convert result to DataFrame and handle data types
                if isinstance(result, list):
                    if result and isinstance(result[0], dict):
                        # If result is already a list of dictionaries, convert directly
                        result_df = pd.DataFrame(result)
                    else:
                        # Clean up the result format
                        cleaned_result = []
                        for item in result:
                            # Handle RealDictRow objects
                            if hasattr(item, 'items'):
                                cleaned_item = dict(item)
                            else:
                                # Flatten nested tuples completely
                                while isinstance(item, tuple):
                                    if len(item) == 1:
                                        item = item[0]
                                    else:
                                        break
                                
                                if isinstance(item, tuple):
                                    cleaned_item = list(item)
                                else:
                                    cleaned_item = [item]
                            cleaned_result.append(cleaned_item)
                        
                        # Create DataFrame with proper column names
                        if cleaned_result:
                            result_df = pd.DataFrame(cleaned_result)
                            # Use original column names if available
                            if isinstance(cleaned_result[0], dict):
                                result_df.columns = list(cleaned_result[0].keys())
                            else:
                                # Rename columns if they are numeric
                                result_df.columns = [f'Column_{i+1}' for i in range(len(result_df.columns))]
                        else:
                            result_df = pd.DataFrame()
                else:
                    result_df = pd.DataFrame([str(result)])
                
                # Display results
                if not result_df.empty:
                    st.dataframe(result_df)
                else:
                    st.write("No results found.")
                
                # Download button for CSV
                if not result_df.empty:
                    csv = result_df.to_csv(index=False).encode('utf-8')
                    st.download_button("Download Results", csv, "results.csv", "text/csv")
            except Exception as e:
                st.error(f"Error executing {db_choice} query: {str(e)}")

if __name__ == "__main__":
    main()
