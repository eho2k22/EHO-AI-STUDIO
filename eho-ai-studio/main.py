from flask import Flask, render_template, request, session

# OpenAI Library
# Copyright (c) 2023 OpenAI
# https://github.com/openai/openai-python


import openai
import os
import io
import warnings
import json

import smtplib
from email.mime.text import MIMEText
import email.message 

from supabase import create_client
from array import array 


userapikey=""
userprompt=""
usertemp=""
useremail=""
answer = ""
engine_temperature = 0.5
response = None
response_edited = None

jokeprompt = "Tell me a funny joke about AI in 25 words or less"
jokeanswer = ""


convoconjunctor= " given that "
convoconjunctor2 = " , as well as that "
response_err = "there is no answer"
response_err2 = "given information does not provide"
response_filter = "I am"
response_filter2 = "I'm"
response_filter3 = "My"
response_filter4 = "my"
response_filter5 = "I"
response_default = " requiring more research "
clear_convo = "CLEAR_CONVO"

supa_url = os.environ['SUPABASE_URL']
supa_key = os.environ['SUPABASE_KEY']

supabase = create_client(supa_url, supa_key)

print("supabase client initiated successfully! ")

records=[]

#prompt of the day 
pod_prompt = ""
pod_results=[]
pod_results = supabase.table('Transcripts').select("*").eq('rank', 888).execute()

for pod_record in pod_results:

    # fetch the JSON object at pod_record[1], and get the first and only record at pod_record[1][0]
    # convert the JSON DATA object into a Python dictionary
    json_obj = pod_record[1][0]
    dict_data = json.loads(json.dumps(json_obj))


    # Fetch and Print the PROMPT value
    print(" Prompt of the Day = " ) 
    pod_prompt = list(dict_data.values())[2]
    print(pod_prompt) 

    break

# Use SYSTEM API key

try:
    openai.api_key = os.environ['OPENAI_KEY']
except:
    print("Sorry, No API Key available")


# Define a function to generate a response using OpenAI API
def generate_response(prompt, previous_context):
    if previous_context == "" or previous_context is None :
        print("GENERATE_RESPONSE CONTEXT is EMPTY!! ")
        response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=prompt,
        max_tokens=1000,
        n=1,
        stop=None,
        temperature=0.5
         )
    else: 
        #print("GENERATE_RESPONSE CONTEXT NOT EMPTY :  " + previous_context)
        response = openai.Completion.create(
            engine="text-davinci-003",
            prompt=prompt + convoconjunctor + previous_context,
            max_tokens=1000,
            n=1,
            stop=None,
            temperature=0.5
         )
    return response.choices[0].text.strip()


app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ['OPENAI_KEY']

@app.route('/conversation', methods=['GET', 'POST'])
def conversation():

    convo_history = ['']
    convo_context = ""
    dict_data = {}
    convo_history_str = json.dumps({})



    # check if the session variable convo_history exists, if not create it
    # print("CURRENT Session ID:", session.sid)

    if ('convo_ID' not in session) or (session['convo_ID'] == 0) or (session['convo_ID'] == 10005) or (session['convo_ID'] == 10000)  :
        
        print("Initializing NEW session Variable convo_ID")
    
        # FETCH latest convo_ID record 
        cid_results=[]
        cid_results = supabase.table('Conversations').select("*").order('convo_ID').limit(1).execute()
        cid_record_id=0
        cid_record_history=['']

        for cid_record in cid_results:
    
            # FETCH the JSON object from the list
            # convert the JSON DATA object into a Python dictionary
            cid_json_obj = cid_record[1][0]
            dict_data = json.loads(json.dumps(cid_json_obj))


            # Fetch and Print the convoID value
            cid_record_id = list(dict_data.values())[2]
            print("Conversation ID = " + str(cid_record_id) ) 

            cid_record_history = list(dict_data.values())[4]

            break

        # setting NEW convo_ID to decrement 5 
        session['convo_ID'] = cid_record_id - 5 
        print(" new SESSION ID = " + str(cid_record_id - 5 ) ) 
        # insert NEW convo_ID into DB 
        #save UserPrompt and Answer as a record into Transcripts table

        record = {
        'convo_ID': cid_record_id - 5
        }

        #reset records before appending 
        records = []
        records.append(record)

        # Insert the records into the NFT table
        try:
            data = supabase.table('Conversations').insert(records).execute()
        except:
            print("OOPS.. INSERT went WRONG while saving New Conversation ID into DB ")
            return render_template("error.html", userapikey=openai.api_key)


    else:
        # convo_ID already exists, fetch the existing convo data 
        print("Session Variable convo_ID ALREADY EXISTS !!")
        
        convo_ID = session['convo_ID']
        
        print("EXISTING Session Variable convo_ID == " + str(convo_ID))
    
        cid_results=[]
        cid_results = supabase.table('Conversations').select("*").eq('convo_ID', convo_ID).execute()

        # if len(cid_results) == 0 --> meaning Conversation ID data no longer exists in DB !! 
        # In which case,  need to RESET Session Convo_ID and Re-create NEW Convo_ID 


        for cid_record in cid_results:
    
            # fetch the JSON object from the list
            # convert the JSON DATA object into a Python dictionary
            cid_json_obj = cid_record[1][0]
            dict_data = json.loads(json.dumps(cid_json_obj))

            convo_context = list(dict_data.values())[3]
            print("convo_context equals ") 
            print(convo_context)
            convo_history = list(dict_data.values())[4]

            break
    
    if request.method == "GET":
        #return render_template("conversation.html")
        if ('convo_ID' not in session) or (session['convo_ID'] == 0) or (session['convo_ID'] == 10005) or (session['convo_ID'] == 10000)  :
            return render_template('conversation.html', conversation_history=convo_history, conversation_length=len(convo_history))

        else : 
            convo_ID = session['convo_ID']
        
            print("EXISTING Session Variable convo_ID == " + str(convo_ID))
    
            cid_results=[]
            cid_results = supabase.table('Conversations').select("*").eq('convo_ID', convo_ID).execute()

            if (convo_context is None) :
                convo_context = ""
            if (convo_history is None) :
                convo_history = ['']
    
            # Convert the array to a JSON string and remove the square brackets
            convo_history_str = json.dumps(convo_history, ensure_ascii=False)[1:-1]
        
            print("convo_history_str is : ") 
            print(convo_history_str)
            
            if (convo_context == ""):
                return render_template('conversation.html')            
            else:
                print("about to GET conversation.html,  what is the convo_histroy_str ? " + convo_history_str)
                return render_template('conversation.html', conversation_history=convo_history, conversation_length=len(convo_history), convo_history_str=convo_history_str)


    elif request.method == 'POST':
        response = ""
        response_edited = ""
        prompt = request.form['prompt']

    
        if convo_context is None:
            print("about to POST QUERY,  convo_context is NONE ???")
            convo_context = ""
            response = ""    
        if convo_history is None:
            print("about to POST QUERY,  convo_history is NONE ???")
            convo_history = ['']

        if (clear_convo.lower() != prompt.lower() ):
            print("NOT CLEAR_CONVO command!!!")
            response = generate_response(prompt, convo_context)
            # if response is empty or null,  AI may be confused.  Clear Context, but Leave History as is 
            if ((response == "" or response is None) and convo_context != ""):
                print("RESPONSE is EMPTY... may be confused !! ")
                convo_context = ""
                supabase.table('Conversations').update({"convo_context" : ""}).eq('convo_ID', convo_ID).execute()
                response = generate_response(prompt, convo_context)
            
            # if response includes I'm or I am,   AI may later get confused.  Adjust Context
            if (response_filter.lower() in response.lower() or 
                    response_filter2.lower() in response.lower() or 
                    response_filter3.lower() in response.lower() ):
                print("RESPONSE contains I'm or I am , maybe confused.  Adjust Response!! ")
                response_edited = response.replace(response_filter, "You are")
                print("EDITED RESPONSE 1  : " + response_edited) 
                response_edited = response_edited.replace(response_filter2, "You are")
                print("EDITED RESPONSE 2 : " + response_edited) 
                response_edited = response_edited.replace(response_filter3, "Your")
                print("EDITED RESPONSE 3 : " + response_edited) 
                response_edited = response_edited.replace(response_filter4, "your")
                print("EDITED RESPONSE 4 : " + response_edited) 
                response_edited = response_edited.replace(response_filter5, "you")
                print("EDITED RESPONSE 5 : " + response_edited) 
            
            # if response includes err or err2  AI may be confused.  Clear Context, but Leave History as is 
            if ((response_err.lower() in response.lower() or response_err2.lower() in response.lower()) 
                    and convo_context != ""):
                print("RESPONSE suggests AI may be confused !! ")
                convo_context = ""
                supabase.table('Conversations').update({"convo_context" : ""}).eq('convo_ID', convo_ID).execute()
                response = generate_response(prompt, convo_context)

          
        print("prompt  = " + prompt) 
        print("response = " + response) 


        if response is None:
            response = ""

        if response_err.lower() in response.lower() : 
            response = response_default
        
        if response_err2.lower() in response.lower() : 
            response = response_default

        if (convo_context is not None):
            print("convo_context = " + convo_context)

        if ((convo_history is not None) and len(convo_history) >= 10) or (clear_convo.lower() in prompt.lower()):

            #empty conversation if converesation context > 10
            print("convo_context = " + convo_context)
            print("About to empty conversation history when reaching 10 !!") 
            convo_history.clear()

            print("about to reset convo_context !!") 
            convo_context = ""
            if (clear_convo.lower() in prompt.lower()):
                print("CLEARING CONVERSATION !!!") 
                #CLEARING OUT Conversation ID  in DB
                supabase.table('Conversations').update({"convo_context" : "", "convo_history" : [] }).eq('convo_ID', convo_ID).execute()
                return render_template('conversation.html', conversation_history=[], conversation_length=0)
  
    
        #previous_response defined as CONTEXT 
        #convo_context = convo_context + convoconjunctor + response 
        print("Current Convo Pair :  " + prompt + " -xxxx- " + response) 

        convo_history.append(prompt + " -xxxx- " + response) 
        print("convo_history length AFTER APPEND = " + str(len(convo_history))) 

        if ((convo_context == "") or (convo_context is None)) :
            if (response_edited == ""):
                convo_context = convoconjunctor + response 
            else:
                convo_context = convoconjunctor + response_edited
        else :
            if (response_edited == ""):
                convo_context = convo_context + convoconjunctor2 + response 
            else:
                convo_context = convo_context + convoconjunctor2 + response_edited

        print(" LATEST Convo Context before committing to DB:  " + convo_context) 

        # Convert the array to a JSON string and remove the square brackets
        convo_history_str = json.dumps(convo_history, ensure_ascii=False)[1:-1]

        
        print("convo_history_str is : ") 
        print(convo_history_str)
        
        #Updating context data of Conversation ID  in DB
        supabase.table('Conversations').update({"convo_context" : f'{convo_context}', "convo_history" : f'{{{convo_history_str}}}' }).eq('convo_ID', convo_ID).execute()

    if (convo_context is None) :
        convo_context = ""
    if (convo_history is None) :
        convo_context = ['']
    
    print("convo_history_str AFTER POST is : " + convo_history_str)
    return render_template('conversation.html', conversation_history=convo_history, conversation_length=len(convo_history), convo_history_str=convo_history_str)


@app.route('/conversation_nm', methods=['GET', 'POST'])
def conversation_nm():

    convo_history = ['']
    convo_context = ""
    dict_data = {}
    convo_history_str = json.dumps({})

    # check if the session variable convo_history exists, if not create it
    # print("CURRENT Session ID:", session.sid)

    if ('convo_ID' not in session) or (session['convo_ID'] == 0) or (session['convo_ID'] == 10005) or (session['convo_ID'] == 10000)  :
        
        print("Initializing NEW session Variable convo_ID")
    
        # FETCH latest convo_ID record 
        cid_results=[]
        cid_results = supabase.table('Conversations').select("*").order('convo_ID').limit(1).execute()
        cid_record_id=0
        cid_record_history=['']

        for cid_record in cid_results:
    
            # FETCH the JSON object from the list
            # convert the JSON DATA object into a Python dictionary
            cid_json_obj = cid_record[1][0]
            dict_data = json.loads(json.dumps(cid_json_obj))


            # Fetch and Print the convoID value
            cid_record_id = list(dict_data.values())[2]
            print("Conversation ID = " + str(cid_record_id) ) 

            cid_record_history = list(dict_data.values())[4]

            break

        # setting NEW convo_ID to decrement 5 
        session['convo_ID'] = cid_record_id - 5 
        print(" new SESSION ID = " + str(cid_record_id - 5 ) ) 
        # insert NEW convo_ID into DB 
        #save UserPrompt and Answer as a record into Transcripts table

        record = {
        'convo_ID': cid_record_id - 5
        }

        #reset records before appending 
        records = []
        records.append(record)

        # Insert the records into the NFT table
        try:
            data = supabase.table('Conversations').insert(records).execute()
        except:
            print("OOPS.. INSERT went WRONG while saving New Conversation ID into DB ")
            return render_template("error.html", userapikey=openai.api_key)


    else:
        # convo_ID already exists, fetch the existing convo data 
        print("Session Variable convo_ID ALREADY EXISTS !!")
        
        convo_ID = session['convo_ID']
        
        print("EXISTING Session Variable convo_ID == " + str(convo_ID))
    
        cid_results=[]
        cid_results = supabase.table('Conversations').select("*").eq('convo_ID', convo_ID).execute()

        # if len(cid_results) == 0 --> meaning Conversation ID data no longer exists in DB !! 
        # In which case,  need to RESET Session Convo_ID and Re-create NEW Convo_ID 


        for cid_record in cid_results:
    
            # fetch the JSON object from the list
            # convert the JSON DATA object into a Python dictionary
            cid_json_obj = cid_record[1][0]
            dict_data = json.loads(json.dumps(cid_json_obj))

            convo_context = list(dict_data.values())[3]
            print("convo_context equals ") 
            print(convo_context)
            convo_history = list(dict_data.values())[4]

            break
    
    if request.method == "GET":
        #return render_template("conversation.html")
        if ('convo_ID' not in session) or (session['convo_ID'] == 0) or (session['convo_ID'] == 10005) or (session['convo_ID'] == 10000)  :
            return render_template('conversation_nm.html', conversation_history=convo_history, conversation_length=len(convo_history))

        else : 
            convo_ID = session['convo_ID']
        
            print("EXISTING Session Variable convo_ID == " + str(convo_ID))
    
            cid_results=[]
            cid_results = supabase.table('Conversations').select("*").eq('convo_ID', convo_ID).execute()

            if (convo_context is None) :
                convo_context = ""
            if (convo_history is None) :
                convo_history = ['']
            
            # Convert the array to a JSON string and remove the square brackets
            convo_history_str = json.dumps(convo_history, ensure_ascii=False)[1:-1]
        
            print("convo_history_str is : ") 
            print(convo_history_str)
        
    
            if (convo_context == ""):
                return render_template('conversation_nm.html')            
            else:
                return render_template('conversation_nm.html', conversation_history=convo_history, conversation_length=len(convo_history), convo_history_str=convo_history_str)


    elif request.method == 'POST':
        response = ""
        response_edited = ""
        prompt = request.form['prompt']

    
        if convo_context is None:
            print("about to POST QUERY,  convo_context is NONE ???")
            convo_context = ""
            response = ""    
        if convo_history is None:
            print("about to POST QUERY,  convo_history is NONE ???")
            convo_history = ['']

        if (clear_convo.lower() != prompt.lower() ):
            print("NOT CLEAR_CONVO command!!!")
            response = generate_response(prompt, convo_context)
            # if response is empty or null,  AI may be confused.  Clear Context, but Leave History as is 
            if ((response == "" or response is None) and convo_context != ""):
                print("RESPONSE is EMPTY... may be confused !! ")
                convo_context = ""
                supabase.table('Conversations').update({"convo_context" : ""}).eq('convo_ID', convo_ID).execute()
                response = generate_response(prompt, convo_context)
            
            # if response includes I'm or I am,   AI may later get confused.  Adjust Context
            if (response_filter.lower() in response.lower() or 
                    response_filter2.lower() in response.lower() or 
                    response_filter3.lower() in response.lower() ):
                print("RESPONSE contains I'm or I am , maybe confused.  Adjust Response!! ")
                response_edited = response.replace(response_filter, "You are")
                print("EDITED RESPONSE 1  : " + response_edited) 
                response_edited = response_edited.replace(response_filter2, "You are")
                print("EDITED RESPONSE 2 : " + response_edited) 
                response_edited = response_edited.replace(response_filter3, "Your")
                print("EDITED RESPONSE 3 : " + response_edited) 
                response_edited = response_edited.replace(response_filter4, "your")
                print("EDITED RESPONSE 4 : " + response_edited) 
                response_edited = response_edited.replace(response_filter5, "you")
                print("EDITED RESPONSE 5 : " + response_edited) 
            
            # if response includes err or err2  AI may be confused.  Clear Context, but Leave History as is 
            if ((response_err.lower() in response.lower() or response_err2.lower() in response.lower()) 
                    and convo_context != ""):
                print("RESPONSE suggests AI may be confused !! ")
                convo_context = ""
                supabase.table('Conversations').update({"convo_context" : ""}).eq('convo_ID', convo_ID).execute()
                response = generate_response(prompt, convo_context)

          
        print("prompt  = " + prompt) 
        print("response = " + response) 


        if response is None:
            response = ""

        if response_err.lower() in response.lower() : 
            response = response_default
        
        if response_err2.lower() in response.lower() : 
            response = response_default

        if (convo_context is not None):
            print("convo_context = " + convo_context)

        if ((convo_history is not None) and len(convo_history) >= 10) or (clear_convo.lower() in prompt.lower()):

            #empty conversation if converesation context > 10
            print("convo_context = " + convo_context)
            print("About to empty conversation history when reaching 10 !!") 
            convo_history.clear()

            print("about to reset convo_context !!") 
            convo_context = ""
            if (clear_convo.lower() in prompt.lower()):
                print("CLEARING CONVERSATION !!!") 
                #CLEARING OUT Conversation ID  in DB
                supabase.table('Conversations').update({"convo_context" : "", "convo_history" : [] }).eq('convo_ID', convo_ID).execute()
                return render_template('conversation_nm.html', conversation_history=[], conversation_length=0)
  
    
        #previous_response defined as CONTEXT 
        #convo_context = convo_context + convoconjunctor + response 
        print("Current Convo Pair :  " + prompt + " -xxxx- " + response) 

        convo_history.append(prompt + " -xxxx- " + response) 
        print("convo_history length AFTER APPEND = " + str(len(convo_history))) 

        if ((convo_context == "") or (convo_context is None)) :
            if (response_edited == ""):
                convo_context = convoconjunctor + response 
            else:
                convo_context = convoconjunctor + response_edited
        else :
            if (response_edited == ""):
                convo_context = convo_context + convoconjunctor2 + response 
            else:
                convo_context = convo_context + convoconjunctor2 + response_edited

        print(" LATEST Convo Context before committing to DB:  " + convo_context) 

        # Convert the array to a JSON string and remove the square brackets
        convo_history_str = json.dumps(convo_history, ensure_ascii=False)[1:-1]
        
        print("convo_history_str is : ") 
        print(convo_history_str)
        
        #Updating context data of Conversation ID  in DB
        supabase.table('Conversations').update({"convo_context" : f'{convo_context}', "convo_history" : f'{{{convo_history_str}}}' }).eq('convo_ID', convo_ID).execute()

    if (convo_context is None) :
        convo_context = ""
    if (convo_history is None) :
        convo_context = ['']
    
    print("convo_history_str AFTER POST in NIGHT_MODE is : " + convo_history_str)
    return render_template('conversation_nm.html', conversation_history=convo_history, conversation_length=len(convo_history), convo_history_str=convo_history_str)


@app.route("/", methods=["GET", "POST"])
def index():

    if request.method == "POST":
        print(request.form["prompt"])
        userprompt = request.form["prompt"]
        #userapikey = request.form["apikey"]
        usertemp = request.form["temperature"]

        print("Your Question is: "+ userprompt)
        print("Your API Key is:" + userapikey)
        print("Your Requested Temperature is: " + usertemp)

        if (openai.api_key == ""):
            openai.api_key = userapikey

        available_003 = False
        available_eho = False 
        available_gpt = False 
    
        try: 
            models = openai.Model.list()

        except: 
            print("sorry, wrong key")
            return render_template("error.html", userapikey=openai.api_key)
    

        print("Available Models are: ")
        for model in models['data']:
            print(model.id)
            if (model.id == "gpt-3.5-turbo"):
                available_gpt = True
            if (model.id == "text-davinci-003"):
                available_003 = True
            if (model.id == "davinci:ft-personal:eho-23-2023-03-04-21-00-29"):
                available_eho = True

        if (usertemp == "Standard"):
            engine_temperature = 0.5
        if (usertemp == "High"):
            engine_temperature = 1.0
        if (usertemp == "Ultra"):
            engine_temperature = 1.5

        print("Temperature set to " + usertemp + "at : " + str(engine_temperature))

        if (available_gpt):
            try: 
                print("Davinci-GPT is available !! ")
                response = openai.ChatCompletion.create(
                    engine="gpt-3.5-turbo",
                    prompt=userprompt,
                    max_tokens=1000,
                    n=1,
                    stop=None,
                    temperature=engine_temperature,
                )
            except:
                print("something went wrong while processing your question.. ")
                return render_template("error.html", userapikey=openai.api_key)
        
        elif (available_eho):
            try: 
                print("Davinci-EHO is available !! ")
                response = openai.Completion.create(
                    engine="davinci:ft-personal:eho-23-2023-03-04-21-00-29",
                    prompt=userprompt,
                    max_tokens=1000,
                    n=1,
                    stop=None,
                    temperature=engine_temperature,
                )
            except:
                print("something went wrong while processing your question.. ")
                return render_template("error.html", userapikey=openai.api_key)

        elif (available_003):
            try: 
                print("Davinci-003 is available !! ")
                response = openai.Completion.create(
                    engine="text-davinci-003",
                    prompt=userprompt,
                    max_tokens=2048,
                    n=1,
                    stop=None,
                    temperature=engine_temperature,
                )
            except:
                print("something went wrong while processing your question.. ")
                return render_template("error.html", userapikey=openai.api_key)
        
        else:
            try: 
                response = openai.Completion.create(
                    engine="text-davinci-002",
                    prompt=userprompt,
                    max_tokens=2048,
                    n=1,
                    stop=None,
                    temperature=engine_temperature,
                )
            except:
                print("something went wrong while processing your question.. ")
                return render_template("error.html", userapikey=openai.api_key)
    

        answer = response.choices[0].text
    
        if userprompt.lower() == "exit":
            return render_template('index.html', jokeanswer=jokeanswer, pod_prompt=pod_prompt)
        
        #answer = answer_question(userprompt)
        print("ANSWER IS: " + answer)


        #save UserPrompt and Answer as a record into Transcripts table

        record = {
        'prompt': userprompt,
        'response': answer,
        }

        #reset records before appending 
        records = []
        records.append(record)

        # Insert the records into the NFT table
        try:
            data = supabase.table('Transcripts').insert(records).execute()
        except:
            print("oops.. INSERT went wrong while saving transcripts into Supabase ")
            return render_template("error.html", userapikey=openai.api_key)


        return render_template("answer.html", userprompt=userprompt, answer=answer, userapikey=openai.api_key)
    
    return render_template('index.html', jokeanswer=jokeanswer, pod_prompt=pod_prompt)


@app.route('/night_mode', methods=["GET", "POST"])
def night_mode():
    if request.method == "POST":
        print(request.form["prompt"])
        userprompt = request.form["prompt"]
        #userapikey = request.form["apikey"]
        usertemp = request.form["temperature"]

        print("NIGHT MODE: Your Question is: "+ userprompt)
        print("Your API Key is:" + userapikey)
        print("Your Requested Temperature is: " + usertemp)

        if (openai.api_key == ""):
            openai.api_key = userapikey

        try: 
            models = openai.Model.list()
        except: 
            print("sorry, wrong key")
            return render_template("error_nm.html", userapikey=openai.api_key)

        available_003 = False
        available_eho = False 
        available_gpt = False 
        models = openai.Model.list()
        print("Available Models are: ")
        for model in models['data']:
            print(model.id)
            if (model.id == "text-davinci-003"):
                available_003 = True
            if (model.id == "davinci:ft-personal:eho-23-2023-03-04-21-00-29"):
                available_eho = True


        if (usertemp == "Standard"):
            engine_temperature = 0.5
        if (usertemp == "High"):
            engine_temperature = 1.0
        if (usertemp == "Ultra"):
            engine_temperature = 1.5

        print("Temperature set to " + usertemp + "at : " + str(engine_temperature))


        if (available_gpt):
            try: 
                print("Davinci-GPT is available !! ")
                response = openai.ChatCompletion.create(
                    engine="gpt-3.5-turbo",
                    prompt=userprompt,
                    max_tokens=1000,
                    n=1,
                    stop=None,
                    temperature=engine_temperature,
                )
            except:
                print("something went wrong while processing your question.. ")
                return render_template("error.html", userapikey=openai.api_key)

        elif (available_eho):
            try: 
                print("Davinci-EHO is available !! ")
                response = openai.Completion.create(
                    engine="davinci:ft-personal:eho-23-2023-03-04-21-00-29",
                    prompt=userprompt,
                    max_tokens=1000,
                    n=1,
                    stop=None,
                    temperature=engine_temperature,
                )
            except:
                print("something went wrong while processing your question.. ")
                return render_template("error.html", userapikey=openai.api_key)

        elif (available_003):
            try: 
                print("Davinci-003 is available !! ")
                response = openai.Completion.create(
                    engine="text-davinci-003",
                    prompt=userprompt,
                    max_tokens=2048,
                    n=1,
                    stop=None,
                    temperature=engine_temperature,
                )
            except:
                print("something went wrong while processing your question.. ")
                return render_template("error.html", userapikey=openai.api_key)


        else:
            try: 
                response = openai.Completion.create(
                    engine="text-davinci-002",
                    prompt=userprompt,
                    max_tokens=2048,
                    n=1,
                    stop=None,
                    temperature=engine_temperature,
                )
            except:
                print("something went wrong while processing your question.. ")
                return render_template("error.html", userapikey=openai.api_key)
    

        answer = response.choices[0].text
    
        if userprompt.lower() == "exit":
            return render_template('night_mode.html', jokeanswer=jokeanswer, pod_prompt=pod_prompt)
        
        #answer = answer_question(userprompt)
        print("ANSWER IS: " + answer)

        #save UserPrompt and Answer as a record into Transcripts table

        record = {
        'prompt': userprompt,
        'response': answer,
        }
        #reset records before appending 
        records = []
        records.append(record)

        # Insert the records into the Transcripts table
        try:
            data = supabase.table('Transcripts').insert(records).execute()
        except:
            print("oops.. INSERT went wrong while saving Transacript Record into Supabase !! ")
            return render_template("error.html", userapikey=openai.api_key)


        return render_template("answer_nm.html", userprompt=userprompt, answer=answer, userapikey=openai.api_key)
    
    return render_template('night_mode.html', jokeanswer=jokeanswer, pod_prompt=pod_prompt)

@app.route('/gallery')
def gallery():
    return render_template('gallery.html')

@app.route('/answer_nm')
def answer_nm():
    return render_template('answer_nm.html')

@app.route('/gallery_nm')
def gallery_nm():
    return render_template('gallery_nm.html')

@app.route('/terms')
def terms():
    return render_template('terms.html')

@app.route('/privacy')
def privacy():
    return render_template('privacy.html')


@app.route("/sendemail", methods=["GET", "POST"])
def sendemail():
    # Your Gmail account information
    message = email.message.EmailMessage()
    useremail = ""
    answer = ""
    userprompt = ""
    json_history = json.dumps({})
    convoindex = 0 

    try:
        useremail = request.form["useremail"]
    except:
        print("no useremail")
    
    try: 
        answer =  request.form["answer"]
        userprompt = request.form["userprompt"]

    except:
        print("no answer or no userprompt")
        
    try: 
        json_history = request.form["conversation_history"]

    except:
        print("no Conversation History!!??")


    sender_email = os.environ['SENDER_EMAIL']
    sender_password = os.environ['SENDER_PASSWORD']
    receiver_email = useremail

    json_history_list = json.loads("[" + json_history + "]")
    json_history_string = json.dumps(json_history_list)



    # Create the message
    if (json_history is None) or (not json_history) :
        message = MIMEText("Your Question : \n" + userprompt + "\n" + "\n" + "Our Response : \n" + answer + "\n" + "\n" + "Sincerely \n" + "EHO AI STUDIO 23")

    else : 
        #re-construct context from conversation_history 
        convomessage = ""
        json_list = json.loads(json_history_string)

        for item in json_list:
            if (item != "" and len(item) > 5):
                convomessage = convomessage + "You prompted : " + item.split(" -xxxx- ")[0].strip() + "\n"
                convomessage = convomessage + "EHO P&R Bot responded : " + item.split(" -xxxx- ")[1].strip() + "\n \n"
      

        print("convomessage = " + convomessage) 
        message = MIMEText(convomessage)
        
    
    message["Subject"] = "YOUR P&R AI GENIE Transcript is Ready!" 
    message["From"] = sender_email
    message["To"] = receiver_email


    # Create a connection to the Gmail SMTP server
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        # Log in to the email account
        server.login(sender_email, sender_password)
        # Send the email
        server.sendmail(sender_email, receiver_email, message.as_string())
        # Close the server connection
        server.quit()

    return render_template("useremail.html", useremail=useremail)


@app.route("/sendemail_nm", methods=["GET", "POST"])
def sendemail_nm():
    print("SEND MAIL NIGHT MODE!!")
    # Your Gmail account information

    message = email.message.EmailMessage()
    useremail = ""
    answer = ""
    userprompt = ""
    json_history = json.dumps({})
    convoindex = 0
    convomessage = ""

    try:
        useremail = request.form["useremail"]
    except:
        print("no useremail")
    
    try: 
        answer =  request.form["answer"]
        userprompt = request.form["userprompt"]

    except:
        print("no answer or no userprompt")

        
    try: 
        json_history = request.form["conversation_history"]

    except:
        print("no Conversation History!!??")


    sender_email = os.environ['SENDER_EMAIL']
    sender_password = os.environ['SENDER_PASSWORD']
    receiver_email = useremail

    json_history_list = json.loads("[" + json_history + "]")
    json_history_string = json.dumps(json_history_list)


    # Create the message
    if (json_history is None) or (not json_history) :
        message = MIMEText("Your Question : \n" + userprompt + "\n" + "\n" + "Our Response : \n" + answer + "\n" + "\n" + "Sincerely \n" + "EHO AI STUDIO 23")
    else : 
        #re-construct email message body with convo_history 

        convomessage = ""
        json_list = json.loads(json_history_string)

        for item in json_list:
            if (item != "" and len(item) > 5):
                convomessage = convomessage + "You prompted : " + item.split(" -xxxx- ")[0].strip() + "\n"
                convomessage = convomessage + "EHO P&R Bot responded : " + item.split(" -xxxx- ")[1].strip() + "\n \n" 
      

        print("convomessage = " + convomessage) 
        message = MIMEText(convomessage)

    message["Subject"] = "YOUR EHO P&R AI GENIE Transcript is Ready!" 
    message["From"] = sender_email
    message["To"] = receiver_email


    # Create a connection to the Gmail SMTP server
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        # Log in to the email account
        server.login(sender_email, sender_password)
        # Send the email
        server.sendmail(sender_email, receiver_email, message.as_string())
        # Close the server connection
        server.quit()

    return render_template("useremail_nm.html", useremail=useremail)


if __name__ == '__main__':
    app.run(host="127.0.0.1", port=8081, debug=True)