from flask import Flask, render_template, request, redirect, url_for, session
from sqlalchemy import Column, Integer, String, Numeric, create_engine, text, Table, MetaData, select, engine, and_

app = Flask(__name__)
app.debug = True
app.secret_key = 'Budders23!'

# connection string is in the format mysql://Root:Budders23!@server/boatdb
connection = "mysql://root:Budders23!@localhost/final170"
engine = create_engine(connection, echo=True)
conn = engine.connect()


def h(str):
    alph = "abcdefghijklmnopqrstuvwxyz"
    sum = 0
    for char in str:
        sum += alph.find(char) + 1
    return sum


@app.route('/')
def index():
    return render_template("index.html")


@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        if request.form['password'] == 'Admin1':
            password = request.form['password']
        else:
            password = request.form['password']
            password = h(password)
        query = text("SELECT * FROM accounts170 WHERE email = :email AND password = :password")
        params = {"email": email, "password": password}
        result = conn.execute(query, params)
        user = result.fetchone()
        if user is None:
            return render_template('index.html')
        else:
            session['id'] = user[0]
            session['first_name'] = user[1]
            session['last_name'] = user[2]
            session['email'] = user[5]
            session['type'] = user[8]
            session['balance'] = user[10]
            session['ssn'] = user[3]
            session['Address'] = user[6]
            if user[8] == 'Admin':
                return redirect(url_for('admin'))
            elif user[9] == 'pending':
                return render_template('index.html')
            else:
                acc = conn.execute(text("SELECT id FROM accounts170"))
                return redirect(url_for('viewTransactions', acc=acc))
    else:
        return render_template('index.html')


@app.route('/admin')
def admin():
    approved_accounts = conn.execute(text("SELECT * FROM accounts170 WHERE status = 'approved'")).fetchall()

    approved_transactions = conn.execute(text("SELECT * FROM transactions170 WHERE status = 'approved'")).fetchall()

    pending_accounts = conn.execute(text("SELECT * FROM accounts170 WHERE status = 'pending'")).fetchall()

    pending_transactions = conn.execute(text("SELECT * FROM transactions170 WHERE status = 'pending'")).fetchall()

    return render_template('admin.html', approved_accounts=approved_accounts, approved_transactions=approved_transactions,
                           pending_accounts=pending_accounts, pending_transactions=pending_transactions)


@app.route('/approve_account/<int:id>', methods=['POST'])
def approve_account(id):
    action = request.form['action']
    if action == 'approve':
        conn.execute(text("UPDATE accounts170 SET status = 'approved' WHERE id = :id"), {'id': id})
    elif action == 'deny':
        conn.execute(text("DELETE FROM accounts170 WHERE id = :id"), {'id': id})
    conn.commit()
    return redirect(url_for('admin'))


@app.route('/approve_transaction/<int:id>', methods=['POST'])
def approve_transaction(id):
    action = request.form['action']
    if action == 'approve':
        conn.execute(text("UPDATE transactions170 SET status = 'approved' WHERE id = :id"), {'id': id})
    elif action == 'deny':
        conn.execute(text("DELETE FROM transactions170 WHERE id = :id"), {'id': id})
    conn.commit()
    return redirect(url_for('admin'))


@app.route('/register', methods=['GET'])
def register():
    return render_template('register.html')


@app.route('/add_account', methods=['POST'])
def add_account():
    max_id_query = text("SELECT MAX(id) FROM accounts170")
    max_id = conn.execute(max_id_query).fetchone()[0]
    new_id = max_id + 1 if max_id is not None else 1

    first_name = request.form['first_name']
    last_name = request.form['last_name']
    ssn = request.form['ssn']
    phone_number = request.form['phone_number']
    email = request.form['email']
    address = request.form['address']
    if request.form == 'Admin1':
        password = request.form['password']
    else:
        password = request.form['password']
        password = h(password)
    type = 'customer'
    status = 'pending'
    balance = '0'

    query = text("INSERT INTO accounts170 (id, first_name, last_name, ssn, phone_number, email, address,"
                 " password, type, status, balance)"
                 " VALUES (:id, :first_name, :last_name, :ssn, :phone_number, :email, :address, :password, :type,"
                 " :status, :balance)")
    params = {"id": new_id, "first_name": first_name, "last_name": last_name, "ssn": ssn, "phone_number": phone_number,
              "email": email, "address": address, "password": password, "type": type, "status": status, "balance": balance}
    conn.execute(query, params)
    conn.commit()

    return render_template('index.html')


@app.route('/get_accounts')
def get_accounts():
    query = text("SELECT first_name, last_name, phone_number, email FROM accounts170 WHERE status != 'pending'")
    result = conn.execute(query)
    accounts = []
    for row in result:
        accounts.append(row)
    return render_template('accounts.html', accounts=accounts)


@app.route('/transactions')
def transactions():
    query = text("SELECT * FROM transactions WHERE status = 'approved'")
    result = conn.execute(query)
    transactions = result.fetchall()
    return render_template('admin.html', transactions=transactions)


@app.route('/acctransactions')
def viewTransactions():
    query = text("SELECT * FROM transactions170 WHERE id = 'session.id'")
    result = conn.execute(query)
    acctransactions = result.fetchall()
    return render_template('accpage.html', acctransactions=acctransactions)


@app.route('/deposit', methods=['POST'])
def deposit():
    amount = float(request.form['amount'])
    user_id = session.get('id')
    status = 'approved'
    query = text("SELECT balance FROM accounts170 WHERE id = :user_id")
    params = {'user_id': user_id}
    result = conn.execute(query, params).fetchone()
    balance = result[0]
    new_balance = balance + amount
    conn.execute(text("INSERT INTO transactions170 (id, balance, amount, status)"
                      " VALUES (:user_id, :balance, :amount, :status)"),
                 {'user_id': user_id, 'balance': balance, 'amount': amount, 'status': status})
    conn.execute(text("UPDATE accounts170 SET balance = :new_balance WHERE id = :user_id"), {'new_balance': new_balance, 'user_id': user_id})
    conn.commit()
    session['balance'] = new_balance
    return redirect(url_for('viewTransactions'))


@app.route("/add_transaction", methods=["POST"])
def add_transaction():
    recipient_id = request.form["acc-number"]
    amount = float(request.form["amount"])

    query = text("SELECT balance FROM accounts170 WHERE id = :id")
    params = {"id": recipient_id}
    result = conn.execute(query, params).fetchone()
    if result is None:
        return "Recipient account does not exist"

    query = text("SELECT balance FROM accounts170 WHERE id = :id")
    params = {"id": session["id"]}
    result = conn.execute(query, params).fetchone()
    if result is None:
        return "Sender account does not exist"
    sender_balance = result[0]
    if sender_balance < amount:
        return "Insufficient balance"

    new_sender_balance = sender_balance - amount
    query = text("UPDATE accounts170 SET balance = :balance WHERE id = :id")
    params = {"id": session["id"], "balance": new_sender_balance}
    conn.execute(query, params)

    query = text("SELECT balance FROM accounts170 WHERE id = :id")
    params = {"id": recipient_id}
    result = conn.execute(query, params).fetchone()
    recipient_balance = result[0]
    new_recipient_balance = recipient_balance + amount
    query = text("UPDATE accounts170 SET balance = :balance WHERE id = :id")
    params = {"id": recipient_id, "balance": new_recipient_balance}
    conn.execute(query, params)

    query = text("INSERT INTO transactions170 (id, balance, amount, status) VALUES (:id, :balance, :amount, 'approved')")
    params = {"id": session["id"], "balance": new_sender_balance, "amount": -amount}
    conn.execute(query, params)

    query = text("INSERT INTO transactions170 (id, balance, amount, status) VALUES (:id, :balance, :amount, 'approved')")
    params = {"id": recipient_id, "balance": new_recipient_balance, "amount": amount}
    conn.execute(query, params)

    conn.commit()
    return render_template('accpage.html', balance=new_sender_balance)


if __name__ == '__main__':
    app.run(debug=True)

