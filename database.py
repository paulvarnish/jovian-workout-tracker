import sqlite3 as sql
import results
db = sql.connect("app.db")
cursor = db.cursor()

# create users, exercises, exercise logs, workouts.
# add an exercise log to a workout or remove it from that workout.
# search exercises.

class DatabaseHelper:
    def create_user(self, username: str, password: str):
        # enforce allowed characters
        for char in username:
            if char not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-.":
                return results.Error("format", "username can only contain lower/uppercase letters, numbers, underscores, dashes, full stops")
        # creates a user unless the username already exists (will be caught by the IntegrityError if it does)
        try:
            cursor.execute(f"INSERT INTO user (username, password) VALUES ('{username}', '{password}')")
            db.commit()
            return results.Success("user created successfully")
        except sql.IntegrityError:
            return results.Error("format", "username already exists")
    
    def _get_password(self, username: str):
        for char in username:
            if char not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-.":
                return results.Error("format", "username can only contain lower/uppercase letters, numbers, underscores, dashes, full stops")
        possible = cursor.execute(f"SELECT * FROM user WHERE username='{username}'").fetchall()
        db.commit()
        if len(possible) == 0:
            return results.Error("format", "username doesn't exist")
        return results.Item(possible[0][2]) # so here we specify possible[0][2] as the data. Element 2 is the password.
    
    def _get_id(self, username):
        if username is not None:
            for char in username:
                if char not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-.":
                    return results.Error("format", "username can only contain lower/uppercase letters, numbers, underscores, dashes, full stops")
        possible = cursor.execute(f"SELECT * FROM user WHERE username='{username}'").fetchall()
        db.commit()
        if len(possible) == 0:
            return results.Error("format", "username doesn't exist")
        return results.Item(possible[0][0]) # element 0 is the userId

    def create_exercise(self, title: str, muscle_group: str, description: str, user_id):
        # inserts a NEW exercise record with the given details
        same = cursor.execute(f"SELECT * FROM exercise WHERE (userId={user_id} OR userId IS NULL) AND title=?", (title, )).fetchall()
        db.commit()
        if len(same):
            return results.Error("format", "exercise of the same name already exists in your database")
        alr = cursor.execute(f"SELECT * FROM exercise WHERE userId={user_id}").fetchall()
        if len(alr) >= 500:
            return results.Error("format", "too many exercises in your database (max. 500)")
        cursor.execute(f"INSERT INTO exercise (title, muscleGroup, description, userId) VALUES (?, ?, ?, {user_id})", (title, muscle_group, description))
        db.commit()
        new_id = cursor.execute(f"SELECT * FROM exercise WHERE userId={user_id} AND title=?", (title,)).fetchall()[0][0]
        return results.Success("exercise created successfully", new_id)
    
    def all_exercise_names(self, user_id: int):
        # returns the list of all exercises that a user can select (preset, or his own)
        search_results = cursor.execute(f"SELECT * FROM exercise WHERE (userId={user_id} OR userId IS NULL)")
        db.commit()
        return results.Success("found successfully", search_results.fetchall())
    
    def create_log(self, date: str, exercise_id: int, user_id: int, workout_id: int, weight: float, sets: int, reps: float, description: str):
        # workout_id=-1 means the log is not part of a workout initially
        # weight / reps can be float; the former just means a noninteger number of kg, and "fractional reps" are an actual thing.
        exercise = cursor.execute(f"SELECT * FROM exercise WHERE id={exercise_id} AND (userId={user_id} OR userId IS NULL)").fetchall()
        if len(exercise) == 0:
            return results.Error("format", "unauthorized or exercise doesn't exist")
        if workout_id != -1:
            workout = cursor.execute(f"SELECT * FROM workout WHERE id={workout_id} AND userid={user_id}").fetchall()
            if len(workout) == 0:
                return results.Error("format", "unauthorized or workout doesn't exist")
        logs_of_exercise = self.log_of_exercise(exercise_id, user_id).data
        if len(logs_of_exercise) >= 5000:
            return results.Error("format", "too many logs (max. 5000)")
        cursor.execute(f"INSERT INTO exerciseLog (date, exerciseId, userId, workoutId, weight, sets, reps, description) VALUES (?, {exercise_id}, {user_id}, {"NULL" if workout_id == -1 else workout_id}, {weight}, {sets}, {reps}, ?)", (date, description))
        db.commit()
        return results.Success("log created successfully")
    
    def update_log(self, user_id: int, log_id: str, date: str, weight: float, sets: int, reps: float, description: str, workout_id: int):
        # this function is also called for each log in a workout when the workout is updated.
        log = cursor.execute(f"SELECT * FROM exerciseLog WHERE id={log_id}").fetchall()
        db.commit()
        if len(log) == 0:
            return results.Error("format", "log doesn't exist")
        if log[0][3] != user_id:
            return results.Error("format", "unauthorized")
        cursor.execute(f"UPDATE exerciseLog SET (date, weight, sets, reps, description{", workoutId"*(workout_id!=-1)}) = (?, ?, ?, ?, ?{", ?"*(workout_id!=-1)}) WHERE id={log_id}", (date, weight, sets, reps, description) if workout_id==-1 else (date, weight, sets, reps, description, workout_id))
        # ", workoutId"*(workout_id!=-1) is there to only update that field if it's not -1 (removing a log from a workout is a different function)
        db.commit()
        return results.Success("log updated successfully")
    
    def log_of_exercise(self, exercise_id: int, user_id: int):
        # returns all of a user's logs of a given exercise
        search_results = cursor.execute(f"SELECT * FROM exerciseLog WHERE exerciseId={exercise_id} AND userId={user_id}")
        return results.Success("found logs", search_results.fetchall())
    
    def workout_of_log(self, user_id: int, log_id: int):
        # returns which workout a log belongs to.
        same = cursor.execute(f"SELECT * FROM exerciseLog WHERE id={log_id}").fetchall()
        db.commit()
        if len(same) == 0:
            return results.Error("format", "log doesn't exist")
        if same[0][3] != user_id:
            return results.Error("format", "unauthorized")
        return results.Success("found workout of given log", same[0][4])
    
    def create_workout(self, user_id: int, date: str, title: str, description: str):
        by_user = cursor.execute(f"SELECT * FROM workout WHERE userId={user_id}").fetchall()
        db.commit()
        if len(by_user) >= 5000:
            return results.Error("format", "too many workouts (max. 5000)")
        same = cursor.execute(f"SELECT * FROM workout WHERE userId={user_id} AND title=?", (title,)).fetchall()
        db.commit()
        if len(same):
            return results.Error("format", "workout with the same name already made by this user")
        cursor.execute(f"INSERT INTO workout (userId, date, title, description) VALUES ({user_id}, ?, ?, ?)", (date, title, description))
        db.commit()
        return results.Success("workout created successfully")
    
    def update_workout(self, user_id: int, workout_id: int, date: str, title: str, description: str):
        # updates the main details (date, title, description) of a workout.
        same = cursor.execute(f"SELECT * FROM workout WHERE userId={user_id} AND title=?", (title,)).fetchall()
        db.commit()
        if len(same) and same[0][0] != workout_id:
            return results.Error("format", "workout with the same name already made by this user")
        workout = cursor.execute(f"SELECT * FROM workout WHERE id={workout_id}").fetchall()
        db.commit()
        if len(workout) == 0:
            return results.Error("format", "workout doesn't exist")
        if workout[0][2] != user_id:
            return results.Error("format", "unauthorized")
        cursor.execute(f"UPDATE workout SET (date, title, description) = (?, ?, ?) WHERE id={workout_id}", (date, title, description))
        db.commit()
        return results.Success("workout updated successfully")
    
    def user_workout(self, user_id: int):
        # returns all workouts of a given user.
        search_results = cursor.execute(f"SELECT * FROM workout WHERE userId={user_id}")
        db.commit()
        return results.Success("found workouts", search_results.fetchall())
    
    def _get_workout_by_id(self, workout_id: int, user_id: int):
        # retrieves the workout of a given ID (useful as the ID is specified in the URL)
        res = cursor.execute(f"SELECT * FROM workout WHERE id={workout_id}").fetchall()
        db.commit()
        if len(res) == 0:
            return results.Error("where", "workout doesn't exist")
        workout = res[0]
        if workout[2] != user_id and workout[2] is not None:
            return results.Error("where", "not authorized to view workout")
        return results.Success("found successfully", workout)
    
    def logs_associated(self, workout_id: int, user_id: int):
        # returns the logs of a given workout.
        res = cursor.execute(f"SELECT * FROM workout WHERE id={workout_id}").fetchall()
        db.commit()
        if len(res) == 0:
            return results.Error("where", "workout doesn't exist")
        workout = res[0]
        if workout[2] != user_id and workout[2] is not None:
            return results.Error("where", "not authorized to view workout")
        logs = cursor.execute(f"SELECT * FROM exerciseLog WHERE workoutId={workout_id}").fetchall()
        db.commit()
        return results.Success("found successfully", logs)
    
    def add_log(self, user_id: int, log_id: int, workout_id: int):
        # adds a log to a workout (not to be confused with CREATING a new log)
        log = cursor.execute(f"SELECT * FROM exerciseLog WHERE id={log_id}").fetchall()
        db.commit()
        if len(log) == 0:
            return results.Error("format", "log doesn't exist")
        if log[0][3] != user_id:
            return results.Error("format", "unauthorized")
        workout = cursor.execute(f"SELECT * FROM workout WHERE id={workout_id}").fetchall()
        db.commit()
        if len(workout) == 0:
            return results.Error("format", "workout doesn't exist")
        if log[0][4] is not None:
            return results.Error("format", "log already belongs to a workout")
        cursor.execute(f"UPDATE exerciseLog SET workoutId={workout_id} WHERE id={log_id}")
        db.commit()
        return results.Success("log added successfully")
    
    def remove_log(self, log_id: int):
        # from a workout
        log = cursor.execute(f"SELECT * FROM exerciseLog WHERE id={log_id}")
        db.commit()
        if len(log.fetchall()) == 0:
            return results.Error("format", "log doesn't exist")
        cursor.execute(f"UPDATE exerciseLog SET workoutId=NULL WHERE id={log_id}")
        db.commit()
        return results.Success("log removed successfully")
    
    def search_exercises(self, query: str, user_id: int):
        res = cursor.execute(f"SELECT * FROM exercise WHERE instr(lower(title), ?) AND (userId IS NULL OR userId=?)", (query.lower(), user_id))
        db.commit()
        return res.fetchall()
    
    def _get_exercise_by_id(self, exercise_id: int, user_id: int):
        res = cursor.execute(f"SELECT * FROM exercise WHERE id={exercise_id}").fetchall()
        db.commit()
        if len(res) == 0:
            return results.Error("where", "exercise doesn't exist")
        exercise = res[0]
        if exercise[4] != user_id and exercise[4] is not None:
            return results.Error("where", "not authorized to view exercise")
        return results.Success("found successfully", exercise)

