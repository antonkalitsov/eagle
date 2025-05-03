
### **README: Instructions to Set Up and Run the Application**

#### **1. Prerequisites**
Before running the application, ensure the following software is installed on your PC:
- **Python 3.10 or higher**: [Download Python](https://www.python.org/downloads/)
- **MySQL Server**: [Download MySQL](https://dev.mysql.com/downloads/)
- **pip** (Python package manager): Comes pre-installed with Python.
- **MySQL Connector for Python**: Installed via pip.

---

#### **2. Clone or Copy the Project**
1. Copy the project folder to your PC.
2. Ensure the folder structure is intact, and all files (e.g., app.py, templates, static files) are present.

---

#### **3. Set Up the Database**
1. Open MySQL Workbench or any MySQL client.
2. Create a new database:
   ```sql
   CREATE DATABASE apprestaurant;
   ```
3. Import the database schema:
   - Locate the SQL file (e.g., apprestaurant.sql) in the project folder.
   - Run the SQL script to create the necessary tables:
     ```sql
     USE apprestaurant;
     SOURCE path_to_sql_file/apprestaurant.sql;
     ```
4. Ensure the database contains the following tables:
   - `users`
   - `restaurants`
   - `menu`
   - `orders`
   - `order_items`
   - `finished_orders`
   - `bonus_criteria`

---

#### **4. Configure the Application**
1. Open the app.py file.
2. Update the database connection details in the `get_db_connection` function:
   ```python
   def get_db_connection():
       return mysql.connector.connect(
           host='localhost',  # Change if your MySQL server is on a different host
           user='root',       # Replace with your MySQL username
           password='your_password',  # Replace with your MySQL password
           database='apprestaurant'  # Ensure this matches the database name
       )
   ```

---

#### **5. Install Required Python Packages**
1. Open a terminal or command prompt.
2. Navigate to the project folder.
3. Install the required Python packages:
   ```bash
   pip install flask flask-session mysql-connector-python
   ```

---

#### **6. Run the Application**
1. In the terminal, navigate to the project folder.
2. Start the Flask application:
   ```bash
   python app.py
   ```
3. The application will start on `http://127.0.0.1:5000/` by default.

---

#### **7. Access the Application**
1. Open a web browser and go to:
   ```
   http://127.0.0.1:5000/
   ```
2. Use the following roles to log in:
   - **Admin**: Manage restaurants, menu items, and view reports.
   - **Employee**: Accept and complete orders.
   - **Client**: Browse menus and place orders.

---

#### **8. Default Credentials (Optional)**
If the database includes default users, use the following credentials:
- **Admin**:
  - Username: `admin`
  - Password: `admin123`
  - Role: `admin`
- **Employee**:
  - Username: `employee1`
  - Password: `employee123`
  - Role: `employee`
- **Client**:
  - Username: `client1`
  - Password: `client123`
  - Role: client

---

#### **9. Troubleshooting**
- **Error: Missing Python Packages**:
  - Ensure all required packages are installed using `pip install`.
- **Error: Database Connection**:
  - Verify the database credentials in app.py.
  - Ensure the MySQL server is running.
- **Error: Port Already in Use**:
  - Stop any other application using port 5000 or run Flask on a different port:
    ```bash
    python app.py --port=5001
    ```

---

#### **10. Additional Notes**
- To deploy the application in a production environment, use a WSGI server like **Gunicorn** or **uWSGI** with **Nginx**.
- For real-time notifications, consider integrating **Flask-SocketIO**.

---

Save this content as `readme.txt` in the root folder of your project. Let me know if you need further assistance! 😊