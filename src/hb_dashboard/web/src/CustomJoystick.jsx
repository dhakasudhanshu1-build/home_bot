import { useState, useRef, useEffect } from 'react';

export default function CustomJoystick({ onMove, onStop, size = 150 }) {
  const [position, setPosition] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const containerRef = useRef(null);

  const radius = size / 2;
  const maxDistance = radius * 0.8; // Max distance the stick can travel

  const handlePointerDown = (e) => {
    setIsDragging(true);
    updatePosition(e.clientX, e.clientY);
  };

  const handlePointerMove = (e) => {
    if (!isDragging) return;
    updatePosition(e.clientX, e.clientY);
  };

  const handlePointerUp = () => {
    setIsDragging(false);
    setPosition({ x: 0, y: 0 });
    if (onStop) onStop();
  };

  useEffect(() => {
    const handleGlobalPointerUp = () => {
      if (isDragging) {
        setIsDragging(false);
        setPosition({ x: 0, y: 0 });
        if (onStop) onStop();
      }
    };
    
    if (isDragging) {
      window.addEventListener('pointerup', handleGlobalPointerUp);
    }
    return () => {
      window.removeEventListener('pointerup', handleGlobalPointerUp);
    };
  }, [isDragging, onStop]);

  const updatePosition = (clientX, clientY) => {
    if (!containerRef.current) return;
    
    const rect = containerRef.current.getBoundingClientRect();
    const centerX = rect.left + radius;
    const centerY = rect.top + radius;
    
    let dx = clientX - centerX;
    let dy = clientY - centerY;
    
    const distance = Math.sqrt(dx * dx + dy * dy);
    
    if (distance > maxDistance) {
      dx = (dx / distance) * maxDistance;
      dy = (dy / distance) * maxDistance;
    }
    
    setPosition({ x: dx, y: dy });
    
    if (onMove) {
      // Normalize values between -1 and 1
      onMove({
        x: dx / maxDistance,
        y: -dy / maxDistance // Invert Y so up is positive
      });
    }
  };

  return (
    <div 
      ref={containerRef}
      style={{ width: size, height: size }}
      className="rounded-full bg-gray-900 border border-gray-700 shadow-inner relative touch-none"
      onPointerDown={handlePointerDown}
      onPointerMove={handlePointerMove}
    >
      <div 
        style={{ 
          width: size * 0.4, 
          height: size * 0.4,
          transform: `translate(calc(${position.x}px - 50%), calc(${position.y}px - 50%))`
        }}
        className="absolute top-1/2 left-1/2 rounded-full bg-indigo-500 shadow-lg shadow-indigo-500/50 cursor-grab active:cursor-grabbing transition-transform duration-75 ease-out"
      />
    </div>
  );
}
