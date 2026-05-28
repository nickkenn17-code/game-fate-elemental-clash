# Fate Elemental Clash

A containerized multiplayer combat simulation built with a microservice architecture. This project demonstrates real-time state management, asynchronous message queuing, and cloud deployment.

**Live Server:** [http://34.101.205.113:5173](http://34.101.205.113:5173)

## Architecture Overview

The system is split into five Docker containers to separate the frontend interface, websocket gateway, message queuing, data storage, and game logic.

* **Frontend (React + Vite):** A fluid, responsive UI built with Flexbox. It handles the WebSocket connections to the server and dynamically routes to the host IP.
* **Gateway (Flask + SocketIO):** The main server hub. It manages player rooms, accepts incoming connections, and broadcasts combat results back to the React clients.
* **Message Queue (RabbitMQ):** Prevents race conditions. Since both players can submit their moves at the exact same millisecond, RabbitMQ queues the incoming network requests so the backend processes them in chronological order.
* **State Database (Redis):** High-speed, in-memory storage for player HP, room states, and active roles. 
* **Engine Worker (Python):** A background script that pulls actions from RabbitMQ, runs the elemental math, updates Redis, and pushes the final calculated data back to Flask.

## Key Engineering Solutions

* **Ghost Memory Mitigation:** Implemented a hard reset protocol. It automatically wipes old Redis keys when a room is initialized, preventing corrupted health bars caused by abandoned browser tabs or mid-game page refreshes.
* **Decoupled Identifiers:** Players can enter custom display names in the UI, while the backend strictly categorizes them via a manual role selector (`player1` and `player2`) to prevent the mathematical logic from breaking.
* **Dynamic Cloud Routing:** The frontend automatically detects the browser's current host IP, allowing the exact same codebase to work locally on `localhost` or globally on a virtual machine without requiring manual configuration changes.

## Local Setup

**Requirements:** Docker and Docker Compose.

1. Clone the repository:
   ```bash
   git clone [https://github.com/nickkenn17-code/game-fate-elemental-clash.git](https://github.com/nickkenn17-code/game-fate-elemental-clash.git)
   cd game-fate-elemental-clash
