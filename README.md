# Promptlys

Promptlys is a web application built with Flask, a Python web framework, and powered by OpenAI's GPT-3.5-Turbo language model. It allows users to ask questions and receive AI-generated responses based on the provided prompt.

Features
Question-Answering: Users can enter a prompt or question, and the application will generate a response using the OpenAI API.
Conversation Mode: Users can engage in a conversation with the AI model by providing multiple prompts in a conversational format. The application maintains a conversation history and context to generate meaningful responses.
Personalization: Users can customize the API key and temperature settings for generating responses according to their preferences.
Email Transcripts: Users have the option to receive the question and answer transcripts via email by providing their email address.
Setup and Usage
To set up and run the Flask AI Genie application, follow these steps:

Install the required dependencies by running pip install -r requirements.txt.
Set up the necessary environment variables, including OPENAI_KEY, SUPABASE_URL, SUPABASE_KEY, SENDER_EMAIL, and SENDER_PASSWORD. These variables are used for API keys, Supabase database configuration, and email sending.
Run the application using python app.py. The application will run on http://localhost:8081 by default.
Access the application in a web browser and interact with the AI Genie by entering prompts and questions.
Additional Information
The Flask AI Genie application demonstrates how to integrate OpenAI's powerful GPT-3.5 language model into a Flask web application. It showcases features such as conversation handling, personalization options, and email integration. The application leverages Supabase, an open-source Firebase alternative, to store and retrieve question-answer transcripts for future reference.

The code is well-documented, providing explanations and comments throughout to aid understanding and further customization. It also includes error handling and validation to ensure a smooth user experience. Feel free to explore and modify the code according to your needs.

Please note that this application requires valid API keys and credentials for OpenAI and Supabase. Make sure to provide the necessary environment variables to enable seamless functionality.

For any issues or questions, please refer to the official OpenAI documentation or reach out to the Flask AI Genie development team.

Enjoy using Flask AI Genie and have fun exploring the capabilities of OpenAI's GPT-3.5-Turbo language model!
