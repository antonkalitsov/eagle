from flask import Flask, render_template, request, redirect, url_for, session
import mysql.connector
from flask_session import Session

# Инициализация на Flask приложението
app = Flask(__name__)
app.secret_key = 'supersecret'  # Тайна ключова дума за сесиите
app.config['SESSION_TYPE'] = 'filesystem'  # Тип на сесиите
Session(app)  # Активиране на сесиите

# Функция за връзка с базата данни
def get_db_connection():
    return mysql.connector.connect(
        host='localhost',
        user='root',
        password='your_password',  # Парола за базата данни
        database='apprestaurant'  # Име на базата данни
    )

# Функция за извличане на менюто от базата данни
def get_menu_from_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name, price FROM menu")  # Извличане на име и цена на елементите от менюто
    items = cursor.fetchall()
    conn.close()
    return dict(items)

# Функция за запис на поръчка в базата данни
def save_order_to_db(order_items, total_price, restaurant_id, client_address):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Записване на поръчката в таблицата orders
    cursor.execute(
        "INSERT INTO orders (total_price, restaurant_id, client_address) VALUES (%s, %s, %s)",
        (total_price, restaurant_id, client_address)
    )
    order_id = cursor.lastrowid

    # Записване на всеки елемент от поръчката в таблицата order_items
    for item_name, details in order_items.items():
        cursor.execute(
            "INSERT INTO order_items (order_id, item_name, quantity, price) VALUES (%s, %s, %s, %s)",
            (order_id, item_name, details['quantity'], details['price'])
        )

    conn.commit()
    conn.close()

# Регистрация на нов потребител
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()

        if user:
            return render_template('register.html', error="Username already exists!")  # Грешка при дублиране на потребителско име

        # Записване на нов потребител в базата данни
        cursor.execute("INSERT INTO users (username, password, role) VALUES (%s, %s, %s)",
                       (username, password, role))
        conn.commit()
        conn.close()

        return redirect(url_for('login'))  # Пренасочване към страницата за вход

    return render_template('register.html')

# Страница за вход
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE username = %s AND role = %s", (username, role))
        user = cursor.fetchone()
        conn.close()

        if user and user['password'] == password:
            # Запазване на информацията за потребителя в сесията
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']

            # Пренасочване според ролята на потребителя
            if role == 'client':
                return redirect(url_for('home'))
            elif role == 'employee':
                return redirect(url_for('employee_dashboard'))
            elif role == 'admin':
                return redirect(url_for('admin'))
        else:
            return render_template('login.html', error="Invalid credentials or role")  # Грешка при невалидни данни

    return render_template('login.html')

# Начална страница за клиента
@app.route('/index')
def home():
    if 'role' in session and session['role'] == 'client':
        return render_template('index.html')
    return redirect(url_for('login'))

# Страница за служител
@app.route('/employee')
def employee_dashboard():
    if 'role' not in session or session['role'] != 'employee':
        return redirect(url_for('login'))

    employee_id = session.get('user_id')

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Извличане на неприети поръчки
    cursor.execute("""
        SELECT o.*, r.address AS restaurant_address, o.client_address
        FROM orders o
        JOIN restaurants r ON o.restaurant_id = r.id
        WHERE o.accepted_by IS NULL
        AND o.id NOT IN (SELECT order_id FROM finished_orders)
    """)
    unaccepted_orders = cursor.fetchall()

    # Извличане на приетите поръчки на служителя
    cursor.execute("""
        SELECT o.*, r.address AS restaurant_address, o.client_address
        FROM orders o
        JOIN restaurants r ON o.restaurant_id = r.id
        WHERE o.accepted_by = %s
        AND o.id NOT IN (SELECT order_id FROM finished_orders)
    """, (employee_id,))
    my_orders = cursor.fetchall()

    conn.close()

    return render_template('employee.html',
                           unaccepted_orders=unaccepted_orders,
                           my_orders=my_orders,
                           username=session.get('username'))

# Завършване на поръчка
@app.route('/complete_order', methods=['POST'])
def complete_order():
    if 'role' not in session or session['role'] != 'employee':
        return redirect(url_for('login'))

    order_id = request.form['order_id']
    employee_id = session['user_id']

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO finished_orders (order_id, employee_id)
        VALUES (%s, %s)
    """, (order_id, employee_id))
    conn.commit()
    conn.close()

    return redirect(url_for('employee_dashboard'))

# Меню и поръчка
@app.route('/menu', methods=['GET', 'POST'])
def display_menu():
    if 'role' not in session or session['role'] != 'client':
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Извличане на всички ресторанти
    cursor.execute("SELECT * FROM restaurants")
    restaurants = cursor.fetchall()

    # Извличане на менюто за всеки ресторант
    for restaurant in restaurants:
        cursor.execute("SELECT * FROM menu WHERE restaurant_id = %s", (restaurant['id'],))
        restaurant['menu'] = cursor.fetchall()

    # Извличане на уникални категории
    cursor.execute("SELECT DISTINCT category FROM menu")
    categories = [row['category'] for row in cursor.fetchall()]

    # Филтриране по категория
    selected_category = request.args.get('category')
    if selected_category:
        for restaurant in restaurants:
            restaurant['menu'] = [item for item in restaurant['menu'] if item['category'] == selected_category]

    if request.method == 'POST':
        order_items = {}
        total_price = 0
        restaurant_id = request.form.get('restaurant_id')
        client_address = request.form.get('client_address')

        # Обработка на поръчката
        for restaurant in restaurants:
            for item in restaurant['menu']:
                name = item['name']
                price = item['price']
                quantity = int(request.form.get(f'quantity_{name}', 0))
                if quantity > 0:
                    order_items[name] = {'quantity': quantity, 'price': price}
                    total_price += quantity * price

        save_order_to_db(order_items, total_price, restaurant_id, client_address)

        return render_template('menu.html', restaurants=restaurants, categories=categories, selected_category=selected_category, total=total_price)

    return render_template('menu.html', restaurants=restaurants, categories=categories, selected_category=selected_category)

# Страница за администратор
@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if 'role' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    revenue = None
    start_date = None
    end_date = None
    employee_revenue = None

    # Извличане на критерии за бонуси
    cursor.execute("SELECT * FROM bonus_criteria LIMIT 1")
    bonus_criteria = cursor.fetchone()
    orders_required = bonus_criteria['orders_required']
    bonus_amount = bonus_criteria['bonus_amount']

    if request.method == 'POST':
        # Обработка на редактиране на критерии за бонуси
        if 'edit_bonus_criteria' in request.form:
            orders_required = int(request.form['orders_required'])
            bonus_amount = int(request.form['bonus_amount'])
            cursor.execute("""
                UPDATE bonus_criteria
                SET orders_required = %s, bonus_amount = %s
            """, (orders_required, bonus_amount))
            conn.commit()

    conn.close()
    return render_template('admin.html', orders_required=orders_required, bonus_amount=bonus_amount)

# Изход от системата
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
