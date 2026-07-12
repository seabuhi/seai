"use client"

import React, { useRef, useState, useMemo } from 'react'
import { Canvas, useFrame } from '@react-three/fiber'
import { Float, PerspectiveCamera, OrbitControls, Sphere, Cylinder } from '@react-three/drei'
import * as THREE from 'three'
import { motion, AnimatePresence } from 'framer-motion'

function LampModel({ isOn, onToggle }: { isOn: boolean; onToggle: () => void }) {
    const chainRef = useRef<THREE.Group>(null)
    const [isPulling, setIsPulling] = useState(false)

    // Subtle swinging animation for the lamp
    useFrame((state) => {
        if (chainRef.current) {
            const t = state.clock.getElapsedTime()
            chainRef.current.position.y = isPulling ? -0.2 : 0
        }
    })

    return (
        <group position={[0, 2.5, 0]}>
            {/* Ceiling Mount */}
            <Cylinder args={[0.2, 0.2, 0.1, 32]} position={[0, 1, 0]}>
                <meshStandardMaterial color="#111" />
            </Cylinder>

            {/* Wire */}
            <Cylinder args={[0.01, 0.01, 2, 8]} position={[0, 0, 0]}>
                <meshStandardMaterial color="#000" />
            </Cylinder>

            {/* Lamp Shade (Conical) */}
            <mesh position={[0, -1, 0]} rotation={[Math.PI, 0, 0]}>
                <coneGeometry args={[1, 1.2, 32, 1, true]} />
                <meshStandardMaterial color="#050505" side={THREE.DoubleSide} metalness={0.8} roughness={0.2} />
            </mesh>

            {/* Inner Decorative Ring */}
            <mesh position={[0, -0.9, 0]} rotation={[Math.PI / 2, 0, 0]}>
                <torusGeometry args={[0.6, 0.02, 16, 100]} />
                <meshStandardMaterial color="#c2410c" emissive={isOn ? "#f97316" : "#000"} emissiveIntensity={isOn ? 2 : 0} />
            </mesh>

            {/* Light Bulb */}
            <Sphere args={[0.2, 32, 32]} position={[0, -1.2, 0]}>
                <meshStandardMaterial
                    color={isOn ? "#fff" : "#444"}
                    emissive={isOn ? "#fff" : "#222"}
                    emissiveIntensity={isOn ? 5 : 0}
                />
                {isOn && <pointLight intensity={10} distance={10} color="#fff" shadow-mapSize={[1024, 1024]} />}
            </Sphere>

            {/* Pull Chain */}
            <group
                ref={chainRef}
                position={[0.3, -0.8, 0]}
                onClick={(e) => {
                    e.stopPropagation()
                    setIsPulling(true)
                    setTimeout(() => {
                        setIsPulling(false)
                        onToggle()
                    }, 150)
                }}
                onPointerOver={() => (document.body.style.cursor = 'pointer')}
                onPointerOut={() => (document.body.style.cursor = 'auto')}
            >
                {/* Chain Wire */}
                <Cylinder args={[0.005, 0.005, 1, 8]} position={[0, -0.5, 0]}>
                    <meshStandardMaterial color="#333" />
                </Cylinder>
                {/* Chain Handle */}
                <Sphere args={[0.05, 16, 16]} position={[0, -1, 0]}>
                    <meshStandardMaterial color="#000" metalness={1} roughness={0} />
                </Sphere>
            </group>
        </group>
    )
}

export default function Lamp() {
    const [isOn, setIsOn] = useState(false)

    return (
        <div className="w-[300px] h-[400px] relative">
            <Canvas shadows>
                <PerspectiveCamera makeDefault position={[0, 0, 5]} />
                <ambientLight intensity={0.2} />
                {/* Fill light */}
                <pointLight position={[2, 2, 2]} intensity={0.5} />

                <Float speed={1.5} rotationIntensity={0.2} floatIntensity={0.5}>
                    <LampModel isOn={isOn} onToggle={() => setIsOn(!isOn)} />
                </Float>

                {/* Backdrop Glow when ON */}
                <AnimatePresence>
                    {isOn && (
                        <mesh position={[0, -1.5, -2]} scale={10}>
                            <planeGeometry />
                            <meshStandardMaterial
                                color="#fff"
                                transparent
                                opacity={0.05}
                                emissive="#fff"
                                emissiveIntensity={1}
                            />
                        </mesh>
                    )}
                </AnimatePresence>
            </Canvas>

            {/* Status indicator */}
            <div className="absolute bottom-4 right-4 flex items-center gap-2 pointer-events-none">
                <div className={`w-2 h-2 rounded-full ${isOn ? 'bg-orange-500 shadow-[0_0_10px_orange]' : 'bg-zinc-800'}`} />
                <span className="text-[10px] font-bold uppercase tracking-widest text-zinc-500">
                    Aura Light: {isOn ? 'Active' : 'Standby'}
                </span>
            </div>
        </div>
    )
}
