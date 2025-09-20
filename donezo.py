import sqlite3
import datetime
import time
import threading
import speech_recognition as sr
from twilio.rest import Client


# ================= Database Setup =================
def init_db():
    conn = sqlite3.connect("tasks.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task TEXT NOT NULL,
            deadline TEXT NOT NULL,
            phone TEXT NOT NULL,
            done INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()

# ================= Add Task =================
def add_task(task, deadline, phone):
    conn = sqlite3.connect("tasks.db")
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO tasks (task, deadline, phone) VALUES (?, ?, ?)",
        (task, deadline, phone)
    )
    conn.commit()
    conn.close()
    print(f"✅ Task Added: {task} at {deadline}")

# ================= View Tasks =================
def view_tasks():
    conn = sqlite3.connect("tasks.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tasks WHERE done=0")
    rows = cursor.fetchall()
    conn.close()
    print("\n📋 Pending Tasks:")
    for row in rows:
        print(f"ID: {row[0]}, Task: {row[1]}, Deadline: {row[2]}, Phone: {row[3]}")

# ================= Voice Input =================
def voice_input():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("🎤 Say your task...")
        audio = recognizer.listen(source)
        try:
            task = recognizer.recognize_google(audio)
            print("You said:", task)
            return task
        except sr.UnknownValueError:
            print("❌ Could not understand audio")
            return None

# ================= Twilio SMS =================
def send_sms(phone, task):
    # Use your own Twilio credentials
    account_sid = "TWILIO_SID"
    auth_token = "TWILIO_AUTH_TOKEN"
    from_number = "TWILIO_PHONE"

    client = Client(account_sid, auth_token)
    try:
        message = client.messages.create(
            body=f"🔔 Reminder: {task}",
            from_=from_number,
            to=phone
        )
        print(f"📨 SMS sent to {phone}: {task}")
    except Exception as e:
        print(f"❌ Failed to send SMS to {phone}: {e}")

# ================= Reminder Checker =================
def reminder_checker():
    while True:
        conn = sqlite3.connect("tasks.db")
        cursor = conn.cursor()
        now = datetime.datetime.now()
        cursor.execute("SELECT id, task, deadline, phone FROM tasks WHERE done=0")
        rows = cursor.fetchall()

        for row in rows:
            task_id, task, deadline_str, phone = row
            try:
                task_deadline = datetime.datetime.strptime(deadline_str, "%Y-%m-%d %H:%M")
            except ValueError:
                print(f"❌ Invalid date format for task '{task}'")
                continue

            # Send SMS if deadline passed (missed or due now)
            if task_deadline <= now:
                send_sms(phone, task)
                cursor.execute("UPDATE tasks SET done=1 WHERE id=?", (task_id,))

        conn.commit()
        conn.close()
        time.sleep(5)  # Check twice a minute4
# ================= Main App =================
def main():
    init_db()
    threading.Thread(target=reminder_checker, daemon=True).start()

    while True:
        print("\n=== ✅ DONEZO To-Do List ===")
        print("1. Add Task (Manual)")
        print("2. Add Task (Voice)")
        print("3. View Tasks")
        print("4. Exit")

        choice = input("Enter choice: ")

        if choice == "1":
            task = input("Enter task: ")
            deadline_input = input("Enter deadline (YYYY-MM-DD HH:MM): ")
            phone = input("Enter Verified Phone number: ")
            add_task(task, deadline_input, phone)

        elif choice == "2":
            task = voice_input()
            if task:
                deadline_input = input("Enter deadline (YYYY-MM-DD HH:MM): ")
                phone = input("Enter Verified phone number: ")
                add_task(task, deadline_input, phone)

        elif choice == "3":
            view_tasks()

        elif choice == "4":
            print("👋 Exiting Donezo...")
            break
        else:
            print("❌ Invalid choice. Try again.")

if __name__ == "__main__":
    main()
