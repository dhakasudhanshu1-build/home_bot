import { useState, useRef, useEffect, useCallback } from 'react';
import { 
  RiDashboardLine, 
  RiGamepadLine, 
  RiMapPinLine, 
  RiCameraLensLine,
  RiRobot2Line
} from 'react-icons/ri';
import CustomJoystick from './CustomJoystick';

function App() {
  const [activeTab, setActiveTab] = useState('control');
  const [isConnected, setIsConnected] = useState(false);
  const [cameraFrame, setCameraFrame] = useState(null);
  const [isCameraConnected, setIsCameraConnected] = useState(false);
  const [isMapConnected, setIsMapConnected] = useState(false);
  const wsRef = useRef(null);
  const cameraWsRef = useRef(null);
  const mapWsRef = useRef(null);
  const reconnectTimer = useRef(null);
  const cameraReconnectTimer = useRef(null);
  const mapReconnectTimer = useRef(null);

  // Map state stored in refs for performance (avoid re-renders on every pose)
  const mapCanvasRef = useRef(null);
  const mapImageRef = useRef(null);
  const mapMetaRef = useRef(null);
  const robotPoseRef = useRef(null);
  const animFrameRef = useRef(null);

  const currentVel = useRef({ linear: 0.0, angular: 0.0 });
  const isDragging = useRef(false);
  const keys = useRef({ w: false, a: false, s: false, d: false, shift: false });
  const wasActive = useRef(false);

  // Native WebSocket connection
  const connectWebSocket = useCallback(() => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) return;

    const ws = new WebSocket('ws://localhost:8000/ws/teleop');

    ws.onopen = () => {
      setIsConnected(true);
      console.log('WebSocket connected');
    };

    ws.onclose = () => {
      setIsConnected(false);
      console.log('WebSocket disconnected, reconnecting...');
      reconnectTimer.current = setTimeout(connectWebSocket, 3000);
    };

    ws.onerror = (err) => {
      console.log('WebSocket error', err);
      ws.close();
    };

    wsRef.current = ws;
  }, []);

  // Keyboard Event Listeners
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (activeTab !== 'control') return;
      const key = e.key.toLowerCase();
      if (key === 'w') keys.current.w = true;
      if (key === 'a') keys.current.a = true;
      if (key === 's') keys.current.s = true;
      if (key === 'd') keys.current.d = true;
      if (key === 'shift') keys.current.shift = true;
      if (key === ' ') {
        // Spacebar for emergency stop
        keys.current.w = false;
        keys.current.a = false;
        keys.current.s = false;
        keys.current.d = false;
        isDragging.current = false;
        sendMessage(JSON.stringify({ linear: 0.0, angular: 0.0 }));
      }
    };

    const handleKeyUp = (e) => {
      const key = e.key.toLowerCase();
      if (key === 'w') keys.current.w = false;
      if (key === 'a') keys.current.a = false;
      if (key === 's') keys.current.s = false;
      if (key === 'd') keys.current.d = false;
      if (key === 'shift') keys.current.shift = false;
    };

    window.addEventListener('keydown', handleKeyDown);
    window.addEventListener('keyup', handleKeyUp);

    return () => {
      window.removeEventListener('keydown', handleKeyDown);
      window.removeEventListener('keyup', handleKeyUp);
    };
  }, [activeTab]); // Depend on activeTab to only listen when in control

  // Camera WebSocket connection
  const connectCameraWs = useCallback(() => {
    if (cameraWsRef.current && cameraWsRef.current.readyState === WebSocket.OPEN) return;
    const ws = new WebSocket('ws://localhost:8000/ws/camera');
    ws.onopen = () => { setIsCameraConnected(true); };
    ws.onmessage = (event) => { setCameraFrame(event.data); };
    ws.onclose = () => {
      setIsCameraConnected(false);
      setCameraFrame(null);
      cameraReconnectTimer.current = setTimeout(connectCameraWs, 3000);
    };
    ws.onerror = () => { ws.close(); };
    cameraWsRef.current = ws;
  }, []);

  // ==================== MAP CANVAS DRAWING ====================
  const drawMap = useCallback(() => {
    const canvas = mapCanvasRef.current;
    const img = mapImageRef.current;
    const meta = mapMetaRef.current;
    if (!canvas || !img || !meta) return;

    const ctx = canvas.getContext('2d');
    const container = canvas.parentElement;
    if (!container) return;

    // Fit canvas to container
    const cw = container.clientWidth;
    const ch = container.clientHeight;
    const scale = Math.min(cw / meta.width, ch / meta.height);
    const dw = Math.floor(meta.width * scale);
    const dh = Math.floor(meta.height * scale);
    canvas.width = dw;
    canvas.height = dh;

    // Draw map image
    ctx.drawImage(img, 0, 0, dw, dh);

    // Draw robot
    const pose = robotPoseRef.current;
    if (pose) {
      const px = ((pose.x - meta.origin_x) / meta.resolution) * scale;
      const py = (meta.height - (pose.y - meta.origin_y) / meta.resolution) * scale;
      const r = Math.max(6, 10 * scale / 2);

      // Robot body
      ctx.beginPath();
      ctx.arc(px, py, r, 0, 2 * Math.PI);
      ctx.fillStyle = 'rgba(99, 102, 241, 0.9)';
      ctx.fill();
      ctx.strokeStyle = '#fff';
      ctx.lineWidth = 2;
      ctx.stroke();

      // Direction arrow
      const arrowLen = r * 2;
      const ax = px + arrowLen * Math.cos(-pose.yaw);
      const ay = py + arrowLen * Math.sin(-pose.yaw);
      ctx.beginPath();
      ctx.moveTo(px, py);
      ctx.lineTo(ax, ay);
      ctx.strokeStyle = '#22d3ee';
      ctx.lineWidth = 3;
      ctx.stroke();

      // Arrowhead
      const headLen = 6;
      const angle = Math.atan2(ay - py, ax - px);
      ctx.beginPath();
      ctx.moveTo(ax, ay);
      ctx.lineTo(ax - headLen * Math.cos(angle - 0.5), ay - headLen * Math.sin(angle - 0.5));
      ctx.moveTo(ax, ay);
      ctx.lineTo(ax - headLen * Math.cos(angle + 0.5), ay - headLen * Math.sin(angle + 0.5));
      ctx.stroke();
    }
  }, []);

  // Animation loop for map
  useEffect(() => {
    if (activeTab !== 'map') return;
    let running = true;
    const loop = () => {
      if (!running) return;
      drawMap();
      animFrameRef.current = requestAnimationFrame(loop);
    };
    loop();
    return () => { running = false; cancelAnimationFrame(animFrameRef.current); };
  }, [activeTab, drawMap]);

  // Map WebSocket connection
  const connectMapWs = useCallback(() => {
    if (mapWsRef.current && mapWsRef.current.readyState === WebSocket.OPEN) return;
    const ws = new WebSocket('ws://localhost:8000/ws/map');
    ws.onopen = () => { setIsMapConnected(true); };
    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        if (msg.type === 'map') {
          mapMetaRef.current = { width: msg.width, height: msg.height, resolution: msg.resolution, origin_x: msg.origin_x, origin_y: msg.origin_y };
          const img = new window.Image();
          img.onload = () => { mapImageRef.current = img; };
          img.src = `data:image/png;base64,${msg.data}`;
        } else if (msg.type === 'pose') {
          robotPoseRef.current = { x: msg.x, y: msg.y, yaw: msg.yaw };
        }
      } catch (e) { console.error('Map WS parse error', e); }
    };
    ws.onclose = () => {
      setIsMapConnected(false);
      mapReconnectTimer.current = setTimeout(connectMapWs, 3000);
    };
    ws.onerror = () => { ws.close(); };
    mapWsRef.current = ws;
  }, []);

  // Connect map WS when map tab is active
  useEffect(() => {
    if (activeTab === 'map') {
      connectMapWs();
    } else {
      if (mapWsRef.current) { mapWsRef.current.close(); mapWsRef.current = null; }
      if (mapReconnectTimer.current) clearTimeout(mapReconnectTimer.current);
    }
    return () => { if (mapReconnectTimer.current) clearTimeout(mapReconnectTimer.current); };
  }, [activeTab, connectMapWs]);

  // Connect camera WS when camera tab is active
  useEffect(() => {
    if (activeTab === 'camera') {
      connectCameraWs();
    } else {
      if (cameraWsRef.current) { cameraWsRef.current.close(); cameraWsRef.current = null; }
      if (cameraReconnectTimer.current) clearTimeout(cameraReconnectTimer.current);
    }
    return () => {
      if (cameraReconnectTimer.current) clearTimeout(cameraReconnectTimer.current);
    };
  }, [activeTab, connectCameraWs]);

  useEffect(() => {
    connectWebSocket();
    
    // Continuous publisher at 10Hz to prevent ROS2 timeouts
    const publishInterval = setInterval(() => {
      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        
        let linear = 0.0;
        let angular = 0.0;
        let isKeyboardActive = false;

        if (activeTab === 'control') {
          const max_lin = keys.current.shift ? 1.0 : 0.5;
          const max_ang = keys.current.shift ? 2.0 : 1.0;

          if (keys.current.w) linear += max_lin;
          if (keys.current.s) linear -= max_lin;
          if (keys.current.a) angular += max_ang;
          if (keys.current.d) angular -= max_ang;

          if (keys.current.w || keys.current.s || keys.current.a || keys.current.d) {
            isKeyboardActive = true;
          }
        }

        const isActive = isKeyboardActive || isDragging.current;

        if (isActive) {
          if (isKeyboardActive) {
            wsRef.current.send(JSON.stringify({ linear, angular }));
          } else {
            wsRef.current.send(JSON.stringify(currentVel.current));
          }
          wasActive.current = true;
        } else if (wasActive.current) {
          wsRef.current.send(JSON.stringify({ linear: 0.0, angular: 0.0 }));
          wasActive.current = false;
        }
      }
    }, 100);

    return () => {
      if (reconnectTimer.current) clearTimeout(reconnectTimer.current);
      if (wsRef.current) wsRef.current.close();
      clearInterval(publishInterval);
    };
  }, [connectWebSocket, activeTab]);

  const sendMessage = (msg) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(msg);
    }
  };

  // Joystick handling
  const handleJoystickMove = (event) => {
    const max_linear_vel = 0.5; // m/s
    const max_angular_vel = 1.0; // rad/s
    
    currentVel.current = {
      linear: event.y * max_linear_vel,
      angular: -event.x * max_angular_vel
    };
    isDragging.current = true;
    
    // Also send immediately for fast response
    sendMessage(JSON.stringify(currentVel.current));
  };

  const handleJoystickStop = () => {
    isDragging.current = false;
    currentVel.current = { linear: 0.0, angular: 0.0 };
    sendMessage(JSON.stringify(currentVel.current));
  };

  const navItems = [
    { id: 'dashboard', icon: <RiDashboardLine size={24} />, label: 'Overview' },
    { id: 'control', icon: <RiGamepadLine size={24} />, label: 'Manual Control' },
    { id: 'map', icon: <RiMapPinLine size={24} />, label: 'Live Map' },
    { id: 'camera', icon: <RiCameraLensLine size={24} />, label: 'Camera' },
    { id: 'ai', icon: <RiRobot2Line size={24} />, label: 'AI Assistant' },
  ];

  return (
    <div className="flex h-screen bg-gray-950 text-gray-100 overflow-hidden font-sans">
      
      {/* Sidebar */}
      <aside className="w-20 lg:w-64 bg-gray-900 border-r border-gray-800 flex flex-col justify-between transition-all duration-300">
        <div>
          <div className="h-20 flex items-center justify-center lg:justify-start lg:px-8 border-b border-gray-800">
            <div className="w-10 h-10 bg-indigo-600 rounded-xl flex items-center justify-center shadow-lg shadow-indigo-500/30">
              <RiRobot2Line size={24} className="text-white" />
            </div>
            <span className="hidden lg:block ml-4 text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-indigo-400 to-cyan-400">
              HomeBot
            </span>
          </div>
          <nav className="p-4 space-y-2 mt-4">
            {navItems.map((item) => (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                className={`w-full flex items-center p-3 rounded-xl transition-all duration-200 group relative ${
                  activeTab === item.id 
                    ? 'bg-indigo-600/10 text-indigo-400' 
                    : 'text-gray-400 hover:bg-gray-800 hover:text-gray-100'
                }`}
              >
                <div className={`transition-transform duration-200 ${activeTab === item.id ? 'scale-110' : 'group-hover:scale-110'}`}>
                  {item.icon}
                </div>
                <span className="hidden lg:block ml-4 font-medium">{item.label}</span>
                
                {activeTab === item.id && (
                  <div className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-8 bg-indigo-500 rounded-r-full" />
                )}
              </button>
            ))}
          </nav>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="flex-1 flex flex-col relative overflow-hidden">
        
        {/* Header */}
        <header className="h-20 bg-gray-900/50 backdrop-blur-md border-b border-gray-800 flex items-center justify-between px-8 sticky top-0 z-10">
          <h1 className="text-2xl font-bold text-gray-100 capitalize">
            {activeTab.replace('-', ' ')}
          </h1>
          <div className="flex items-center space-x-6">
            <div className="flex items-center bg-gray-800/50 px-4 py-2 rounded-full border border-gray-700/50">
              <div className="relative flex h-3 w-3 mr-3">
                {isConnected && (
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                )}
                <span className={`relative inline-flex rounded-full h-3 w-3 ${isConnected ? 'bg-emerald-500' : 'bg-rose-500'}`}></span>
              </div>
              <span className="text-sm font-medium text-gray-300">
                {isConnected ? 'Backend Connected' : 'Backend Disconnected'}
              </span>
            </div>
          </div>
        </header>

        {/* Dynamic Content Rendering */}
        <div className="flex-1 overflow-auto p-8">
          
          {activeTab === 'control' ? (
            <div className="max-w-7xl mx-auto h-full flex flex-col items-center justify-center border border-gray-800 rounded-3xl bg-gray-900/40 p-8 shadow-2xl relative overflow-hidden">
              {/* Decorative elements */}
              <div className="absolute top-0 right-0 w-64 h-64 bg-indigo-500/10 rounded-full blur-3xl -translate-y-1/2 translate-x-1/2"></div>
              <div className="absolute bottom-0 left-0 w-64 h-64 bg-cyan-500/10 rounded-full blur-3xl translate-y-1/2 -translate-x-1/2"></div>
              
              <h2 className="text-2xl font-semibold mb-2">Teleoperation Mode</h2>
              <p className="text-gray-400 mb-8">Use the joystick or keyboard to manually navigate the robot.</p>
              
              <div className="flex flex-col md:flex-row items-center justify-center gap-12 z-10">
                {/* Joystick Control */}
                <div className="bg-gray-800/80 p-8 rounded-[3rem] shadow-inner shadow-gray-950/50 backdrop-blur-md border border-gray-700">
                  <CustomJoystick 
                    size={150} 
                    onMove={handleJoystickMove} 
                    onStop={handleJoystickStop}
                  />
                </div>

                {/* Keyboard Controls Guide */}
                <div className="bg-gray-800/50 p-6 rounded-3xl border border-gray-700 flex flex-col items-center">
                  <h3 className="text-sm font-semibold text-gray-400 mb-4 uppercase tracking-widest">Keyboard Controls</h3>
                  
                  <div className="flex flex-col items-center space-y-2">
                    <div className="w-12 h-12 bg-gray-700 border-b-4 border-gray-900 rounded-lg flex items-center justify-center font-bold text-gray-300 shadow-sm">W</div>
                    <div className="flex space-x-2">
                      <div className="w-12 h-12 bg-gray-700 border-b-4 border-gray-900 rounded-lg flex items-center justify-center font-bold text-gray-300 shadow-sm">A</div>
                      <div className="w-12 h-12 bg-gray-700 border-b-4 border-gray-900 rounded-lg flex items-center justify-center font-bold text-gray-300 shadow-sm">S</div>
                      <div className="w-12 h-12 bg-gray-700 border-b-4 border-gray-900 rounded-lg flex items-center justify-center font-bold text-gray-300 shadow-sm">D</div>
                    </div>
                  </div>

                  <div className="mt-6 w-full space-y-3">
                    <div className="flex items-center justify-between text-xs text-gray-400 bg-gray-900/50 px-3 py-2 rounded-lg">
                      <span>Turbo Mode</span>
                      <kbd className="px-2 py-1 bg-gray-700 rounded font-mono text-gray-300">SHIFT</kbd>
                    </div>
                    <div className="flex items-center justify-between text-xs text-rose-400 bg-rose-500/10 px-3 py-2 rounded-lg border border-rose-500/20">
                      <span>Emergency Stop</span>
                      <kbd className="px-2 py-1 bg-rose-500/20 rounded font-mono text-rose-300">SPACE</kbd>
                    </div>
                  </div>
                </div>
              </div>

              <div className="mt-12 flex space-x-4 z-10">
                <div className="px-6 py-3 bg-gray-800/50 rounded-xl border border-gray-700 flex flex-col items-center min-w-[120px]">
                  <span className="text-xs text-gray-500 font-semibold tracking-wider uppercase">Status</span>
                  <span className={`font-mono font-bold text-lg ${isConnected ? 'text-emerald-400' : 'text-rose-400'}`}>
                    {isConnected ? 'ACTIVE' : 'OFFLINE'}
                  </span>
                </div>
                <div className="px-6 py-3 bg-gray-800/50 rounded-xl border border-gray-700 flex flex-col items-center min-w-[120px]">
                  <span className="text-xs text-gray-500 font-semibold tracking-wider uppercase">Max Speed</span>
                  <span className="font-mono font-bold text-lg text-indigo-300">0.5 m/s</span>
                </div>
              </div>
            </div>
          ) : activeTab === 'map' ? (
            <div className="max-w-7xl mx-auto h-full flex flex-col border border-gray-800 rounded-3xl bg-gray-900/40 shadow-2xl relative overflow-hidden">
              <div className="flex items-center justify-between px-6 py-4 border-b border-gray-800">
                <div className="flex items-center space-x-3">
                  <RiMapPinLine size={20} className="text-indigo-400" />
                  <h2 className="text-lg font-semibold">Live Map</h2>
                </div>
                <div className="flex items-center space-x-2">
                  <div className={`h-2.5 w-2.5 rounded-full ${isMapConnected ? 'bg-emerald-500 animate-pulse' : 'bg-rose-500'}`}></div>
                  <span className="text-xs text-gray-400 font-medium">{isMapConnected ? 'Connected' : 'Disconnected'}</span>
                </div>
              </div>
              <div className="flex-1 flex items-center justify-center p-4 bg-black/20 relative">
                <canvas ref={mapCanvasRef} className="rounded-xl border border-gray-700/30" />
                {!mapImageRef.current && (
                  <div className="absolute inset-0 flex items-center justify-center">
                    <div className="text-center space-y-4">
                      <div className="w-16 h-16 mx-auto border-4 border-gray-700 border-t-indigo-500 rounded-full animate-spin"></div>
                      <p className="text-gray-500">Waiting for map data...</p>
                      <p className="text-xs text-gray-600">Launch SLAM or map_server to publish /map</p>
                    </div>
                  </div>
                )}
              </div>
            </div>
          ) : activeTab === 'camera' ? (
            <div className="max-w-7xl mx-auto h-full flex flex-col border border-gray-800 rounded-3xl bg-gray-900/40 shadow-2xl relative overflow-hidden">
              <div className="flex items-center justify-between px-6 py-4 border-b border-gray-800">
                <div className="flex items-center space-x-3">
                  <RiCameraLensLine size={20} className="text-indigo-400" />
                  <h2 className="text-lg font-semibold">Live Camera Feed</h2>
                </div>
                <div className="flex items-center space-x-2">
                  <div className={`h-2.5 w-2.5 rounded-full ${isCameraConnected ? 'bg-emerald-500 animate-pulse' : 'bg-rose-500'}`}></div>
                  <span className="text-xs text-gray-400 font-medium">{isCameraConnected ? 'Streaming' : 'Disconnected'}</span>
                </div>
              </div>
              <div className="flex-1 flex items-center justify-center p-4 bg-black/30">
                {cameraFrame ? (
                  <img src={`data:image/jpeg;base64,${cameraFrame}`} alt="Robot Camera" className="max-w-full max-h-full rounded-2xl shadow-2xl border border-gray-700/50 object-contain" />
                ) : (
                  <div className="text-center space-y-4">
                    <div className="w-16 h-16 mx-auto border-4 border-gray-700 border-t-indigo-500 rounded-full animate-spin"></div>
                    <p className="text-gray-500">Waiting for camera stream...</p>
                  </div>
                )}
              </div>
            </div>
          ) : (
            <div className="max-w-7xl mx-auto h-full flex flex-col items-center justify-center border-2 border-dashed border-gray-800 rounded-3xl bg-gray-900/20">
              <div className="text-center space-y-4">
                <div className="inline-block p-4 bg-gray-800 rounded-2xl shadow-xl">
                  {navItems.find(i => i.id === activeTab)?.icon}
                </div>
                <h2 className="text-xl font-medium text-gray-300">
                  {navItems.find(i => i.id === activeTab)?.label} Area
                </h2>
                <p className="text-gray-500 max-w-sm mx-auto">
                  Coming soon!
                </p>
              </div>
            </div>
          )}

        </div>

      </main>
    </div>
  );
}

export default App;
