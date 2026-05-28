# Fate Elemental Clash

Fate Elemental Clash is a real-time multiplayer web game built on a containerized microservice architecture. The primary objective of the project was to engineer a distributed system capable of handling simultaneous player inputs without data corruption or state overwriting.

**Live Google Cloud Server:** [http://34.101.205.113:5173](http://34.101.205.113:5173)

## How It Works Under the Hood

The entire application is containerized utilizing Docker and divided into five distinct microservices:

* **React + Vite (Frontend):** A responsive UI that communicates with the backend over WebSockets. It dynamically detects the host IP, ensuring the exact same codebase functions seamlessly on both a local machine and the live cloud server.
* **Flask + SocketIO (Gateway):** The primary server hub that manages player rooms and broadcasts game updates back to the clients.
* **RabbitMQ (Message Queue):** Integrated to prevent race conditions. If both players execute an attack at the exact same millisecond, RabbitMQ queues the incoming requests chronologically so the backend engine processes them safely.
* **Redis (Database):** A high-speed, in-memory data store utilized to track player health, elements, and active roles. 
* **Python Engine (Worker):** A background script that consumes actions from the queue, calculates the elemental damage multipliers, updates Redis, and pushes the final results back to the Flask server.

## Notable Engineering Solutions
* **Ghost Memory Mitigation:** Previously, an abandoned browser session would leave stale health data trapped in Redis, corrupting subsequent matches. To resolve this, a hard reset protocol was implemented to automatically wipe room data the moment a new session initializes.
* **Decoupled Identifiers:** The backend mathematical logic requires strict `player1` and `player2` identifiers. To improve user experience, the UI permits custom display names while silently binding them to the strict backend roles via a manual selector.

## Running it Locally

To run the stack locally, Docker must be installed on the host machine.

1. Clone the repository:
   ```bash
   git clone [https://github.com/nickkenn17-code/game-fate-elemental-clash.git](https://github.com/nickkenn17-code/game-fate-elemental-clash.git)
   cd game-fate-elemental-clash

2. Run the code:
   ```bash
   docker compose up
