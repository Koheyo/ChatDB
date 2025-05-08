# ChatDB - Natural Language Interface for SQL/NoSQL Databases
ChatDB is a powerful tool that allows users to interact with SQL and NoSQL databases using natural language queries. It leverages LLM (Large Language Model) technology to convert natural language into database queries and execute them.

## Features
- Natural language to SQL/NoSQL query conversion
- Support for multiple database types:
  - MySQL
  - MongoDB
- Interactive web interface using Streamlit
- Query validation and execution
- Results visualization and export capabilities
- Schema management and inspection

## Prerequisites
### Software Requirements
- Python 3.8 or higher
- MySQL Server (for MySQL support)
- MongoDB Server (for MongoDB support)

### API Keys and Credentials
- Azure OpenAI API Key
- Database credentials for your chosen database(s)

## Installation
1. Clone the repository:
```bash
git clone https://github.com/Koheyo/ChatDB.git
cd ChatDB
```
2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows, use: venv\Scripts\activate
```
3. Install the required dependencies:
```bash
pip install -r requirements.txt
```
4. Set up environment variables:
Create a `.env` file in the project root with the following variables:
```
AZURE_OPENAI_API_KEY=your_azure_openai_api_key
ENDPOINT_URL=your_azure_endpoint_url
DEPLOYMENT_NAME=your_deployment_name
DATABASE_URL=your_database_url
```

## Database Setup
### MySQL Setup
1. Install MySQL Server
2. Create a database named "Movie"
3. Update the connection details in `src/db/rdbms_connector.py`:
```python
host="localhost"
user="your_username"
password="your_password"
database="Movie"
```
4. Import the sample data:
   - The sample data files are located in `src/databases/mysql/`
   - Before running the import script, update the database connection in `src/databases/mysql/import_mysql.py`:
   ```python
   conn = mysql.connector.connect(
       host="localhost",
       user="your_username",
       password="your_password",
       database="Movie",
       ssl_disabled=True
   )
   ```
   - Then run the import script:
   ```bash
   python src/databases/mysql/import_mysql.py
   ```
   This will import:
   - merged_movies.json
   - merged_actors.json
   - merged_directors.json

### MongoDB Setup
1. Install MongoDB Server
2. Create a database named "sales"
3. The default connection URL is "mongodb://localhost:27017/"
4. Import the sample data:
   - The sample data files are located in `src/databases/mongodb/`
   - Before running the import script, update the MongoDB connection URL in `src/databases/mongodb/import_mongodb.py` if needed:
   ```python
   client = MongoClient('mongodb://localhost:27017/')  # Update this if your MongoDB is not running locally
   ```
   - Then run the import script:
   ```bash
   python src/databases/mongodb/import_mongodb.py
   ```
   This will import:
   - customers.json (300 customer records)
   - orders.json (1200 order records)
   - products.json (100 product records)

## Usage

1. Start the application:
```bash
streamlit run app.py
```
2. Open your web browser and navigate to `http://localhost:8501`
3. Using the interface:
   - Select your database type (MySQL or MongoDB)
   - View the database schema
   - Enter your natural language query
   - Click "Generate Query" to convert your query
   - Click "Execute Query" to run the query
   - View and download results

## Project Structure

```
ChatDB/
│── src/
│   │── __init__.py
│   │── config.py                   # Configuration settings
│   │── databases/                  # Database files and import scripts
│   │   │── mongodb/               # MongoDB data files and import script
│   │   │   │── import_mongodb.py  # Script to import MongoDB data
│   │   │── mysql/                 # MySQL data files and import script
│   │   │   │── import_mysql.py    # Script to import MySQL data
│   │── llm/                        # LLM integration and query processing
│   │   │── __init__.py
│   │   │── llm_integration.py      # Azure OpenAI integration
│   │── db/                         # Database connectors and operations
│── app.py                          # Main application entry point
│── requirements.txt                # Project dependencies
│── README.md                       # This file
│── .gitignore                      # Git ignore rules
│── deploy.sh                       # Deployment script
│── LICENSE                         # Project license
```


## Deployment

The project is configured for automated deployment to AWS EC2 using GitHub Actions. The deployment process is handled by `deploy.sh` script and `.github/workflows/deploy.yml` workflow.

### Deployment Process
1. When changes are pushed to the main branch, GitHub Actions automatically triggers the deployment workflow
2. The workflow:
   - Connects to the EC2 instance using SSH
   - Pulls the latest code from the repository
   - Installs/updates dependencies
   - Restarts the application service

### Manual Deployment
To deploy manually, you can run the deployment script:
```bash
./deploy.sh
```

### Deployment Configuration
- The deployment is configured in `.github/workflows/deploy.yml`
- Environment variables and secrets are stored in GitHub repository secrets
- The EC2 instance is configured with the necessary security groups and IAM roles

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support, please open an issue in the GitHub repository or contact the maintainers.



