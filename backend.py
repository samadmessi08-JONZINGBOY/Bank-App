import re
import random
import os

import bcrypt
import smtplib
import pyttsx3
import speech_recognition as sr
from email.mime.text import MIMEText

import mysql.connector as sql


class Bank:
    def __init__(self, bank_name):
        self.bank_name = bank_name

        try:
            self.conn = sql.connect(
                host="127.0.0.1",
                port="3306",
                user="root",
                password="",
                database="Bank_vault"
            )
            self.mycursor = self.conn.cursor(dictionary=True)
            self.conn.autocommit = True
            print("Database connection successful")
        except sql.Error as e:
            print(f"Database connection failed: {e}")
            raise

        self.otp_store = {}


    
    def send_email(self, to_email, subject, body):
        sender_email = "SMTP_EMAIL"
        sender_password = "SMTP_PASSWORD"

        try:
            msg = MIMEText(body)
            msg["Subject"] = subject
            msg["From"] = sender_email
            msg["To"] = to_email

            server = smtplib.SMTP("smtp.gmail.com", 587)
            server.starttls()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, to_email, msg.as_string())
            server.quit()
            print("Email sent successfully")
        except Exception as e:
            print(f"Failed to send email: {e}")

    def speak(self, text):
        try:
            engine = pyttsx3.init()
            engine.say(text)
            engine.runAndWait()
        except Exception as e:
            print(f"Voice output failed: {e}")

    def listen(self):
        recognizer = sr.Recognizer()
        try:
            with sr.Microphone() as source:
                print("Listening...")
                audio = recognizer.listen(source)

            text = recognizer.recognize_google(audio)
            print(f"You said: {text}")
            return text.lower()
        except sr.UnknownValueError:
            print("Sorry, I couldn't understand that.")
            return ""
        except sr.RequestError:
            print("Speech service unavailable.")
            return ""
        except OSError as e:
            print(f"Microphone not available: {e}")
            return ""

    def is_valid_email(self, email):
        pattern = r"^[a-zA-Z][\w\.-]*@[\w\.-]+\.[a-zA-Z]{2,3}$"
        return re.match(pattern, email) is not None

    def is_valid_password(self, password):
        pattern = r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*()_+\-=\[\]{}|;:,.<>?]).{8,}$"
        return re.match(pattern, password) is not None

    def hash_password(self, password):
        hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
        return hashed.decode("utf-8")

    def check_password(self, password, hashed_password):
        return bcrypt.checkpw(password.encode("utf-8"), hashed_password.encode("utf-8"))

    def suggest_password(self):
        lowercase = "abcdefghijklmnopqrstuvwxyz"
        uppercase = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        digits = "0123456789"
        special = "!@#$%^&*"

        password_chars = [
            random.choice(lowercase),
            random.choice(uppercase),
            random.choice(digits),
            random.choice(special)
        ]

        all_chars = lowercase + uppercase + digits + special
        for _ in range(6):
            password_chars.append(random.choice(all_chars))

        random.shuffle(password_chars)
        return "".join(password_chars)

    def email_exists(self, email):
        try:
            query = "SELECT * FROM accounts_table WHERE email = %s"
            self.mycursor.execute(query, (email,))
            existing_user = self.mycursor.fetchone()
            return existing_user is not None
        except sql.Error as e:
            print(f"Database error: {e}")
            return False

    def send_otp(self, email, fullname):
        otp = str(random.randint(100000, 999999))
        self.otp_store[email] = otp

        email_body = f"""
        Hi {fullname},

        Your One-Time Password (OTP) for account verification is: {otp}

        Please enter this code to complete your registration.
        """
        self.send_email(email, "Your OTP Verification Code", email_body)

    def verify_otp(self, email, entered_otp):
        correct_otp = self.otp_store.get(email)

        if correct_otp is None:
            return False

        if entered_otp.strip() == correct_otp:
            del self.otp_store[email]
            return True

        return False

    def generate_account_number(self):
        while True:
            account_number = str(random.randint(1000000000, 9999999999))
            query = "SELECT * FROM accounts_table WHERE account_number = %s"
            self.mycursor.execute(query, (account_number,))
            existing = self.mycursor.fetchone()
            if not existing:
                return account_number

    

    def Create_Account(self, fullname, email, password):
        if not self.is_valid_email(email):
            return {
                "status": False,
                "message": "Invalid email format"
            }

        if not self.is_valid_password(password):
            return {
                "status": False,
                "message": "Password must be at least 8 characters and include uppercase, lowercase, a number, and a special character"
            }

        try:
            query = "SELECT * FROM accounts_table WHERE email = %s"
            self.mycursor.execute(query, (email,))
            existing_user = self.mycursor.fetchone()

            if existing_user:
                return {
                    "status": False,
                    "message": "Email already exists"
                }

            account_number = self.generate_account_number()
            hashed_password = self.hash_password(password)

            query = "INSERT INTO accounts_table (fullname, email, password, account_number, balance, role) VALUES (%s, %s, %s, %s, %s, %s)"
            values = (fullname, email, hashed_password, account_number, 0.00, "customer")
            self.mycursor.execute(query, values)
            self.conn.commit()

            email_body = f"""
            Hi {fullname},

            Welcome to {self.bank_name}!

            Your account has been created successfully.
            Your account number is: {account_number}

            Thank you for banking with us.
            """
            self.send_email(email, f"Welcome to {self.bank_name}!", email_body)

            return {
                "status": True,
                "message": f"Account created successfully. Your account number is {account_number}"
            }
        except sql.Error as e:
            return {
                "status": False,
                "message": f"Database error: {e}"
            }

    def login_account(self, email, password):
        if email == "admin" and password == "admin123":
            return {
                "status": True,
                "message": "Admin login successful",
                "role": "admin"
            }

        try:
            query = "SELECT * FROM accounts_table WHERE email = %s"
            self.mycursor.execute(query, (email,))
            account = self.mycursor.fetchone()

            if not account:
                return {
                    "status": False,
                    "message": "Invalid email or password"
                }

            if not self.check_password(password, account["password"]):
                return {
                    "status": False,
                    "message": "Invalid email or password"
                }

            if account["status"] == "frozen":
                return {
                    "status": False,
                    "message": "This account has been frozen. Please contact support."
                }

            return {
                "status": True,
                "message": f"Login successful, welcome {account['fullname']}",
                "role": "customer",
                "account": account
            }
        except sql.Error as e:
            return {
                "status": False,
                "message": f"Database error: {e}"
            }

    

    def check_balance(self, account_id):
        try:
            query = "SELECT balance FROM accounts_table WHERE id = %s"
            self.mycursor.execute(query, (account_id,))
            account = self.mycursor.fetchone()

            if not account:
                return {
                    "status": False,
                    "message": "Account not found"
                }

            return {
                "status": True,
                "message": f"Your current balance is {account['balance']}"
            }
        except sql.Error as e:
            return {
                "status": False,
                "message": f"Database error: {e}"
            }

    def deposit(self, account_id, amount):
        try:
            amount = int(amount)
        except ValueError:
            return {
                "status": False,
                "message": "Amount must be a valid number"
            }

        if amount <= 0:
            return {
                "status": False,
                "message": "Amount must be greater than zero"
            }

        try:
            query = "SELECT * FROM accounts_table WHERE id = %s"
            self.mycursor.execute(query, (account_id,))
            account = self.mycursor.fetchone()

            if not account:
                return {
                    "status": False,
                    "message": "Account not found"
                }

            new_balance = account["balance"] + amount

            update_query = "UPDATE accounts_table SET balance = %s WHERE id = %s"
            self.mycursor.execute(update_query, (new_balance, account_id))

            log_query = "INSERT INTO transactions_table (account_id, type, amount, balance_after) VALUES (%s, %s, %s, %s)"
            self.mycursor.execute(log_query, (account_id, "deposit", amount, new_balance))

            self.conn.commit()

            email_body = f"""
            Hi {account['fullname']},

            Your account has received a credit alert.

            Amount Credited: {amount}
            New Balance: {new_balance}

            Thank you for banking with us.
            """
            self.send_email(account["email"], "Credit Alert", email_body)

            return {
                "status": True,
                "message": f"Deposit successful. New balance: {new_balance}"
            }
        except sql.Error as e:
            return {
                "status": False,
                "message": f"Database error: {e}"
            }

    def withdraw(self, account_id, amount):
        try:
            amount = int(amount)
        except ValueError:
            return {
                "status": False,
                "message": "Amount must be a valid number"
            }

        if amount <= 0:
            return {
                "status": False,
                "message": "Amount must be greater than zero"
            }

        try:
            query = "SELECT balance FROM accounts_table WHERE id = %s"
            self.mycursor.execute(query, (account_id,))
            account = self.mycursor.fetchone()

            if not account:
                return {
                    "status": False,
                    "message": "Account not found"
                }

            if account["balance"] < amount:
                return {
                    "status": False,
                    "message": "Insufficient funds"
                }

            new_balance = account["balance"] - amount

            update_query = "UPDATE accounts_table SET balance = %s WHERE id = %s"
            self.mycursor.execute(update_query, (new_balance, account_id))

            log_query = "INSERT INTO transactions_table (account_id, type, amount, balance_after) VALUES (%s, %s, %s, %s)"
            self.mycursor.execute(log_query, (account_id, "withdrawal", amount, new_balance))

            self.conn.commit()

            return {
                "status": True,
                "message": f"Withdrawal successful. New balance: {new_balance}"
            }
        except sql.Error as e:
            return {
                "status": False,
                "message": f"Database error: {e}"
            }

    def pay_bill(self, account_id, bill_type, amount):
        try:
            amount = int(amount)
        except ValueError:
            return {
                "status": False,
                "message": "Amount must be a valid number"
            }

        if amount <= 0:
            return {
                "status": False,
                "message": "Amount must be greater than zero"
            }

        try:
            query = "SELECT balance FROM accounts_table WHERE id = %s"
            self.mycursor.execute(query, (account_id,))
            account = self.mycursor.fetchone()

            if not account:
                return {
                    "status": False,
                    "message": "Account not found"
                }

            if account["balance"] < amount:
                return {
                    "status": False,
                    "message": "Insufficient funds"
                }

            new_balance = account["balance"] - amount

            update_query = "UPDATE accounts_table SET balance = %s WHERE id = %s"
            self.mycursor.execute(update_query, (new_balance, account_id))

            log_query = "INSERT INTO transactions_table (account_id, type, amount, balance_after) VALUES (%s, %s, %s, %s)"
            self.mycursor.execute(log_query, (account_id, "bill_payment", amount, new_balance))

            self.conn.commit()

            return {
                "status": True,
                "message": f"{bill_type} bill payment successful. New balance: {new_balance}"
            }
        except sql.Error as e:
            return {
                "status": False,
                "message": f"Database error: {e}"
            }

    def view_my_transactions(self, account_id):
        try:
            query = "SELECT * FROM transactions_table WHERE account_id = %s ORDER BY created_at DESC"
            self.mycursor.execute(query, (account_id,))
            transactions = self.mycursor.fetchall()

            if not transactions:
                return {
                    "status": False,
                    "message": "No transactions yet"
                }

            print(transactions)

            return {
                "status": True,
                "message": "Transactions listed above"
            }
        except sql.Error as e:
            return {
                "status": False,
                "message": f"Database error: {e}"
            }

    

    def view_all_accounts(self):
        try:
            query = "SELECT * FROM accounts_table WHERE role = 'customer'"
            self.mycursor.execute(query)
            accounts = self.mycursor.fetchall()

            if not accounts:
                return {
                    "status": False,
                    "message": "No accounts available"
                }

            for account in accounts:
                print(f"""
        --------------------------
        ID : {account["id"]}
        Fullname : {account["fullname"]}
        Email : {account["email"]}
        Account_Number : {account["account_number"]}
        Balance : {account["balance"]}
        Status : {account["status"]}
        """)

            return {
                "status": True,
                "message": "All accounts listed above"
            }
        except sql.Error as e:
            return {
                "status": False,
                "message": f"Database error: {e}"
            }

    def view_all_transactions(self):
        try:
            query = """SELECT transactions_table.*, accounts_table.fullname, accounts_table.account_number
                       FROM transactions_table
                       JOIN accounts_table ON transactions_table.account_id = accounts_table.id
                       ORDER BY transactions_table.created_at DESC"""
            self.mycursor.execute(query)
            transactions = self.mycursor.fetchall()

            if not transactions:
                return {
                    "status": False,
                    "message": "No transactions available"
                }

            for txn in transactions:
                print(f"""
        --------------------------
        Transaction_ID : {txn["transaction_id"]}
        Account Holder : {txn["fullname"]}
        Account_Number : {txn["account_number"]}
        Type : {txn["type"]}
        Amount : {txn["amount"]}
        Balance_After : {txn["balance_after"]}
        Date : {txn["created_at"]}
        """)

            return {
                "status": True,
                "message": "All transactions listed above"
            }
        except sql.Error as e:
            return {
                "status": False,
                "message": f"Database error: {e}"
            }

    def freeze_account(self, account_number):
        try:
            query = "SELECT * FROM accounts_table WHERE account_number = %s"
            self.mycursor.execute(query, (account_number,))
            account = self.mycursor.fetchone()

            if not account:
                return {
                    "status": False,
                    "message": "Account not found"
                }

            update_query = "UPDATE accounts_table SET status = 'frozen' WHERE account_number = %s"
            self.mycursor.execute(update_query, (account_number,))
            self.conn.commit()

            return {
                "status": True,
                "message": f"Account {account_number} has been frozen"
            }
        except sql.Error as e:
            return {
                "status": False,
                "message": f"Database error: {e}"
            }

    def unfreeze_account(self, account_number):
        try:
            query = "SELECT * FROM accounts_table WHERE account_number = %s"
            self.mycursor.execute(query, (account_number,))
            account = self.mycursor.fetchone()

            if not account:
                return {
                    "status": False,
                    "message": "Account not found"
                }

            update_query = "UPDATE accounts_table SET status = 'active' WHERE account_number = %s"
            self.mycursor.execute(update_query, (account_number,))
            self.conn.commit()

            return {
                "status": True,
                "message": f"Account {account_number} has been unfrozen"
            }
        except sql.Error as e:
            return {
                "status": False,
                "message": f"Database error: {e}"
            }

    def delete_account(self, account_number):
        try:
            query = "SELECT * FROM accounts_table WHERE account_number = %s"
            self.mycursor.execute(query, (account_number,))
            account = self.mycursor.fetchone()

            if not account:
                return {
                    "status": False,
                    "message": "Account not found"
                }

            query = "DELETE FROM accounts_table WHERE account_number = %s"
            self.mycursor.execute(query, (account_number,))
            self.conn.commit()

            return {
                "status": True,
                "message": "Account deleted successfully"
            }
        except sql.Error as e:
            return {
                "status": False,
                "message": f"Database error: {e}"
            }
