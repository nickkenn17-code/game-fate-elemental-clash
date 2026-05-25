import { useState, useEffect, useRef } from 'react';
import { io } from 'socket.io-client';
import './App.css';

// Connect to local Flask backend
const socket = io('http://localhost:5000');

function App() {
  const [room, setRoom] = useState('FateRoom1');
  const [playerId, setPlayerId] = useState('player1');
  const [inGame, setInGame] = useState(false);
  const [phase, setPhase] = useState('rpc');
  const [log, setLog] = useState(['Welcome to the Holy Grail War.']);
  const [attacker, setAttacker] = useState(null);
  const [playerName, setPlayerName] = useState('');

  // Health Bar State
  const [p1Hp, setP1Hp] = useState(100);
  const [p2Hp, setP2Hp] = useState(100);
  
  // Auto-scroll reference for the log box
  const logEndRef = useRef(null);

  useEffect(() => {
    socket.on('game_update', (data) => addLog(data.msg));
    socket.on('move_locked', (data) => addLog(`${data.player_id} locked in a move!`));
    
    // Master Reset Listener
    socket.on('server_reset', (data) => {
      setP1Hp(100);
      setP2Hp(100);
      setPhase('rpc');
      setAttacker(null);
      addLog(data.msg);
    });

    // RPC Listener with Tie Fix
    socket.on('rpc_result', (data) => {
      if (data.winner === 'tie') {
         addLog('Weapons clashed! It is a tie. Go again.');
         setPhase('rpc'); 
      } else {
         setAttacker(data.attacker);
         setPhase('element');
         addLog(`Priority Secured! ${data.attacker} is the Vanguard.`);
      }
    });

    // Elemental Damage Listener
    socket.on('element_result', (data) => {
      addLog(`Clash! Attacker (${data.attacker_choice}) vs Defender (${data.defender_choice})`);
      addLog(`Attacker takes ${data.dmg_to_attacker} DMG | Defender takes ${data.dmg_to_defender} DMG`);
      
      setP1Hp(data.p1_hp);
      setP2Hp(data.p2_hp);

      // Game Over Logic
      if (data.p1_hp <= 0 || data.p2_hp <= 0) {
         const winner = data.p1_hp <= 0 ? 'Player 2' : 'Player 1';
         addLog(`BATTLE CONCLUDED. ${winner} is victorious!`);
         setPhase('gameover');
      } else {
         setPhase('rpc');
         setAttacker(null);
         addLog('-----------------------------------');
         addLog('Next Round: Establish Priority (Rock-Paper-Scissors)');
      }
    });

    return () => {
      socket.off('game_update');
      socket.off('move_locked');
      socket.off('server_reset');
      socket.off('rpc_result');
      socket.off('element_result');
    };
  }, []);

  // Auto-scroll the log box
  useEffect(() => {
    logEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [log]);

  const addLog = (msg) => setLog(prev => [...prev, msg]);

  const joinGame = () => {
    // If left blank, default to the assigned role
    const finalName = playerName.trim() === '' ? playerId : playerName;
    setPlayerName(finalName); 
    
    // Transmit both the role and the display name to the server
    socket.emit('join_game', { room, player_id: playerId, player_name: finalName });
    setInGame(true);
  };

  const makeMove = (moveType, choice) => {
    socket.emit('make_move', { room, player_id: playerId, move_type: moveType, choice });
    setPhase('waiting'); // Prevents double-clicks and ghost logs
  };

  const leaveGame = () => {
    makeMove('reset', 'all');
    setInGame(false);
    setLog(['Welcome to the Holy Grail War.']);
  };

  // --- UI: LOGIN SCREEN ---
  if (!inGame) {
    return (
      <div className="container login-theme">
        <h1 className="title">FATE<br/>ELEMENTAL CLASH</h1>
        <div className="card login-box">
          <input value={room} onChange={e => setRoom(e.target.value)} placeholder="Room Name" />
          <input value={playerName} onChange={e => setPlayerName(e.target.value)} placeholder="Display Name (e.g. Nicholas)" />
          
          <select 
            value={playerId} 
            onChange={e => setPlayerId(e.target.value)} 
            style={{ width: '100%', padding: '14px', marginBottom: '15px', background: 'rgba(0,0,0,0.5)', color: 'var(--gold-royal)', border: '1px solid var(--gold-muted)', borderRadius: '2px', fontFamily: 'Montserrat, sans-serif' }}
          >
            <option value="player1">Role: Player 1</option>
            <option value="player2">Role: Player 2</option>
          </select>

          <button className="primary-btn" onClick={joinGame}>Enter the Grail War</button>
        </div>
      </div>
    );
  }

  // --- UI: ACTIVE GAME SCREEN ---
  return (
    <div className="container game-theme">
      
      <header className="card header-box">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid rgba(212, 175, 55, 0.2)', paddingBottom: '15px', marginBottom: '15px' }}>
          <h2 className="room-title" style={{ borderBottom: 'none', paddingBottom: '0', marginBottom: '0' }}>
            Room: {room} | Agent: {playerName} ({playerId})
          </h2>
          <button 
            className="action-btn fire" 
            style={{ padding: '8px 15px', flex: 'none', color: 'white', backgroundColor: 'rgba(255, 51, 51, 0.1)', border: '1px solid #660000', fontFamily: 'Montserrat, sans-serif' }} 
            onClick={leaveGame}
          >
            Exit Battle
          </button>
        </div>
        
        {/* Visual Health Bars */}
        <div className="hp-dashboard">
          <div className="hp-row">
            <span className="hp-label">Player 1: {Math.max(0, p1Hp)} HP</span>
            <div className="hp-track"><div className="hp-fill p1-fill" style={{ width: `${Math.max(0, p1Hp)}%` }}></div></div>
          </div>
          <div className="hp-row">
            <span className="hp-label">Player 2: {Math.max(0, p2Hp)} HP</span>
            <div className="hp-track"><div className="hp-fill p2-fill" style={{ width: `${Math.max(0, p2Hp)}%` }}></div></div>
          </div>
        </div>
      </header>

      <main className="card game-board">
        {phase === 'rpc' && (
          <div className="controls">
            <h3 className="phase-title">Phase 1: Priority</h3>
            <div className="button-group">
              <button className="action-btn" onClick={() => makeMove('rpc', 'rock')}>Rock</button>
              <button className="action-btn" onClick={() => makeMove('rpc', 'paper')}>Paper</button>
              <button className="action-btn" onClick={() => makeMove('rpc', 'scissors')}>Scissors</button>
            </div>
          </div>
        )}

        {phase === 'waiting' && (
          <div className="controls">
            <h3 className="phase-title" style={{ textAlign: 'center', color: 'var(--text-muted)' }}>
              Transmitting to Server...
            </h3>
          </div>
        )}

        {phase === 'element' && (
          <div className="controls">
            <h3 className="phase-title">Phase 2: Elemental Strike</h3>
            <p className={`turn-indicator ${attacker === playerId ? 'is-attacker' : 'is-defender'}`}>
              {attacker === playerId ? "VANGUARD (Attacking)" : "GUARD (Defending)"}
            </p>
            
            {/* The Character Card Grid */}
            <div className="character-selection">
              <div className="character-card fire-card" onClick={() => makeMove('element', 'fire')}>
                <div className="card-image-wrapper">
                  <img src="/public/oda.png" alt="Archer" />
                </div>
                <div className="card-name">Archer (Fire)</div>
              </div>
              
              <div className="character-card water-card" onClick={() => makeMove('element', 'water')}>
                <div className="card-image-wrapper">
                  <img src="/public/meli.png" alt="Saber" />
                </div>
                <div className="card-name">Saber (Water)</div>
              </div>
              
              <div className="character-card leaf-card" onClick={() => makeMove('element', 'leaf')}>
                <div className="card-image-wrapper">
                  <img src="/public/enkidu.png" alt="Lancer" />
                </div>
                <div className="card-name">Lancer (Earth)</div>
              </div>
            </div>
          </div>
        )}

        {phase === 'gameover' && (
          <div className="controls">
            <h3 className="phase-title" style={{ textAlign: 'center', color: 'var(--element-leaf)' }}>SIMULATION COMPLETE</h3>
            <button className="primary-btn" onClick={() => makeMove('reset', 'all')}>Initialize New Round</button>
          </div>
        )}
      </main>

      <div className="card log-box">
        {log.map((msg, i) => <p key={i} className="log-entry">{msg}</p>)}
        <div ref={logEndRef} />
      </div>

    </div>
  );
}

export default App;