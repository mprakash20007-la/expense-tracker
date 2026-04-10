from flask import Flask, render_template, request, redirect
import sqlite3
import requests

app = Flask(__name__)

# 🌍 Get live rates (base INR)
def get_rates():
    try:
        url = "https://api.exchangerate-api.com/v4/latest/INR"
        res = requests.get(url)
        data = res.json()
        return data["rates"]
    except:
        return {"INR":1, "USD":0.012, "EUR":0.011, "GBP":0.0095, "JPY":1.8}

# 🗄️ DB setup
def init_db():
    conn = sqlite3.connect('expenses.db')
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            amount REAL,
            category TEXT,
            currency TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

@app.route('/', methods=['GET','POST'])
def index():
    conn = sqlite3.connect('expenses.db')
    cur = conn.cursor()

    # ➕ Add
    if request.method == 'POST':
        amount = float(request.form['amount'])
        category = request.form['category']
        currency = request.form['currency']

        cur.execute(
            "INSERT INTO expenses (amount, category, currency) VALUES (?, ?, ?)",
            (amount, category, currency)
        )
        conn.commit()
        return redirect('/')

    cur.execute("SELECT * FROM expenses")
    data = cur.fetchall()

    rates = get_rates()

    # 💰 Total in INR
    total = 0
    for row in data:
        amount = row[1]
        currency = row[3]

        if currency == "INR":
            total += amount
        else:
            total += amount / rates.get(currency, 1)

    # 📊 Chart data
    category_data = {}
    for row in data:
        category = row[2]
        amount = row[1]
        currency = row[3]

        if currency == "INR":
            value = amount
        else:
            value = amount / rates.get(currency, 1)

        category_data[category] = category_data.get(category, 0) + value

    conn.close()

    return render_template(
        'index.html',
        expenses=data,
        total=round(total,2),
        rates=rates,
        category_data=category_data
    )

@app.route('/delete/<int:id>')
def delete(id):
    conn = sqlite3.connect('expenses.db')
    cur = conn.cursor()
    cur.execute("DELETE FROM expenses WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)