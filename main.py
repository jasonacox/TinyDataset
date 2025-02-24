import os
import json
import sqlite3
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from llm_client import generate_qa

app = FastAPI()

# Set up templates for UI rendering
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# Initialize database
from database import insert_fact, insert_qa, get_qa, delete_qa, update_qa, export_jsonl, init_db, get_facts, get_qa_entry

# Delete the database file if it exists
if os.path.exists("qa_data.db"):
    os.remove("qa_data.db")
init_db()

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "facts": get_facts()})

@app.post("/generate/")
async def generate_questions(fact: str = Form(...)):
    fact_id = insert_fact(fact)
    qa_pairs = generate_qa(fact)
    # Insert Q&A pairs into the database
    for qa in qa_pairs:
        q = qa["question"]
        a = qa["answer"]
        insert_qa(fact_id, q, a)

    # Rebuild entire table from database
    qa_pairs = get_qa()
    # Generate the new rows of the table to be inserted into the UI
    qa_html = ""
    for qa in qa_pairs:
        print(f"QA: {qa}")
        qa_html += f"""
        <tr id="qa-{qa['id']}">
            <td>{qa['question']}</td>
            <td>{qa['answer']}</td>
            <td>
                <button class="action-btn edit-btn" 
                        hx-get="/edit_qa/{qa['id']}" 
                        hx-target="#qa-{qa['id']}" 
                        hx-swap="outerHTML">Edit</button>
                <button class="action-btn delete-btn" 
                        hx-delete="/delete_qa/{qa['id']}" 
                        hx-target="#qa-{qa['id']}" 
                        hx-swap="outerHTML">Delete</button>
            </td>
        </tr>
        """
    return HTMLResponse(qa_html)

@app.get("/export/")
async def export_data():
    r = export_jsonl()
    return r

@app.get("/get_qa/")
async def get_qa_data():
    qa_pairs = get_qa()
    print(f"QA pairs: {qa_pairs}")
    html = ""
    for qa in qa_pairs:
        html += f"""
        <tr id="qa-{qa['id']}">
            <td>{qa['question']}</td>
            <td>{qa['answer']}</td>
            <td>
                <button class="action-btn edit-btn" 
                        hx-get="/edit_qa/{qa['id']}" 
                        hx-target="#qa-{qa['id']}" 
                        hx-swap="outerHTML">Edit</button>
                <button class="action-btn delete-btn" 
                        hx-delete="/delete_qa/{qa['id']}" 
                        hx-target="#qa-{qa['id']}" 
                        hx-swap="outerHTML">Delete</button>
            </td>
        </tr>
        """
    return HTMLResponse(html)

@app.delete("/delete_qa/{qa_id}")
async def delete_qa_entry(qa_id: int):
    delete_qa(qa_id)
    return JSONResponse({"success": True})


@app.get("/edit_qa/{qa_id}")
async def edit_qa_entry(qa_id: int):
    qa = get_qa_entry(qa_id)
    return HTMLResponse(f"""
        <tr id="qa-{qa_id}">
            <form hx-put="/update_qa/{qa_id}" hx-target="#qa-{qa_id}" hx-swap="outerHTML">
                <td><input type="text" name="question" value="{qa['question']}" required></td>
                <td><input type="text" name="answer" value="{qa['answer']}" required></td>
                <td>
                    <button type="submit" class="action-btn">Save</button>
                </td>
            </form>
        </tr>
    """)

@app.put("/update_qa/{qa_id}")
async def update_qa_entry(qa_id: int, question: str = Form(...), answer: str = Form(...)):
    update_qa(qa_id, question, answer)
    return get_qa_data()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
