import streamlit as st
from utils import generate_query, execute_sql, execute_mongo, get_nosql_schema


def main():
    st.title("Natural Language to SQL/NoSQL Query")
    db_choice = st.radio("Select Database Type", ("SQL", "NoSQL"))
    user_query = st.text_area("Enter your query in natural language")
    if st.button("Generate Query"):
        if user_query:
            db_type = "sql" if db_choice == "SQL" else "nosql"
            query = generate_query(user_query, db_type)
            st.code(query, language="sql" if db_type == "sql" else "json")
            if st.button("Execute Query"):
                if db_type == "sql":
                    result_df = execute_sql(query)
                else:
                    collection = list(get_nosql_schema().keys())[0]
                    filter_query = {}  # Modify as needed
                    result_df = execute_mongo(collection, filter_query)
                st.dataframe(result_df)
                csv = result_df.to_csv(index=False).encode('utf-8')
                st.download_button("Download Results", csv, "results.csv", "text/csv")

if __name__ == "__main__":
    main()
