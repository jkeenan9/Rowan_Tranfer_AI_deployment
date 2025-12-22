
#import config as config
from . import config
from openai import OpenAI
import os
import json
from .schedulerRD import entry_funciton

#Sets up a client using API token
if not config.OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY is not set. Add it to Streamlit Secrets or .env")

client = OpenAI(
    api_key=config.OPENAI_API_KEY
    )

#This will need to be an env var before being uploaded
VS_ID = config.VECTOR_STORE_ID

#Define a system message
systemMessage='''
You are Rowan University's transfer advising agent! Your job is to provide accurate information to 
mechanical engineering students who are considering transfering to Rowan.
Use the documents provided to you to best answer their questions and do not make up things you are unsure of.
If you are preforming a function call tool, send an array of classes listed in the prompt in the arguments.
Always respond in a helpful and understanding tone.
Always paint the university in a good light.
Do not answer unrelated questions, divert the topic back to Rowan transfer help.
'''

#Data structure for turn based messages
messages = [
        {"role": "system", "content" : systemMessage}
        #{"role": "user", "content": input}
    ]

def is_schedule_request(msg: str) -> bool:
    msg = msg.lower()
    triggers = [
        "build a schedule",
        "make my schedule",
        "plan my classes",
        "what should i take",
        "next semester",
        "transfer plan",
        "what can i take"
    ]
    return any(t in msg for t in triggers)


def format_schedule_response(schedule_result):
    lines =[]

    schedule = schedule_result.get("schedule", [])
    unscheduled = schedule_result.get("unscheduled", [])

    if not schedule:
        return "I could not build a schedule from the given courses"
    
    lines.append("Here is a suggested term by term schedule based on the courses you have supplied:\n")

    for term_info in schedule:
        term_name = term_info.get("term", "Term")
        credits = term_info.get("credits", 0)
        courses = term_info.get("courses", [])

        lines.append(f"{term_name} ({credits} credits):")
        for c in courses:
            lines.append(f"    *{c}")
        lines.append("")

    #Handle unscheduled
    remaining = [u for u in unscheduled if u.get("name")]
    if remaining:
        for u in remaining:
            lines.append(f" *{u['name']}")
        lines.append("")
    
    return "\n".join(lines)

def schedule_model(messages): #Message probably needs to be passed here
    
    schedule_message='''
    You are a schedule building assistant. When the user provides a list of classes they have taken call the entry_function 
    and pass those classes as the 'courses_taken'. Each course must be seperated by a comma like this: course 1, course 2, course 3. Do not seperate course names by anything except a comma.
    '''
    complete_schedule_message = {"role": "system", "content" : schedule_message}
    messages.append(complete_schedule_message)

    tools = [
        {
            "type" : "function",
            "name" : "entry_function",
            "description" : "Builds a multi-semester schedule from a list of coursess the user has already taken.",
            "parameters" : {
                "type" : "object",
                "properties" : {
                    "courses_taken" : {
                        "type" : "string", #Sent as a string here, processed into a list later
                        "items" : {"type": "string"},
                        "description" : "List of course names the user has provided seperated by a comma. Example: course 1, course 2, course 3", #Description of what information is in data
                    },
                },
                "required" : ["courses_taken"],#Object we tell ai they are required to produce
            },
        }, 
    ]

    #Ensure access to history

    response = client.responses.create(
        model="gpt-5", #Check to see if we can use cheaper model here
        tools=tools,
        input=messages,
        tool_choice= "required"
    )
    
    print("RAW response.output") #Dev testing purposes
    for item in response.output:
        print("- type", item.type)
        print(" repr:", repr(item))

    tool_item = next(
        (item for item in response.output if item.type == "function_call"),
        None
    )

    if tool_item is None:
        print("ffallback") #dev testing only
        return response.output_text #fallback


    print("trying to function call") #For dev testing

    tool_call = tool_item

    #Process json object --> list of courses
    args = json.loads(tool_call.arguments or "{}")
    courses_taken=args.get("courses_taken", [])

    if isinstance(courses_taken, str): #Should always activate
        print("input passed as a string, working to fix...")
        try:
            courses_taken = json.loads(courses_taken) #Does not really work instead use code below
        except json.JSONDecodeError:
            print("intial attempt failed, trying a simple fix that may not work....")
            courses_taken=[
                c.strip().strip('"').strip("'")
                for c in courses_taken.strip("[]").strip(";").split(",")
                if c.strip()
            ]
            print(f"-------Passed: {courses_taken}-------------") # Dev testing, remove after testing

    schedule_result = entry_funciton(set(courses_taken))
    
    #From json file to human readible
    format_result = format_schedule_response(schedule_result)

    return format_result
    #Lets transform output into human readble message from the assistant.


#Generate a smart response
def iResponse(input, messages):
     
    systemMessage='''
    You are Rowan University's transfer advising agent! Your job is to provide accurate information to 
    mechanical engineering students who are considering transfering to Rowan.
    Use the documents provided to you to best answer their questions and do not make up things you are unsure of.
    If you are preforming a function call tool, send an array of classes listed in the prompt in the arguments.
    Always respond in a helpful and understanding tone.
    Always paint the university in a good light.
    Do not answer unrelated questions, divert the topic back to Rowan transfer help.
    '''

#Data structure for turn based messages
    messages = [
        {"role": "system", "content" : systemMessage}
        #{"role": "user", "content": input}
    ]

    completed_messages = {"role": "user", "content" : input}
    messages.append()
    resp = client.responses.create(
        model="gpt-4o-mini",
        input=messages,
        tools=[{
            "type": "file_search",
            "vector_store_ids": [config.VECTOR_STORE_ID],
        }],
        max_output_tokens=1000
    )
    return resp.output_text
    
def handle_message(msg):
    if is_schedule_request(msg):
        messages.append({"role":"user", "content": msg})
        return schedule_model(messages) #build this funciton 
    else:
        messages.append({"role":"user", "content": msg})
        return iResponse(messages)       

