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

    // 1. Scene, Camera, WebGL Renderer
    const scene = new THREE.Scene();
    scene.fog = new THREE.FogExp2(0x07070b, 0.028);

    const camera = new THREE.PerspectiveCamera(
      55,
      container.clientWidth / container.clientHeight,
      0.1,
      1000
    );
    camera.position.set(0, 1.5, 22);

    const renderer = new THREE.WebGLRenderer({
      alpha: true,
      antialias: true,
      powerPreference: 'high-performance',
    });
    renderer.setSize(container.clientWidth, container.clientHeight);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.2;
    container.appendChild(renderer.domElement);

    // 2. Center Group (holds the Anamorphic Film Crystal & Orbital Rings)
    const centerGroup = new THREE.Group();
    scene.add(centerGroup);

    // Outer Faceted Crystal (Icosahedron Wireframe + Inner Solid)
    const crystalGeo = new THREE.IcosahedronGeometry(4.2, 1);
    const crystalMatWire = new THREE.MeshBasicMaterial({
      color: 0xe8b74a,
      wireframe: true,
      transparent: true,
      opacity: 0.35 * intensity,
    });
    const crystalMesh = new THREE.Mesh(crystalGeo, crystalMatWire);
    centerGroup.add(crystalMesh);

    // Inner Glowing Core (Prismatic Violet)
    const innerGeo = new THREE.OctahedronGeometry(2.4, 0);
    const innerMat = new THREE.MeshBasicMaterial({
      color: 0x6c63ff,
      wireframe: true,
      transparent: true,
      opacity: 0.55 * intensity,
    });
    const innerMesh = new THREE.Mesh(innerGeo, innerMat);
    centerGroup.add(innerMesh);

    // 3. Orbital Anamorphic Film Aperture Rings (3 Concentric Gimbal Rings)
    const rings: THREE.Mesh[] = [];
    const ringConfigs = [
      { radius: 6.2, tube: 0.04, color: 0x38bdf8, rotSpeed: 0.008, tilt: [Math.PI / 4, 0, 0] },
      { radius: 8.0, tube: 0.03, color: 0xe8b74a, rotSpeed: -0.005, tilt: [0, Math.PI / 3, Math.PI / 6] },
      { radius: 9.8, tube: 0.03, color: 0x6c63ff, rotSpeed: 0.006, tilt: [Math.PI / 6, Math.PI / 4, 0] },
    ];

    ringConfigs.forEach((cfg) => {
      const geo = new THREE.TorusGeometry(cfg.radius, cfg.tube, 8, 80);
      const mat = new THREE.MeshBasicMaterial({
        color: cfg.color,
        transparent: true,
        opacity: 0.45 * intensity,
      });
      const ring = new THREE.Mesh(geo, mat);
      ring.rotation.set(cfg.tilt[0], cfg.tilt[1], cfg.tilt[2]);
      centerGroup.add(ring);
      rings.push(ring);
    });

    // 4. Volumetric Anamorphic Projector Light Cone
    // Cylinder open at top expanding outward like a 70mm theatrical projection beam
    const coneGeo = new THREE.CylinderGeometry(14, 0.4, 28, 32, 1, true);
    const coneMat = new THREE.MeshBasicMaterial({
      color: 0x6c63ff,
      wireframe: true,
      transparent: true,
      opacity: 0.08 * intensity,
      side: THREE.DoubleSide,
    });
    const lightCone = new THREE.Mesh(coneGeo, coneMat);
    lightCone.rotation.x = Math.PI / 2;
    lightCone.position.z = -6;
    scene.add(lightCone);

    // 5. 3D Floating Data Photons / Cinema Dust Motes (1,400 Particles)
    const particleCount = 1400;
    const particleGeo = new THREE.BufferGeometry();
    const positions = new Float32Array(particleCount * 3);
    const colors = new Float32Array(particleCount * 3);
    const velocities = new Float32Array(particleCount * 3);

    const cGold = new THREE.Color(0xe8b74a);
    const cViolet = new THREE.Color(0x6c63ff);
    const cCyan = new THREE.Color(0x38bdf8);

    for (let i = 0; i < particleCount; i++) {
      const i3 = i * 3;
      // Cylinder distribution matching the light beam
      const radius = Math.random() * 22;
      const theta = Math.random() * Math.PI * 2;
      const z = (Math.random() - 0.5) * 40;

      positions[i3] = Math.cos(theta) * radius;
      positions[i3 + 1] = Math.sin(theta) * radius * 0.7; // slight elliptical anamorphic squeeze
      positions[i3 + 2] = z;

      velocities[i3] = (Math.random() - 0.5) * 0.02;
      velocities[i3 + 1] = (Math.random() - 0.5) * 0.02;
      velocities[i3 + 2] = Math.random() * 0.05 + 0.02; // drift forward toward camera

      // Tri-chromatic color palette
      const rVal = Math.random();
      const chosenColor = rVal < 0.45 ? cGold : rVal < 0.8 ? cViolet : cCyan;
      colors[i3] = chosenColor.r;
      colors[i3 + 1] = chosenColor.g;
      colors[i3 + 2] = chosenColor.b;
    }

    particleGeo.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    particleGeo.setAttribute('color', new THREE.BufferAttribute(colors, 3));

    const particleMaterial = new THREE.PointsMaterial({
      size: 0.18,
      vertexColors: true,
      transparent: true,
      opacity: 0.7 * intensity,
      blending: THREE.AdditiveBlending,
      depthWrite: false,
    });

    const particles = new THREE.Points(particleGeo, particleMaterial);
    scene.add(particles);

    // 6. Interactive Mouse & Drag Tilt Mechanics
    let mouseX = 0;
    let mouseY = 0;
    let targetCameraX = 0;
    let targetCameraY = 1.5;

    let isDragging = false;
    let prevMousePos = { x: 0, y: 0 };
    let dragRotY = 0;
    let dragRotX = 0;

    const handleMouseMove = (e: MouseEvent) => {
      const halfW = window.innerWidth / 2;
      const halfH = window.innerHeight / 2;
      mouseX = (e.clientX - halfW) / halfW;
      mouseY = (e.clientY - halfH) / halfH;

      if (isDragging) {
        const deltaX = e.clientX - prevMousePos.x;
        const deltaY = e.clientY - prevMousePos.y;
        dragRotY += deltaX * 0.005;
        dragRotX += deltaY * 0.005;
        prevMousePos = { x: e.clientX, y: e.clientY };
      }
    };

    const handleMouseDown = (e: MouseEvent) => {
      isDragging = true;
      prevMousePos = { x: e.clientX, y: e.clientY };
    };

    const handleMouseUp = () => {
      isDragging = false;
    };

    window.addEventListener('mousemove', handleMouseMove);
    window.addEventListener('mousedown', handleMouseDown);
    window.addEventListener('mouseup', handleMouseUp);

    // 7. Responsive Viewport Handler
    const handleResize = () => {
      if (!container) return;
      camera.aspect = container.clientWidth / container.clientHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(container.clientWidth, container.clientHeight);
    };

    window.addEventListener('resize', handleResize);

    // 8. Dynamic Animation Loop
    let animationFrameId: number;
    const clock = new THREE.Clock();

    const animate = () => {
      animationFrameId = requestAnimationFrame(animate);
      const elapsed = clock.getElapsedTime();

      // Smooth camera interpolation toward mouse coordinates
      targetCameraX = mouseX * 5.0;
      targetCameraY = 1.5 + mouseY * -3.0;

      camera.position.x += (targetCameraX - camera.position.x) * 0.04;
      camera.position.y += (targetCameraY - camera.position.y) * 0.04;
      camera.lookAt(0, 0, 0);

      // Rotate Center Crystal with drag decay
      centerGroup.rotation.y = elapsed * 0.15 + dragRotY;
      centerGroup.rotation.x = Math.sin(elapsed * 0.2) * 0.15 + dragRotX;

      crystalMesh.rotation.y = elapsed * -0.2;
      crystalMesh.rotation.z = Math.cos(elapsed * 0.15) * 0.2;

      innerMesh.rotation.x = elapsed * 0.4;
      innerMesh.rotation.y = elapsed * 0.3;

      // Animate Aperture Rings
      rings[0].rotation.z += 0.004;
      rings[1].rotation.x -= 0.003;
      rings[2].rotation.y += 0.005;

      // Gentle Projector Light Cone pulse
      lightCone.rotation.z = elapsed * 0.05;
      coneMat.opacity = (0.07 + Math.sin(elapsed * 1.8) * 0.02) * intensity;

      // Drift Photons forward (Z-axis reset loop)
      const posAttr = particleGeo.attributes.position as THREE.BufferAttribute;
      const posArr = posAttr.array as Float32Array;

      for (let i = 0; i < particleCount; i++) {
        const i3 = i * 3;
        posArr[i3] += velocities[i3];
        posArr[i3 + 1] += velocities[i3 + 1];
        posArr[i3 + 2] += velocities[i3 + 2];

        // Loop back when passing camera plane
        if (posArr[i3 + 2] > 20) {
          posArr[i3 + 2] = -25;
        }
      }
      posAttr.needsUpdate = true;

      renderer.render(scene, camera);
    };

    animate();

    // Cleanup resources on unmount
    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mousedown', handleMouseDown);
      window.removeEventListener('mouseup', handleMouseUp);
      window.removeEventListener('resize', handleResize);
      cancelAnimationFrame(animationFrameId);

      crystalGeo.dispose();
      crystalMatWire.dispose();
      innerGeo.dispose();
      innerMat.dispose();
      coneGeo.dispose();
      coneMat.dispose();
      particleGeo.dispose();
      particleMaterial.dispose();
      renderer.dispose();

      if (container.contains(renderer.domElement)) {
        container.removeChild(renderer.domElement);
      }
    };
  }, [intensity]);

  return (
    <div
      ref={mountRef}
      className={`absolute inset-0 cursor-grab active:cursor-grabbing overflow-hidden ${className}`}
      title="Click and drag to rotate the 3D Anamorphic Film Crystal"
    />
  );
};
