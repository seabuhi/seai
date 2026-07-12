"use client"

import React, { useRef, useMemo } from 'react'
import { Canvas, useFrame } from '@react-three/fiber'
import { Points, PointMaterial } from '@react-three/drei'
import * as THREE from 'three'

function ParticleField() {
    const ref = useRef<THREE.Points>(null)

    const particlesCount = 2000
    const positions = useMemo(() => {
        const pos = new Float32Array(particlesCount * 3)
        for (let i = 0; i < particlesCount; i++) {
            pos[i * 3] = (Math.random() - 0.5) * 10
            pos[i * 3 + 1] = (Math.random() - 0.5) * 10
            pos[i * 3 + 2] = (Math.random() - 0.5) * 10
        }
        return pos
    }, [])

    useFrame((state) => {
        if (ref.current) {
            ref.current.rotation.x = state.clock.getElapsedTime() * 0.05
            ref.current.rotation.y = state.clock.getElapsedTime() * 0.03
        }
    })

    return (
        <group rotation={[0, 0, Math.PI / 4]}>
            <Points ref={ref} positions={positions} stride={3} frustumCulled={false}>
                <PointMaterial
                    transparent
                    color="#8b5cf6"
                    size={0.015}
                    sizeAttenuation={true}
                    depthWrite={false}
                    blending={THREE.AdditiveBlending}
                />
            </Points>
        </group>
    )
}

function FloatingOrbs() {
    return (
        <>
            <mesh position={[-2, 1, -2]}>
                <sphereGeometry args={[0.5, 32, 32]} />
                <meshStandardMaterial color="#3b82f6" emissive="#3b82f6" emissiveIntensity={2} transparent opacity={0.2} />
            </mesh>
            <mesh position={[3, -2, -1]}>
                <sphereGeometry args={[0.8, 32, 32]} />
                <meshStandardMaterial color="#8b5cf6" emissive="#8b5cf6" emissiveIntensity={2} transparent opacity={0.15} />
            </mesh>
        </>
    )
}

export default function NeuralBackground() {
    return (
        <div className="fixed inset-0 -z-20 bg-[#020202]">
            <Canvas camera={{ position: [0, 0, 5], fov: 75 }}>
                <ambientLight intensity={0.5} />
                <pointLight position={[10, 10, 10]} intensity={1} />
                <ParticleField />
                <FloatingOrbs />
            </Canvas>
            {/* Radial Gradient Overlay for depth */}
            <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,transparent_0%,rgba(0,0,0,0.8)_100%)] pointer-events-none" />
        </div>
    )
}
