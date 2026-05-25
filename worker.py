import pika
import redis
import json
import os
import time
from flask_socketio import SocketIO
from game_logic import resolve_rpc, calculate_combat

# 1. Grab the Docker network hostnames (defaults to localhost if not found)
REDIS_HOST = os.getenv('REDIS_HOST', 'redis')
RABBITMQ_HOST = os.getenv('RABBITMQ_HOST', 'rabbitmq')

# 2. Connect to Redis (State Management)
print(f"Connecting to Redis at {REDIS_HOST}...")
db = redis.Redis(host=REDIS_HOST, port=6379, db=0, decode_responses=True)

# 3. Connect SocketIO Bridge (inject REDIS_HOST)
socketio = SocketIO(message_queue=f'redis://{REDIS_HOST}:6379/0')

# 4. Connect to RabbitMQ (With Cloud-Native Retry Loop!)
print(f"Connecting to RabbitMQ at {RABBITMQ_HOST}...")
while True:
    try:
        connection = pika.BlockingConnection(pika.ConnectionParameters(RABBITMQ_HOST, heartbeat=0))
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
    
    # LINK: UI Confirmation
    if move_type != 'reset':
        socketio.emit('move_locked', {'player_id': event['player_id']}, to=room)
    
    # THE MASTER RESET OVERRIDE
    if move_type == 'reset':
        db.delete(f"{room}_hp_player1", f"{room}_hp_player2", f"{room}_attacker", f"{room}_defender")
        db.delete(f"{room}_player1_rpc", f"{room}_player2_rpc", f"{room}_player1_element", f"{room}_player2_element")
        socketio.emit('server_reset', {'msg': 'SERVER OVERRIDE: Timeline reset. HP restored to 100.'}, to=room)
        print(f"[Worker] Room {room} memory explicitly wiped.")
        return # Stop processing and exit

    p1_choice = db.get(f"{room}_player1_{move_type}")
    p2_choice = db.get(f"{room}_player2_{move_type}")

    if p1_choice and p2_choice:
        print(f"[Worker] Both players locked in {move_type}! Calculating...")
        
        # --- PHASE 1: PRIORITY (ROCK PAPER SCISSORS) ---
        if move_type == 'rpc':
            winner = resolve_rpc(p1_choice, p2_choice)
            db.delete(f"{room}_player1_rpc", f"{room}_player2_rpc")
            
            if winner == 'tie':
                socketio.emit('rpc_result', {'winner': 'tie'}, to=room)
                print("[Worker] RPC Tie. Restarting phase.")
            else:
                # Assign roles
                attacker = winner
                defender = 'player2' if winner == 'player1' else 'player1'
                db.set(f"{room}_attacker", attacker)
                db.set(f"{room}_defender", defender)
                
                # Only initialize Health Bars if they don't already exist in Redis!
                if not db.exists(f"{room}_hp_player1"):
                    db.set(f"{room}_hp_player1", 100)
                    db.set(f"{room}_hp_player2", 100)
                
                socketio.emit('rpc_result', {
                    'winner': winner, 
                    'attacker': attacker,
                    'defender': defender
                }, to=room)
                print(f"[Worker] Roles assigned: {attacker} is Attacking!")

        # --- PHASE 2: ELEMENTAL CLASH ---
        elif move_type == 'element':
            attacker = db.get(f"{room}_attacker")
            
            # Figure out who picked which element
            attacker_choice = p1_choice if attacker == 'player1' else p2_choice
            defender_choice = p2_choice if attacker == 'player1' else p1_choice
            
            # Calculate Damage using your custom logic
            dmg_to_defender, dmg_to_attacker = calculate_combat(attacker_choice, defender_choice)
            
            # Retrieve current HP from Redis
            p1_hp = int(db.get(f"{room}_hp_player1"))
            p2_hp = int(db.get(f"{room}_hp_player2"))
            
            # Deduct HP
            if attacker == 'player1':
                p1_hp -= dmg_to_attacker
                p2_hp -= dmg_to_defender
            else:
                p2_hp -= dmg_to_attacker
                p1_hp -= dmg_to_defender
                
            # Save new HP back to Redis
            db.set(f"{room}_hp_player1", p1_hp)
            db.set(f"{room}_hp_player2", p2_hp)
            db.delete(f"{room}_player1_element", f"{room}_player2_element")
            
            # If the game is over, wipe the HP from Redis so the next game starts fresh
            if p1_hp <= 0 or p2_hp <= 0:
                db.delete(f"{room}_hp_player1", f"{room}_hp_player2")
            
            socketio.emit('element_result', {
                'attacker_choice': attacker_choice,
                'defender_choice': defender_choice,
                'dmg_to_defender': dmg_to_defender,
                'dmg_to_attacker': dmg_to_attacker,
                'p1_hp': p1_hp,
                'p2_hp': p2_hp
            }, to=room)
            print(f"[Worker] Clash complete! P1 HP: {p1_hp} | P2 HP: {p2_hp}")

print("Fate Game Worker is listening for RabbitMQ messages...")
channel.basic_consume(queue='game_moves', on_message_callback=process_move, auto_ack=True)
channel.start_consuming()