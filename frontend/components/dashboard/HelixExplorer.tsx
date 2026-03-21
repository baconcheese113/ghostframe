'use client';

import React, { useRef, useMemo } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { OrbitControls, Html } from '@react-three/drei';
import * as THREE from 'three';
import { FRAME_COLORS, EFFECT_COLORS, NUCLEOTIDE_COLORS } from '@/lib/colors';
import type { FrameEffect } from '@/lib/types';

const HELIX_RADIUS = 1.0;
const HELIX_PITCH = 0.4;
const BP_COUNT = 24;

interface HelixSceneProps {
  sequence: string;
  variant: FrameEffect | null;
}

function HelixScene({ sequence, variant }: HelixSceneProps) {
  const groupRef = useRef<THREE.Group>(null);

  useFrame((_, delta) => {
    if (groupRef.current && !variant) {
      groupRef.current.rotation.y += delta * 0.15;
    }
  });

  const { strand1Geo, strand2Geo, rods, framePlanes, variantSphere } = useMemo(() => {
    const pts1: THREE.Vector3[] = [];
    const pts2: THREE.Vector3[] = [];

    for (let i = 0; i <= BP_COUNT * 8; i++) {
      const t = (i / (BP_COUNT * 8)) * Math.PI * 2 * 2.5;
      const y = (i / (BP_COUNT * 8)) * HELIX_PITCH * BP_COUNT * 0.5 - HELIX_PITCH * BP_COUNT * 0.25;
      pts1.push(new THREE.Vector3(Math.cos(t) * HELIX_RADIUS, y, Math.sin(t) * HELIX_RADIUS));
      pts2.push(
        new THREE.Vector3(
          Math.cos(t + Math.PI) * HELIX_RADIUS,
          y,
          Math.sin(t + Math.PI) * HELIX_RADIUS,
        ),
      );
    }

    const c1 = new THREE.CatmullRomCurve3(pts1);
    const c2 = new THREE.CatmullRomCurve3(pts2);
    const strand1Geo = new THREE.TubeGeometry(c1, BP_COUNT * 12, 0.04, 6, false);
    const strand2Geo = new THREE.TubeGeometry(c2, BP_COUNT * 12, 0.04, 6, false);

    // Base-pair rods
    const rods: React.ReactElement[] = [];
    for (let i = 0; i < BP_COUNT; i++) {
      const t = i / BP_COUNT;
      const p1 = c1.getPoint(t);
      const p2 = c2.getPoint(t);
      const mid = new THREE.Vector3().addVectors(p1, p2).multiplyScalar(0.5);
      const len = p1.distanceTo(p2);
      const dir = new THREE.Vector3().subVectors(p2, p1).normalize();
      const q = new THREE.Quaternion().setFromUnitVectors(new THREE.Vector3(0, 1, 0), dir);
      const nt = (sequence[i % sequence.length] ?? 'A').toUpperCase() as keyof typeof NUCLEOTIDE_COLORS;
      const color = NUCLEOTIDE_COLORS[nt] ?? '#22d3ee';
      rods.push(
        <mesh key={i} position={mid} quaternion={q}>
          <cylinderGeometry args={[0.018, 0.018, len, 4]} />
          <meshBasicMaterial color={color} transparent opacity={0.55} />
        </mesh>,
      );
    }

    // 6 frame ribbons
    const framePlanes: React.ReactElement[] = [];
    for (let frame = 1; frame <= 6; frame++) {
      const ribbonR = HELIX_RADIUS + 0.22 + (frame - 1) * 0.12;
      const pts: THREE.Vector3[] = [];
      for (let i = 0; i <= BP_COUNT * 4; i++) {
        const t = (i / (BP_COUNT * 4)) * Math.PI * 2 * 2.5;
        const y =
          (i / (BP_COUNT * 4)) * HELIX_PITCH * BP_COUNT * 0.5 - HELIX_PITCH * BP_COUNT * 0.25;
        pts.push(new THREE.Vector3(Math.cos(t) * ribbonR, y, Math.sin(t) * ribbonR));
      }
      const curve = new THREE.CatmullRomCurve3(pts);
      const ribbonGeo = new THREE.TubeGeometry(curve, BP_COUNT * 8, 0.022, 3, false);
      const isActiveFrame = variant?.frame === frame;
      const fc = FRAME_COLORS[frame];
      framePlanes.push(
        <mesh key={`frame-${frame}`} geometry={ribbonGeo}>
          <meshBasicMaterial
            color={fc}
            transparent
            opacity={isActiveFrame ? 0.75 : 0.18}
          />
        </mesh>,
      );
    }

    // Variant sphere
    let variantSphere: React.ReactElement | null = null;
    if (variant) {
      const relPos = Math.min((variant.position % BP_COUNT) / BP_COUNT, 0.95);
      const t = relPos * Math.PI * 2 * 2.5;
      const y =
        relPos * HELIX_PITCH * BP_COUNT * 0.5 - HELIX_PITCH * BP_COUNT * 0.25;
      const vPos = new THREE.Vector3(Math.cos(t) * HELIX_RADIUS, y, Math.sin(t) * HELIX_RADIUS);
      const effectColor = EFFECT_COLORS[variant.new_class] ?? '#22d3ee';
      variantSphere = (
        <group position={vPos}>
          <mesh>
            <sphereGeometry args={[0.12, 12, 12]} />
            <meshStandardMaterial color={effectColor} emissive={effectColor} emissiveIntensity={1.5} />
          </mesh>
          <pointLight color={effectColor} intensity={1.5} distance={1.2} />
          <Html distanceFactor={6} style={{ pointerEvents: 'none' }}>
            <div
              style={{
                background: 'rgba(2,14,28,0.88)',
                border: `1px solid ${effectColor}66`,
                borderRadius: '6px',
                padding: '4px 8px',
                whiteSpace: 'nowrap',
                fontSize: '10px',
                fontFamily: 'JetBrains Mono, monospace',
                color: effectColor,
                backdropFilter: 'blur(8px)',
              }}
            >
              Fr{variant.frame}: {variant.ref_aa}→{variant.alt_aa} ({variant.new_class})
            </div>
          </Html>
        </group>
      );
    }

    return { strand1Geo, strand2Geo, rods, framePlanes, variantSphere };
  }, [sequence, variant]);

  return (
    <group ref={groupRef}>
      {/* Backbones */}
      <mesh geometry={strand1Geo}>
        <meshBasicMaterial color="#22d3ee" transparent opacity={0.6} />
      </mesh>
      <mesh geometry={strand2Geo}>
        <meshBasicMaterial color="#818cf8" transparent opacity={0.6} />
      </mesh>
      {rods}
      {framePlanes}
      {variantSphere}
    </group>
  );
}

interface HelixExplorerProps {
  sequence: string;
  variant: FrameEffect | null;
}

export default function HelixExplorer({ sequence, variant }: HelixExplorerProps) {
  return (
    <div
      data-testid="helix-explorer"
      className="w-full h-full"
      style={{ minHeight: '260px', cursor: 'grab' }}
    >
      <Canvas
        camera={{ position: [0, 0, 5.5], fov: 50 }}
        dpr={[1, 2]}
        gl={{ antialias: true, alpha: true }}
        style={{ background: 'transparent' }}
      >
        <ambientLight intensity={0.4} />
        <directionalLight position={[3, 5, 3]} intensity={0.8} />
        <HelixScene sequence={sequence} variant={variant} />
        <OrbitControls enablePan={false} minDistance={3} maxDistance={9} />
      </Canvas>

      {/* Frame legend */}
      <div className="absolute bottom-2 left-2 flex flex-wrap gap-1.5">
        {[1, 2, 3, 4, 5, 6].map((f) => (
          <span
            key={f}
            className="flex items-center gap-1 rounded px-1.5 py-0.5 text-[9px] font-data"
            style={{
              background: `${FRAME_COLORS[f]}18`,
              border: `1px solid ${FRAME_COLORS[f]}40`,
              color: variant?.frame === f ? FRAME_COLORS[f] : '#64748b',
              fontWeight: variant?.frame === f ? 600 : 400,
            }}
          >
            <span
              className="h-1.5 w-1.5 rounded-full"
              style={{ background: FRAME_COLORS[f] }}
            />
            Fr{f}
          </span>
        ))}
      </div>
    </div>
  );
}
