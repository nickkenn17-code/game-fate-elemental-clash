# worker.py
import pika
import redis
import json
import os
import time
from flask_socketio import SocketIO
from game_logic import resolve_rpc, calculate_damage

# 1. Grab the Docker network hostnames (defaults to localhost if not found)
REDIS_HOST = os.getenv('REDIS_HOST', 'redis')
RABBITMQ_HOST = os.getenv('RABBITMQ_HOST', 'rabbitmq')

# 2. Connect to Redis (State Management)
print(f"Connecting to Redis at {REDIS_HOST}...")
db = redis.Redis(host=REDIS_HOST, port=6379, db=0, decode_responses=True)

# 3. Connect SocketIO Bridge (MUST use the f-string to inject REDIS_HOST)
socketio = SocketIO(message_queue=f'redis://{REDIS_HOST}:6379/0')

# 4. Connect to RabbitMQ (With Cloud-Native Retry Loop!)
print(f"Connecting to RabbitMQ at {RABBITMQ_HOST}...")
while True:
    try:
        connection = pika.BlockingConnection(pika.ConnectionParameters(RABBITMQ_HOST))
        channel = connection.channel()
        channel.queue_declare(queue='game_moves')
        print("Success: Connected to RabbitMQ!")
        break # Break out of the loop once connected!
    except pika.exceptions.AMQPConnectionError:
        print("RabbitMQ not ready yet, waiting 3 seconds...")
        time.sleep(3) # Wait 3 seconds and try again

# 5. The Game Logic Engine
def process_move(ch, method, properties, body):
    event = json.loads(body)
    room = event['room']
    move_type = event['move_type']

    print(f"\n[Worker] Received move event: {event}")

    p1_choice = db.get(f"{room}_player1_{move_type}")
    p2_choice = db.get(f"{room}_player2_{move_type}")

    if p1_choice and p2_choice:
        print(f"[Worker] Both players locked in {move_type}! Calculating...")
        
        if move_type == 'rpc':
            winner = resolve_rpc(p1_choice, p2_choice)
            db.delete(f"{room}_player1_rpc", f"{room}_player2_rpc")
            
            socketio.emit('rpc_result', {
                'winner': winner, 
                'p1_choice': p1_choice, 
                'p2_choice': p2_choice
            }, to=room)
            print(f"[Worker] RPC Result sent: {winner} wins priority!")

        elif move_type == 'element':
            damage = calculate_damage(p1_choice, p2_choice)
            current_hp = int(db.get(f"{room}_hp_player2"))
            new_hp = current_hp - damage
            db.set(f"{room}_hp_player2", new_hp)
            
            db.delete(f"{room}_player1_element", f"{room}_player2_element")
            
            socketio.emit('element_result', {
                'damage': damage,
                'p2_new_hp': new_hp,
                'p1_element': p1_choice,
                'p2_element': p2_choice
            }, to=room)
            print(f"[Worker] Elemental clash! {damage} damage dealt.")

print("Fate Game Worker is listening for RabbitMQ messages...")
channel.basic_consume(queue='game_moves', on_message_callback=process_move, auto_ack=True)
channel.start_consuming()