import React, { useEffect, useRef } from 'react';
import * as THREE from 'three';

interface Cinema3DCanvasProps {
  className?: string;
  intensity?: number;
}

export const Cinema3DCanvas: React.FC<Cinema3DCanvasProps> = ({
  className = '',
  intensity = 1.0,
}) => {
  const mountRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const container = mountRef.current;
    if (!container) return;

    // 1. Scene, Camera, Renderer
    const scene = new THREE.Scene();
    scene.fog = new THREE.FogExp2(0x0a0a0f, 0.035);

    const camera = new THREE.PerspectiveCamera(
      60,
      container.clientWidth / container.clientHeight,
      0.1,
      1000
    );
    camera.position.z = 24;
    camera.position.y = 2;

    const renderer = new THREE.WebGLRenderer({
      alpha: true,
      antialias: true,
      powerPreference: 'high-performance',
    });
    renderer.setSize(container.clientWidth, container.clientHeight);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    container.appendChild(renderer.domElement);

    // 2. 3D Cinematic Film Reel / Torus Wireframe (The Core Artifact)
    const torusGeometry = new THREE.TorusGeometry(8, 2.2, 16, 100);
    const torusMaterial = new THREE.MeshBasicMaterial({
      color: 0x6c63ff,
      wireframe: true,
      transparent: true,
      opacity: 0.22 * intensity,
    });
    const torusMesh = new THREE.Mesh(torusGeometry, torusMaterial);
    torusMesh.rotation.x = Math.PI / 3;
    scene.add(torusMesh);

    // Inner Gold Reel Ring
    const innerTorusGeo = new THREE.TorusGeometry(5, 0.6, 12, 60);
    const innerTorusMat = new THREE.MeshBasicMaterial({
      color: 0xe8b74a,
      wireframe: true,
      transparent: true,
      opacity: 0.35 * intensity,
    });
    const innerTorus = new THREE.Mesh(innerTorusGeo, innerTorusMat);
    torusMesh.add(innerTorus);

    // 3. 3D Probability Wave Particles (Box-Office Statistical Wave)
    const particleCount = 1800;
    const particleGeo = new THREE.BufferGeometry();
    const positions = new Float32Array(particleCount * 3);
    const colors = new Float32Array(particleCount * 3);
    const originalY = new Float32Array(particleCount);

    const colorGold = new THREE.Color(0xe8b74a);
    const colorPurple = new THREE.Color(0x6c63ff);
    const colorCyan = new THREE.Color(0x38bdf8);

    for (let i = 0; i < particleCount; i++) {
      const i3 = i * 3;
      // Spread across a 3D volume
      const x = (Math.random() - 0.5) * 60;
      const z = (Math.random() - 0.5) * 50;
      // Gaussian probability bell curve shape in Y
      const dist = Math.sqrt(x * x + z * z);
      const y = Math.exp(-0.015 * dist * dist) * 8 - 4 + (Math.random() - 0.5) * 2;

      positions[i3] = x;
      positions[i3 + 1] = y;
      positions[i3 + 2] = z;
      originalY[i] = y;

      // Color gradient: Gold in center, Purple in mid, Cyan at edge
      let chosenColor = colorGold;
      if (dist > 12) chosenColor = colorPurple;
      if (dist > 25) chosenColor = colorCyan;

      colors[i3] = chosenColor.r;
      colors[i3 + 1] = chosenColor.g;
      colors[i3 + 2] = chosenColor.b;
    }

    particleGeo.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    particleGeo.setAttribute('color', new THREE.BufferAttribute(colors, 3));

    const particleMaterial = new THREE.PointsMaterial({
      size: 0.22,
      vertexColors: true,
      transparent: true,
      opacity: 0.75 * intensity,
      blending: THREE.AdditiveBlending,
    });

    const particles = new THREE.Points(particleGeo, particleMaterial);
    scene.add(particles);

    // 4. Subtle Ambient & Point Lights
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.4);
    scene.add(ambientLight);

    const goldPoint = new THREE.PointLight(0xe8b74a, 2, 40);
    goldPoint.position.set(0, 10, 10);
    scene.add(goldPoint);

    // 5. Mouse Interaction with Smooth Lerp
    let mouseX = 0;
    let mouseY = 0;
    let targetX = 0;
    let targetY = 0;

    const handleMouseMove = (e: MouseEvent) => {
      const halfW = window.innerWidth / 2;
      const halfH = window.innerHeight / 2;
      mouseX = (e.clientX - halfW) * 0.0008;
      mouseY = (e.clientY - halfH) * 0.0008;
    };

    window.addEventListener('mousemove', handleMouseMove);

    // 6. Resize Handler
    const handleResize = () => {
      if (!container) return;
      camera.aspect = container.clientWidth / container.clientHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(container.clientWidth, container.clientHeight);
    };

    window.addEventListener('resize', handleResize);

    // 7. Render Animation Loop
    let animationFrameId: number;
    let clock = new THREE.Clock();

    const animate = () => {
      animationFrameId = requestAnimationFrame(animate);
      const elapsed = clock.getElapsedTime();

      // Smooth mouse follow
      targetX += (mouseX - targetX) * 0.05;
      targetY += (mouseY - targetY) * 0.05;

      camera.position.x = targetX * 12;
      camera.position.y = 2 + targetY * -8;
      camera.lookAt(0, 0, 0);

      // Rotate 3D Torus
      torusMesh.rotation.z = elapsed * 0.12;
      torusMesh.rotation.y = elapsed * 0.08;
      innerTorus.rotation.x = elapsed * -0.2;

      // Animate wave on particles
      const posAttr = particleGeo.attributes.position as THREE.BufferAttribute;
      const array = posAttr.array as Float32Array;

      for (let i = 0; i < particleCount; i++) {
        const i3 = i * 3;
        const x = array[i3];
        const z = array[i3 + 2];
        // Sinusoidal wave ripple
        array[i3 + 1] = originalY[i] + Math.sin(elapsed * 1.5 + x * 0.15 + z * 0.1) * 0.8;
      }
      posAttr.needsUpdate = true;

      renderer.render(scene, camera);
    };

    animate();

    // Cleanup
    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('resize', handleResize);
      cancelAnimationFrame(animationFrameId);

      torusGeometry.dispose();
      torusMaterial.dispose();
      innerTorusGeo.dispose();
      innerTorusMat.dispose();
      particleGeo.dispose();
      particleMaterial.dispose();
      renderer.dispose();

      if (container.contains(renderer.domElement)) {
        container.removeChild(renderer.domElement);
      }
    };
  }, [intensity]);

  return <div ref={mountRef} className={`absolute inset-0 pointer-events-none ${className}`} />;
};

