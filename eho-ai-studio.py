from flask import Flask, render_template, request

import openai
import os
import io
import warnings

# Use your own API key

openai.api_key = os.environ['OPENAI_KEY']
userprompt=""
answer = ""

print("OPENAI KEY = ")

print(os.environ['OPENAI_KEY'])

def answer_question(question):
    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=question,
        max_tokens=2048,
        n=1,
        stop=None,
        temperature=0.5,
    )
    return response.choices[0].text


#while True:
    #question = input("What's your question? ")
    #if question.lower() == "exit":
        #break
    #print(answer_question(question))


app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():


    if request.method == "POST":
        print(request.form["prompt"])
        userprompt = request.form["prompt"]

        print("Your Question is:"+ userprompt)
    
        if userprompt.lower() == "exit":
            return render_template('index.html')
        
        answer = answer_question(userprompt)
        print("ANSWER IS: " + answer)

        return render_template("answer.html", userprompt=userprompt, answer=answer)
    
    return render_template('index.html')


@app.route('/night_mode')
def night_mode():
    return render_template('night_mode.html')

@app.route('/gallery')
def gallery():
    return render_template('gallery.html')

if __name__ == '__main__':
    app.run(host="127.0.0.1", port=8081, debug=True)


*****************************************************************


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

conversation_history=[]
convolength=0
convocontext=" starting conversation "
convoconjunctor= " given that "
convoconjunctor2 = " , as well as that "
userapikey=""
userprompt=""
usertemp=""
useremail=""
answer = ""
engine_temperature = 0.5
jokeprompt = "Tell me a funny joke about AI in 25 words or less"
response = None


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
    print("POD_Record = ")
    print(pod_record)
    print("POD_Record index 0 = ")
    print(pod_record[0]) 
    print("POD_Record index 1 = ")
    print(pod_record[1]) 
    

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





# PRINT THE PUN OF THE DAY 

try: 
    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=jokeprompt,
        max_tokens=2048,
        n=1,
        stop=None,
        temperature=engine_temperature,
        )
except:
    print("something went wrong while processing your Joke Prompt.. ")
                

jokeanswer = response.choices[0].text


# Define a function to generate a response using OpenAI API
def generate_response(prompt, previous_context):
    if previous_context == "":
        print("GENERATE RESPONSE CONTEXT is EMPTY!! ")
        response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=prompt,
        max_tokens=1000,
        n=1,
        stop=None,
        temperature=0.5
         )
    else: 
        print("GENERATE RESPONSE CONTEXT is " + previous_context)
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
    # check if the session list variable exists, if not create it
    if 'conversation_history' not in session:
        print("Initializing Session Variable conversation_history")
        session['conversation_history'] = []
  
    
    if request.method == "GET":
        return render_template("conversation.html")
    elif request.method == 'POST':
        prompt = request.form['prompt']
    
        convocontext = ""
        convoindex = 0
        #re-construct context from conversation_history 
        for conversation in session['conversation_history']:
            if (convoindex == 0):
                convocontext = convocontext + convoconjunctor + conversation.split(" -xxxx- ")[1].strip()
            else :
                convocontext = convocontext + convoconjunctor2 + conversation.split(" -xxxx- ")[1].strip()
            convoindex +=1
            print("convo index = " + str(convoindex))

        #re-construct context from conversation_history 
        #for conversation in conversation_history:
            #if (convoindex == 0):
                #convocontext = convocontext + convoconjunctor + conversation.split(" -xxxx- ")[1].strip()
            #else :
                #convocontext = convocontext + convoconjunctor2 + conversation.split(" -xxxx- ")[1].strip()

            #convoindex +=1
        
        print("conversation context = " + convocontext) 

        #print("conversation length = " + str(len(conversation_history)))

        print("conversation length = " + str(len(session['conversation_history']))) 


        response = generate_response(prompt, convocontext)
        print("prompt  = " + prompt) 
        print("response = " + response) 
        print("convocontext = " + convocontext)
        #if 'convolength' in session and session['convolength'] > 5:

            #empty conversation if converesation context > 5 
            #conversation_history = []
            #print("conversation length = " + convolength) 
            #print("about to empty conversation history !!") 
            #session['conversation_history'] = []
            #session['convolength'] = 0


        if  (len(session['conversation_history']) >= 5):

            #empty conversation if converesation context > 5 
            print("about to empty conversation history when it reaches 5 !!") 
            session['conversation_history'].clear()
            print("about to reset convocontext !!") 
            convocontext = ""
            #session['conversation_history'] = []
            #session['convolength'] = 0
        
        #previous_response defined as CONTEXT 
        #convocontext = convocontext + convoconjunctor + response 
        print("Convo Pair :  " + prompt + " -xxxx- " + response) 

        session['conversation_history'].append(prompt + " -xxxx- " + response) 
        #session['conversation_history'].append(prompt + " - " + response) 
       
        #if prompt:
           # conversation_history = session.get('conversation_history', [])
           # response = generate_response(prompt, conversation_history)
            #conversation_history.append((prompt, response))
            #session['conversation_history'] = conversation_history
    
        #else:
    #session.pop('conversation_history', None)
    
    #return render_template('conversation.html', conversation_history=session.get('conversation_history', []))
    return render_template('conversation.html', conversation_history=session['conversation_history'], conversation_length=len(session['conversation_history']))



#@app.route("/conversation", methods=["GET", "POST"])
#def conversation():
   # if request.method == "GET":
   #     return render_template("conversation.html")
    #elif request.method == "POST":
       # prompt = request.form["prompt"]
      #  previous_response = prompt
       # response = generate_response(prompt)
      #  conversation_history = [prompt + " - " + response]
      #  for i in range(2):
         #   prompt = request.form["prompt"]
         #   response = generate_response(prompt, previous_response)
          #  previous_response += response
            #conversation_history.append(previous_response)
         #   conversation_history.append(prompt + " - " + response)
      #  return render_template("conversation.html", conversation_history=conversation_history)


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