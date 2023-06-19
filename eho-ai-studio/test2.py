import base64


import openai
import os
import io
import warnings
import json
import re
import time
import sys

import smtplib
from email.mime.text import MIMEText
import email.message 

from supabase import create_client
from array import array 




# Set the base API endpoint to a custom URL

##  https://api.openai.com/v1/chat/completions
##  https://5yeeyz5uyd.execute-api.us-east-1.amazonaws.com

##base_url = "https://5yeeyz5uyd.execute-api.us-east-1.amazonaws.com"
##openai.api_client.base_url = base_url



print(sys.executable)


# Example of an OpenAI ChatCompletion request
# https://platform.openai.com/docs/guides/chat

# record the time before the request is sent
start_time = time.time()



print("****** NON-STREAMING API TESTING BELOW********************")

# send a ChatCompletion request to count to 100
response = openai.ChatCompletion.create(
    model='gpt-3.5-turbo',
    messages=[
        {'role': 'user', 'content': 'Count to 100, with a comma between each number and no newlines. E.g., 1, 2, 3, ...'}
    ],
    temperature=0,
)

# calculate the time it took to receive the response
response_time = time.time() - start_time

# print the time delay and text received
print(f"Full response received {response_time:.2f} seconds after request")
print(f"Full response received:\n{response}")


print("****** STREAMING TESTING BELOW********************")

# Example of an OpenAI ChatCompletion request with stream=True
# https://platform.openai.com/docs/guides/chat

# record the time before the request is sent
start_time = time.time()

# send a ChatCompletion request to count to 100
response = openai.ChatCompletion.create(
    model='gpt-3.5-turbo',
    messages=[
        {"role": "system", "content": "You are a smart assistant with a great sense of humor and always start your response with courteous greetings "},
        {'role': 'user', 'content': 'Repeat the following greetings word for word please:  Welcome to Promptlys!  If you feel annoyed or frustrated trying to come up with prompts,  you are not alone! Here you can access and learn from quality prompts created by the best prompt creators in the field.'}
    ],
    temperature=0,
    stream=True  # again, we set stream=True
)

# create variables to collect the stream of chunks
collected_chunks = []
collected_messages = []
# iterate through the stream of events
for chunk in response:
    chunk_time = time.time() - start_time  # calculate the time delay of the chunk
    collected_chunks.append(chunk)  # save the event response
    chunk_message = chunk['choices'][0]['delta']  # extract the message
    collected_messages.append(chunk_message)  # save the message
    chunk_content = ""
    try: 
        chunk_content = chunk['choices'][0]['delta']['content']
        # yield "data: {}\n\n".format(chunk_content)  # yield the chunk content as SSE data

    except (KeyError, IndexError):
        continue  # continue to the next chunk if the necessary keys don't exist

    #print(f"Message received {chunk_time:.2f} seconds after request: **** {chunk_message}  ****")  # print the delay and text
    #print(f"CONTENT received {chunk_time:.2f} seconds after request: **** {chunk_content}  ****")  # print the delay and text


# print the time delay and text received
print(f"Full response received {chunk_time:.2f} seconds after request")
full_reply_content = ''.join([m.get('content', '') for m in collected_messages])
print(f"Full conversation received: {full_reply_content}")


