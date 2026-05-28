# Fate Elemental Clash

Fate Elemental Clash is a real-time multiplayer web game I built for my software engineering assignment. The goal was to build a distributed system that could handle simultaneous player inputs without breaking or overwriting data. 

**Live Google Cloud Server:** [http://34.101.205.113:5173](http://34.101.205.113:5173)

## How It Works Under the Hood

The whole application is containerized using Docker and is split into five distinct services:

* **React + Vite (Frontend):** A responsive UI that talks to the backend over WebSockets. It dynamically detects the host IP, so the same code works on my local laptop and the live cloud server without manual changes.
* **Flask + SocketIO (Gateway):** The main hub that manages player rooms and broadcasts game updates back to the browsers.
* **RabbitMQ (Message Queue):** I added this to prevent race conditions. If both players lock in an attack at the exact same millisecond, RabbitMQ lines up the requests chronologically so the engine processes them safely.
* **Redis (Database):** A fast in-memory store used to track player health, elements, and active roles. 
* **Python Engine (Worker):** A background script that pulls moves from the queue, calculates the elemental damage multipliers, updates Redis, and pushes the results back to the Flask server.

## Notable Fixes
* **The "Ghost" Data Bug:** Originally, if a player closed their browser mid-game, their old health data would stay trapped in Redis and corrupt the next game. I implemented a hard reset protocol that automatically wipes stale room data the moment a new session initializes.
* **Role Assignments:** The game logic requires strict `player1` and `player2` identifiers to run the math, but I wanted players to use their own names. The UI lets players enter custom display names while silently binding them to the strict backend roles via a manual selector.

## Running it Locally

If you want to run the stack on your own machine, you just need Docker installed.

1. Clone the repository:
   ```bash
   git clone [https://github.com/nickkenn17-code/game-fate-elemental-clash.git](https://github.com/nickkenn17-code/game-fate-elemental-clash.git)
   cd game-fate-elemental-clash
