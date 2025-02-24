import sqlite3
import json

DB_FILE = "qa_data.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS facts (id INTEGER PRIMARY KEY, fact TEXT UNIQUE)")
    cursor.execute("CREATE TABLE IF NOT EXISTS qa_pairs (id INTEGER PRIMARY KEY, fact_id INTEGER, question TEXT, answer TEXT, UNIQUE(fact_id, question))")
    conn.commit()
    conn.close()

def insert_fact(fact):
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO facts (fact) VALUES (?)", (fact,))
        conn.commit()
        fact_id = cursor.lastrowid
        return fact_id
    except sqlite3.IntegrityError:
        # Fact already exists get the id
        cursor.execute("SELECT id FROM facts WHERE fact=?", (fact,))
        fact_id = cursor.fetchone()[0]
        return fact_id
    finally:
        conn.close()

def get_facts():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT fact FROM facts")
    facts = [row[0] for row in cursor.fetchall()]
    conn.close()
    return facts

def insert_qa(fact_id, question, answer):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    print(f"Inserting: {fact_id} - {question} - {answer}")
    cursor.execute("INSERT OR IGNORE INTO qa_pairs (fact_id, question, answer) VALUES (?, ?, ?)", (fact_id, question, answer))
    conn.commit()
    conn.close()

def get_qa():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    # return id, fact, question, answer
    cursor.execute("SELECT qa_pairs.id, facts.fact, qa_pairs.question, qa_pairs.answer FROM qa_pairs JOIN facts ON qa_pairs.fact_id = facts.id")
    qa_pairs = [{"id": row[0], "fact": row[1], "question": row[2], "answer": row[3]} for row in cursor.fetchall()]
    conn.close()
    return qa_pairs

def export_jsonl():
    filename = "qa_data.jsonl"
    # return just question and answer from database
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT question, answer FROM qa_pairs")
    qa_pairs = [{"question": row[0], "answer": row[1]} for row in cursor.fetchall()]
    conn.close()
    with open(filename, "w") as f:
        for qa in qa_pairs:
            f.write(json.dumps(qa) + "\n")
    return qa_pairs

def delete_qa(qa_id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM qa_pairs WHERE id=?", (qa_id,))
    conn.commit()
    conn.close()

def get_qa_entry(qa_id):
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT question, answer FROM qa_pairs WHERE id=?", (qa_id,))
        row = cursor.fetchone()
        if row:
            return {"question": row[0], "answer": row[1]}
        else:
            return {"error": "QA pair not found"}

def update_qa(qa_id, question, answer):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("UPDATE qa_pairs SET question=?, answer=? WHERE id=?", (question, answer, qa_id))
    conn.commit()
    conn.close()
