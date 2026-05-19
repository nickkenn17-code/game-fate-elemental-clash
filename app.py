from flask import Flask
from flask_socketio import SocketIO, join_room, emit
import redis
import pika
import json
import os
import time

app = Flask(__name__)
app.config['SECRET_KEY'] = 'fate_secret_key'

# Get hostnames from environment variables (defaults to 'localhost' for local testing)
REDIS_HOST = os.getenv('REDIS_HOST', 'redis')
RABBITMQ_HOST = os.getenv('RABBITMQ_HOST', 'rabbitmq')

socketio = SocketIO(app, cors_allowed_origins="*", message_queue=f'redis://{REDIS_HOST}:6379/0')

# --- REDIS CONNECTION ---
db = redis.Redis(host=REDIS_HOST, port=6379, db=0, decode_responses=True)
try:
    db.ping()
    print("Success: Connected to Redis at {REDIS_HOST}!")
except redis.ConnectionError:
    print("Error: Could not connect to Redis.")

# --- RABBITMQ CONNECTION ---
print(f"Connecting to RabbitMQ at {RABBITMQ_HOST}...")
while True:
    try:
        rabbitmq_connection = pika.BlockingConnection(pika.ConnectionParameters(RABBITMQ_HOST))
        rabbitmq_channel = rabbitmq_connection.channel()
        rabbitmq_channel.queue_declare(queue='game_moves')
        print(f"Success: Connected to RabbitMQ at {RABBITMQ_HOST}!")
        break # Break the loop once connected
    except pika.exceptions.AMQPConnectionError:
        print("RabbitMQ not ready yet, waiting 3 seconds...")
        time.sleep(3) # Wait and try again

@app.route('/')
def index():
    return "Fate Elemental Clash Backend is Running!"

# --- WEBSOCKET EVENTS ---

@socketio.on('join_game')
def handle_join(data):
    room = data['room']
    player_id = data['player_id'] # e.g., 'player1' or 'player2'
    
    join_room(room) # Places the player in a specific SocketIO room
    
    # Initialize HP in Redis if it is a new game
    if not db.exists(f"{room}_hp_player1"):
        db.set(f"{room}_hp_player1", 10)
        db.set(f"{room}_hp_player2", 10)
        
    print(f"{player_id} joined room: {room}")
    emit('game_update', {'msg': f'{player_id} has joined the game :)'}, to=room)

@socketio.on('make_move')
def handle_move(data):
    room = data['room']
    player_id = data['player_id'] 
    move_type = data['move_type'] # Will be 'rpc' (rock/paper/scissors) or 'element'
    choice = data['choice']       # e.g., 'rock', 'fire', 'water'

    # 1. Save the hidden choice in Redis (e.g., "room1_player1_rpc" = "rock")
    db.set(f"{room}_{player_id}_{move_type}", choice)
    print(f"Saved to Redis: {player_id} chose {choice} for {move_type}")
    
    # 2. Publish an event to RabbitMQ
    move_event = json.dumps({
        "room": room,
        "player_id": player_id,
        "move_type": move_type
    })
    
    rabbitmq_channel.basic_publish(
        exchange='',
        routing_key='game_moves',
        body=move_event
    )
    print(f"Published to RabbitMQ: {move_event}")
    
    # 3. Notify BOTH players that a move was locked in (without revealing what it is!)
    emit('move_locked', {'player_id': player_id, 'msg': 'Move locked in !!!'}, to=room)

if __name__ == '__main__':
    print("Starting Fate Game Server...")
    socketio.run(app, debug=True, host='0.0.0.0', port=5000, allow_unsafe_werkzeug=True)