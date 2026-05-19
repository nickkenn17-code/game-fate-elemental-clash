import { useState, useEffect } from 'react';
import { io } from 'socket.io-client';
import './App.css';

// Connect to  local Flask backend
const socket = io('http://localhost:5000');

function App() {
  const [room, setRoom] = useState('FateRoom1');
  const [playerId, setPlayerId] = useState('player1');
  const [inGame, setInGame] = useState(false);
  const [phase, setPhase] = useState('rpc'); // Starts with Rock-Paper-Scissors
  const [log, setLog] = useState(['Welcome to Fate Elemental Clash!']);
  const [attacker, setAttacker] = useState(null);

  // useEffect acts as  "listener" for messages from the Flask/Worker backend
  useEffect(() => {
    socket.on('game_update', (data) => addLog(data.msg));
    socket.on('move_locked', (data) => addLog(`${data.player_id} locked in a move!`));
    
    // Listen for the Rock-Paper-Scissors result
    socket.on('rpc_result', (data) => {
      addLog(`Clash! ${data.p1_choice} vs ${data.p2_choice}. Winner: ${data.winner}`);
      if (data.winner === 'tie') {
         addLog('It is a tie! Go again.');
      } else {
         setAttacker(data.winner);
         setPhase('element'); // Switch the UI to the Elemental phase
         addLog(`${data.winner} gets to attack! Choose your element.`);
      }
    });

    // Listen for the Elemental damage result
    socket.on('element_result', (data) => {
      addLog(`Element Clash! P1: ${data.p1_element} vs P2: ${data.p2_element}. Damage: ${data.damage}`);
      setPhase('rpc'); // Reset back to Rock-Paper-Scissors for the next round
      setAttacker(null);
      addLog('-----------------------------------');
      addLog('Next Round: Rock-Paper-Scissors!');
    });

    return () => {
      socket.off('game_update');
      socket.off('move_locked');
      socket.off('rpc_result');
      socket.off('element_result');
    };
  }, []);

  const addLog = (msg) => setLog(prev => [...prev, msg]);

  const joinGame = () => {
    socket.emit('join_game', { room, player_id: playerId });
    setInGame(true);
  };

  const makeMove = (moveType, choice) => {
    socket.emit('make_move', { room, player_id: playerId, move_type: moveType, choice });
  };

  // --- UI: LOGIN SCREEN ---
  if (!inGame) {
    return (
      <div className="container">
        <h1 className="title">Fate Elemental Clash</h1>
        <div className="login-box">
          <input value={playerId} onChange={e => setPlayerId(e.target.value)} placeholder="Player ID (player1 or player2)" />
          <input value={room} onChange={e => setRoom(e.target.value)} placeholder="Room Name" />
          <button className="primary-btn" onClick={joinGame}>Enter Battle</button>
        </div>
      </div>
    );
  }

  // --- UI: ACTIVE GAME SCREEN ---
  return (
    <div className="container">
      <h2 className="header">Room: {room} | You: {playerId}</h2>
      
      <div className="game-board">
        {/* Only show these buttons during the RPC phase */}
        {phase === 'rpc' && (
          <div className="controls">
            <h3>Phase: Rock Paper Scissors</h3>
            <div className="button-group">
              <button onClick={() => makeMove('rpc', 'rock')}>Rock</button>
              <button onClick={() => makeMove('rpc', 'paper')}>Paper</button>
              <button onClick={() => makeMove('rpc', 'scissors')}>Scissors</button>
            </div>
          </div>
        )}

        {/* Only show these buttons during the Element phase */}
        {phase === 'element' && (
          <div className="controls">
            <h3>Phase: Elemental Clash</h3>
            <p className="turn-indicator">{attacker === playerId ? "⚔️ You are attacking!" : "🛡️ You are defending!"}</p>
            <div className="button-group">
              <button className="fire" onClick={() => makeMove('element', 'fire')}>Fire (Saber)</button>
              <button className="water" onClick={() => makeMove('element', 'water')}>Water (Archer)</button>
              <button className="leaf" onClick={() => makeMove('element', 'leaf')}>Leaf (Lancer)</button>
            </div>
          </div>
        )}
      </div>

      <div className="log-box">
        {log.map((msg, i) => <p key={i}>{msg}</p>)}
      </div>
    </div>
  );
}

export default App;