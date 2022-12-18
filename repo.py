from mysql.connector import connect, Error


class Repo:
    ROLE_MASTER = 1
    ROLE_ADMINISTRATOR = 2

    def __init__(self, host, user, password, db):
        self.connection = None
        self.cursor = None
        self.connect_to_db(host, user, password, db)
        if self.connection is not None and self.cursor is not None:
            self.select_db(db)
            self.get_tables = lambda: self.raw_query("SHOW TABLES")

            self.get_user = lambda username: self.get_query(f"SELECT * FROM user WHERE username='{username}' AND hidden='0'")
            self.get_all_users = lambda: self.raw_query("SELECT * FROM user JOIN role ON user.role_id=role.id WHERE hidden='0'")
            self.login_user = lambda username, password: self.get_query(f"SELECT * FROM user WHERE username='{username}' AND password='{password}' AND hidden='0'")
            self.login_user_safe = lambda username, password: self.get_query("SELECT * FROM user WHERE username=%(u)s AND password=%(p)s", params={'u': username, 'p': password})
            self.add_u = lambda username, password, fio, role_id: self.write_query(f"INSERT INTO user SET username='{username}', fio='{fio}', password='{password}', role_id='{role_id}'")
            self.rm_user = lambda id: self.write_query(f"DELETE FROM user WHERE id='{id}'")
            self.select_users = lambda: self.raw_query("SELECT id, fio FROM user WHERE role_id='1' AND hidden='0'")
            self.hide_user = lambda id: self.write_query(f"UPDATE user SET hidden='1' WHERE id='{id}'")
            self.change_user_secret_key = lambda username, secret_key: self.write_query(
                f"UPDATE user SET secret_key='{secret_key}' WHERE username='{username}'")

            self.get_roles = lambda: self.raw_query("SELECT * from role")

            self.get_services = lambda: self.raw_query("SELECT * FROM service_type WHERE hidden='0'")
            self.add_service = lambda name, price, duration: self.write_query(f"INSERT INTO service_type SET name='{name}', price='{price}', duration='{duration}'")
            self.rm_service = lambda id: self.write_query(f"DELETE FROM service_type WHERE id='{id}'")
            self.select_services = lambda: self.raw_query("SELECT id, name FROM service_type WHERE hidden='0'")
            self.hide_service = lambda id: self.raw_query(f"UPDATE service_type SET hidden='1' WHERE id='{id}'")

            self.get_clients = lambda: self.raw_query("SELECT * FROM client")
            self.add_client = lambda name, number: self.write_query(f"INSERT INTO client SET first_name='{name}', number='{number}'")
            self.get_client_by_name_number = lambda name, number: self.get_query(f"SELECT * FROM client WHERE first_name='{name}' AND number='{number}'")
            self.rm_client = lambda id: self.write_query(f"DELETE FROM client WHERE id='{id}'")
            self.select_clients = lambda: self.raw_query("SELECT id, CONCAT(first_name, ' ', number) FROM client")

            self.get_orders = lambda: self.raw_query("SELECT *, (SELECT SEC_TO_TIME( SUM( TIME_TO_SEC( `duration` ) ) ) FROM order_has_service_type os JOIN service_type s ON os.service_type_id=s.id WHERE os.order_id=o.id) FROM manicure.order o JOIN client c, user u, status s WHERE o.client_id=c.id AND o.user_id=u.id AND o.status_id=s.id ORDER BY date")
            self.add_order = lambda date, user_id, client_id: self.write_query(f"INSERT INTO manicure.order SET date='{date}', user_id='{user_id}', client_id='{client_id}'")
            self.get_order_by_user_date = lambda user, date: self.raw_query(f"SELECT * FROM manicure.order WHERE user_id='{user}' AND date='{date}'")
            self.get_order = lambda id: self.raw_query(f"SELECT *, (SELECT SEC_TO_TIME( SUM( TIME_TO_SEC( `duration` ) ) ) FROM order_has_service_type os JOIN service_type s ON os.service_type_id=s.id WHERE os.order_id=o.id), (SELECT SUM(price) FROM order_has_service_type os JOIN service_type s ON os.service_type_id=s.id WHERE os.order_id=o.id) FROM manicure.order o JOIN client c, user u, status s WHERE o.client_id=c.id AND o.user_id=u.id AND o.status_id=s.id AND o.id='{id}'")
            self.rm_order = lambda id: self.write_query(f"DELETE FROM manicure.order WHERE id='{id}'")
            self.change_order_status = lambda id, status: self.write_query(f"UPDATE manicure.order SET status_id='{status}' WHERE id='{id}'")
            self.get_client_orders = lambda client_id: self.raw_query(f"SELECT * FROM manicure.order WHERE client_id='{client_id}'")
            self.get_user_orders = lambda user_id: self.raw_query(f"SELECT *, (SELECT SEC_TO_TIME( SUM( TIME_TO_SEC( `duration` ) ) ) FROM order_has_service_type os JOIN service_type s ON os.service_type_id=s.id WHERE os.order_id=o.id) FROM manicure.order o JOIN client c, user u, status s WHERE o.client_id=c.id AND o.user_id=u.id AND o.status_id=s.id AND user_id='{user_id}' ORDER BY date")

            self.add_service_to_order = lambda order_id, service_id: self.write_query(f"INSERT INTO order_has_service_type SET order_id='{order_id}', service_type_id='{service_id}'")
            self.rm_order_services = lambda id: self.write_query(f"DELETE FROM order_has_service_type WHERE order_id='{id}'")
            self.get_services_of_order = lambda id: self.raw_query(f"SELECT * FROM order_has_service_type os JOIN service_type s ON os.service_type_id=s.id WHERE order_id='{id}'")
            self.select_statuses = lambda: self.raw_query("SELECT * FROM status")
            self.get_service_orders = lambda service_id: self.raw_query(f"SELECT * FROM order_has_service_type WHERE service_type_id='{service_id}'")

            self.get_turnover = lambda: self.raw_query("SELECT DATE_FORMAT(date, '%Y-%m-%d'), SUM(price) FROM order_has_service_type os JOIN manicure.order o, service_type s WHERE os.order_id=o.id AND os.service_type_id=s.id AND MONTH(date)=MONTH(NOW()) GROUP BY YEAR(date), MONTH(date), DAY(date)")

    def connect_to_db(self, host, user, password, db):
        try:
            self.connection = connect(host=host, user=user, password=password)
            self.cursor = self.connection.cursor()
            self.cursor.execute("SHOW DATABASES")
            for res in self.cursor:
                if res[0] == db:
                    self.cursor.fetchall()
                    return
            for line in open('dump.sql'):
                self.cursor.execute(line)
            self.connection.commit()
            print('dump loaded successfully')
        except Error as e:
            print(e)

    def select_db(self, db):
        self.cursor.execute(f"USE {db}")

    def raw_query(self, query):
        if self.cursor and query:
            self.cursor.execute(query)
            return self.cursor.fetchall()

    def write_query(self, query):
        if self.cursor and query:
            self.cursor.execute(query)
            self.connection.commit()
            return self.cursor.fetchall()

    def get_query(self, query, params=None):
        if self.cursor and query:
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)
            return self.cursor.fetchone()

    def get_one_query(self, query):
        if self.cursor and query:
            self.cursor.execute(query)
            return self.cursor.fetchone()[0]

    def add_user(self, username, password, fio, role):
        if not self.get_user(username):
            self.add_u(username, password, fio, role)
            return True
        else:
            return False

    def add_client_check(self, name, number):
        if not self.get_client_by_name_number(name, number):
            self.add_client(name, number)
            return True
        return False

    def add_order_check(self, date, user, client, services):
        if self.check_order_date(user, date):
            self.add_order(date, user, client)
            order_id = self.get_order_by_user_date(user, date)[0][0]
            for i in services:
                self.add_service_to_order(order_id, i)
            return True
        return False

    def check_order_date(self, user_id, new_date):
        dates = self.raw_query(f"SELECT o.date, SEC_TO_TIME( SUM( TIME_TO_SEC( `duration` ) ) ) FROM order_has_service_type JOIN service_type s, manicure.order o WHERE service_type_id=s.id AND order_id=o.id AND o.user_id='{user_id}' GROUP BY o.date")
        for date in dates:
            if abs((new_date - date[0]).total_seconds()) < date[1].total_seconds():
                return False
        return True

    def get_orders_sorted(self, user, client, date1, date2):
        q = "SELECT *, (SELECT SEC_TO_TIME( SUM( TIME_TO_SEC( `duration` ) ) ) FROM order_has_service_type os JOIN service_type s ON os.service_type_id=s.id WHERE os.order_id=o.id) FROM manicure.order o JOIN client c, user u, status s WHERE o.client_id=c.id AND o.user_id=u.id AND o.status_id=s.id"
        if user:
            q = q + f" AND o.user_id='{user}'"
        if client:
            q = q + f" AND o.client_id='{client}'"
        if date1:
            q = q + f" AND o.date > '{date1}'"
        if date2:
            q = q + f" AND o.date < '{date2}'"
        q = q + ' ORDER BY o.date'
        return self.raw_query(q)

    def remove_user(self, id):
        orders = self.get_user_orders(id)
        for o in orders:
            self.remove_order(o[0])
        self.rm_user(id)

    def remove_service(self, id):
        orders = self.get_service_orders(id)
        for o in orders:
            self.remove_order(o[0])
        self.rm_service(id)

    def remove_order(self, id):
        self.rm_order_services(id)
        self.rm_order(id)

    def remove_client(self, id):
        orders = self.get_client_orders(id)
        for o in orders:
            self.remove_order(o[0])
        self.rm_client(id)

    def hide_user_with_orders(self, id):
        orders = self.get_user_orders(id)
        for o in orders:
            if o[4] == 1:
                self.remove_order(o[0])
        self.hide_user(id)

    def add_secret_key_to_user(self, username, secret_key):
        user_key = self.raw_query(f"SELECT secret_key FROM user WHERE username='{username}'")
        if user_key[0][0] is None:
            self.change_user_secret_key(username, secret_key)
            return True
        return False

    def toggle_2fa(self, id):
        user_2fa = self.raw_query(f"SELECT 2fa FROM user WHERE id='{id}'")
        if user_2fa[0][0] == 0:
            self.write_query(f"UPDATE user SET 2fa='1' WHERE id='{id}'")
            return True
        else:
            self.write_query(f"UPDATE user SET 2fa='0' WHERE id='{id}'")
            return False