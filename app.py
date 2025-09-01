from flask import (
    Flask,
    request,
    Response,
    render_template_string,
    render_template,
    stream_with_context,
    jsonify,
    send_from_directory,
)
import uuid
from pathlib import Path
import threading
import time
from contextlib import redirect_stdout
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, String, DateTime, JSON
from datetime import datetime
from flask import request, jsonify
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, String, DateTime, JSON
from datetime import datetime
import re
import pymysql
import json
import sqlite3
import ast
import uuid
import json
import os
from urllib.parse import urlparse, unquote
import whisper
import requests  # At the top of your file
import os
import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv  # pip install python-dotenv
# Import required modules (install with: pip install pymysql sqlalchemy)
from sqlalchemy import create_engine, text, MetaData, Table
from sqlalchemy.exc import SQLAlchemyError
import re
from typing import Dict, List, Any, Union
BASE_DIR = Path(__file__).resolve().parent
UPLOAD_FOLDER = "."
app = Flask(__name__)
MYSQL_URI = "mysql+pymysql://admin:PaZxEQB2@mysql-197364-0.cloudclusters.net:19852/arttest"
engine = create_engine(MYSQL_URI)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()





class Test(Base):
    __tablename__ = "table_of_tables"
    table_hash = Column(String(150), primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    table_name = Column(String(500))
    data = Column(JSON)

class OutputCapture:
    def __init__(self):
        self._lines = []
        self._lock = threading.Lock()

    def write(self, data):
        if data:
            with self._lock:
                self._lines.append(data)

    def flush(self):
        pass  # Needed for file-like compatibility

    def pop_new_lines(self):
        with self._lock:
            lines = self._lines[:]
            self._lines.clear()
        return lines

def execute_create_table(create_table_sql):
    """
    Executes the given CREATE TABLE SQL command on the MySQL database.
    
    Parameters:
        create_table_sql (str): The SQL statement to execute.
    """
    if not isinstance(create_table_sql, str):
        raise ValueError("create_table_sql must be a string containing a single SQL statement.")

    conn = pymysql.connect(
        host="mysql-197364-0.cloudclusters.net",
        port=19852,
        user="admin",
        password="PaZxEQB2",
        database="arttest"
    )

    try:
        with conn.cursor() as cur:
            cur.execute(create_table_sql)
        conn.commit()
        conn.close()
        return "✅ Table created successfully."
    except Exception as e:
        conn.close()
        return f"❌ Error creating table: {e}"

def insert_into_table(db_path, table_name, schema, row_data):
    col_names = [col[0] for col in schema]
    # join into one comma-separated string
    col_names_str = ", ".join(col_names)
    # Create placeholders for parameterized query
    placeholders = ", ".join(["%s"] * len(schema))
    placeholders=""
    for x in range(len(schema)):
        if x!=0:
            placeholders+=","
        if schema[x][1]=="TEXT":
            placeholders+="'"+row_data[x]+"'"
    sql =f"INSERT INTO {table_name} ({col_names_str}) VALUES ({placeholders})"
    return sql

def download_mp4(url, output_dir="downloads"):
    """
    Download MP4 file from URL

    Args:
        url (str): URL to download MP4 from
        output_dir (str): Directory to save file

    Returns:
        str: Path to downloaded file
    """
    os.makedirs(output_dir, exist_ok=True)

    # Get filename from URL
    parsed_url = urlparse(url)
    filename = unquote(parsed_url.path.split('/')[-1])
    if not filename.lower().endswith('.mp4'):
        filename += '.mp4'

    file_path = os.path.join(output_dir, filename)

    print(f"Downloading: {url}")
    response = requests.get(url, stream=True)
    response.raise_for_status()

    with open(file_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)

    print(f"Downloaded: {file_path}")
    return file_path

def _upload_to_r2(filepath: str) -> str:
    """Upload to Cloudflare R2 using environment variables."""

    # Get credentials from environment
    bucket_name = "newtest"
    account_id = "bae6511d03ccae51ff96d8bb56308556"
    access_key = "ccab359608261dc528f4aea2b7abcb27"
    secret_key = "5b788309b666517984120b6c473630288f2f6ce40ecd351976fafe57c9fbd10f"

    if not all([bucket_name, account_id, access_key, secret_key]):
        raise ValueError("Missing Cloudflare R2 credentials in environment variables")

    filename = os.path.basename(filepath)

    r2 = boto3.client(
        's3',
        endpoint_url=f"https://{account_id}.r2.cloudflarestorage.com",
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key
    )

    try:
        r2.upload_file(
            filepath, bucket_name, filename,
            ExtraArgs={'ContentType': 'video/mp4','ACL': 'public-read' },

        )

        url = f"https://pub-bbd4b49a88d042e4a910874e7f1617b1.r2.dev/{filename}"
        print(f"✅ Uploaded to Cloudflare R2: {url}")
        return url

    except ClientError as e:
        raise Exception(f"R2 upload failed: {e}")


"""
Parse formatted data string and insert into MySQL table based on JSON template structure

Args:
    json_template (dict): Template defining column names and types
    data_string (str): Comma-separated data values
    table_name (str): Name of the target MySQL table
    mysql_uri (str): MySQL connection URI

Returns:
    bool: True if insertion successful, False otherwise
"""

"""
def insert_data_to_table(json_template, data_values, table_name, mysql_uri):

    try:
        # Import required modules (install with: pip install pymysql sqlalchemy)
        from sqlalchemy import create_engine, text
        # Parse the data string
        # Get column names from JSON template
        columns = list(json_template.keys())
        
        # Handle rowDescription column if data is shorter
        if len(data_values) == len(columns) - 1 and 'rowDescription' in columns:
            data_values.append('')  # Add empty rowDescription
        elif len(data_values) != len(columns):
            raise ValueError(f"Data mismatch: {len(data_values)} values for {len(columns)} columns")
        
        # Create data dictionary with type conversion
        data_dict = {}
        for i, col in enumerate(columns):
            value = data_values[i]
            
            # Type conversion based on JSON template type
            if isinstance(json_template[col], float):
                try:
                    data_dict[col] = float(value) if value and value != '' else 0.0
                except ValueError:
                    data_dict[col] = 0.0
            elif isinstance(json_template[col], int):
                try:
                    data_dict[col] = int(value) if value and value != '' else 0
                except ValueError:
                    data_dict[col] = 0
            else:
                data_dict[col] = value  # Keep as string
        
        # Create database engine
        engine = create_engine(mysql_uri)
        
        # Prepare SQL INSERT statement with named parameters
        column_names = ', '.join(columns)
        placeholders = ', '.join([f':{col}' for col in columns])
        sql_insert = f"INSERT INTO {table_name} ({column_names}) VALUES ({placeholders})"
        
        # Execute the insertion
        with engine.connect() as connection:
            result = connection.execute(text(sql_insert), data_dict)
            connection.commit()
            
        print(f"✅ Successfully inserted data into {table_name}")
        return True
        
    except Exception as e:
        print(f"❌ Error inserting data: {str(e)}")
        return False
"""

def insert_data_to_table(json_template, data_values, table_name, mysql_uri):
    """
    Securely parse formatted data string and insert into MySQL table based on JSON template structure
    
    Args:
        json_template (dict): Template defining column names and types
        data_values (list): List of data values
        table_name (str): Name of the target MySQL table (must be alphanumeric + underscore)
        mysql_uri (str): MySQL connection URI
    
    Returns:
        bool: True if insertion successful, False otherwise
    """
    
    try:
        
        # Input validation and sanitization
        if not isinstance(json_template, dict) or not json_template:
            raise ValueError("json_template must be a non-empty dictionary")
        
        if not isinstance(data_values, list):
            raise ValueError("data_values must be a list")
        
        # Validate table name (only alphanumeric and underscores allowed)
        if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', table_name):
            raise ValueError("Invalid table name. Only alphanumeric characters and underscores allowed")
        
        # Validate column names from template (prevent SQL injection)
        for col_name in json_template.keys():
            if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', col_name):
                raise ValueError(f"Invalid column name: {col_name}")
        
        # Get column names from JSON template
        columns = list(json_template.keys())

        # Handle rowDescription column if data is shorter
        if len(data_values) == len(columns) - 1 and 'rowDescription' in columns:
            data_values = data_values.copy()  # Don't modify original list
            data_values.append('')  # Add empty rowDescription
        elif len(data_values) != len(columns):
            raise ValueError(f"Data mismatch: {len(data_values)} values for {len(columns)} columns")
        
        # Create data dictionary with safe type conversion
        data_dict = {}
        for i, col in enumerate(columns):
            value = data_values[i]

            # Type conversion based on JSON template type with bounds checking
            if isinstance(json_template[col], float):
                try:
                    converted_value = float(value) if value and str(value).strip() != '' else 0.0
                    # Check for reasonable bounds to prevent overflow
                    if abs(converted_value) > 1e308:  # Near float max
                        raise ValueError(f"Float value too large: {converted_value}")
                    data_dict[col] = converted_value
                except (ValueError, OverflowError):
                    data_dict[col] = 0.0
            elif isinstance(json_template[col], int):
                try:
                    converted_value = int(float(value)) if value and str(value).strip() != '' else 0
                    # Check for reasonable integer bounds
                    if abs(converted_value) > 2**63 - 1:  # 64-bit signed integer max
                        raise ValueError(f"Integer value too large: {converted_value}")
                    data_dict[col] = converted_value
                except (ValueError, OverflowError):
                    data_dict[col] = 0
            else:
                # String handling with length limits
                str_value = str(value) if value is not None else ''
                # Limit string length to prevent memory issues (adjust as needed)
                if len(str_value) > 65535:  # TEXT field limit in MySQL
                    str_value = str_value[:65535]
                data_dict[col] = str_value
        
        # Create database engine with additional security settings
        engine = create_engine(
            mysql_uri,
            pool_pre_ping=True,  # Verify connections before use
            pool_recycle=3600,   # Recycle connections every hour
            connect_args={
                'charset': 'utf8mb4',
                'autocommit': False  # Explicit transaction control
            }
        )
        
        # Verify table exists and get its structure for additional validation
        metadata = MetaData()
        with engine.connect() as connection:
            # Use reflection to get actual table structure
            try:
                table = Table(table_name, metadata, autoload_with=engine)
                actual_columns = set(table.columns.keys())
                template_columns = set(columns)
                
                # Check if all template columns exist in actual table
                missing_columns = template_columns - actual_columns
                if missing_columns:
                    raise ValueError(f"Columns not found in table: {missing_columns}")
                    
            except Exception as e:
                raise ValueError(f"Table '{table_name}' does not exist or is not accessible: {str(e)}")
        
        # Prepare SQL INSERT statement with named parameters (safe from SQL injection)
        column_names = ', '.join(f'`{col}`' for col in columns)  # Backticks for column names
        placeholders = ', '.join([f':{col}' for col in columns])
        
        # Use parameterized query (immune to SQL injection)
        sql_insert = f"INSERT INTO `{table_name}` ({column_names}) VALUES ({placeholders})"
        
        # Execute the insertion with proper transaction handling
        with engine.connect() as connection:
            with connection.begin():  # Explicit transaction
                result = connection.execute(text(sql_insert), data_dict)
                # Transaction is automatically committed if no exception occurs
            
        print(f"✅ Successfully inserted data into {table_name}")
        return True
        
    except SQLAlchemyError as e:
        print(f"❌ Database error: {str(e)}")
        return False
    except ValueError as e:
        print(f"❌ Validation error: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        return False


#this needs a rework so that the switch statment is in a config file
"""

Template is such 
Inputype in tranform in collum one.

float
noted by _float

int
noted by _int

date by _date

bool by _bool

time by _time

and zipcode 
by _zip

and not now but eventaly global time _Gzip

and address 
by _address

The way this function works now is simple it takes in a header of a csv hash it and use it to generate a table

It should error if its not in the right formate or if the table names is used or bad. 
"""
def generate_table_schema_and_json(tablename, column_string):
    # Parse the column string
    columns = [col.strip() for col in column_string.split(',')]    
    # Add the rowDescription column
    columns.append('rowDescription')
    
    # Generate SQL column definitions
    sql_columns = []
    template = []
    
    # Add auto-incrementing primary key as first column
    sql_columns.append("dataUpdated DATETIME DEFAULT CURRENT_TIMESTAMP")
    if "id" not in columns:
        sql_columns.append("id INT AUTO_INCREMENT PRIMARY KEY")
    for col in columns:
        if col.endswith('_float'):
            sql_columns.append(f"{col} FLOAT")
            template.append([col, 0.0])
        elif col.endswith('_int'):
            sql_columns.append(f"{col} INT")
            template.append([col, "INT"])
        elif col.endswith('_date') or col.upper() == 'DATE':
            sql_columns.append(f"{col} DATE")
            template.append([col, "YYYY-MM-DD"])
        elif col == 'Audio':
            sql_columns.append("transcript TEXT")
            sql_columns.append("file TEXT")
            template.append(["transcript", "TEXT"])
            template.append(["file", "TEXT"])
        elif col == 'transcript':
            UUID = str(uuid.uuid1())
            sql_columns.append(f"transcript{UUID} TEXT")
            template.append(["transcript" + UUID, "TEXT"])
        elif col == 'file':
            UUID = str(uuid.uuid1())
            sql_columns.append(f"file{UUID} TEXT")
            template.append(["file" + UUID, "TEXT"])
        else:
            if col=="id":
                sql_columns.append(f"{col} VARCHAR(128) PRIMARY KEY")
                template.append([col, "TEXT"])
            else:
                sql_columns.append(f"{col} TEXT")
                template.append([col, "TEXT"])
        
    sql_create = f"CREATE TABLE {tablename} ({', '.join(sql_columns)});"
    return sql_create, template

def execute_insert(insert_table_sql):
    """
    Executes the given CREATE TABLE SQL command on the MySQL database.
    
    Parameters:
        create_table_sql (str): The SQL statement to execute.
    """

    conn = pymysql.connect(
        host="mysql-197364-0.cloudclusters.net",
        port=19852,
        user="admin",
        password="PaZxEQB2",
        database="arttest"
    )

    try:
        with conn.cursor() as cur:
            cur.execute(insert_table_sql)
        conn.commit()
        conn.close()
        return "✅ Table created successfully."
    except Exception as e:
        conn.close()
        return f"❌ Error creating table: {e}"

def insert_test(table_hash_val,table_name_val,data_val):
    """
    Insert a new record into table_hash with provided fields.
    Expects JSON with:
        - table_hash (required, varchar(150))
        - table_name (optional, varchar(500))
        - data (optional, JSON)
    """
    db = SessionLocal()
    new_record = Test(
        table_hash=table_hash_val,
        table_name=table_name_val,
        data=data_val
    )

    db.add(new_record)
    db.commit()
    db.refresh(new_record)
    
    return jsonify({
        "success": True,
        "id": new_record.table_hash,
        "created_at": new_record.created_at.isoformat(),
        "updated_at": new_record.updated_at.isoformat()
    })

def transcribe_mp4(file_path, model_size="base"):
    """
    Transcribe MP4 file using Whisper

    Args:
        file_path (str): Path to MP4 file
        model_size (str): Whisper model size ('tiny', 'base', 'small', 'medium', 'large')

    Returns:
        str: Transcribed text
    """
    print(f"Loading Whisper model: {model_size}")
    model = whisper.load_model(model_size)

    print(f"Transcribing: {file_path}")
    result = model.transcribe(file_path)

    # Save transcription
    transcript_path = file_path.replace('.mp4', '_transcript.txt')
    with open(transcript_path, 'w', encoding='utf-8') as f:
        f.write(result["text"])

    print(f"Transcription saved: {transcript_path}")
    return result["text"]


"""
this is also ugly and will have to be reworked in tandum with 
generate_table_schema_and_json

"""
def process(line,schema):
    """
    Splits a string by commas and strips whitespace from each part.
    
    Args:
        line (str): The input string to split.
        
    Returns:
        list: A list of strings split by commas.
    """
    value = line.split(",")

    if schema[0][0]=="transcript":
        values=[part.strip() for part in line.split(",")]
        file=download_mp4(values[0])
        cloudsaved=_upload_to_r2(file)
        values[0]=cloudsaved
        transcipt=transcribe_mp4(file)
        transcipt=transcipt.replace("'", "")
        os.remove(file)
        values=[transcipt]+values+["desc"]
        return values
    else:
        return value+["desc"]

def process_transcription(path,jsondata):
    with open(path, "r", encoding="utf-8") as f:
        db = SessionLocal()
        record = db.query(Test).filter(Test.table_name == jsondata).first()
        exists = record is not None
        
        response = {"exists": exists}
        # Include table name if record is found
        if exists and record:
            table_name = record.table_name 
            schema = record.data 
        print(f"interting into  {table_name} from {schema}", flush=True)
        count=0
        for i, line in enumerate(f, start=1):
            if count!=0:
                processed = process(line,json.loads(schema))
                sqloutput=insert_into_table("db_path", table_name, json.loads(schema), processed)
                print("\n\n\n\n"+sqloutput+"\n\n\n\n")
                execute_insert(sqloutput)

                print(sqloutput+f" Processing line {i} from {path}: {line.strip()}" + " into "+jsondata, flush=True)
            count+=1



template_str = """
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Live Transcription</title>
  <style>
    body { font-family: Arial, Helvetica, sans-serif; max-width: 900px; margin: 40px auto; background: #f5f5f5; }
    .card { background: #fff; padding: 30px 40px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,.1); }
    h1 { text-align: center; }
    #output { white-space: pre-wrap; font-family: monospace; background: #000; color: #0f0; padding: 10px; border-radius: 6px; height: 350px; overflow-y: auto; margin-top: 20px; display: none; }
    button { background: #0069d9; color: #fff; border: none; padding: 12px 25px; border-radius: 4px; font-size: 16px; width: 100%; }
    button:disabled { background: #6c757d; }
  </style>
</head>
<body>
  <div class="card">
    <h1>Upload Data</h1>
    <form id="upload-form" enctype="multipart/form-data">
      <input type="file" id="file-input" name="file" accept=".csv" required> <br><br>
      <button id="btn">Start</button>
    </form>
    <div id="output"></div>
  </div>

<div class="modal-overlay" id="modalOverlay">
  <div class="modal">
    <h2>Upload Confirmation</h2>
    <p id="uploadMessage"></p>
    <button onclick="closeUploadConfirmation()">OK</button>
  </div>
</div>


<div class="modal-overlay" id="modalOverlayask">
  <div class="modal">
    <h2>Enter Table Name</h2>
    <input type="text" id="tableNameInput" placeholder="e.g. customer_data" />
    <div>
      <button id="okBtn">OK</button>
      <button class="cancel-btn" id="cancelBtn">Cancel</button>
    </div>
  </div>
</div>

  <style>
    body {
      font-family: Arial, sans-serif;
      background-color: #f4f4f4;
    }

    .modal-overlay {
      display: none;
      position: fixed;
      top: 0; 
      left: 0;
      width: 100%; 
      height: 100%;
      background: rgba(0, 0, 0, 0.5);
      z-index: 1000;
      justify-content: center;
      align-items: center;
    }

    .modal {
      background: #fff;
      padding: 20px 30px;
      border-radius: 8px;
      max-width: 400px;
      text-align: center;
      box-shadow: 0 4px 8px rgba(0,0,0,0.2);
      animation: fadeIn 0.3s ease-in-out;
    }

    .modal h2 {
      margin-bottom: 15px;
    }

    .modal p {
      margin-bottom: 20px;
    }

    .modal button {
      background: #007BFF;
      color: white;
      border: none;
      padding: 10px 20px;
      border-radius: 4px;
      cursor: pointer;
    }

    .modal button:hover {
      background: #0056b3;
    }

    @keyframes fadeIn {
      from { opacity: 0; transform: scale(0.8); }
      to { opacity: 1; transform: scale(1); }
    }
  </style>

  <style>
    body {
      font-family: Arial, sans-serif;
      background-color: #f4f4f4;
    }

    .modal-overlay {
      display: none;
      position: fixed;
      top: 0; left: 0;
      width: 100%; height: 100%;
      background: rgba(0,0,0,0.5);
      z-index: 1000;
      justify-content: center;
      align-items: center;
    }

    .modal {
      background: white;
      padding: 20px 30px;
      border-radius: 8px;
      max-width: 400px;
      width: 90%;
      box-shadow: 0 4px 8px rgba(0,0,0,0.2);
      animation: fadeIn 0.3s ease-in-out;
      text-align: center;
    }

    .modal h2 {
      margin-bottom: 15px;
    }

    .modal input[type="text"] {
      width: 90%;
      padding: 8px;
      margin-bottom: 20px;
      border: 1px solid #ccc;
      border-radius: 4px;
      font-size: 14px;
    }

    .modal button {
      background: #007BFF;
      color: white;
      border: none;
      padding: 10px 20px;
      border-radius: 4px;
      cursor: pointer;
      margin: 0 5px;
    }

    .modal button:hover {
      background: #0056b3;
    }

    .modal .cancel-btn {
      background: #6c757d;
    }
    .modal .cancel-btn:hover {
      background: #545b62;
    }

    @keyframes fadeIn {
      from { opacity: 0; transform: scale(0.8); }
      to { opacity: 1; transform: scale(1); }
    }
  </style>
</head>
<body>


<div class="modal-overlay" id="modalOverlay">
  <div class="modal">
    <h2>Enter Table Name</h2>
    <input type="text" id="tableNameInput" placeholder="e.g. customer_data" />
    <div>
      <button id="okBtn">OK</button>
      <button class="cancel-btn" id="cancelBtn">Cancel</button>
    </div>
  </div>
</div>

<script>

tableName_="";

function askForTableName(hash,firstLine) {
  return new Promise((resolve) => {
    const overlay = document.getElementById('modalOverlayask');
    const input = document.getElementById('tableNameInput');
    const okBtn = document.getElementById('okBtn');
    const cancelBtn = document.getElementById('cancelBtn');

    overlay.style.display = 'flex';
    input.value = '';
    input.focus();

    function close(value) {
      overlay.style.display = 'none';
      okBtn.removeEventListener('click', okHandler);
      cancelBtn.removeEventListener('click', cancelHandler);
      resolve(value);
    }

    function okHandler() {
      makeTable(input.value, hash, firstLine)
      console.log(input.value+" "+firstLine+" "+hash);


      close(input.value.trim() || null);
    }
    function cancelHandler() {
      close(null);
    }

    okBtn.addEventListener('click', okHandler);
    cancelBtn.addEventListener('click', cancelHandler);

    // Allow Enter/Escape keyboard shortcuts
    input.onkeydown = (e) => {
      if (e.key === 'Enter') okHandler();
      if (e.key === 'Escape') cancelHandler();
    };
  });
}




async function makeTable(tableName, hash, topline) {
  const url = '/make_table';
  
  const bodyData = {
    Table_Name: tableName,
    hash: hash,
    topline: topline
  };
  console.log("inhere");

  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(bodyData)
  });
    console.log(response);
  if (!response.ok) {
    throw new Error(`HTTP error! Status: ${response.status}`);
  }

  const result = await response.json();
  console.log(result);
  console.log('Server response:', result);
  alert(result)

}


function showUploadConfirmation(tableName) {
  document.getElementById('uploadMessage').textContent =
    `This file will be uploaded to "${tableName}"`;
    tableName_=tableName;
  document.getElementById('modalOverlay').style.display = 'flex';
}

function closeUploadConfirmation() {
  document.getElementById('modalOverlay').style.display = 'none';
}

async function checkTest(testValue,table_info) {
    try {
        const response = await fetch('/check_test', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                test: testValue,
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const result = await response.json();
        
        // Alert based on the exists property
        if (result.exists === true) {
            showUploadConfirmation(result.table_name);
        } else if (result.exists === false) {
            askForTableName(testValue,table_info)
        } else {
            alert('Unexpected response format');
        }

        return result;
        
    } catch (error) {
        console.error('Error:', error);
        alert('Error occurred: ' + error.message);
    }
}

document.getElementById('file-input').addEventListener('change', function() {
  const file = this.files[0];
  if (!file) return;

  const reader = new FileReader();
  reader.onload = async function(e) {
    // Get only the first line from the file
    const firstLine = e.target.result.split(/\\r?\\n/)[0];
    // Encode as Uint8Array
    const encoder = new TextEncoder();
    const data = encoder.encode(firstLine);
    // Compute SHA-256 hash
    const hashBuffer = await crypto.subtle.digest('SHA-256', data);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    // Convert to hex string
    const hashHex = hashArray.map(b => b.toString(16).padStart(2, '0')).join('');

    checkTest(hashHex,firstLine);

  };
  reader.readAsText(file);
});

const form   = document.getElementById('upload-form');
const output = document.getElementById('output');
const btn    = document.getElementById('btn');
form.addEventListener('submit', e => {
  e.preventDefault();
  const data = new FormData(form);
  data.append('tableName', tableName_); // Add your table name
  btn.disabled = true; btn.textContent = 'Running…';
  output.style.display = 'block'; output.textContent='';
  alert(tableName_)
  if (tableName_==""){
    alert("database it not loaded");
  }
  else{
    fetch('/upload', {method:'POST', body:data}).then(resp => {
        const reader   = resp.body.getReader();
        const decoder  = new TextDecoder();
        function read(){
          reader.read().then(({done,value}) => {
            if(done){ btn.disabled=false; btn.textContent='Start'; return; }
            output.textContent += decoder.decode(value);
            output.scrollTop = output.scrollHeight;
            read();
          });
        }
        read();
    });
  }


});


</script>

<script>



  const result = { table_name: 'customer_data' }; // example variable
  
  document.getElementById('showModalBtn').addEventListener('click', function() {
    document.getElementById('uploadMessage').textContent =
      `This file will be uploaded to "${result.table_name}"`;
    document.getElementById('modalOverlay').style.display = 'flex';
  });
  function closeModal() {
    document.getElementById('modalOverlay').style.display = 'none';
  }
</script>
</body>
</html>
"""



@app.route("/", methods=["GET"])
def upload_page():
    return render_template("upload.html")
    #return render_template_string(template_str)

@app.route("/upload", methods=["POST"])
def transcribe_route():
    if "file" not in request.files:
        return "No file part", 400
    f = request.files["file"]
    if not f.filename.lower().endswith(".csv"):
        return "CSV required", 400
    session_id = uuid.uuid4().hex
    csv_path = "/tmp/"+f"{session_id}.csv"
    f.save(csv_path)
    tableName=request.form.get('tableName')
    cap = OutputCapture()

    def worker():
        #try:
        with redirect_stdout(cap):

            process_transcription(str(csv_path),tableName)
        print("=== DONE ===", flush=True)
        return
        #except Exception as e:
            #print(f"❌ {e}", flush=True)

    threading.Thread(target=worker, daemon=True).start()

    def stream():
        last = time.time()
        while True:
            for ln in cap.pop_new_lines():
                yield ln
                last = time.time()
            if time.time() - last > 10:
                yield "⏳ still working\n"
                last = time.time()
            if not threading.active_count() > 1 and not cap._lines:
                break
            time.sleep(0.1)

    return Response(stream_with_context(stream()), mimetype="text/plain")

@app.route('/make_table', methods=['POST'])
def make_table():
    data = request.get_json()
    table_name = data.get('Table_Name')
    hash_value = data.get('hash')
    topline = data.get('topline')
    tableid = str(uuid.uuid1())
    tableid = re.sub("-", "", tableid)
    table_name=table_name+"_"+tableid
    sql=generate_table_schema_and_json(table_name,topline)
    print(sql,flush=True)
    output=execute_create_table(sql[0])
    insert_test(hash_value,table_name,json.dumps(sql[1]) )  
    return jsonify({
        "table_name": table_name,
        "hash": hash_value,
        "topline": topline,
        "tableid": tableid,
        "created": sql[0],
        "json": sql[1],
        "output":output
    })

@app.route('/check_test', methods=['POST'])
def check_test():
    """Check if test value matches a table_hash"""
    try:
        request_data = request.get_json()
        if not request_data:
            return jsonify({"error": "No JSON data provided"}), 400
        
        if 'test' not in request_data:
            return jsonify({"error": "test field is required"}), 400
        
        test_id = request_data['test']
        
        db = SessionLocal()
        try:
            record = db.query(Test).filter(Test.table_hash == test_id).first()
            exists = record is not None
            
            response = {"exists": exists}
            
            # Include table name if record is found
            if exists and record:
                response["table_name"] = record.table_name  # Adjust field name as needed
            
            return jsonify(response), 200
        
        except Exception as e:
            return jsonify({"error": str(e)}), 500
        finally:
            db.close()
    
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/health')
def health_check():
    return jsonify({
        "status": "healthy",
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=True)
