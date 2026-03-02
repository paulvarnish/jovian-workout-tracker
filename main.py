from nicegui import ui, app # UI
import middle # relay requests to the backend
import urllib # parse URLs
from datetime import datetime # mainly for date graphs

def is_logged_in():
    return app.storage.user.get("authenticated")

def cur_username():
    return app.storage.user.get("username")

def user_state():
    return cur_username() if is_logged_in() else None

# called on every page to show the same header everywhere
def header():
    with ui.header().style("background-color: #ADD8E6; height: 80px; padding-left: 5px; padding-right: 5px;").classes("items-center"):
        if is_logged_in():
            ui.link("My workouts", "/workouts")
            ui.link("Create exercise", "/create-exercise")
        ui.space()
        searchbar = ui.input(placeholder="Search for exercises...").props('bg-color="white" filled')
        def go_search():
            ui.navigate.to(f"/search?query={urllib.parse.quote_plus(searchbar.value)}")
        ui.icon("search").on("click", go_search)
        ui.space()
        if is_logged_in():
            ui.label(cur_username()).classes("text-black italic")
            ui.link("Log out", "/logout")
        else:
            ui.link("Create account", "/signup").classes("no-underline text-black")
            ui.link("Log in", "/login").classes("no-underline text-black")

@ui.page("/") # ui.page(given_url) syntax specifies that the following function is to be called when the URL is given_url
def home_page():
    header()

@ui.page("/create-exercise")
def create_exercise():
    if not is_logged_in():
        ui.navigate.to("/")
        return
    header()
    ui.label("Create a new exercise").classes("font-bold text-4xl") # text-4xl means the 4th font size (in ascending order)
    ui.label("Title")
    input_title = ui.input().classes("w-full")
    ui.label("Description")
    input_desc = ui.textarea().classes("w-full")
    ui.label("Muscle group (make it as customized as you want)")
    input_muscle = ui.input().classes("w-full")
    def try_create():
        result = middle.create_exercise(cur_username(), input_title.value, input_desc.value, input_muscle.value)
        if result.form == 0:
            ui.navigate.to(f"/exercise?exercise_id={result.data}")
        else:
            ui.notify(result.msg, type="negative") # the ui.notify function displays a message at the bottom of the screen
            # type="negative" makes it red
    ui.button("Create").on("click", try_create)

@ui.page("/exercise")
def exercise(exercise_id: int): # now when the page function has a parameter, it means that if you write [url]?parameter=value, it passes value as an argument to the function e.g. /exercise?exercise_id=5 -> exercise(5)
    exercise_result = middle.retrieve_exercise(exercise_id, user_state())
    if exercise_result.form != 0: # recall form=0 means the result is a Success so this redirects to the homepage unless the exercise was successfully found
        ui.navigate.to("/")
        return
    header()
    result = exercise_result.data
    ui.label(result[1]).classes("font-bold text-4xl")
    ui.label("preset exercise" if result[4] is None else "your own exercise").classes("italic")
    ui.label(f"Hits: {result[2]}")
    ui.separator()
    # the ui.grid syntax acts similarly to in CSS
    # in CSS, you can specify the columns of the grid using "fr" syntax to indicate the ratios between the widths of each column
    # so 3fr 2fr 1fr 1fr means 3/7, 2/7, 1/7, 1/7 of the horizontal space respectively
    with ui.grid(columns="1fr 1fr 1fr").classes("w-full"):
        with ui.element().classes("col-span-2"):
            ui.label(result[3])
        with ui.element():
            if is_logged_in():
                ui.label("Recent logs (date format YYYY-MM-DD)").classes("font-bold")
                logs = sorted(middle.log_of_exercise(exercise_id, cur_username()).data, key=lambda log: log[1], reverse=True)
                with ui.grid(columns="3fr 2fr 1fr 1fr").classes("w-full"):
                    for i in range(min(3, len(logs))):
                        log = logs[i]
                        ui.label("DATE")
                        ui.label("WEIGHT (KG)")
                        ui.label("SETS")
                        ui.label("REPS")

                        ui.label(log[1])
                        ui.label(log[5])
                        ui.label(log[7])
                        ui.label(log[6])

                        ui.label(log[8]).classes("col-span-3")
                        ui.icon("expand_circle_down")
                        ui.separator().classes("col-span-4")
                def show_all():
                    ui.navigate.to(f"/exerciselogs?exercise_id={exercise_id}")
                ui.button("Show all").on("click", show_all)
        with ui.element().classes("bg-white"):
            ui.label("Create a new log...").classes("font-bold text-3xl")
            with ui.grid(columns="1fr 1fr 1fr").classes("w-full"):
                ui.label("Weight")
                ui.label("Sets")
                ui.label("Reps")

                input_weight = ui.number(min=0)
                input_sets = ui.number(precision=0, min=0)
                input_reps = ui.number(min=0)

                ui.label("Date").classes("col-span-3")
                input_date = ui.date_input().classes("col-span-3")
                ui.label("Description").classes("col-span-3")
                input_desc = ui.textarea().classes("col-span-3")

                def handle():
                    if is_logged_in():
                        result = middle.create_log(exercise_id, cur_username(), input_weight.value, int(input_sets.value), input_reps.value, input_date.value, input_desc.value)
                        if result.form == 0:
                            ui.navigate.reload()
                        else:
                            ui.notify(result.msg, type="negative")
                    else:
                        ui.notify("must be logged in", type="negative")

                ui.button("Create").on("click", handle)
        logs_of_exercise = sorted(middle.log_of_exercise(exercise_id, cur_username()).data, key=lambda a: a[1])
        if len(logs_of_exercise):
            with ui.element().classes("bg-white"):
                ui.label("Your progress")
                with ui.matplotlib(figsize=(11, 10)).figure as fig:
                    x = [datetime.fromisoformat(log[1]) for log in logs_of_exercise]
                    y = [log[5] for log in logs_of_exercise]
                    fig.gca().tick_params("x", rotation=90)
                    
                    fig.gca().set_xlabel("Date")
                    fig.gca().set_ylabel("Weight")
                    fig.gca().plot_date(x, y, "-o", xdate=True) # plots a date graph, as opposed to a regular graph
                    # this way, gaps between points depend on the gap in date

                


@ui.page("/exerciselogs")
def logs(exercise_id: int):
    exercise_result = middle.retrieve_exercise(exercise_id, user_state())
    if exercise_result.form != 0:
        ui.navigate.to("/")
        return
    header()
    result = exercise_result.data
    ui.label(f"{result[1]} - your logs").classes("font-bold text-4xl")
    ui.label(f"Hits: {result[2]}")
    ui.separator()
    logs = sorted(middle.log_of_exercise(exercise_id, cur_username()).data, key=lambda log: log[1], reverse=True) # sort in DECREASING order of log[1], the second field in a log, which is the date
    def edit_log(log):
        with ui.dialog().props("persistent") as dialog, ui.card(): # the "persistent" prop means the dialog can only be closed from within the code, and not on the user-end.
            ui.label("Editing log").classes("font-bold text-2xl")
            with ui.grid(columns="1fr 1fr"):
                ui.label("Date")
                input_date = ui.date_input(value=log[1])
                ui.label("Weight")
                input_weight = ui.number(min=0, value=log[5])
                ui.label("Sets")
                input_sets = ui.number(precision=0, min=0, value=log[7])
                ui.label("Reps")
                input_reps = ui.number(min=0, value=log[6])
                ui.label("Description").classes("col-span-full")
                input_desc = ui.textarea(value=log[8]).classes("col-span-full")
            def try_save():
                attempt = middle.update_log(log[0], user_state(), input_weight.value, input_sets.value, input_reps.value, input_date.value, input_desc.value)
                if attempt.form == 0:
                    ui.navigate.reload()
                else:
                    ui.notify(attempt.msg, type="negative")
            def try_cancel():
                dialog.close()
            ui.button("Save").on("click", try_save)
            ui.button("Cancel").on("click", try_cancel)
        dialog.open()
    def edit_log_lambda(log):
        return lambda: edit_log(log)
    def add_log(log):
        with ui.dialog().props("persistent") as dialog, ui.card():
            ui.label("Add to workout").classes("font-bold text-2xl")
            workouts_list = sorted(middle.retrieve_workouts(cur_username()).data, key=lambda workout: (workout[1], workout[0]), reverse=True)
            workout_names = [workout[3] for workout in workouts_list]
            workouts_info = {workout[3]: workout[0] for workout in workouts_list}
            # creates a list of names of workouts, as well as a dictionary that corresponds each workout to its ID
            # both using comprehension syntax in Python
            input_workout = ui.select(options=workout_names, with_input=True)
            def try_add():
                attempt = middle.add_log(log[0], user_state(), workouts_info[input_workout.value])
                if attempt.form == 0:
                    ui.navigate.reload()
                else:
                    ui.notify(attempt.msg, type="negative")
            def try_cancel():
                dialog.close()
            ui.button("Add").on("click", try_add)
            ui.button("Cancel").on("click", try_cancel)
        dialog.open()
    def add_log_lambda(log):
        return lambda: add_log(log)
    def remove_log(log):
        middle.remove_log(log[0], user_state())
        ui.navigate.reload()
    def remove_log_lambda(log):
        return lambda: remove_log(log)
    with ui.grid(columns="4fr 20fr 4fr 2fr 2fr 3fr 3fr").classes("w-full"):
        for log in logs:
            workout_of_log = middle.workout_of_log(log[0], user_state()).data
            ui.space()
            ui.space()
            ui.label("WEIGHT (KG)")
            ui.label("SETS")
            ui.label("REPS")
            ui.space() # an empty element
            if workout_of_log is None:
                ui.space()
            else:
                ui.label(f"In '{middle.retrieve_workout(workout_of_log, user_state()).data[3]}'")

            ui.label(log[1])
            ui.label(log[8])
            ui.label(log[5])
            ui.label(log[7])
            ui.label(log[6])
            ui.button("Edit").on_click(edit_log_lambda(log))
            if workout_of_log is None:
                ui.button("Add to workout").on_click(add_log_lambda(log))
            else:
                ui.button("Remove from workout").on_click(remove_log_lambda(log))
            
            ui.separator().classes("col-span-full")

@ui.page("/workouts")
def workouts():
    if not is_logged_in():
        ui.navigate.to("/")
        return
    workouts_list = sorted(middle.retrieve_workouts(cur_username()).data, key=lambda workout: (workout[1], workout[0]), reverse=True) # sort the workouts in decreasing order of the pair (date, ID) so essentially decreasing by date and break ties by ID. In other words, more recently created workouts first
    header()
    ui.label("Your workouts").classes("font-bold text-4xl")
    with ui.grid(columns="1fr 1fr 1fr").classes("w-full gap-10"):
        with ui.card().classes("h-100"):
            ui.label("Create a new workout").classes("italic text-3xl")
            ui.label("Give your workout a name. You can't have two workouts with the same name.")
            input_title = ui.input().classes("w-full")
            def create_workout():
                result = middle.create_workout(cur_username(), input_title.value)
                if result.form == 0:
                    ui.navigate.reload()
                else:
                    ui.notify(result.msg, type="negative")
            ui.button("Create").on("click", create_workout)
        def go_edit(workout_id):
            return lambda: ui.navigate.to(f"/edit-workout?workout_id={workout_id}")
        for workout in workouts_list:
            with ui.card().classes("h-100"):
                ui.label(workout[3]).classes("font-bold text-3xl")
                ui.label(workout[1])
                ui.separator()
                ui.label(workout[4])
                ui.button("Edit").on("click", go_edit(workout[0]))

@ui.page("/edit-workout")
def edit_workout(workout_id: int):
    workout_result = middle.retrieve_workout(workout_id, user_state())
    if workout_result.form != 0:
        ui.navigate.to("/")
        return
    workout = workout_result.data
    header()
    with ui.row():
        ui.label(f"Editing {workout[3]}").classes("font-bold text-4xl")
        save_changes = ui.button("Save changes")
        discard_changes = ui.button("Discard changes")
        
    ui.label("Title")
    input_global_title = ui.input(value=workout[3]).classes("w-full")
    ui.label("Date")
    input_global_date = ui.date_input(value=workout[1]).classes("w-full")
    ui.label("Description")
    input_global_desc = ui.textarea(value=workout[4]).classes("w-full")
    ui.label("Logs")
    log_list = []
    logs_associated = middle.logs_associated(workout_id, user_state()).data
    for log in logs_associated:
        log_dict = {
            "log_id": log[0], # can be None
            "exercise_id": log[2],
            "date": log[1],
            "weight": log[5],
            "sets": log[7],
            "reps": log[6],
            "description": log[8],
            "deleted": False,
            "edited": False,
            "existing": 2
        }
        log_list.append(log_dict)
        # existing = 0 means it's a completely new log
        # existing = 1 means it's a log that existed in the database but is newly added to the workout
        # existing = 2 means it's a log that was already in the workout
        # deleted overrides edited; the latter is always set to True after the log is changed once, even if changes are later rolled back
    log_grid = ui.element().classes("w-full")
    log_elements = []
    # is a list of dictionaries that store the NiceGUI elements responsible for displaying a log's information.

    def update_log(i):
        log = log_list[i]
        grid_here = log_elements[i]["grid"]
        with grid_here:
            log_elements[i]["exercise"].set_text(middle.retrieve_exercise(log["exercise_id"], user_state()).data[1])
            log_elements[i]["exercise"].classes("font-bold")
            log_elements[i]["description"].set_text(log["description"])
            log_elements[i]["date"].set_text(log["date"])
            log_elements[i]["weight"].set_text(log["weight"])
            log_elements[i]["sets"].set_text(log["sets"])
            log_elements[i]["reps"].set_text(log["reps"])
        if log["deleted"]:
            log_elements[i]["delete"].set_text("Restore")
        else:
            log_elements[i]["delete"].set_text("Delete")
        if grid_here.classes.count("bg-red"): grid_here.classes.remove("bg-red")
        if grid_here.classes.count("bg-green"): grid_here.classes.remove("bg-green")
        if grid_here.classes.count("bg-yellow"): grid_here.classes.remove("bg-yellow")
        if log["deleted"]:
            grid_here.classes("bg-red")
        elif log["existing"] != 2:
            grid_here.classes("bg-green")
        elif log["edited"]:
            grid_here.classes("bg-yellow")
    def go_toggle_delete_log(i):
        log_list[i]["deleted"] = not log_list[i]["deleted"]
        update_log(i)
    def toggle_delete_log(i):
        return lambda: go_toggle_delete_log(i)
    def go_edit_log(i):
        if log_list[i]["deleted"]:
            return
        with ui.dialog().props("persistent") as dialog, ui.card():
            ui.label("Editing log").classes("font-bold text-2xl")
            with ui.grid(columns="1fr 1fr"):
                all_exercises = middle.all_exercise_names(cur_username())
                exercise_info = {exercise[1]: exercise[0] for exercise in all_exercises.data}
                exercise_names = [exercise[1] for exercise in all_exercises.data]
                ui.label("Exercise")
                input_exercise = ui.select(options=exercise_names, with_input=True, value=middle.retrieve_exercise(log_list[i]["exercise_id"], user_state()).data[1])
                ui.label("Date")
                input_date = ui.date_input(value=log_list[i]["date"])
                ui.label("Weight")
                input_weight = ui.number(min=0, value=log_list[i]["weight"])
                ui.label("Sets")
                input_sets = ui.number(precision=0, min=0, value=log_list[i]["sets"])
                ui.label("Reps")
                input_reps = ui.number(min=0, value=log_list[i]["reps"])
                ui.label("Description").classes("col-span-full")
                input_desc = ui.textarea(value=log_list[i]["description"]).classes("col-span-full")
            def try_save():
                log_list[i]["exercise_id"] = exercise_info[input_exercise.value]
                log_list[i]["date"] = input_date.value
                log_list[i]["weight"] = input_weight.value
                log_list[i]["sets"] = input_sets.value
                log_list[i]["reps"] = input_reps.value
                log_list[i]["description"] = input_desc.value
                log_list[i]["edited"] = True
                dialog.close()
                update_log(i)
            def try_cancel():
                dialog.close()
            ui.button("Save").on("click", try_save)
            ui.button("Cancel").on("click", try_cancel)
        dialog.open()
    def edit_log(i):
        return lambda: go_edit_log(i)
    
    def add_element(i):
        with log_grid:
            grid_here = ui.grid(columns="12fr 1fr 1fr 1fr 1fr").classes("w-full")
            with grid_here:
                exercise_label = ui.label()
                ui.label("DATE")
                ui.label("WEIGHT (KG)")
                ui.label("SETS")
                ui.label("REPS")
                description_label = ui.label()
                date_label = ui.label()
                weight_label = ui.label()
                sets_label = ui.label()
                reps_label = ui.label()
                with ui.row().classes("col-span-full"):
                    ui.button("Edit").on("click", edit_log(i))
                    delete_button = ui.button("Delete").on("click", toggle_delete_log(i))
                ui.separator().classes("col-span-full")
            log_element = {
                "exercise": exercise_label,
                "date": date_label,
                "weight": weight_label,
                "sets": sets_label,
                "reps": reps_label,
                "description": description_label,
                "delete": delete_button,
                "grid": grid_here
            }
            log_elements.append(log_element)
    
    all_exercises = middle.all_exercise_names(cur_username())
    exercise_info ={exercise[1]: exercise[0] for exercise in all_exercises.data}
    exercise_names = [exercise[1] for exercise in all_exercises.data]
    
    
    for i, log in enumerate(log_list):
        add_element(i)
        update_log(i)
    
    with ui.grid(columns="2fr 1fr 1fr 1fr").classes("w-200"):
        ui.label("Add a new log - give exercise name, weight, sets, reps. Or use an existing log. Note logs created here won't save for their respective exercises unless you click 'save changes' above.").classes("col-span-full")
        ui.space()
        ui.label("WEIGHT (KG)")
        ui.label("SETS")
        ui.label("REPS")
        
        input_exercise = ui.select(options=exercise_names, with_input=True)
        input_weight = ui.number(min=0)
        input_sets = ui.number(precision=0, min=0)
        input_reps = ui.number(min=0)
        ui.label("Date").classes("col-span-full")
        input_date = ui.date_input().classes("col-span-full")
        ui.label("Description").classes("col-span-full")
        input_desc = ui.textarea().classes("col-span-full")
        def create_log():
            if input_exercise.value is None:
                ui.notify("Please enter an exercise", type="negative")
                return
            log_list.append({
                "log_id": None, # can be None
                "exercise_id": exercise_info[input_exercise.value],
                "date": input_date.value,
                "weight": input_weight.value,
                "sets": input_sets.value,
                "reps": input_reps.value,
                "description": input_desc.value,
                "deleted": False,
                "edited": False,
                "existing": 0
            })
            add_element(len(log_list) - 1)
            update_log(len(log_list) - 1)
            input_exercise.value = None
            input_date.value = None
            input_weight.value = None
            input_sets.value = None
            input_reps.value = None
            input_desc.value = None
        def choose_log():
            with ui.dialog().props("persistent") as dialog, ui.card():
                ui.label("Choose the exercise, then enter the date of the log. Finally click 'search' and find the right log.")
                input_exercise = ui.select(options=exercise_names).classes("w-full")
                with ui.grid(columns="3fr 1fr").classes("w-full"):
                    input_date = ui.date_input()
                    search_button = ui.button("Search")
                log_results = ui.grid(columns="5fr 1fr 1fr 1fr 1fr").classes("w-full")
                def search_logs():
                    log_results.clear()
                    if input_exercise.value is None:
                        ui.notify("Please enter an exercise", type="negative")
                        return
                    logs_of_exercise = middle.log_of_exercise(exercise_info[input_exercise.value], cur_username()).data
                    def add_log(log):
                        dialog.close()
                        log_list.append({
                            "log_id": log[0], # can be None
                            "exercise_id": log[2],
                            "date": log[1],
                            "weight": log[5],
                            "sets": log[7],
                            "reps": log[6],
                            "description": log[8],
                            "deleted": False,
                            "edited": False,
                            "existing": 1
                        })
                        # passing len(log_list) - 1 to the functions means that the program should pull data from the last element of the lists (i.e. at their lengths minus one) when populating the page with information
                        add_element(len(log_list) - 1)
                        update_log(len(log_list) - 1)
                    def add_log_lambda(log):
                        return lambda: add_log(log)
                    with log_results:
                        for log in logs_of_exercise:
                            if log[1] == input_date.value:
                                ui.label("DESCRIPTION")
                                ui.label("WEIGHT")
                                ui.label("SETS")
                                ui.label("REPS")
                                ui.space()
                                ui.label(log[8])
                                ui.label(log[5])
                                ui.label(log[7])
                                ui.label(log[6])
                                ui.button("Add").on("click", add_log_lambda(log))
                                ui.separator().classes("col-span-full")
                search_button.on("click", search_logs)
                def leave():
                    dialog.close()
                ui.button("Cancel").on("click", leave)

            dialog.open()
        with ui.row().classes("col-span-full"):
            ui.button("Create").on("click", create_log)
            ui.button("Import from existing log...").on("click", choose_log)
        
    def go_save():
        result = middle.update_workout(workout_id, user_state(), input_global_date.value, input_global_title.value, input_global_desc.value)
        if result.form != 0:
            ui.notify(result.msg, type="negative")
            return
        for log in log_list:
            if log["deleted"]:
                if log["existing"] == 2:
                    middle.remove_log(log["log_id"], user_state())
                # if delete a created one (i.e. existing is 0 or 1), do nothing
            else:
                if log["existing"] == 2 and not log["edited"]:
                    continue # no update needed
                if log["existing"] == 2:
                    middle.update_log(log["log_id"], user_state(), log["weight"], log["sets"], log["reps"], log["date"], log["description"])
                elif log["existing"] == 1:
                    middle.update_log(log["log_id"], user_state(), log["weight"], log["sets"], log["reps"], log["date"], log["description"], workout_id)
                else:
                    middle.create_log(log["exercise_id"], user_state(), log["weight"], log["sets"], log["reps"], log["date"], log["description"], workout_id)
        ui.navigate.reload()
    def go_discard():
        ui.navigate.to("/workouts")
    
    save_changes.on("click", go_save)
    discard_changes.on("click", go_discard)


@ui.page("/search")
def search(query: str):
    search_results_obj = middle.search(query, user_state())
    if search_results_obj.form != 0:
        ui.navigate.to("/")
        return
    search_results = search_results_obj.data
    header()
    ui.label(f"Search results for '{query}'")
    ui.label(f"{len(search_results)} result{"" if len(search_results) == 1 else "s"} found.") # it puts the word "result" in plural unless there's exactly one result (just a little detail)
    def view_exercise(exercise_id):
        return lambda: ui.navigate.to(f"/exercise?exercise_id={exercise_id}")
    with ui.grid(columns="1fr 1fr 1fr").classes("w-full gap-10"):
        for result in search_results:
            with ui.card().classes("h-100"):
                ui.label(result[1]).classes("font-bold text-3xl")
                ui.label("preset exercise" if result[4] is None else "your own exercise").classes("italic")
                ui.label(f"Hits: {result[2]}")
                ui.label(result[3]).classes("text-body1").classes("absolute-bottom w-100")
                ui.button("View").classes("absolute-bottom-right").on("click", view_exercise(result[0]))

@ui.page("/signup")
def signup():
    header()
    with ui.card().classes("absolute-center"):
        username = ui.input(label="Username")
        password = ui.input(label="Password", password=True, password_toggle_button=True)
        confirm_password = ui.input(label="Confirm password", password=True, password_toggle_button=True)
        def try_create():
            if password.value == confirm_password.value:
                response = middle.create_user(username.value, password.value)
                if response.form == 0:
                    app.storage.user["authenticated"] = True
                    app.storage.user["username"] = username.value
                    ui.navigate.to("/")
                else:
                    ui.notify(response.msg, type="negative")
            else:
                ui.notify("passwords don't match", type="negative")
        ui.button(text="Sign up", on_click=try_create)

@ui.page("/login")
def login():
    header()
    with ui.card().classes("absolute-center"):
        username = ui.input(label="Username")
        password = ui.input(label="Password", password=True, password_toggle_button=True) # password_toggle_button allows you to view the password if you want
        def try_login():
            response = middle.authenticate(username.value, password.value)
            if response.form == 0:
                app.storage.user["authenticated"] = True
                app.storage.user["username"] = username.value
                ui.navigate.to("/")
            else:
                ui.notify(response.msg, type="negative")
        ui.button(text="Login", on_click=try_login)

@ui.page("/logout")
def logout():
    app.storage.user["authenticated"] = False
    app.storage.user["username"] = None
    ui.navigate.to("/")


ui.run(storage_secret="secret") # the storage_secret argument allows the program to keep data persistent even when the user closes the page. This is important to keep users logged in over time.
# this is shown via the app.storage.user dictionary, which contains a boolean for whether the user is authenticated, as well as a string which is the user's current username.