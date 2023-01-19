from flask import Flask, render_template, request

import openai
import os
import io
import warnings

# Use your own API key

#openai.api_key = os.environ['OPENAI_KEY']
openai.api_key = ""

userapikey = ""
userprompt=""
usertemp=""
answer = ""
engine_temperature = 0.5

#def answer_question(question):
 #   response = openai.Completion.create(
  #      engine="text-davinci-003",
   #     prompt=question,
    #    max_tokens=2048,
     #   n=1,
      #  stop=None,
       # temperature=0.5,
   # )
   # return response.choices[0].text


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
        userapikey = request.form["apikey"]
        usertemp = request.form["temperature"]

        print("Your Question is: "+ userprompt)
        print("Your API Key is:" + userapikey)
        print("Your Requested Temperature is: " + usertemp)

        openai.api_key = userapikey


        if (usertemp == "Standard"):
            engine_temperature = 0.5
        if (usertemp == "High"):
            engine_temperature = 1.0
        if (usertemp == "Ultra"):
            engine_temperature = 1.5

        print("Temperature set to " + usertemp + "at : " + str(engine_temperature))

        try: 
            response = openai.Completion.create(
                engine="text-davinci-003",
                prompt=userprompt,
                max_tokens=2048,
                n=1,
                stop=None,
                temperature=engine_temperature,
            )
        except:
            return render_template("error.html", userapikey=userapikey)

        answer = response.choices[0].text
    
        if userprompt.lower() == "exit":
            return render_template('index.html')
        
        #answer = answer_question(userprompt)
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
