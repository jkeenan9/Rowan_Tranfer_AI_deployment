import csv
import json
from pathlib import Path
import os

def csv_to_dict(file):
    big_dict={}

    with open(file, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)

        for row in reader:
            key = row["title"] #This will be key in big dictionary

            value_dict = {k: v for k,v in row.items() if k!= "title"} #Creates dictionaries in value

            for field in ("prereq_all", "prereq_one_of"):

                raw = value_dict.get(field, "") #Gather prereqs

                if raw is None:
                    raw = "" #Normalization
                
                raw = raw.strip()

                if raw == "" or raw.lower() == "none":
                    value_dict[field] = [] #Creates empty list if no prereqs
                
                else:
                    #List comprehension, takes string and turns it into a list
                    value_dict[field] = [item.strip() for item in raw.split(",")]

            raw_priority = value_dict.get("Priority").strip().lower()

            if raw_priority in ("true", "1", "y", "TRUE"):
                value_dict["Priority"] = True
            elif raw_priority in ("false", "False", "FALSE"):
                value_dict["Priority"] = False
            else:
                value_dict["Priority"] = False #if nothing defined
            # Normalize offered_in
            
            
            raw_offered = str(value_dict.get("offered_in", "")).strip()
            if raw_offered == "" or raw_offered.lower() == "none":
                value_dict["offered_in"] = []
            else:
                # Split into list and lowercase
                value_dict["offered_in"] = [item.strip().lower() for item in raw_offered.split(",")]


            big_dict[key] = value_dict
    return big_dict

def assume_completed(completed):
    changed = True
    while changed:
        changed = False
        for course in list(completed):
            prereqs = catalog[course]["prereq_all"] + catalog[course]["prereq_one_of"]

            for p in prereqs:
                if p not in completed:
                    completed.add(p)
                    changed = True
    return completed

def can_take(course_name, completed, catalog):
    course = catalog[course_name]
    all_of = course.get("prereq_all", [])
    one_of = course.get("prereq_one_of", [])

    #Ensure every prereq is met before recommending a course
    for p in all_of:
        if p not in completed:
            return False
        
    #Prereq all and completed
    if not one_of:
        return True

    for p in one_of:
        if p in completed:
            return True
    
    return False #If no conditions are tripped


def build_semester(term, completed, courses_remaining, catalog, credit_limit): #These all need to be passed
    eligible = []
    for course_name in courses_remaining:
        course_name_dict = catalog[course_name]
        #print(course_name)
        if term not in course_name_dict["offered_in"]:
            #print("Not finding term")
            continue 
        if not can_take(course_name, completed, catalog):
            #print("Not passing funciton")
            continue

        eligible.append(course_name)
        #print(course_name)

    #print("Out of for loop")
    #Here is the lambda function line that I don't understand
    eligible.sort(key=lambda cname: (not catalog[cname]["Priority"],)) #This will put any classes with priority = True first
    #print(eligible)
    

    #Credit limit
    semester_courses = []
    used_credits = 0

    for course_name in eligible:
        credits_str = catalog[course_name]["credits"]
        credits = int(credits_str)
        if used_credits + credits <= credit_limit:
            semester_courses.append(course_name)
            used_credits += credits

    return semester_courses, used_credits


def debug_remaining(courses_remaining, courses_completed, catalog):
    print("\n===== DEBUG REMAINING COURSES =====")
    for cname in courses_remaining:
        if cname not in catalog:
            print(f"\n{cname}: NOT FOUND in catalog (name mismatch?)")
            continue

        data = catalog[cname]
        offered = data.get("offered_in", [])
        all_of = data.get("prereq_all", [])
        one_of = data.get("prereq_one_of", [])

        print(f"\nCourse: {cname}")
        print("  offered_in:", offered)
        print("  prereq_all:", all_of)
        print("  prereq_one_of:", one_of)
        print("  can_take with final completed?:", can_take(cname, courses_completed, catalog))




def entry_funciton(taken):
    #Path of CSV File
    #csv_file=r"C:\Users\jimmy\Documents\fall2025\RowanProj\development\csv2dictCheck.csv"
    csv_file = Path(__file__).resolve().parents[1] / "data" / "csv2dictCheck.csv"
    #Sanity check (can be removed after ensuring it works)
    print("CWD:", os.getcwd())
    print("CSV path:", csv_file)
    print("Exists:", csv_file.exists())
    #End of sanity check
    global catalog
    catalog = csv_to_dict(csv_file)
    all_courses = set(catalog.keys())

    #This should now come from our ai
    #taken = {"Prin & Apps ECE for Non Majors", "Sophomore Clinic II", "Dynamics", "Mat Sci. and Mfg.", "Intro Thermal Fluid Sci.", "Math for Eng Analysis", "Chemistry 1", "Intro Sci Prog: Matlab/CAD"}
    courses_completed = assume_completed(set(taken))
    courses_remaining = all_courses - courses_completed


    schedule = [] #Overall schedule populates at the end
    max_credits = 18
    semester_counter = 0
    no_progress_terms = 0
    starting_semester = "fall"
    next_semester = "spring"
    building = True
    while courses_remaining and no_progress_terms < 4:  #Best way for now
        term_id = semester_counter % 2

        #Term logic
        if term_id == 0:
            term = starting_semester
        else:
            term = next_semester 

        semester_courses, semester_credits =  build_semester(term, courses_completed, courses_remaining, catalog, max_credits)
        semester_counter += 1
        if not semester_courses:
            #print(f"No courses schedulable in {term}. Trying next term...")
            no_progress_terms += 1
            semester_counter += 1
            continue

        no_progress_terms = 0 #If it gets through if statement above, reset
        
        schedule.append({
            "term" : term.capitalize(),
            "credits": semester_credits,
            "courses" : semester_courses
        }) 
        """
            [
                {
                    "name" : cname,
                }
                for cname in semester_courses #Not surewhat this line does
            ]
        """

        
        for course_name in semester_courses:
            courses_completed.add(course_name)
            courses_remaining.remove(course_name)
        
        courses_completed = assume_completed(courses_completed) #Chat suggested this

    unscheduled = []
    for cname in courses_remaining:
        data = catalog[cname]
        unscheduled.append({
            "name" : cname
        })

    
    result = {
        "schedule" : schedule,
        "unscheduled" : unscheduled

    }
    return result

    """
    for entry in schedule:
        term = entry["term"].capitalize()
        print(term, "Credits:", semester_credits)
        for course in entry["courses"]:
            print("-", course)

    print("\nUnscheduled courses still in courses_remaining:")
    for cname in courses_remaining:
        print(" -", cname)


    debug_remaining(courses_remaining, courses_completed, catalog)
    """