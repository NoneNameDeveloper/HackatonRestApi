import json
import websocket
import random
from threading import Thread    
import uuid
import requests
import traceback

import time

from urllib.parse import quote

base_url = "http://greed.implario.net:8096"
company_token = "1Ly23aDMsRBpKiqShdScHA"



ws = websocket.create_connection('wss://web.tada.team/messaging/1ee07992-fa6d-6af2-817c-0242ac110006', header={"token": "TqrUB34qzCM3i21gKtIeSfAJ8E7NsAYQXYsyfBcI9SjCXsh5JQZ2lTiHi7xPQOPZ7wEL3K2KUI3kP8m8sI0heN5zUoGgwpF25VIO0WmWhMUYce51a3VWdIteQf6ICKI4"})

print('connected')
work = []
def update_messages():
    while True:
        try:
            time.sleep(3)
            for w in work:
                url = f"{base_url}/get_conversation?token={company_token}&conversation_id={w[1]}"
                api_response = requests.get(url).json()
                print("EDITING, MOUTHFUL API: " + str(api_response))

                t = api_response['conversation']['response_text'] + str(random.random())
                u = w[0]
                response = {"event":"client.message.updated","confirm_id":str(random.random()),"params":{"to":from_id,"content":{"text":t,"type":"plain"},"message_id":u,"linked_messages":[],"reply_to":None,"uploads":[],"old_style_attachment":True}}
                print("EDITING, TO TADA" + str(response))
                print(ws)
                ws.send(json.dumps(response))
        except Exception:
            print(traceback.format_exc())


thread = Thread(target = update_messages)
# thread.start()


# a = {"event":"server.message.updated","confirm_id":"46LSJZk7v2Ht","params":{"messages":[{"content":{"text":"234","type":"plain"},"push_text":"234","from":"d-1ee07992-fee2-6ad3-817c-0242ac110006","to":"d-1ee08521-919c-636d-829a-0242ac110013","message_id":"92e41fa8-4f3e-4c61-ab71-7b7725679686","created":"2023-06-11T13:30:14.932711Z","gentime":1686490214970880824,"chat_type":"direct","chat":"d-1ee07992-fee2-6ad3-817c-0242ac110006","prev":"35811433-d5f0-4219-8af0-ea3c8aaaa31c","is_last":true,"silently":true,"num":23}],"delayed":false,"chat_counters":[{"jid":"d-1ee07992-fee2-6ad3-817c-0242ac110006","chat_type":"direct","gentime":1686490214934543934,"num_unread":3,"num_unread_notices":0,"last_read_message_id":"44897ab9-920d-4568-8557-486df542ffc7","last_activity":"2023-06-11T13:30:14.932711Z"}],"team_unread":{"direct":{"messages":6,"notice_messages":0,"chats":4},"group":{"messages":3,"notice_messages":0,"chats":1},"meeting":{"messages":0,"notice_messages":0,"chats":0},"task":{"messages":0,"notice_messages":0,"chats":0}},"badge":9}}

while True:
    data = ws.recv()
    print(f"FROM TADA: {data}")
    event = json.loads(data)
    if "confirm_id" in event:
        ws.send(json.dumps({"event":"client.confirm","params":{"confirm_id":event['confirm_id']}}))
    if event.get("event") == "server.message.updated":
        message = event['params']['messages'][0]
        text = message['content']['text']
        from_id = message['from']
        url = f"{base_url}/new_conversation?user_id={4545}&token={company_token}&initial_message={quote(text)}"
        api_response = requests.post(url).json()
        print("MOUTHFUL API: " + str(api_response))

        u = str(uuid.uuid4())
        w = (u, api_response['conversation']['conversation_id'])
        work.append(w)
        print("WORK: " + str(work))

        response = {"event":"client.message.updated","confirm_id":str(random.random()),"params":{"to":from_id,"content":{"text":api_response['conversation']['response_text'],"type":"plain"},"message_id":u,"linked_messages":[],"reply_to":None,"uploads":[],"old_style_attachment":True}}
        print("MESSAGE TO TADA" + str(response))
        ws.send(json.dumps(response))
        while True:
            data = ws.recv()
            print(f"FROM TADA: {data}")
            event = json.loads(data)
            if "confirm_id" in event:
                ws.send(json.dumps({"event":"client.confirm","params":{"confirm_id":event['confirm_id']}}))
            url = f"{base_url}/get_conversation?token={company_token}&conversation_id={w[1]}"
            api_response = requests.get(url).json()
            print("EDITING, MOUTHFUL API: " + str(api_response))

            t = api_response['conversation']['response_text']
            u = w[0]
            response = {"event":"client.message.updated","confirm_id":str(random.random()),"params":{"to":from_id,"content":{"text":t,"type":"plain"},"message_id":u,"linked_messages":[],"reply_to":None,"uploads":[],"old_style_attachment":True}}
            print("EDITING, TO TADA" + str(response))
            print(ws)
            ws.send(json.dumps(response))
            if api_response['conversation']['response_finished']:
                break
        


        
        


        


