# HomeBot Web Development Guide 🚀

Welcome to the frontend side of HomeBot! Since you are already familiar with ROS2 and backend robotics, this guide is specifically designed to bridge your knowledge into the modern web development ecosystem.

Here, we will explain the tools we are using, why we chose them, and how they fit together to create a premium robot dashboard.

---

## 1. The Core Stack: What Are We Using?

We are building a **Single Page Application (SPA)**. Instead of reloading the page every time you click a button (like old websites), the entire dashboard loads once, and we use JavaScript to dynamically update the screen in real-time. This is essential for robotics since we need continuous, uninterrupted data streams (like video and joystick control).

### 🔹 Node.js and npm
**What it is:** `Node.js` is a runtime that allows JavaScript to run outside the browser (on your computer). `npm` (Node Package Manager) is like `apt` or `pip`, but for JavaScript.
**Why we use it:** To install frontend libraries (like React and Tailwind) and to run our local development server.
**ROS Analogy:** `Node.js` is like your Python/C++ environment, and `npm` is like `colcon` + `rosdep` combined.

### 🔹 Vite (Pronounced "Veet")
**What it is:** A blazing fast frontend build tool.
**Why we use it:** In the past, tools like Webpack were used to bundle JavaScript, but they were slow. Vite serves your code instantly during development and bundles it tightly for production.
**ROS Analogy:** Vite is the `colcon build` of the web world, but it recompiles your code in milliseconds while the app is running (Hot Module Replacement).

### 🔹 React
**What it is:** A JavaScript library developed by Facebook for building user interfaces.
**Why we use it:** React allows us to build UI as **Components**. For example, the Sidebar, the Header, and the Joystick are all separate, reusable components. React also handles "State" (data that changes, like robot velocity or battery level) and automatically updates the UI when the state changes.
**ROS Analogy:** React components are like ROS Nodes. They each have a specific job, they hold their own internal state, and they can pass messages (called "props") to each other.

### 🔹 Tailwind CSS
**What it is:** A utility-first CSS framework.
**Why we use it:** Instead of writing hundreds of lines of separate CSS files, Tailwind lets us style elements directly in our HTML/JSX using small, descriptive classes (e.g., `bg-gray-900` for a dark background, `flex` for layout, `rounded-xl` for curved corners). It makes building premium, modern interfaces incredibly fast.
**ROS Analogy:** Instead of writing custom matrix math for every transformation, you use `tf2`. Tailwind provides pre-calculated, beautiful design utilities so you don't have to invent them from scratch.

---

## 2. How the Dashboard Communicates with ROS2

Web browsers cannot communicate directly with ROS2 topics (DDS). We need a bridge.

1. **FastAPI (Python Backend):** We run a FastAPI server alongside a standard ROS2 `rclpy.Node`.
2. **WebSockets:** FastAPI opens a WebSocket connection. WebSockets provide a two-way, persistent connection between the React frontend and the FastAPI backend.
3. **The Data Flow:**
   - **Sending Commands:** You drag the virtual joystick in React -> React sends a JSON message over the WebSocket -> FastAPI receives the JSON -> The `rclpy.Node` converts it to a `geometry_msgs/Twist` and publishes it to `/cmd_vel`.
   - **Receiving Data:** The `rclpy.Node` subscribes to the `/map` topic -> When a new map arrives, it sends the grid data over the WebSocket -> React receives the data and draws it on an HTML5 `<canvas>`.

---

## 3. Understanding the Frontend Directory Structure

If you look inside `hb_dashboard/web/`, you'll see this structure:

```text
web/
├── node_modules/       # Installed JS libraries (like /opt/ros/humble)
├── public/             # Static assets (images, favicons)
├── src/                # The actual source code!
│   ├── App.jsx         # The main entry component (Sidebar + Header + Content)
│   ├── index.css       # Global styles and Tailwind imports
│   └── main.jsx        # The file that mounts React into the browser
├── index.html          # The single HTML file that loads the app
├── package.json        # Manifest file listing dependencies (like package.xml)
├── tailwind.config.js  # Configuration for Tailwind themes and colors
└── vite.config.js      # Configuration for the Vite bundler
```

---

## 4. Crash Course: React Syntax (JSX)

In React, we write **JSX**, which looks like HTML but allows us to run JavaScript directly inside it.

```jsx
import { useState } from 'react';

function RobotStatus() {
  // 'state' is a variable that React watches.
  // When 'isConnected' changes, React automatically updates the UI!
  const [isConnected, setIsConnected] = useState(false);

  return (
    // We use Tailwind classes for styling
    <div className="p-4 bg-gray-800 rounded-lg">
      
      {/* We can use JavaScript logic inside curly braces {} */}
      <h2>Status: {isConnected ? "Online" : "Offline"}</h2>
      
      {/* We can attach event listeners like onClick */}
      <button 
        className="bg-blue-500 text-white px-4 py-2"
        onClick={() => setIsConnected(true)}
      >
        Connect Robot
      </button>
    </div>
  );
}
```

---

## 5. How to Run and Develop

Whenever you want to work on the frontend:

1. **Start the Frontend Development Server:**
   ```bash
   cd ~/hb/src/hb_dashboard/web
   npm run dev
   ```
   *This gives you a URL (usually `localhost:5173`). Whenever you save a `.jsx` file, the browser will update instantly without you having to refresh the page!*

2. **Start the Backend ROS2 Server:**
   ```bash
   cd ~/hb
   colcon build --packages-select hb_dashboard
   source install/setup.bash
   ros2 run hb_dashboard server
   ```

You are now ready to build out the features of the dashboard!
