import msvcrt
from backend import Bank


def masked_input(prompt):
    print(prompt, end="", flush=True)
    typed_password = ""
    while True:
        char = msvcrt.getch()

        if char in (b"\r", b"\n"):
            print("")
            break
        elif char == b"\x08":
            if len(typed_password) > 0:
                typed_password = typed_password[:-1]
                print("\b \b", end="", flush=True)
        else:
            try:
                decoded_char = char.decode("utf-8")
                typed_password += decoded_char
                print("*", end="", flush=True)
            except UnicodeDecodeError:
                pass

    return typed_password


class BankApp(Bank):
    def __init__(self, bank_name):
        super().__init__(bank_name)

    def home_page(self, bank_name):
        self.speak(f"Welcome to {bank_name}")
        while True:
            print(f"""Welcome to {bank_name}
                 1. Create Account
                 2. Login
                 3. About Us
                 4. Exit
                 """)
            print("Type your choice, or type 'v' to speak instead.")
            choice = input("Enter your choice: ")

            if choice.lower() == "v":
                self.speak("Please say your choice")
                choice = self.listen()

            if choice == "1" or choice == "create account":
                self.create_account()
            elif choice == "2" or choice == "login":
                self.login_user()
            elif choice == "3" or choice == "about us":
                self.about_us()
            elif choice == "4" or choice == "exit":
                print("Thank you for banking with us....")
                self.speak("Thank you for banking with us")
                exit()
            else:
                print("Invalid input")

    def about_us(self):
        print(f"""
        Welcome to {self.bank_name}

        Your money, your rules, your peace of mind.

        What We Offer:

        Secure account creation and easy login for every customer.

        Deposit, withdraw, and track every transaction with full transparency.

        Reliable admin oversight to keep every account safe.

        Thank you for trusting us with your finances.
        """)

    def create_account(self):
        fullname = input("Enter your fullname: ")

        suggested_password = self.suggest_password()
        print(f"Suggested password: {suggested_password}")
        choice = input("Use this suggested password? Yes or No: ")

        if choice.lower() == "yes":
            password = suggested_password
        else:
            while True:
                password = masked_input("Enter your password: ")
                if self.is_valid_password(password):
                    break
                else:
                    print("Password must be at least 8 characters and include uppercase, lowercase, a number, and a special character. Please try again.")

        while True:
            email = input("Enter your email: ")
            if self.is_valid_email(email):
                if self.email_exists(email):
                    print("Email already exists. Please try a different email.")
                else:
                    break
            else:
                print("Invalid email format. Please try again.")

        self.send_otp(email, fullname)
        print(f"An OTP has been sent to {email}. Please check your inbox.")

        attempts = 0
        verified = False
        while attempts < 3:
            entered_otp = input("Enter the OTP sent to your email: ")
            if self.verify_otp(email, entered_otp):
                verified = True
                break
            else:
                attempts += 1
                print(f"Incorrect OTP. {3 - attempts} attempt(s) remaining.")

        if not verified:
            print("OTP verification failed. Account creation cancelled.")
            return

        result = self.Create_Account(fullname, email, password)
        print(result["message"])

        if not result["status"]:
            return

        choice = input("Do you wish to login now? Yes or No: ")
        if choice.lower() == "yes":
            self.login_user()

    def login_user(self):
        while True:
            email = input("Enter your email: ")
            password = masked_input("Enter your password: ")

            result = self.login_account(email, password)
            print(result["message"])

            if result["status"]:
                break
            else:
                print("Please try again.")

        if result["role"] == "admin":
            self.speak("Welcome Admin")
            self.admin_dashboard()
        else:
            account = result["account"]
            self.speak(f"Welcome {account['fullname']}")
            self.dashboard(account)


#  User's part 

    def dashboard(self, account):
        while True:
            print(f"""
            Welcome {account['fullname']}
            Account Number: {account['account_number']}

            1. Check Balance
            2. Deposit
            3. Withdraw
            4. Pay Utility Bill
            5. View Transactions
            0. Logout
            """)
            print("Type your choice, or type 'v' to speak instead.")
            choice = input("Choose action: ")

            if choice.lower() == "v":
                self.speak("Please say your choice")
                choice = self.listen()

            if choice == "1" or choice == "check balance":
                result = self.check_balance(account["id"])
                print(result["message"])
            elif choice == "2" or choice == "deposit":
                amount = input("Enter amount to deposit: ")
                result = self.deposit(account["id"], amount)
                print(result["message"])
            elif choice == "3" or choice == "withdraw":
                amount = input("Enter amount to withdraw: ")
                result = self.withdraw(account["id"], amount)
                print(result["message"])
            elif choice == "4" or choice == "pay utility bill":
                self.pay_utility_bill(account)
            elif choice == "5" or choice == "view transactions":
                result = self.view_my_transactions(account["id"])
                if not result["status"]:
                    print(result["message"])
            elif choice == "0" or choice == "logout":
                print("Logging out...")
                self.speak("Goodbye")
                break
            else:
                print("Invalid input")


    def pay_utility_bill(self, account):
        print("""
        Select a bill to pay:
        1. Electricity
        2. Internet
        3. Cable TV
        """)
        choice = input("Choose bill type: ")

        bill_types = {
            "1": "Electricity",
            "2": "Internet",
            "3": "Cable TV"
        }

        bill_type = bill_types.get(choice)

        if not bill_type:
            print("Invalid bill type")
            return

        amount = input(f"Enter amount to pay for {bill_type}: ")
        result = self.pay_bill(account["id"], bill_type, amount)
        print(result["message"])


# Admin's part

    def admin_dashboard(self):
        while True:
            print("""
            Welcome Admin

            1. View All Accounts
            2. View All Transactions
            3. Freeze Account
            4. Unfreeze Account
            5. Delete Account
            6. Logout
            """)
            print("Type your choice, or type 'v' to speak instead.")
            choice = input("Enter your choice: ")

            if choice.lower() == "v":
                self.speak("Please say your choice")
                choice = self.listen()

            if choice == "1" or choice == "view all accounts":
                result = self.view_all_accounts()
                if not result["status"]:
                    print(result["message"])
            elif choice == "2" or choice == "view all transactions":
                result = self.view_all_transactions()
                if not result["status"]:
                    print(result["message"])
            elif choice == "3" or choice == "freeze account":
                account_number = input("Enter the account number to freeze: ")
                result = self.freeze_account(account_number)
                print(result["message"])
            elif choice == "4" or choice == "unfreeze account":
                account_number = input("Enter the account number to unfreeze: ")
                result = self.unfreeze_account(account_number)
                print(result["message"])
            elif choice == "5" or choice == "delete account":
                account_number = input("Enter the account number to delete: ")
                result = self.delete_account(account_number)
                print(result["message"])
            elif choice == "6" or choice == "logout":
                print("Logging out...")
                self.speak("Goodbye")
                break
            else:
                print("Invalid input")


bank = BankApp("Jonzing Trust Bank")
bank.home_page("Jonzing Trust Bank")