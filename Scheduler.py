from multiprocessing.dummy import current_process
from xml.dom.expatbuilder import parseString
from model.Vaccine import Vaccine
from model.Caregiver import Caregiver
from model.Patient import Patient
from util.Util import Util
from db.ConnectionManager import ConnectionManager
import pymssql
import datetime
import re


'''
objects to keep track of the currently logged-in user
Note: it is always true that at most one of currentCaregiver and currentPatient is not null
        since only one user can be logged-in at a time
'''
current_patient = None

current_caregiver = None

def create_patient(tokens):

    if len(tokens) != 3:
        print("Failed to create user.")
        return

        
    username = tokens[1]
    password = tokens[2]
    # check 2: check if the username has been taken already
    if username_exists_patient(username):
        print("Username taken, try again!")
        return
    if strong_pass(password) is True:
        return 

    salt = Util.generate_salt()
    hash = Util.generate_hash(password, salt)

    patient = Patient(username, salt=salt, hash=hash)

    try:
        patient.save_to_db()
    except pymssql.Error as e:
        print("Failed to create user.")
        print("Db-Error:", e)
        quit()
    except Exception as e:
        print("Failed to create user.")
        print(e)
        return
    print("Created user ", username)
    


def create_caregiver(tokens):
    # create_caregiver <username> <password>
    # check 1: the length for tokens need to be exactly 3 to include all information (with the operation name)
    if len(tokens) != 3:
        print("Failed to create user.")
        return

    username = tokens[1]
    password = tokens[2]
    # check 2: check if the username has been taken already
    if username_exists_caregiver(username):
        print("Username taken, try again!")
        return
    if strong_pass(password) is True:
        return 

    salt = Util.generate_salt()
    hash = Util.generate_hash(password, salt)

    # create the caregiver
    caregiver = Caregiver(username, salt=salt, hash=hash)

    # save to caregiver information to our database
    try:
        caregiver.save_to_db()
    except pymssql.Error as e:
        print("Failed to create user.")
        print("Db-Error:", e)
        quit()
    except Exception as e:
        print("Failed to create user.")
        print(e)
        return
    print("Created user ", username)


def username_exists_caregiver(username):
    cm = ConnectionManager()
    conn = cm.create_connection()

    select_username = "SELECT * FROM Caregivers WHERE Username = %s"
    try:
        cursor = conn.cursor(as_dict=True)
        cursor.execute(select_username, username)
        #  returns false if the cursor is not before the first record or if there are no rows in the ResultSet.
        for row in cursor:
            return row['Username'] is not None
    except pymssql.Error as e:
        print("Error occurred when checking username")
        print("Db-Error:", e)
        quit()
    except Exception as e:
        print("Error occurred when checking username")
        print("Error:", e)
    finally:
        cm.close_connection()
    return False


def username_exists_patient(username):
    cm = ConnectionManager()
    conn = cm.create_connection()

    select_username = "SELECT * FROM patients WHERE Username = %s"
    try:
        cursor = conn.cursor(as_dict=True)
        cursor.execute(select_username, username)
        #  returns false if the cursor is not before the first record or if there are no rows in the ResultSet.
        for row in cursor:
            return row['Username'] is not None
    except pymssql.Error as e:
        print("Error occurred when checking username")
        print("Db-Error:", e)
        quit()
    except Exception as e:
        print("Error occurred when checking username")
        print("Error:", e)
    finally:
        cm.close_connection()
    return False


def login_patient(tokens):
    global current_patient
    if current_caregiver is not None or current_patient is not None:
        print("A user is already logged in.")
        return

    if len(tokens) != 3:
        print("Login failed.")
        return

    username = tokens[1]
    password = tokens[2]

    patient = None
    try:
        patient = Patient(username, password=password).get()
    except pymssql.Error as e:
        print("Login failed.")
        print("Db-Error:", e)
        quit()
    except Exception as e:
        print("Login failed.")
        print("Error:", e)
        return

    # check if the login was successful
    if patient is None:
        print("Login failed.")
    else:
        print("Logged in as: " + username)
        current_patient = patient


def login_caregiver(tokens):
    # login_caregiver <username> <password>
    # check 1: if someone's already logged-in, they need to log out first
    global current_caregiver
    if current_caregiver is not None or current_patient is not None:
        print("User already logged in.")
        return

    # check 2: the length for tokens need to be exactly 3 to include all information (with the operation name)
    if len(tokens) != 3:
        print("Login failed.")
        return

    username = tokens[1]
    password = tokens[2]

    caregiver = None
    try:
        caregiver = Caregiver(username, password=password).get()
    except pymssql.Error as e:
        print("Login failed.")
        print("Db-Error:", e)
        quit()
    except Exception as e:
        print("Login failed.")
        print("Error:", e)
        return

    # check if the login was successful
    if caregiver is None:
        print("Login failed.")
    else:
        print("Logged in as: " + username)
        current_caregiver = caregiver


def search_caregiver_schedule(tokens):
    global current_caregiver
    global current_patient
    if current_caregiver is None and current_patient is None:
        print("Please login first!")
        return

    if len(tokens) != 2:
        print("Please try again!")
        return

    date = tokens[1]
    date_tokens = date.split("-")
    if len(date_tokens) != 3:
        print('Please try again!')
        return
    month = int(date_tokens[0])
    day = int(date_tokens[1])
    year = int(date_tokens[2])

    cm = ConnectionManager()
    conn = cm.create_connection()

    all_availability = "SELECT Username FROM Availabilities WHERE time = %s ORDER BY Username"
    num_vacc = "SELECT Name, Doses FROM Vaccines" 
    try:
        d = datetime.datetime(year, month, day)
        cursor = conn.cursor(as_dict=True)
        cursor.execute(all_availability, d)

        print('Caregivers:')
        for row in cursor:
            print(str(row['Username']))
        print()
        print('Vaccine Name + Doses:')
        cursor.execute(num_vacc)
        for row in cursor:
            print(str(row['Name']) + " " + str(row['Doses']))

    except pymssql.Error as e:
        print("Please try again!")
        print("Db-Error:", e)
        quit()
    except ValueError:
        print("Please try again!")
        return
    except Exception as e:
        print("Please try again!")
        print("Error:", e)
        return


def reserve(tokens):
    global current_caregiver
    global current_patient
    if current_caregiver is None and current_patient is None:
        print("Please login first!")
        return
    
    if current_patient is None:
        print("Please login as a patient!")
        return
    
    if len(tokens) != 3:
        print("Please try again!")
        return

    date = tokens[1]
    vaccine_name = tokens[2]
    date_tokens = date.split("-")
    if len(date_tokens) != 3:
        print('Please try again!')
        return
    month = int(date_tokens[0])
    day = int(date_tokens[1])
    year = int(date_tokens[2])

    cm = ConnectionManager()
    conn = cm.create_connection()

    user = "select TOP 1 Username from Availabilities where Time = %s ORDER BY Username"

    app_id = "SELECT TOP 1 * FROM appointments ORDER BY app_id DESC"

    ins_app = "INSERT INTO Appointments (app_date, Pusername, Cusername, vaccine_name) VALUES (%s,%s,%s,%s)"
    # The first value for Appointments, app_ID, is Identity(1,1) and we don't need to specify values for it.
    
    vacc = "SELECT Name FROM Vaccines WHERE Name = %s"

    try:
        d = datetime.datetime(year, month, day)
        cursor = conn.cursor(as_dict=True)
        cursor.execute(user, (d))

        user_care = None
        for row in cursor:
            user_care = (str(row['Username']))

        if user_care is None:
            print("No Caregiver is available!")
            return

        vaccine_exist = None
        cursor.execute(vacc, vaccine_name)
        for row in cursor:
            vaccine_exist = (str(row['Name']))
        if vaccine_exist is None:
            print("No Vaccine exists in this database!")
            return
        vaccine = Vaccine(vaccine_exist, 1).get()
        if vaccine.get_available_doses() == 0:
            print("Not enough available doses!")
            return
        else:
            vaccine.decrease_available_doses(1)

        cursor.execute(ins_app, (d, current_patient.get_username(), user_care, vaccine_name))
        conn.commit()

        cursor.execute(app_id)
        for row in cursor:
            id = (str(row['app_ID']))

        Caregiver(user_care).remove_availability(d)
    
        print("Appointment ID: " + id + " Caregiver username: " + user_care)

        
    except pymssql.Error as e:
        print("Please try again!")
        print("Db-Error:", e)
        quit()
    except ValueError:
        print("Please try again!")
        return
    except Exception as e:
        print("Please try again!")
        print("Error:", e)
        return

        

def upload_availability(tokens):
    #  upload_availability <date>
    #  check 1: check if the current logged-in user is a caregiver
    global current_caregiver
    if current_caregiver is None:
        print("Please login as a caregiver first!")
        return

    # check 2: the length for tokens need to be exactly 2 to include all information (with the operation name)
    if len(tokens) != 2:
        print("Please try again!")
        return

    date = tokens[1]
    # assume input is hyphenated in the format mm-dd-yyyy
    date_tokens = date.split("-")
    month = int(date_tokens[0])
    day = int(date_tokens[1])
    year = int(date_tokens[2])
    try:
        d = datetime.datetime(year, month, day)
        current_caregiver.upload_availability(d)
    except pymssql.Error as e:
        print("Upload Availability Failed")
        print("Db-Error:", e)
        quit()
    except ValueError:
        print("Please enter a valid date!")
        return
    except Exception as e:
        print("Error occurred when uploading availability")
        print("Error:", e)
        return
    print("Availability uploaded!")


def cancel(tokens): #Did the first EC, not cancel.
    pass

def strong_pass(tokens): #Extra Credit
    password = tokens
    special = 0
    alpha = 0
    numeric = 0

    if len(password) < 8:
        print("Your password is not at least 8 characters.")
        return True
    for element in password:
        if element.isalpha():
            alpha += 1
        elif element.isnumeric():
            numeric += 1
    if alpha == 0 or numeric == 0:
        print("You need letters and numbers.")
        return True
    if password.isupper() or password.islower():
        print("You need a mix of upper and lower case letters.")
        return True

    else:
        for letter in password:
            if letter == "!":
                special += 1
                break
            elif letter == "@":
                special += 1
                break
            elif letter == "#":
                special += 1
                break
            elif letter == "?":
                special += 1
                break
    if special == 0:
        print("You need at least one special character: ! @ # ?")
        return True


def add_doses(tokens):
    #  add_doses <vaccine> <number>
    #  check 1: check if the current logged-in user is a caregiver
    global current_caregiver
    if current_caregiver is None:
        print("Please login as a caregiver first!")
        return

    #  check 2: the length for tokens need to be exactly 3 to include all information (with the operation name)
    if len(tokens) != 3:
        print("Please try again!")
        return

    vaccine_name = tokens[1]
    doses = int(tokens[2])
    vaccine = None
    try:
        vaccine = Vaccine(vaccine_name, doses).get()
    except pymssql.Error as e:
        print("Error occurred when adding doses")
        print("Db-Error:", e)
        quit()
    except Exception as e:
        print("Error occurred when adding doses")
        print("Error:", e)
        return

    # if the vaccine is not found in the database, add a new (vaccine, doses) entry.
    # else, update the existing entry by adding the new doses
    if vaccine is None:
        vaccine = Vaccine(vaccine_name, doses)
        try:
            vaccine.save_to_db()
        except pymssql.Error as e:
            print("Error occurred when adding doses")
            print("Db-Error:", e)
            quit()
        except Exception as e:
            print("Error occurred when adding doses")
            print("Error:", e)
            return
    else:
        # if the vaccine is not null, meaning that the vaccine already exists in our table
        try:
            vaccine.increase_available_doses(doses)
        except pymssql.Error as e:
            print("Error occurred when adding doses")
            print("Db-Error:", e)
            quit()
        except Exception as e:
            print("Error occurred when adding doses")
            print("Error:", e)
            return
    print("Doses updated!")


def show_appointments(tokens):
    global current_caregiver
    global current_patient
    if current_caregiver is None and current_patient is None:
        print("Please login first!")
        return

    if len(tokens) != 1:
        print("Please try again!")
        return

    cm = ConnectionManager()
    conn = cm.create_connection()
    
    try:
        if current_caregiver is not None:
            
            all_app = "SELECT * FROM appointments WHERE Cusername = %s ORDER BY app_id"
            cursor = conn.cursor(as_dict=True)
            cursor.execute(all_app, current_caregiver.get_username())

            for row in cursor:
                print(str(row['app_ID']) + " " + str(row['vaccine_name']) + " " + str(row['app_date']) + " " + str(row['Pusername']))
            return

        else: 
            all_app = "SELECT * FROM appointments WHERE Pusername = %s ORDER BY app_id"
            cursor = conn.cursor(as_dict=True)
            cursor.execute(all_app, current_patient.get_username())

            for row in cursor:
                print(str(row['app_ID']) + " " + str(row['vaccine_name']) + " " + str(row['app_date']) + " " + str(row['Cusername']))
            return
    except pymssql.Error as e:
        print("Please try again!")
        print("Db-Error:", e)
        quit()
    except ValueError:
        print("Please try again!")
        return
    except Exception as e:
        print("Please try again!")
        print("Error:", e)
        return


def logout(tokens):
    global current_caregiver
    global current_patient
    if current_caregiver is None and current_patient is None:
        print("Please login first!")
        return

    if len(tokens) != 1:
        print("Please try again!")
        return
    

    print("Successfully logged out!")
    current_patient = None
    current_caregiver = None    
    
    




def start():
    stop = False
    while not stop:
        print()
        print(" *** Please enter one of the following commands *** ")
        print("> create_patient <username> <password>")  # //TODO: implement create_patient (Part 1) yes
        print("> create_caregiver <username> <password>")
        print("> login_patient <username> <password>")  # // TODO: implement login_patient (Part 1) yes
        print("> login_caregiver <username> <password>")
        print("> search_caregiver_schedule <date>")  # // TODO: implement search_caregiver_schedule (Part 2)
        print("> reserve <date> <vaccine>")  # // TODO: implement reserve (Part 2)
        print("> upload_availability <date>")
        print("> cancel <appointment_id>")  # // TODO: implement cancel (extra credit)
        print("> add_doses <vaccine> <number>")
        print("> show_appointments")  # // TODO: implement show_appointments (Part 2)
        print("> logout")  # // TODO: implement logout (Part 2)
        print("> Quit")
        print()
        response = ""
        print("> ", end='')

        try:
            response = str(input())
        except ValueError:
            print("Please try again!")
            break

        #response = response.lower()
        tokens = response.split(" ")
        if len(tokens) == 0:
            ValueError("Please try again!")
            continue
        operation = tokens[0].lower()
        if operation == "create_patient":
            create_patient(tokens)
        elif operation == "create_caregiver":
            create_caregiver(tokens)
        elif operation == "login_patient":
            login_patient(tokens)
        elif operation == "login_caregiver":
            login_caregiver(tokens)
        elif operation == "search_caregiver_schedule":
            search_caregiver_schedule(tokens)
        elif operation == "reserve":
            reserve(tokens)
        elif operation == "upload_availability":
            upload_availability(tokens)
        elif operation == "add_doses":
            add_doses(tokens)
        elif operation == "show_appointments":
            show_appointments(tokens)
        elif operation == "cancel":
            cancel(tokens)
        elif operation == "logout":
            logout(tokens)
        elif operation == "quit":
            print("Bye!")
            stop = True
        else:
            print("Invalid operation name!")


if __name__ == "__main__":
    '''
    // pre-define the three types of authorized vaccines
    // note: it's a poor practice to hard-code these values, but we will do this ]
    // for the simplicity of this assignment
    // and then construct a map of vaccineName -> vaccineObject
    '''

    # start command line
    print()
    print("Welcome to the COVID-19 Vaccine Reservation Scheduling Application!")

    start()
