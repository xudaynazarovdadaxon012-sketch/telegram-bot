import sqlite3

def init_db():
    conn = sqlite3.connect("quiz_bot.db")
    cursor = conn.cursor()
    
    # Savollar jadvalini yaratish
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question TEXT NOT NULL,
            option_1 TEXT NOT NULL,
            option_2 TEXT NOT NULL,
            option_3 TEXT NOT NULL,
            option_4 TEXT NOT NULL,
            correct_option INTEGER NOT NULL
        )
    """)
    
    # Bazada savollar bo'lmasa, boshlang'ich dasturlash savollarini qo'shamiz
    cursor.execute("SELECT COUNT(*) FROM questions")
    if cursor.fetchone()[0] == 0:
        sample_questions = [
            ("Python'da funksiya qaysi kalit so'z yordamida e'lon qilinadi?", "function", "def", "fun", "define", 2),
            ("HTML'da sarlavha (heading) uchun eng katta teg qaysi?", "<h6>", "<head>", "<h1>", "<header>", 3),
            ("Python ma'lumotlar turiga qaysi biri kirmaydi?", "int", "float", "real", "str", 3),
            ("Veb-sahifaning tuzilmasini yaratish uchun qaysi til ishlatiladi?", "Python", "CSS", "HTML", "SQL", 3)
        ]
        cursor.executemany("""
            INSERT INTO questions (question, option_1, option_2, option_3, option_4, correct_option)
            VALUES (?, ?, ?, ?, ?, ?)
        """, sample_questions)
        conn.commit()
        
    conn.close()

if __name__ == "__main__":
    init_db()
