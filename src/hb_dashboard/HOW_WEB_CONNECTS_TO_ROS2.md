# 🔗 How the Web Dashboard Connects to ROS2

## The Problem: Why Can't a Browser Talk to ROS2 Directly?

ROS2 uses a protocol called **DDS** (Data Distribution Service) to send messages
between nodes. Your browser (Chrome/Firefox) only understands **HTTP** and **WebSockets**.

They speak completely different languages:
```
Browser (JavaScript)  ←→  ??? ←→  ROS2 (DDS/Python/C++)
```

So we need a **translator** in the middle. That translator is our **FastAPI Backend Server**.

---

## The Architecture: 3 Layers

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│   LAYER 1: BROWSER (React Frontend)                            │
│   ─────────────────────────────────                             │
│   • Runs at http://localhost:5173                               │
│   • Shows the joystick, map, camera, etc.                      │
│   • Written in JavaScript/React                                │
│   • Has NO access to ROS2 at all                               │
│   • Can only talk via HTTP or WebSocket                        │
│                                                                 │
│   Terminal to start:                                            │
│   $ cd ~/hb/src/hb_dashboard/web && npm run dev                │
│                                                                 │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         │  WebSocket Connection
                         │  ws://localhost:8000/ws/teleop
                         │
                         │  Browser sends: {"linear": 0.5, "angular": 0.0}
                         │  (This is just a JSON text message)
                         │
┌────────────────────────▼────────────────────────────────────────┐
│                                                                 │
│   LAYER 2: FASTAPI BACKEND (The Bridge / Translator)            │
│   ──────────────────────────────────────────────────            │
│   • Runs at http://localhost:8000                               │
│   • Written in Python                                           │
│   • This is BOTH a web server AND a ROS2 node                   │
│   • It receives the JSON from the browser                       │
│   • It converts it into a ROS2 Twist message                    │              
│   • It publishes the Twist to /cmd_vel topic                    │
│                                                                 │
│   Files:                                                        │
│   • server.py  → FastAPI web server (receives WebSocket data)   │
│   • ros_node.py → ROS2 node (publishes /cmd_vel)                │
│                                                                 │
│   Terminal to start:                                            │
│   $ cd ~/hb && colcon build --packages-select hb_dashboard      │
│   $ source install/setup.bash                                   │
│   $ ros2 run hb_dashboard server                                │
│                                                                 │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         │  ROS2 DDS Communication
                         │  Topic: /cmd_vel
                         │  Message: geometry_msgs/Twist
                         │
┌────────────────────────▼────────────────────────────────────────┐
│                                                                 │
│   LAYER 3: GAZEBO + ROBOT (ROS2 Simulation)                    │
│   ──────────────────────────────────────────                    │
│   • The robot subscribes to /cmd_vel                            │
│   • When it receives a Twist, the wheels move                  │
│   • This is the same as using teleop_keyboard or joystick      │
│                                                                 │
│   Terminal to start:                                            │
│   $ ros2 launch home_bringup <your_launch_file>.py             │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## What You Need Running: 3 Terminals

You need **THREE separate terminals** running at the same time:

### Terminal 1: The Robot Simulation (Gazebo)
```bash
cd ~/hb
source install/setup.bash
ros2 launch home_bringup <your_launch_file>.py
```
This starts Gazebo with your robot. The robot listens on `/cmd_vel`.
**You are probably already doing this.**

### Terminal 2: The Backend Bridge (FastAPI + ROS2 Node)
```bash
cd ~/hb
colcon build --packages-select hb_dashboard
source install/setup.bash
ros2 run hb_dashboard server
```
This starts the translator. It:
- Opens a WebSocket server on port 8000
- Creates a ROS2 node that can publish to `/cmd_vel`
- Waits for the browser to connect and send joystick data

**Without this running, the browser has NO way to reach ROS2.**
**This is probably what you are missing!**

### Terminal 3: The Frontend Web App (React/Vite)
```bash
cd ~/hb/src/hb_dashboard/web
npm run dev
```
This starts the web development server on port 5173.
Open http://localhost:5173 in your browser.

---

## The Data Flow When You Drag the Joystick

Here is exactly what happens when you drag the joystick to the right:

```
Step 1: You drag the joystick in the browser
        ↓
Step 2: JavaScript calculates: x=0.8, y=0.0
        ↓
Step 3: JavaScript converts to velocities:
        linear = 0.0 * 0.5 = 0.0 m/s
        angular = -0.8 * 1.0 = -0.8 rad/s (turn right)
        ↓
Step 4: JavaScript sends via WebSocket:
        ws.send('{"linear": 0.0, "angular": -0.8}')
        ↓
Step 5: FastAPI receives the JSON string on port 8000
        ↓
Step 6: Python parses the JSON:
        cmd = json.loads(data)  →  {"linear": 0.0, "angular": -0.8}
        ↓
Step 7: ROS2 node creates a Twist message:
        msg = Twist()
        msg.linear.x = 0.0
        msg.angular.z = -0.8
        ↓
Step 8: ROS2 node publishes to /cmd_vel topic:
        self.cmd_vel_pub.publish(msg)
        ↓
Step 9: Gazebo robot receives /cmd_vel → wheels turn right
```

---

## How to Verify Each Layer is Working

### Check Terminal 2 (Backend):
When you start the backend, you should see:
```
INFO:     Started server process [XXXXX]
INFO:     Waiting for application startup.
[INFO] [hb_dashboard_node]: Dashboard Node initialized
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

### Check Browser Dashboard:
- Top-right should say **"Backend Connected"** (green dot)
- Status card should say **"ACTIVE"** (green)

### Check ROS2 Topics:
In a fourth terminal, you can verify messages are being published:
```bash
source ~/hb/install/setup.bash
ros2 topic echo /cmd_vel
```
When you drag the joystick, you should see Twist messages appearing here.

---

## ROS2 Analogy

Think of it like this:

| Web Dashboard        | ROS2 Equivalent                    |
|---------------------|------------------------------------|
| Browser Joystick    | Physical Joystick / teleop_keyboard|
| WebSocket message   | ROS2 message on a topic            |
| FastAPI Server      | A ROS2 Node (like joy_node)        |
| /cmd_vel publish    | Same as joy_teleop publishing      |

The web dashboard is essentially a **replacement for teleop_keyboard**,
but instead of pressing keys in a terminal, you drag a joystick in a browser.

---

## Common Issues

| Problem                        | Cause                              | Fix                                    |
|-------------------------------|------------------------------------|-----------------------------------------|
| "Backend Disconnected"        | FastAPI server not running          | Start Terminal 2                        |
| "Address already in use"      | Server already running elsewhere    | Kill the old process: `sudo fuser -k 8000/tcp` |
| Joystick moves but robot doesn't | /cmd_vel topic name mismatch    | Check: `ros2 topic list \| grep cmd_vel` |
| Can't open localhost:5173     | Vite dev server not running         | Start Terminal 3                        |
