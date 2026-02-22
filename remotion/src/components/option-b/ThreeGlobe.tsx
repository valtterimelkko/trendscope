import React, { useMemo } from 'react';
import { useCurrentFrame } from 'remotion';
import { ThreeCanvas } from '@remotion/three';
import * as THREE from 'three';

const COLORS = { accentCyan: '#00D9FF', accentBlue: '#3B82F6', bgCard: '#0F172A' };

const WireframeGlobe: React.FC = () => {
  const frame = useCurrentFrame();
  const rotationY = frame * 0.015;
  return (
    <>
      <mesh rotation={[0, rotationY, 0.2]}>
        <sphereGeometry args={[3, 48, 48]} />
        <meshBasicMaterial color={COLORS.accentCyan} wireframe transparent opacity={0.5} />
      </mesh>
      <mesh rotation={[0, rotationY, 0.2]}>
        <sphereGeometry args={[2.95, 32, 32]} />
        <meshBasicMaterial color={COLORS.bgCard} transparent opacity={0.95} />
      </mesh>
      <mesh rotation={[0, -rotationY * 0.5, -0.1]}>
        <sphereGeometry args={[3.2, 32, 32]} />
        <meshBasicMaterial color={COLORS.accentBlue} wireframe transparent opacity={0.25} />
      </mesh>
    </>
  );
};

const DataPoints: React.FC = () => {
  const frame = useCurrentFrame();
  const rotationY = frame * 0.015;
  const points = useMemo(() => {
    const cities = [{ lat: 40.7128, lon: -74.006 }, { lat: 51.5074, lon: -0.1278 }, { lat: 35.6762, lon: 139.6503 }, { lat: -33.8688, lon: 151.2093 }, { lat: 31.2304, lon: 121.4737 }, { lat: 1.3521, lon: 103.8198 }, { lat: -23.5505, lon: -46.6333 }, { lat: 52.52, lon: 13.405 }, { lat: 25.2048, lon: 55.2708 }, { lat: 19.076, lon: 72.8777 }, { lat: 37.7749, lon: -122.4194 }, { lat: 55.7558, lon: 37.6173 }];
    return cities.map((city) => {
      const phi = (90 - city.lat) * (Math.PI / 180);
      const theta = (city.lon + 180) * (Math.PI / 180);
      const radius = 3.05;
      return { x: -(radius * Math.sin(phi) * Math.cos(theta)), y: radius * Math.cos(phi), z: radius * Math.sin(phi) * Math.sin(theta) };
    });
  }, []);

  return (
    <group rotation={[0, rotationY, 0.2]}>
      {points.map((point, index) => (
        <mesh key={index} position={[point.x, point.y, point.z]}>
          <sphereGeometry args={[0.06, 8, 8]} />
          <meshBasicMaterial color={index % 2 === 0 ? COLORS.accentCyan : COLORS.accentBlue} transparent opacity={0.9} />
        </mesh>
      ))}
    </group>
  );
};

const PulseRing: React.FC = () => {
  const frame = useCurrentFrame();
  const pulseScale = 1 + (frame % 60) / 60 * 0.3;
  const pulseOpacity = 1 - (frame % 60) / 60;
  return (
    <mesh rotation={[Math.PI / 2, 0, 0]} scale={[pulseScale, pulseScale, 1]}>
      <ringGeometry args={[3.5, 3.6, 64]} />
      <meshBasicMaterial color={COLORS.accentCyan} transparent opacity={pulseOpacity * 0.3} side={THREE.DoubleSide} />
    </mesh>
  );
};

export const ThreeGlobe: React.FC = () => {
  return (
    <ThreeCanvas width={700} height={700} camera={{ position: [0, 0, 8], fov: 45 }}>
      <ambientLight intensity={0.5} />
      <directionalLight position={[5, 5, 5]} intensity={0.8} />
      <pointLight position={[-5, -5, -5]} color={COLORS.accentCyan} intensity={0.5} />
      <WireframeGlobe />
      <DataPoints />
      <PulseRing />
    </ThreeCanvas>
  );
};
