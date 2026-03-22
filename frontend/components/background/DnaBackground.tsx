'use client';

import React, { useRef } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import * as THREE from 'three';

function HelixMesh() {
  const groupRef = useRef<THREE.Group>(null);

  useFrame((_, delta) => {
    if (groupRef.current) {
      groupRef.current.rotation.y += delta * 0.08;
    }
  });

  const TURNS = 4;
  const POINTS_PER_TURN = 24;
  const TOTAL = TURNS * POINTS_PER_TURN;
  const RADIUS = 1.4;
  const PITCH = 0.55;
  const TUBE_RADIUS = 0.025;
  const ROD_RADIUS = 0.012;

  // Build two helical strand paths
  const strand1Points: THREE.Vector3[] = [];
  const strand2Points: THREE.Vector3[] = [];
  for (let i = 0; i <= TOTAL; i++) {
    const t = (i / TOTAL) * Math.PI * 2 * TURNS;
    const y = (i / TOTAL) * PITCH * TURNS * 2 - PITCH * TURNS;
    strand1Points.push(new THREE.Vector3(Math.cos(t) * RADIUS, y, Math.sin(t) * RADIUS));
    strand2Points.push(
      new THREE.Vector3(Math.cos(t + Math.PI) * RADIUS, y, Math.sin(t + Math.PI) * RADIUS),
    );
  }

  const curve1 = new THREE.CatmullRomCurve3(strand1Points);
  const curve2 = new THREE.CatmullRomCurve3(strand2Points);
  const geo1 = new THREE.TubeGeometry(curve1, TOTAL * 3, TUBE_RADIUS, 6, false);
  const geo2 = new THREE.TubeGeometry(curve2, TOTAL * 3, TUBE_RADIUS, 6, false);
  const strandMat = new THREE.MeshBasicMaterial({
    color: '#22d3ee',
    transparent: true,
    opacity: 0.05,
  });

  // Base-pair rods every N steps
  const rods: React.ReactElement[] = [];
  const rodMat = new THREE.MeshBasicMaterial({
    color: '#22d3ee',
    transparent: true,
    opacity: 0.02,
  });
  for (let i = 0; i < TOTAL; i += 3) {
    const p1 = strand1Points[i];
    const p2 = strand2Points[i];
    if (!p1 || !p2) continue;
    const mid = new THREE.Vector3().addVectors(p1, p2).multiplyScalar(0.5);
    const len = p1.distanceTo(p2);
    const dir = new THREE.Vector3().subVectors(p2, p1).normalize();
    const quaternion = new THREE.Quaternion().setFromUnitVectors(
      new THREE.Vector3(0, 1, 0),
      dir,
    );
    rods.push(
      <mesh key={i} position={mid} quaternion={quaternion} material={rodMat}>
        <cylinderGeometry args={[ROD_RADIUS, ROD_RADIUS, len, 4]} />
      </mesh>,
    );
  }

  return (
    <group ref={groupRef}>
      <mesh geometry={geo1} material={strandMat} />
      <mesh geometry={geo2} material={strandMat} />
      {rods}
    </group>
  );
}

export default function DnaBackground() {
  return (
    <div
      className="hidden sm:block"
      style={{ position: 'fixed', inset: 0, zIndex: 0, pointerEvents: 'none' }}
    >
      <Canvas
        camera={{ position: [0, 0, 6], fov: 55 }}
        gl={{ antialias: true, alpha: true }}
        style={{ background: 'transparent' }}
      >
        <HelixMesh />
      </Canvas>
    </div>
  );
}
