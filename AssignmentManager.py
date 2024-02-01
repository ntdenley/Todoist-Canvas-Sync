"""
Canvas + Todoist Synchronization Program

Original Author: Noah Denley
Created: 01.09.2023

This program makes use of the canvasapi and todoist_api_python libraries which interface with Canvas
and Todoist APIs respectively. By running the program, you will have your current Canvas Assignments
added to your Todoist inbox so that you can easily track and complete tasks.
"""
from dateutil.parser import parse
from datetime import datetime as dt
import pytz
import traceback
from canvasapi import Canvas
from todoist_api_python.api import TodoistAPI
import json

f = open("apiKeys.json")    
data = json.load(f)

# Initialize API keys
CANVAS_API_KEY = data["canvas"]
CANVAS_API_URL = data["canvasURL"]
TODOIST_API_KEY = data["todoist"]

# Setup APIS
canvas = Canvas(CANVAS_API_URL, CANVAS_API_KEY)
todoist = TodoistAPI(TODOIST_API_KEY)

utc = pytz.UTC

# Config Settings
target_project_id = "2297078926" # Main inbox
exclude_classes = [1512975] # ENCS course


def get_existing_tasks():
    try:
        return {task.content:task.id for task in todoist.get_tasks() if task.project_id == target_project_id}
    except Exception as err:
        print(f"Failed to get task from todoist: {err}")
        return None

def create_tasks():

    # Get a list of all courses
    courses = canvas.get_courses(enrollment_state='active')
    existing_tasks = get_existing_tasks()
    if existing_tasks is None:
        return

    #Iterate through each course and its assignments
    for course in courses:
        # Get course name, slicing the course number, keeping only "CS-453" for example
        course_name = course.name[9:15] if hasattr(course, 'name') else course.id
        if course.id not in exclude_classes:
            # Fetch assignments for each class
            assignments = course.get_assignments()

            for assignment in assignments:
                # Skip assignments with no due date...
                if assignment.due_at == None:
                    continue
                # ...and assignments past due date
                if parse(assignment.due_at).replace(tzinfo=None) < dt.now().replace(tzinfo=None):
                    continue
                try:
                    task_name = f"[{course_name}] - {assignment.name}"
                    # Add new tasks
                    if not task_name in existing_tasks:
                        todoist.add_task(content=task_name, project_id=target_project_id, due_datetime=assignment.due_at, labels=[course_name])
                        print(f"[+] {assignment.name} added to Todoist Successfully")
                    # Update existing tasks
                    else:
                        todoist.update_task(task_id=existing_tasks[task_name], due_datetime=assignment.due_at, labels=[course_name])
                        print(f"[.] {assignment.name} updated on Todoist Successfully")

                except Exception as err:
                    # Handle unauthorized access
                    print(f"[!] Failed to add {assignment.name} - ({err})")
                    print(traceback.format_exc())
                    return


if __name__ == "__main__":
    create_tasks()
