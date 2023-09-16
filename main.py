from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import openai
import mysql.connector

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# OpenAI API key
openai.api_key = "YOUR -API-KEY"

# MySQL connection setup
db_connection = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="company"
)
db_cursor = db_connection.cursor()

class UserInput(BaseModel):
    user_input: str

def generate_sql_query_with_openai(prompt):
    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=prompt,
        max_tokens=100,
    )
    return response.choices[0].text.strip()

def execute_sql_query(sql_query):
    try:
        db_cursor.execute(sql_query)
        query_result = db_cursor.fetchall()
        return query_result
    except mysql.connector.Error as err:
        print("MySQL Error:", err)
        return []

@app.get("/")
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/chatbot")
async def chatbot_interaction(data: UserInput):
    user_input = data.user_input

    try:
        # Fetch table descriptions and columns from the database schema
        db_cursor.execute("SHOW TABLES")
        tables = [table[0] for table in db_cursor.fetchall()]

        table_descriptions = {}
        for table in tables:
            db_cursor.execute(f"DESCRIBE {table}")
            columns = [column[0] for column in db_cursor.fetchall()]
            table_descriptions[table] = columns

        # Convert user input to SQL query using OpenAI
        openai_prompt = f"Convert the following user message into an SQL query:\nUser: {user_input}\nTable Descriptions: {table_descriptions}"
        sql_query = generate_sql_query_with_openai(openai_prompt)
        # Execute the SQL query and fetch the response
        query_result = execute_sql_query(sql_query)

        #changing the response for the question

        openai_prompt = f"Create a response for this user question with the result:\nUser: {user_input}\nresult : {query_result}"
        response_from_ai = generate_sql_query_with_openai(openai_prompt)

        if response_from_ai:
            response = f"{response_from_ai}"
        else:
            response = "Sorry, I couldn't find an answer to your question."

        return {"response": response}


    except Exception as e:
        print("Error:", e)
        return {"response": "An error occurred while processing the request."}
    

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
