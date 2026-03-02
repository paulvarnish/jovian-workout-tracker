from database import DatabaseHelper
from cryptography.fernet import Fernet
import base64
import results
import datetime

helper = DatabaseHelper()
with open("key.txt", "r") as f:
    key = bytes(f.read(), "utf-8")

f = Fernet(key)

def create_user(username, password):
    f = Fernet(key)
    token = f.encrypt(bytes(password, 'utf-8'))
    new_token = token.decode("utf-8")
    response = helper.create_user(username, new_token)
    return response

def authenticate(username, password):
    actual = helper._get_password(username)
    if actual.form == 1:
        return actual
    assert actual.form == 10
    in_db = actual.data

    if f.decrypt(in_db).decode("utf-8") == password:
        return results.Success("logged in successfully")
    return results.Error("format", "wrong password")

# NOTE: The repetition of "got_user_id [...] user_id = got_user_id.data" is because I can't encapsulate returning from the given function in a different function. I did try to cut it down as much as possible, though.
# comments on the roles of various functions are omitted as they fulfill similar duties to those described in database.py

def get_user_id(username):
    if username is not None:
        user_id_item = helper._get_id(username)
        return user_id_item
    return results.Item(None)

def search(query, username):
    got_user_id = get_user_id(username)
    if got_user_id.form != 10:
        return got_user_id
    user_id = got_user_id.data
    search_results = helper.search_exercises(query, user_id)
    return results.Success("searched successfully", search_results)

def retrieve_exercise(exercise_id, username):
    got_user_id = get_user_id(username)
    if got_user_id.form != 10:
        return got_user_id
    user_id = got_user_id.data
    search_result = helper._get_exercise_by_id(exercise_id, user_id)
    return search_result

def create_exercise(username, title, description, muscle_group):
    got_user_id = get_user_id(username)
    if got_user_id.form != 10:
        return got_user_id
    user_id = got_user_id.data
    return helper.create_exercise(title, muscle_group, description, user_id)

def create_log(exercise_id, username, weight, sets, reps, date, description, workout_id = -1):
    got_user_id = get_user_id(username)
    if got_user_id.form != 10:
        return got_user_id
    user_id = got_user_id.data
    return helper.create_log(date, exercise_id, user_id, workout_id, weight, sets, reps, description)

def update_log(log_id, username, weight, sets, reps, date, description, workout_id=-1):
    got_user_id = get_user_id(username)
    if got_user_id.form != 10:
        return got_user_id
    user_id = got_user_id.data
    return helper.update_log(user_id, log_id, date, weight, sets, reps, description, workout_id)

def add_log(log_id, username, workout_id):
    got_user_id = get_user_id(username)
    if got_user_id.form != 10:
        return got_user_id
    user_id = got_user_id.data
    return helper.add_log(user_id, log_id, workout_id)

def workout_of_log(log_id, username):
    got_user_id = get_user_id(username)
    if got_user_id.form != 10:
        return got_user_id
    user_id = got_user_id.data
    return helper.workout_of_log(user_id, log_id)

def remove_log(log_id, username):
    got_user_id = get_user_id(username)
    if got_user_id.form != 10:
        return got_user_id
    user_id = got_user_id.data
    return helper.remove_log(log_id)

def log_of_exercise(exercise_id, username):
    got_user_id = get_user_id(username)
    if got_user_id.form != 10:
        return got_user_id
    user_id = got_user_id.data
    return helper.log_of_exercise(exercise_id, user_id)

def retrieve_workouts(username):
    got_user_id = get_user_id(username)
    if got_user_id.form != 10:
        return got_user_id
    user_id = got_user_id.data
    return helper.user_workout(user_id)

def retrieve_workout(workout_id, username):
    got_user_id = get_user_id(username)
    if got_user_id.form != 10:
        return got_user_id
    user_id = got_user_id.data
    search_result = helper._get_workout_by_id(workout_id, user_id)
    return search_result

def create_workout(username, title):
    got_user_id = get_user_id(username)
    if got_user_id.form != 10:
        return got_user_id
    user_id = got_user_id.data
    # it sets the date to be the current date by default
    # because datetime.datetime.now().isoformat() returns a string like "2026-02-15T13:40:12"
    # so by taking the part before the T, we get the current date in ISO format.
    return helper.create_workout(user_id, datetime.datetime.now().isoformat().split("T")[0], title, "Enter description here...")

def update_workout(workout_id, username, date, title, description):
    got_user_id = get_user_id(username)
    if got_user_id.form != 10:
        return got_user_id
    user_id = got_user_id.data
    return helper.update_workout(user_id, workout_id, date, title, description)

def logs_associated(workout_id, username):
    got_user_id = get_user_id(username)
    if got_user_id.form != 10:
        return got_user_id
    user_id = got_user_id.data
    search_result = helper.logs_associated(workout_id, user_id)
    return search_result

def all_exercise_names(username):
    got_user_id = get_user_id(username)
    if got_user_id.form != 10:
        return got_user_id
    user_id = got_user_id.data
    return helper.all_exercise_names(user_id)

#create_user("test4", "password")
#authenticate("test4", "password").display()