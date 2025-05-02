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
    
    # Fetch bonus criteria
    cursor.execute("SELECT * FROM bonus_criteria LIMIT 1")
    bonus_criteria = cursor.fetchone()
    orders_required = bonus_criteria['orders_required']
    bonus_amount = bonus_criteria['bonus_amount']

    if request.method == 'POST':
        # Handle editing bonus criteria
        if 'edit_bonus_criteria' in request.form:
            orders_required = int(request.form['orders_required'])
            bonus_amount = int(request.form['bonus_amount'])
            cursor.execute("""
                UPDATE bonus_criteria
                SET orders_required = %s, bonus_amount = %s
            """, (orders_required, bonus_amount))
            conn.commit()

        # Handle adding a new restaurant
        elif 'add_restaurant' in request.form:
            restaurant_name = request.form['restaurant_name']
            restaurant_address = request.form['restaurant_address']
            cursor.execute("""
                INSERT INTO restaurants (name, address) VALUES (%s, %s)
            """, (restaurant_name, restaurant_address))
            conn.commit()

        # Handle editing a restaurant
        elif 'edit_restaurant' in request.form:
            restaurant_id = request.form['restaurant_id']
            restaurant_name = request.form['restaurant_name']
            restaurant_address = request.form['restaurant_address']
            cursor.execute("""
                UPDATE restaurants
                SET name = %s, address = %s
                WHERE id = %s
            """, (restaurant_name, restaurant_address, restaurant_id))
            conn.commit()

        # Handle deleting a restaurant
        elif 'delete_restaurant' in request.form:
            restaurant_id = request.form['restaurant_id']
            cursor.execute("DELETE FROM restaurants WHERE id = %s", (restaurant_id,))
            conn.commit()

        # Handle adding a new menu item
        elif 'add_menu_item' in request.form:
            restaurant_id = request.form['restaurant_id']
            name = request.form['name']
            price = request.form['price']
            category = request.form['category']
            cursor.execute("""
                INSERT INTO menu (restaurant_id, name, price, category)
                VALUES (%s, %s, %s, %s)
            """, (restaurant_id, name, price, category))
            conn.commit()

        # Handle editing a menu item
        elif 'edit_menu_item' in request.form:
            menu_item_id = request.form['menu_item_id']
            name = request.form['name']
            price = request.form['price']
            category = request.form['category']
            cursor.execute("""
                UPDATE menu
                SET name = %s, price = %s, category = %s
                WHERE id = %s
            """, (name, price, category, menu_item_id))
            conn.commit()

        # Handle deleting a menu item
        elif 'delete_menu_item' in request.form:
            menu_item_id = request.form['menu_item_id']
            cursor.execute("DELETE FROM menu WHERE id = %s", (menu_item_id,))
            conn.commit()

        # Handle employee revenue query
        elif 'employee_revenue_query' in request.form:
            start_date = request.form['start_date']
            end_date = request.form['end_date']
            cursor.execute(f"""
                SELECT u.username, COUNT(f.id) AS completed_orders,
                       SUM(o.total_price) AS total_revenue,
                       FLOOR(COUNT(f.id) / {orders_required}) * {bonus_amount} AS bonus
                FROM finished_orders f
                JOIN orders o ON f.order_id = o.id
                JOIN users u ON f.employee_id = u.id
                WHERE f.finished_at BETWEEN %s AND %s
                AND u.role = 'employee'
                GROUP BY u.username
            """, (start_date, end_date))
            employee_revenue = cursor.fetchall()

        # Handle company revenue query
        elif 'revenue_query' in request.form:
            start_date = request.form['start_date']
            end_date = request.form['end_date']
            cursor.execute(
                "SELECT SUM(total_price) AS revenue FROM orders WHERE created_at BETWEEN %s AND %s",
                (start_date, end_date)
            )
            result = cursor.fetchone()
            revenue = result['revenue'] if result['revenue'] else 0

        # Handle employee revenue query
        elif 'employee_revenue_query' in request.form:
            start_date = request.form['start_date']
            end_date = request.form['end_date']
            cursor.execute("""
                SELECT f.delivery_date, e.username, SUM(o.total_price) AS employee_revenue
                FROM finished_orders f
                JOIN orders o ON f.order_id = o.id
                JOIN employees e ON f.employee_id = e.id
                WHERE f.delivery_date BETWEEN %s AND %s
                GROUP BY e.username
            """, (start_date, end_date))
            employee_revenue = cursor.fetchall()

    # Fetch restaurants and their menus
    cursor.execute("SELECT * FROM restaurants")
    restaurants = cursor.fetchall()
    for restaurant in restaurants:
        cursor.execute("SELECT * FROM menu WHERE restaurant_id = %s", (restaurant['id'],))
        restaurant['menu'] = cursor.fetchall()

    # Fetch menu items for display
    edit_id = request.args.get('edit', type=int)
    cursor.execute("SELECT * FROM menu")
    items = cursor.fetchall()

    conn.close()

    return render_template(
        'admin.html',
        restaurants=restaurants,
        items=items,
        username=session['username'],
        edit_id=edit_id,
        revenue=revenue,
        start_date=start_date,
        end_date=end_date,
        employee_revenue=employee_revenue,
        orders_required=orders_required,
        bonus_amount=bonus_amount
    )

@app.route("/accept_order/<int:order_id>", methods=["POST"])
def accept_order(order_id):
    if session.get("role") != "employee":
        return redirect(url_for("login"))

    employee_id = session.get("user_id")
    conn = get_db_connection()
    cursor = conn.cursor()

    # Проверка дали вече е приета
    cursor.execute("SELECT accepted_by FROM orders WHERE id = %s", (order_id,))
    result = cursor.fetchone()
    if result and result[0] is not None:
        conn.close()
        return redirect(url_for("employee_dashboard"))

    # Приемане на поръчката
    cursor.execute("UPDATE orders SET accepted_by = %s WHERE id = %s", (employee_id, order_id))
    conn.commit()

    cursor.close()
    conn.close()
    return redirect(url_for("employee_dashboard"))

@app.route('/delete_menu_item/<int:item_id>', methods=['POST'])
def delete_menu_item(item_id):
    if 'role' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM menu WHERE id = %s", (item_id,))
    conn.commit()
    conn.close()

    return redirect(url_for('admin'))

# Изход от системата
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
