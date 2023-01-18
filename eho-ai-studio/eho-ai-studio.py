from flask import Flask, render_template, request

import openai
import os
import io
import warnings

# Use your own API key

openai.api_key = os.environ['OPENAI_KEY']
userprompt=""
answer = ""

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
    app.run(host="127.0.0.1", port=8082, debug=True)
