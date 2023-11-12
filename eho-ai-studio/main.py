from flask import Flask, Response, render_template, request, session
from flask_cors import CORS

# OpenAI Library
# Copyright (c) 2023 OpenAI
# https://github.com/openai/openai-python


import openai
import os
import io
import warnings
import json
import re
import time

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
response_filter6 = "nn"
response_default = " requiring more research "
clear_convo = "CLEAR_CONVO"

supa_url = os.environ['SUPABASE_URL']
supa_key = os.environ['SUPABASE_KEY']

gpt_enabled = os.environ['GPT_KEY']
app_version = os.environ['APP_VERSION']

supabase = create_client(supa_url, supa_key)

print("supabase client initiated successfully! ")

records=[]

#prompt of the day 
pod_prompt = ""
pod_results=[]
pod_results = supabase.table('Transcripts').select("*").eq('rank', 888).order('created_at', desc=True).limit(1).execute()

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
    models = []
    available_gpt = False 
    try: 
        print("Iterating through Available Models List")
        models = openai.Model.list()

    except: 
        print("sorry, wrong key")
        return render_template("error.html", app_version=app_version, userapikey=openai.api_key)
    
    for model in models['data']:
        # print(model.id)
        if (model.id == "gpt-4-1106-preview" and gpt_enabled == "YES"):
            available_gpt = True
        if (model.id == "gpt-4-1106-preview"):
            print("GPT4-0613 IS AVAILABLE !!!")
        
    if (available_gpt):
        print("gpt-4-1106-preview is AVAILABLE in generate_response !!! ")
        try: 
            messages = [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "assistant", "content": "This is Context. "},
                {"role": "user", "content": "This is User's Question"}
            ]
     
            for item in messages:
                if item["role"] == "user":
                    item["content"] = prompt
                   
                if item["role"] == "assistant":
                    item["content"] = previous_context
            

            gpt_response = openai.ChatCompletion.create(
                    model="gpt-4-1106-preview",
                    messages=messages 
            )
            
            return gpt_response['choices'][0]['message']['content']

        except Exception as e:
            if 'overloaded' in str(e):
                # handle overloaded error here
                return "My apologies.. currently tied up right now,  will be back on shortly!!"
            else:
                # handle all other errors here
                print(f"something went wrong: {e}")
                return render_template("error.html", app_version=app_version, userapikey=openai.api_key)
        

    
    elif previous_context == "" or previous_context is None :
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

#CORS(app, resources={r"/streaming-page": {"origins": "https://127.0.0.1"}})
CORS(app, resources={r"/streaming-page": {"origins": ["https://127.0.0.1", "https://www.prompts.ai", "https://prompts.ai"]}})

app.config['SECRET_KEY'] = os.environ['OPENAI_KEY']

@app.route('/test_home', methods=['GET', 'POST'])
def test_home():
    return render_template('test_home.html', app_version=app_version)

@app.route('/unicorn_home', methods=['GET', 'POST'])
def unicorn_home():
    return render_template('unicorn_index.html', app_version=app_version)

@app.route('/streaming-intro')
def streaming_intro():

    # create variables to collect the stream of chunks
    full_reply_content = ""

    print("INSIDE Streaming_Intro (): ")

    def intro_generate():
        full_reply_content = ""
        print("INSIDE IntroGenererate (): ")
        print("Full Reply Content is initialized to : ")
        print(full_reply_content)

        
        # send a Generic ChatCompletion request 
        messages=[
                {"role": "system", "content": "You are a smart  assistant with a great sense of humor and always start your response with courteous greetings "},
                {'role': 'user', 'content': "Repeat the following greetings word for word exactly in your response : Welcome to Promptlys! Have you struggled with prompting that communicates effectively and generates desired responses? You have come to the right place! Here at Promptly you can access, learn and share quality prompts created by top-notch Prompt Creators ."}
            ]
                   
        response = openai.ChatCompletion.create(
            model='gpt-4-1106-preview',
            messages=messages,
            temperature=0,
            stream=True  # set stream=True
        )


        start_time = time.time()
        for chunk in response:
            time.sleep(0.2)
            chunk_time = time.time() - start_time
            #print(chunk)
            #yield "data: {}\n\n".format(chunk['choices'][0]['delta'])  # yield the chunk as SSE data
            finish_reason = ""
            chunk_content = ""

            try: 
                finish_reason = chunk['choices'][0]['finish_reason']
                if (finish_reason is not None) and (finish_reason != "") :
                    print("STREAMING STOPPED !!")
                    print("finish_reason ==")
                    print(finish_reason)
                    chunk_content = "THE_END"
                    yield "data: {}\n\n".format(chunk_content)  # yield the chunk content as SSE data
                    break 
            except (KeyError, IndexError):
                continue  # continue to the next chunk if the necessary keys don't exist

            try: 
                chunk_content = chunk['choices'][0]['delta']['content']
                # yield "data: {}\n\n".format(chunk_content)  # yield the chunk content as SSE data
        

            except (KeyError, IndexError):
                continue  # continue to the next chunk if the necessary keys don't exist

            full_reply_content = full_reply_content + chunk_content 
            print("Full Reply Content == ")
            print(full_reply_content)
            
            yield "data: {}\n\n".format(chunk_content)  # yield the chunk content as SSE data

    

    stream_response = Response(intro_generate(), mimetype='text/event-stream')


    # Disable buffering by setting X-Accel-Buffering header to 'no'
    stream_response.headers['X-Accel-Buffering'] = 'no'
    # Add additional headers
    stream_response.headers['Content-Type'] = 'text/event-stream'
    stream_response.headers['Cache-Control'] = 'no-cache'

    return stream_response 



@app.route('/streaming-page')
def streaming_page():

    # create variables to collect the stream of chunks
    full_reply_content = ""

    print("INSIDE Streaming_Page (): ")
    print("Full Reply Content is initialized to : ")
    print(full_reply_content)

    def generate(user_prompt, user_context):
        full_reply_content = ""
        print("INSIDE Genererate (): ")
        print("Full Reply Content is initialized to : ")
        print(full_reply_content)

        if (user_prompt == "") or (user_prompt == "clear_convo"):
            print("Streaming_Page:  user prompt is EMPTY! ")
            user_prompt = "Hello !"
            #yield "data: {}\n\n".format("")  # yield the chunk content as SSE data
        
        # send a Generic ChatCompletion request 
        messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "assistant", "content": "This is User Context. "},
                {'role': 'user', 'content': 'how many cities are there in California? '}
            ]

        for item in messages:
            if item["role"] == "user":
                item["content"] = user_prompt
            if item["role"] == "assistant":
                item["content"] = user_context
                   
        response = openai.ChatCompletion.create(
            model='gpt-4-1106-preview',
            messages=messages,
            temperature=0,
            stream=True  # set stream=True
        )


        start_time = time.time()
        for chunk in response:
            chunk_time = time.time() - start_time
            #print(chunk)
            #yield "data: {}\n\n".format(chunk['choices'][0]['delta'])  # yield the chunk as SSE data
            finish_reason = ""
            chunk_content = ""

            try: 
                finish_reason = chunk['choices'][0]['finish_reason']
                if (finish_reason is not None) and (finish_reason != "") :
                    print("STREAMING STOPPED !!")
                    print("finish_reason ==")
                    print(finish_reason)
                    chunk_content = "THE_END"
                    yield "data: {}\n\n".format(chunk_content)  # yield the chunk content as SSE data
                    break 
            except (KeyError, IndexError):
                continue  # continue to the next chunk if the necessary keys don't exist

            try: 
                chunk_content = chunk['choices'][0]['delta']['content']
                # yield "data: {}\n\n".format(chunk_content)  # yield the chunk content as SSE data

            except (KeyError, IndexError):
                continue  # continue to the next chunk if the necessary keys don't exist

            full_reply_content = full_reply_content + chunk_content 
            print("Full Reply Content == ")
            print(full_reply_content)
            
            yield "data: {}\n\n".format(chunk_content)  # yield the chunk content as SSE data

    
    user_prompt = session.get('user_prompt', '')
    user_context = session.get('user_context', '')
    print("Streaming_Page:  User Prompt == ")
    print(user_prompt)
    print("Streaming_Page:  User Context == ")
    print(user_context)
    #reset user_prompt 
    session['user_prompt'] = ""

    stream_response = Response(generate(user_prompt, user_context), mimetype='text/event-stream')

    if (user_prompt == ""):
        print("Streaming_Page:  user prompt is EMPTY! ")

    # send a Generic ChatCompletion request 
    messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "assistant", "content": "This is User Context. "},
            {'role': 'user', 'content': 'how many cities are there in California? '}
        ]

    for item in messages:
        if item["role"] == "user":
            item["content"] = user_prompt
        if item["role"] == "assistant":
            item["content"] = user_context 
            
                
    response = openai.ChatCompletion.create(
        model='gpt-4-1106-preview',
        messages=messages,
        temperature=0,
        stream=True  # set stream=True
    )

    start_time = time.time()
    for chunk in response:
        chunk_time = time.time() - start_time
        finish_reason = ""
        chunk_content = ""

        try: 
            finish_reason = chunk['choices'][0]['finish_reason']
            if (finish_reason is not None) and (finish_reason != "") :
                print("STREAMING STOPPED !!")
                print("finish_reason ==")
                print(finish_reason)
                chunk_content = "THE_END"
                break 
        except (KeyError, IndexError):
            continue  # continue to the next chunk if the necessary keys don't exist

        try: 
            chunk_content = chunk['choices'][0]['delta']['content']

        except (KeyError, IndexError):
            continue  # continue to the next chunk if the necessary keys don't exist

        full_reply_content = full_reply_content + chunk_content 


    session['user_response'] = full_reply_content 
    print("Streaming_Page (): Full Reply Content After Streaming is :")
    print(full_reply_content)

    # Disable buffering by setting X-Accel-Buffering header to 'no'
    stream_response.headers['X-Accel-Buffering'] = 'no'
    # Add additional headers
    stream_response.headers['Content-Type'] = 'text/event-stream'
    stream_response.headers['Cache-Control'] = 'no-cache'

    return stream_response 
    #return Response(generate(user_prompt), mimetype='text/event-stream')

@app.route('/conversation', methods=['GET', 'POST'])
def conversation():

    convo_history = ['']
    convo_context = ""
    dict_data = {}
    convo_history_str = json.dumps({})
    convo_id_str = ""

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
        convo_id_str = str(cid_record_id - 5 )
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
            return render_template("error.html", app_version=app_version, userapikey=openai.api_key)


    else:
        # convo_ID already exists, fetch the existing convo data 
        print("Session Variable convo_ID ALREADY EXISTS !!")
        
        convo_ID = session['convo_ID']

        convo_id_str= str(convo_ID)
        
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
            return render_template('conversation.html', app_version=app_version, conversation_history=convo_history, conversation_length=len(convo_history), convo_id_str=convo_id_str)

        else : 
            convo_ID = session['convo_ID']
        
            print("EXISTING Session Variable convo_ID == " + str(convo_ID))
    
            #cid_results=[]
            #cid_results = supabase.table('Conversations').select("*").eq('convo_ID', convo_ID).execute()

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
                return render_template('conversation.html', app_version=app_version, conversation_history=convo_history, conversation_length=len(convo_history), convo_history_str=convo_history_str, convo_id_str=convo_id_str)


    elif request.method == 'POST':
        response = ""
        response_edited = ""
        
        prompt = request.form['prompt']
        session['user_prompt'] = prompt
    

        print("CONVERSATION MODE:  POST ACTION")

        if convo_context is None:
            print("about to POST QUERY,  convo_context is NONE ???")
            convo_context = ""
            response = ""    
        if convo_history is None:
            print("about to POST QUERY,  convo_history is NONE ???")
            convo_history = ['']

        if (clear_convo.lower() != prompt.lower() ):
            print("NOT CLEAR_CONVO command!!!")

        # response = generate_response(prompt, convo_context)
        
        # if response is empty or null,  AI may be confused.  Clear Context, but Leave History as is 

        if ((response == "" or response is None) and convo_context != ""):
            print("RESPONSE is EMPTY... may be confused !! ")
            convo_context = ""
            supabase.table('Conversations').update({"convo_context" : ""}).eq('convo_ID', convo_ID).execute()
            # response = generate_response(prompt, convo_context)
        
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
        
        response = session['user_response']
        print("Conversation: User Response from Session == ")
        print(response) 
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
                return render_template('conversation.html', app_version=app_version, conversation_history=[], conversation_length=0)

        
        #previous_response defined as CONTEXT 
        #convo_context = convo_context + convoconjunctor + response 
        print("Current Convo Pair :  " + prompt + " -xxxx- " + response) 

        #If Convo_History > 0, update PREVIOUS CONVO PAIR with user response from SESSION 
        if (len(convo_history) > 0) : 
          
            print("About to Update previous convo: ")
        
            # Define the pattern to match the divider
            pattern = r" -xxxx- "

            # Find the index where the pattern occurs
            match = re.search(pattern, convo_history[len(convo_history) - 1])

            if match:
                # Get the starting index of the matched pattern
                divider_start = match.start()
        
                # Update the substring after the divider with "shop"
                convo_history[len(convo_history) - 1] = convo_history[len(convo_history) - 1][:divider_start] + " -xxxx- " + response 
                print("YES,  MATCH FOUND AND UPDATED Convo History")
                print(convo_history[len(convo_history) - 1])
            else:
                print("Divider pattern not found in the string.")
       

        #append Current Convo Pair 
        convo_history.append(prompt + " -xxxx- " + "") 
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

        #Update user context to session['user_context']
        session['user_context'] = convo_context

        # Convert the array to a JSON string and remove the square brackets
        convo_history_str = json.dumps(convo_history, ensure_ascii=False)[1:-1]


        print("convo_history_str AFTER FORMATTING is : ") 
        print(convo_history_str)

        
        #Updating context data of Conversation ID  in DB
        supabase.table('Conversations').update({"convo_context" : f'{convo_context}', "convo_history" : f'{{{convo_history_str}}}' }).eq('convo_ID', convo_ID).execute()

    if (convo_context is None) :
        convo_context = ""
    if (convo_history is None) :
        convo_context = ['']
    
    print("convo_history_str AFTER POST is : " + convo_history_str)
    return render_template('conversation.html', app_version=app_version, conversation_history=convo_history, conversation_length=len(convo_history), convo_history_str=convo_history_str, convo_id_str=convo_id_str)


@app.route('/conversation_nm', methods=['GET', 'POST'])
def conversation_nm():

    convo_history = ['']
    convo_context = ""
    dict_data = {}
    convo_history_str = json.dumps({})
    convo_id_str = ""

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
        convo_id_str = str(cid_record_id - 5 )
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
            return render_template("error.html", app_version=app_version, userapikey=openai.api_key)


    else:
        # convo_ID already exists, fetch the existing convo data 
        print("Session Variable convo_ID ALREADY EXISTS !!")
        
        convo_ID = session['convo_ID']

        convo_id_str = str(convo_ID)
        
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
            return render_template('conversation_nm.html', app_version=app_version, conversation_history=convo_history, conversation_length=len(convo_history), convo_id_str=convo_id_str)

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
                return render_template('conversation_nm.html', app_version=app_version, conversation_history=convo_history, conversation_length=len(convo_history), convo_history_str=convo_history_str, convo_id_str=convo_id_str)


    elif request.method == 'POST':
        response = ""
        response_edited = ""
        
        prompt = request.form['prompt']
        session['user_prompt'] = prompt
    
    
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
                #response = generate_response(prompt, convo_context)
            
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


        response = session['user_response']
        print("Conversation: User Response from Session == ")
        print(response) 
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
                return render_template('conversation_nm.html', app_version=app_version, conversation_history=[], conversation_length=0)
  
    
        #If Convo_History > 0, update PREVIOUS CONVO PAIR with user response from SESSION 
        if (len(convo_history) > 0) : 
          
            print("About to Update previous convo: ")
        
            # Define the pattern to match the divider
            pattern = r" -xxxx- "

            # Find the index where the pattern occurs
            match = re.search(pattern, convo_history[len(convo_history) - 1])

            if match:
                # Get the starting index of the matched pattern
                divider_start = match.start()
        
                # Update the substring after the divider with "shop"
                convo_history[len(convo_history) - 1] = convo_history[len(convo_history) - 1][:divider_start] + " -xxxx- " + response 
                print("YES,  MATCH FOUND AND UPDATED Convo History")
                print(convo_history[len(convo_history) - 1])
            else:
                print("Divider pattern not found in the string.")


        #append Current Convo Pair 
        convo_history.append(prompt + " -xxxx- " + "") 
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

        
        #Update user context to session['user_context']
        session['user_context'] = convo_context

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
    return render_template('conversation_nm.html', app_version=app_version, conversation_history=convo_history, conversation_length=len(convo_history), convo_history_str=convo_history_str, convo_id_str=convo_id_str)


@app.route("/", methods=["GET", "POST"])
def index():

    if request.method == "POST":
        print(request.form["prompt"])
        userprompt = request.form["prompt"]
        #userapikey = request.form["apikey"]
        usertemp = request.form["temperature"]
        usercheck = ""
        try:
            usercheck = request.form["check"]
        except:
            print("USER CHECK EXCEPTION !!!")

        print("Share Check = " + usercheck) 

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
            return render_template("error.html", app_version=app_version, userapikey=openai.api_key)
    

        print("Available Models are: ")
        for model in models['data']:
            print(model.id)
            if (model.id == "gpt-4-1106-preview"):
                available_gpt = True
            if (model.id == "text-davinci-003"):
                available_003 = True
            #if (model.id == "davinci:ft-personal:eho-23-2023-03-04-21-00-29"):
                #available_eho = True

        if (usertemp == "Standard"):
            engine_temperature = 0.5
        if (usertemp == "High"):
            engine_temperature = 1.0
        if (usertemp == "Ultra"):
            engine_temperature = 1.5

        print("Temperature set to " + usertemp + " at: " + str(engine_temperature))

        if (available_gpt) and (gpt_enabled == "YES"):
            try: 
                print("GPT TURBO is Available !!")
                messages = [
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": "This is User's Question"}
                ]
                #messagees[1]['content'] = userprompt
                for item in messages:
                    if item["role"] == "user":
                        item["content"] = userprompt


                print("gpt-4-1106-preview is available !! ")
                response = openai.ChatCompletion.create(
                    model="gpt-4-1106-preview",
                    messages=messages 
                )

         

            except:
                print("something went wrong while processing your prompt .. ")
                return render_template("error.html", app_version=app_version, userapikey=openai.api_key)
        
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
                print("something went wrong while processing your prompt in EHO model .. ")
                return render_template("error.html", app_version=app_version, userapikey=openai.api_key)

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
                print("something went wrong while processing your prompt.. ")
                return render_template("error.html", app_version=app_version, userapikey=openai.api_key)
        
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
                print("something went wrong while processing your prompt .. ")
                return render_template("error.html", app_version=app_version, userapikey=openai.api_key)
    
        if (not available_gpt) or (gpt_enabled != "YES"): 
            answer = response.choices[0].text
        else:
            answer = response['choices'][0]['message']['content']
    
        # define the regular expression pattern
        pattern = re.compile(r"nn(?=\d)")
        # replace all occurrences of "nn" with "#"
        answer = pattern.sub("#", answer)


        if userprompt.lower() == "exit":
            return render_template('index.html', app_version=app_version, jokeanswer=jokeanswer, pod_prompt=pod_prompt)
        

        #save UserPrompt and Answer as a record into Transcripts table

        if (usercheck == "YES"):
            record = {
            'prompt': userprompt,
            'response': answer,
            'rank': 888,
            }
        else:
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
            return render_template("error.html", app_version=app_version, userapikey=openai.api_key)


        return render_template("answer.html", app_version=app_version, userprompt=userprompt, answer=answer, userapikey=openai.api_key)
    
    return render_template('index.html', app_version=app_version, jokeanswer=jokeanswer, pod_prompt=pod_prompt)


@app.route('/night_mode', methods=["GET", "POST"])
def night_mode():
    if request.method == "POST":
        print(request.form["prompt"])
        userprompt = request.form["prompt"]
        #userapikey = request.form["apikey"]
        usertemp = request.form["temperature"]

        usercheck = ""
        try:
            usercheck = request.form["check"]
        except:
            print("USER CHECK EXCEPTION !!!")


        print("NIGHT MODE: Your Question is: "+ userprompt)
        print("Your API Key is:" + userapikey)
        print("Your Requested Temperature is: " + usertemp)

        if (openai.api_key == ""):
            openai.api_key = userapikey

        try: 
            models = openai.Model.list()
        except: 
            print("sorry, wrong key")
            return render_template("error_nm.html", app_version=app_version, userapikey=openai.api_key)

        available_003 = False
        available_eho = False 
        available_gpt = False 
        models = openai.Model.list()

        for model in models['data']:
            if (model.id == "gpt-4-1106-preview") and (gpt_enabled == "YES"):
                print("YES,  gpt-4-1106-preview is now AVAILABLE!!!")
                available_gpt = True
            if (model.id == "text-davinci-003"):
                available_003 = True
            if (model.id == "gpt-4-1106-preview"):
                print("YES,  gpt-4-1106-preview is now AVAILABLE!!!")


        if (usertemp == "Standard"):
            engine_temperature = 0.5
        if (usertemp == "High"):
            engine_temperature = 1.0
        if (usertemp == "Ultra"):
            engine_temperature = 1.5

        print("Temperature set to " + usertemp + " at : " + str(engine_temperature))


        if (available_gpt) and (gpt_enabled == "YES"):
            try: 
                print("GPT TURBO is Available !!")
                messages = [
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": "This is User's Question"}
                ]
                #messagees[1]['content'] = userprompt
                for item in messages:
                    if item["role"] == "user":
                        item["content"] = userprompt


                print("gpt-4-1106-preview is available !! ")
                response = openai.ChatCompletion.create(
                    model="gpt-4-1106-preview",
                    messages=messages 
                )

                # replace all occurrences of "nn" with "#"
                # response = response.replace(response_filter6, "#")
            except:
                print("something went wrong while processing your prompt .. ")
                return render_template("error_nm.html", app_version=app_version, userapikey=openai.api_key)


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
                return render_template("error.html", app_version=app_version, userapikey=openai.api_key)

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
                return render_template("error.html", app_version=app_version, userapikey=openai.api_key)


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
                return render_template("error.html", app_version=app_version, userapikey=openai.api_key)
    

        if (not available_gpt) or (gpt_enabled != "YES"):
            answer = response.choices[0].text
        else:
            answer = response['choices'][0]['message']['content']

        # define the regular expression pattern
        pattern = re.compile(r"nn(?=\d)")
        # replace all occurrences of "nn" with "#"
        answer = pattern.sub("#", answer)


    
        if userprompt.lower() == "exit":
            return render_template('night_mode.html', app_version=app_version, jokeanswer=jokeanswer, pod_prompt=pod_prompt)
        
        #answer = answer_question(userprompt)
        print("ANSWER IS: " + answer)

        #save UserPrompt and Answer as a record into Transcripts table

    
        if (usercheck == "YES"):
            record = {
            'prompt': userprompt,
            'response': answer,
            'rank': 888,
            }
        else:
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
            return render_template("error.html", app_version=app_version, userapikey=openai.api_key)

        return render_template("answer_nm.html", app_version=app_version, userprompt=userprompt, answer=answer, userapikey=openai.api_key)
    
    return render_template('night_mode.html', app_version=app_version, jokeanswer=jokeanswer, pod_prompt=pod_prompt)

@app.route('/trending', methods=['GET', 'POST'])
def trending():

    pod_prompt = ""
    pod_results=[]
    pod_results = supabase.table('Transcripts').select("*").eq('rank', 888).order('created_at', desc=True).limit(8).execute()
    pod_index = 0
    prompt_list = []
    prompt_list_str = ""

    for pod_record in pod_results:

        # fetch the JSON object at pod_record[1], and get the first and only record at pod_record[1][0]
        # ***this JSON OBJECT REPRESENTS ALL SATISFYING PROMPTS ****
        # convert the JSON DATA object into a Python dictionary
        print(" CURRENT pod_record is : ")
        print( pod_record )
        print(" After printing CURRENT pod_record is : ")
        # this JSON OBJ includes data of ALL satisfying prompts 
        
        print("Total LENGTH of Prompt Items = ")
        print(len(pod_record[1]))

        for i in range(len(pod_record[1])):
            json_obj = pod_record[1][i]
            #print("PRINT this JSON OBJ: ")
            #print(json_obj)
            dict_data = json.loads(json.dumps(json_obj))
            pod_prompt = list(dict_data.values())[2]
            #print("PRINT this PROMPT: ")
            #print(pod_prompt)
            prompt_list.insert(i, pod_prompt)
            prompt_list_str = prompt_list_str + pod_prompt +  " -xxxx- "

        break 


    print("Prompt List is printed below: ")
    for i in range(len(prompt_list)):
        print(prompt_list[i])



    return render_template('trending.html', app_version=app_version, prompt_list=prompt_list, prompt_list_str=prompt_list_str)

@app.route('/trending_nm', methods=['GET', 'POST'])
def trending_nm():

    pod_prompt = ""
    pod_results=[]
    pod_results = supabase.table('Transcripts').select("*").eq('rank', 888).order('created_at', desc=True).limit(8).execute()
    pod_index = 0
    prompt_list = []
    prompt_list_str = ""

    for pod_record in pod_results:

        # fetch the JSON object at pod_record[1], and get the first and only record at pod_record[1][0]
        # ***this JSON OBJECT REPRESENTS ALL SATISFYING PROMPTS ****
        # convert the JSON DATA object into a Python dictionary
        print(" CURRENT pod_record is : ")
        print( pod_record )
        print(" After printing CURRENT pod_record is : ")
        # this JSON OBJ includes data of ALL satisfying prompts 
        
        print("Total LENGTH of Prompt Items = ")
        print(len(pod_record[1]))

        for i in range(len(pod_record[1])):
            json_obj = pod_record[1][i]
            #print("PRINT this JSON OBJ: ")
            #print(json_obj)
            dict_data = json.loads(json.dumps(json_obj))
            pod_prompt = list(dict_data.values())[2]
            #print("PRINT this PROMPT: ")
            #print(pod_prompt)
            prompt_list.insert(i, pod_prompt)
            prompt_list_str = prompt_list_str + pod_prompt +  " -xxxx- "

        break 


    print("Prompt List is printed below: ")
    for i in range(len(prompt_list)):
        print(prompt_list[i])

    return render_template('trending_nm.html', app_version=app_version, prompt_list=prompt_list, prompt_list_str=prompt_list_str)

@app.route('/community', methods=['GET', 'POST'])
def community():

    pod_prompt = ""
    pod_results=[]
 
    pod_index = 0
    prompt_list = []
    prompt_list_str = ""
    search_string = ""

    if request.method == "GET":
        search_string = "Imagine"
        print("You are in Community GET Page")

    if request.method == "POST":

        # Retrieve the search string entered by the user
        try:
            search_string = request.form["search"]
        except: 
            try:
                search_string = request.form["searchfilter"]
            except:
                print("NO SEARCH STRING FOUND!!! ") 

    
        print("Search String is : " + search_string) 
 
        # Query Supabase for prompt data based on search string
    pod_results = supabase.table('Transcripts').select("*").eq('rank', 888).ilike('prompt', f'%{search_string}%').order('created_at', desc=True).execute()
   
    
        ##### refining query by building OR clauses in Query Condition
        
        #keywords = search_string.split()  # Split search string into individual keywords
        #query = supabase.table('Transcripts').select("*").eq('rank', 888)
        
        # Build the query using OR to union all keywords
        # or_conditions = []
        #for keyword in keywords:
            #or_conditions.append({'prompt': {'ilike': f"%{keyword}%"}})
            #or_conditions.append(('prompt', 'ilike', f"%{keyword}%"))

        #print("OR CLAUSE = " ) 

        #for condition in or_conditions:
            #print("OR CONDTION : ")
            #print(condition)
        

        # Create a new empty query
        #new_query = None

        # Combine the OR conditions using union_all
        #for condition in or_conditions:
            #condition_query = query.ilike(*condition)
            #if new_query is None:
                #new_query = condition_query
            #else:
                #new_query = new_query.union_all(condition_query)
        
        #pod_results = query.execute()

    for pod_record in pod_results:

        # fetch the JSON object at pod_record[1], and get the first and only record at pod_record[1][0]
        # ***this JSON OBJECT REPRESENTS ALL SATISFYING PROMPTS ****
        # convert the JSON DATA object into a Python dictionary
        print(" CURRENT pod_record is : ")
        print( pod_record )
        print(" After printing CURRENT pod_record is : ")
        # this JSON OBJ includes data of ALL satisfying prompts 
        
        print("Total LENGTH of Prompt Items = ")
        print(len(pod_record[1]))

        for i in range(len(pod_record[1])):
            json_obj = pod_record[1][i]
            #print("PRINT this JSON OBJ: ")
            #print(json_obj)
            dict_data = json.loads(json.dumps(json_obj))
            pod_prompt = list(dict_data.values())[2]
            #print("PRINT this PROMPT: ")
            #print(pod_prompt)
            prompt_list.insert(i, pod_prompt)
            prompt_list_str = prompt_list_str + pod_prompt +  " -xxxx- "

        break 


    print("Prompt List is printed below: ")
    for i in range(len(prompt_list)):
        print(prompt_list[i])

    return render_template('community.html', app_version=app_version, prompt_list=prompt_list, prompt_list_str=prompt_list_str)

@app.route('/community_nm', methods=['GET', 'POST'])
def community_nm():

    pod_prompt = ""
    pod_results=[]
 
    pod_index = 0
    prompt_list = []
    prompt_list_str = ""
    search_string = ""

    print("YOU are in COMMUNITY PAGE !!")

    if request.method == "GET":
        search_string = "Imagine"

    if request.method == "POST":

        # Retrieve the search string entered by the user
        try:
            search_string = request.form["search"]
        except: 
            try:
                search_string = request.form["searchfilter"]
            except:
                print("NO SEARCH STRING FOUND!!! ") 

    
        print("Search String is : " + search_string) 

        
    # Query Supabase for related prompt data based on the search string
    pod_results = supabase.table('Transcripts').select("*").eq('rank', 888).ilike('prompt', f'%{search_string}%').order('created_at', desc=True).execute()
   

    for pod_record in pod_results:

        # fetch the JSON object at pod_record[1], and get the first and only record at pod_record[1][0]
        # ***this JSON OBJECT REPRESENTS ALL SATISFYING PROMPTS ****
        # convert the JSON DATA object into a Python dictionary
        print(" CURRENT pod_record is : ")
        print( pod_record )
        print(" After printing CURRENT pod_record is : ")
        # this JSON OBJ includes data of ALL satisfying prompts 
        
        print("Total LENGTH of Prompt Items = ")
        print(len(pod_record[1]))

        for i in range(len(pod_record[1])):
            json_obj = pod_record[1][i]
            #print("PRINT this JSON OBJ: ")
            #print(json_obj)
            dict_data = json.loads(json.dumps(json_obj))
            pod_prompt = list(dict_data.values())[2]
            #print("PRINT this PROMPT: ")
            #print(pod_prompt)
            prompt_list.insert(i, pod_prompt)
            prompt_list_str = prompt_list_str + pod_prompt +  " -xxxx- "

        break 

    print("Prompt List is printed below: ")
    for i in range(len(prompt_list)):
        print(prompt_list[i])

    return render_template('community_nm.html', app_version=app_version, prompt_list=prompt_list, prompt_list_str=prompt_list_str)






@app.route('/founders')
def founders():
    return render_template('founders.html', app_version=app_version)

@app.route('/founders_nm')
def founders_nm():
    return render_template('founders_nm.html', app_version=app_version)


@app.route('/mission')
def mission():
    return render_template('mission.html', app_version=app_version)

@app.route('/mission_nm')
def mission_nm():
    return render_template('mission_nm.html', app_version=app_version)


@app.route('/advisory')
def advisory():
    return render_template('advisory.html', app_version=app_version)

@app.route('/advisory_nm')
def advisory_nm():
    return render_template('advisory_nm.html', app_version=app_version)

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
    return render_template('terms.html', app_version=app_version)

@app.route('/privacy')
def privacy():
    return render_template('privacy.html', app_version=app_version)


@app.route("/sendemail", methods=["GET", "POST"])
def sendemail():
    # Your Gmail account information
    message = email.message.EmailMessage()
    useremail = ""
    answer = ""
    userprompt = ""
    json_history = json.dumps({})
    convoindex = 0 
    prompt_list = ""

    try:
        useremail = request.form["useremail"]
    except:
        print("SENDEMAIL:  no useremail")
    
    try: 
        answer =  request.form["answer"]
        userprompt = request.form["userprompt"]
    except:
        print("SENDEMAIL LIGHT MODE: no answer or no userprompt")
        
    try: 
        json_history = request.form["conversation_history"]
    except:
        print("no Conversation History!!??")

    try: 
        prompt_list = request.form["prompt_list"]
    except:
        print("No Prompt List!!")


    sender_email = os.environ['SENDER_EMAIL']
    sender_password = os.environ['SENDER_PASSWORD']
    receiver_email = useremail

    json_history_list = json.loads("[" + json_history + "]")
    json_history_string = json.dumps(json_history_list)

    print("userprompt is : " + userprompt) 
    print("answer is : " + answer) 
    print("useremail is : " + useremail) 
    print("json_history_string : " + json_history_string) 


    # Recreating PROMPT_LIST MESSAGE Text 
    if (prompt_list != ""):
        print("*** SENDEMAIL : CREATE PROMPT LIST MESSAGE ***")
        print("YAY! Prompt_List is NOT EMPTY :  " + prompt_list) 

        formatted_prompt_list = ""
        prompt_split_list = prompt_list.split(" -xxxx- ")
        
        for i in range(len(prompt_split_list)):
            if (prompt_split_list[i] != ""):
                formatted_prompt_list = formatted_prompt_list + str(i+1) + " " + prompt_split_list[i] + "\n \n"
        
        message = MIMEText(formatted_prompt_list)

    # Recreating CONVERSATION MESSAGE Text 
    elif (json_history is not None) and len(json_history_list) > 1 : 
        #re-construct context from conversation_history 
        print("*** SENDEMAIL : CREATE CONVO HISTORY MESSAGE ***")
        print("Convo JSON HISTORY is : ")
        print(json_history)

        print("*** CONVO HISTORY LENGTH = *** ")
        print(len(json_history_list))


        convomessage = ""
        json_list = json.loads(json_history_string)

        for item in json_list:
            if (item != "" and len(item) > 5):
                convomessage = convomessage + "You : " + item.split(" -xxxx- ")[0].strip() + "\n"
                convomessage = convomessage + "Promptly GENIE : " + item.split(" -xxxx- ")[1].strip() + "\n \n"
      
        print("convomessage = " + convomessage) 
        message = MIMEText(convomessage)
    
    # Recreating the message based on simple Prompt and Response
    else:
        print("*** SENDEMAIL : CREATE P&R MESSAGE ***")
        message = MIMEText("Your Prompt : \n" + userprompt + "\n \n" + "Our Response : \n" + answer + "\n \n" + " Promptlys.ai ")

        
    
    message["Subject"] = "Your Promptlys AI Genie Transcript is Ready!" 
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

    return render_template("useremail.html", useremail=useremail, app_version=app_version)


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
    prompt_list = ""

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

    
    try: 
        prompt_list = request.form["prompt_list"]
    except:
        print("No Prompt List!!")


    sender_email = os.environ['SENDER_EMAIL']
    sender_password = os.environ['SENDER_PASSWORD']
    receiver_email = useremail

    json_history_list = json.loads("[" + json_history + "]")
    json_history_string = json.dumps(json_history_list)

    # Recreating PROMPT_LIST MESSAGE Text 
    if (prompt_list != ""):
        print("*** SENDEMAIL_NM : CREATE PROMPT LIST MESSAGE ***")
        print("YAY! Prompt_List is NOT EMPTY :  " + prompt_list) 

        formatted_prompt_list = ""
        prompt_split_list = prompt_list.split(" -xxxx- ")
        
        for i in range(len(prompt_split_list)):
            if (prompt_split_list[i] != ""):
                formatted_prompt_list = formatted_prompt_list + str(i+1) + " " + prompt_split_list[i] + "\n \n"
        
        message = MIMEText(formatted_prompt_list)

    # Recreating CONVERSATION MESSAGE Text 
    elif (json_history is not None) and len(json_history_list) > 1 : 
        #re-construct context from conversation_history 
        print("*** SENDEMAIL_NM : CREATE CONVO HISTORY MESSAGE ***")
        print("Convo JSON HISTORY is : ")
        print(json_history)

        print("*** CONVO HISTORY LENGTH = *** ")
        print(len(json_history_list))

        convomessage = ""
        json_list = json.loads(json_history_string)

        for item in json_list:
            if (item != "" and len(item) > 5):
                convomessage = convomessage + "You : " + item.split(" -xxxx- ")[0].strip() + "\n"
                convomessage = convomessage + "Promptlys GENIE: " + item.split(" -xxxx- ")[1].strip() + "\n \n"
      
        print("convomessage = " + convomessage) 
        message = MIMEText(convomessage)
    
    # Recreating the message based on simple Prompt and Response
    else:
        print("*** SENDEMAIL_NM : CREATE P&R MESSAGE ***")
        message = MIMEText("Your Prompt : \n" + userprompt + "\n \n" + "Our Response : \n" + answer + "\n \n" + " Promptlys.ai ")



    message["Subject"] = "Promptlys P&R AI GENIE Transcript is Ready!" 
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

    return render_template("useremail_nm.html", useremail=useremail, app_version=app_version)


if __name__ == '__main__':
    app.run(host="127.0.0.1", port=8081, debug=True)