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

from supabase import create_client
from array import array 


userapikey=""
userprompt=""
usertemp=""
useremail=""
answer = ""
engine_temperature = 0.5
response = None

jokeprompt = "Tell me a funny joke about AI in 25 words or less"
jokeanswer = ""

convo_history = ['']
convo_context = ""
dict_data = {}
convoconjunctor= " given that "
convoconjunctor2 = " , as well as that "


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
    #print("POD_Record = ")
    #print(pod_record)
    #print("POD_Record index 0 = ")
    #print(pod_record[0]) 
    #print("POD_Record index 1 = ")
    #print(pod_record[1]) 
    

    # fetch the JSON object from the list
    # convert the JSON DATA object into a Python dictionary
    json_obj = pod_record[1][0]
    dict_data = json.loads(json.dumps(json_obj))


    # Fetch and Print the PROMPT value
    print(" Prompt of the Day = " ) 
    pod_prompt = list(dict_data.values())[2]
    print(pod_prompt) 

    break

# Use your own API key

try:
    openai.api_key = os.environ['OPENAI_KEY']
except:
    print("Sorry, No Key available")




# Define a function to generate a response using OpenAI API
def generate_response(prompt, previous_context):
    if previous_context == "":
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
        print("GENERATE_RESPONSE CONTEXT NOT EMPTY :  " + previous_context)
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


    # check if the session variable convo_history exists, if not create it
    #print("CURRENT Session ID:", session.sid)
    if ('convo_ID' not in session) or (session['convo_ID'] == 0) :
        print("Initializing session Variable convo_ID")
    
        # fetch latest convo_ID record 
        cid_results=[]
        cid_results = supabase.table('Conversations').select("*").order('convo_ID').limit(1).execute()
        cid_record_id=0

        for cid_record in cid_results:
    
            # fetch the JSON object from the list
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
        return render_template("conversation.html")
    elif request.method == 'POST':
        prompt = request.form['prompt']
    
 
        #re-construct convo_context from convo_history 
        #for conversation in convo_history:
           # if (convoindex == 0):
             #   convo_context = convo_context + convoconjunctor + conversation.split(" -xxxx- ")[1].strip()
           # else :
              #  convo_context = convo_context + convoconjunctor2 + conversation.split(" -xxxx- ")[1].strip()

           # convoindex +=1
        
        print("convo context = " + convo_context) 
        print("convo_history length = " + str(len(convo_history))) 

        response = generate_response(prompt, convo_context)
        print("prompt  = " + prompt) 
        print("response = " + response) 
        print("convo_context = " + convo_context)


        if  (len(convo_history) >= 7):

            #empty conversation if converesation context > 5 
            print("about to empty conversation history when it reaches 5 !!") 
            convo_history.clear()
    
            #resetting Conversation ID 
            #session['convo_ID'] = 0

            print("about to reset convo_context !!") 
            convo_context = ""
      
            
        
        #previous_response defined as CONTEXT 
        #convo_context = convo_context + convoconjunctor + response 
        print("Current Convo Pair :  " + prompt + " -xxxx- " + response) 

        convo_history.append(prompt + " -xxxx- " + response) 
        #session['convo_history'].append(prompt + " - " + response) 
        print("convo_history length AFTER APPEND = " + str(len(convo_history))) 

        # Convert the array to a JSON string and remove the square brackets
        convo_history_str = json.dumps(convo_history)[1:-1]

        #Updating context data of Conversation ID  in DB
        supabase.table('Conversations').update({"convo_context" : f'{convo_context}', "convo_history" : f'{{{convo_history_str}}}' }).eq('convo_ID', convo_ID).execute()

    return render_template('conversation.html', conversation_history=convo_history, conversation_length=len(convo_history))


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
    
        try: 
            models = openai.Model.list()
        except: 
            print("sorry, wrong key")
            return render_template("error.html", userapikey=openai.api_key)
    

        print("Available Models are: ")
        for model in models['data']:
            print(model.id)
            if (model.id == "text-davinci-003"):
                available_003 = True

        if (usertemp == "Standard"):
            engine_temperature = 0.5
        if (usertemp == "High"):
            engine_temperature = 1.0
        if (usertemp == "Ultra"):
            engine_temperature = 1.5

        print("Temperature set to " + usertemp + "at : " + str(engine_temperature))

        if (available_003):
            try: 
                print("Davince-003 is available !! ")
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
        models = openai.Model.list()
        print("Available Models are: ")
        for model in models['data']:
            print(model.id)
            if (model.id == "text-davinci-003"):
                available_003 = True


        if (usertemp == "Standard"):
            engine_temperature = 0.5
        if (usertemp == "High"):
            engine_temperature = 1.0
        if (usertemp == "Ultra"):
            engine_temperature = 1.5

        print("Temperature set to " + usertemp + "at : " + str(engine_temperature))

        if (available_003):
            try: 
                print("Davince-003 is available !! ")
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
            print("oops.. INSERT went wrong while saving transacript into Supabase ")
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
    useremail = request.form["useremail"]
    
    answer =  request.form["answer"]
    userprompt = request.form["userprompt"]

    print("user email : " + useremail)
    print("user prompt : " + userprompt)
    print("user answer : " + answer)

    sender_email = os.environ['SENDER_EMAIL']
    sender_password = os.environ['SENDER_PASSWORD']
    receiver_email = useremail

    # Create the message
    message = MIMEText("Your Question : \n" + userprompt + "\n" + "\n" + "Our Response : \n" + answer + "\n" + "\n" + "Sincerely \n" + "EHO AI STUDIO 23")
    message["Subject"] = "Q&A AI GENIE Transcript is Ready!" 
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
    useremail = request.form["useremail"]
    
    answer =  request.form["answer"]
    userprompt = request.form["userprompt"]

    print("user email : " + useremail)
    print("user prompt : " + userprompt)
    print("user answer : " + answer)

    sender_email = os.environ['SENDER_EMAIL']
    sender_password = os.environ['SENDER_PASSWORD']
    receiver_email = useremail

    # Create the message
    message = MIMEText("Your Question : \n" + userprompt + "\n" + "\n" + "Our Response : \n" + answer + "\n" + "\n" + "Sincerely \n" + "EHO AI STUDIO 23")
    message["Subject"] = "Q&A AI GENIE Transcript is Ready!" 
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