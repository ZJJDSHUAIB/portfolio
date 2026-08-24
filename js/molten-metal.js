/**
 * MoltenMetal —— ES Module 版熔岩金属 WebGL 背景
 * =================================================
 * 依赖 ogl(通过 importmap 引入)。
 *
 * 用法:
 *   import { MoltenMetal } from './js/molten-metal.js';
 *   const mm = new MoltenMetal(containerEl, { color1: '#5227FF', ... });
 *   mm.setOptions({ speed: 0.5, ... });   // 更新参数
 *   mm.destroy();                          // 销毁
 */
import { Renderer, Program, Mesh, Triangle } from 'ogl';

const hexToRgb = (hex) => {
  const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
  if (!result) return [1, 1, 1];
  return [
    parseInt(result[1], 16) / 255,
    parseInt(result[2], 16) / 255,
    parseInt(result[3], 16) / 255,
  ];
};

const colorModeToFloat = (mode) => (mode === 'ember' ? 1 : mode === 'frost' ? 2 : 0);

const vertex = `#version 300 es
in vec2 position;
void main() {
  gl_Position = vec4(position, 0.0, 1.0);
}
`;

const fragment = `#version 300 es
precision highp float;
uniform vec2 iResolution;
uniform float iTime;
uniform float uSpeed;
uniform float uScale;
uniform float uDetail;
uniform float uGlow;
uniform float uCoreSize;
uniform float uSwirl;
uniform float uFold;
uniform float uBlackPoint;
uniform float uBrightness;
uniform float uColorMode;
uniform float uGrain;
uniform float uGrainIntensity;
uniform float uOpacity;
uniform vec2 uMouse;
uniform float uMouseStrength;
uniform bool uEnableMouse;
uniform vec3 uColor1;
uniform vec3 uColor2;
uniform vec3 uColor3;
out vec4 fragColor;

float hash(vec2 p) {
  return fract(sin(dot(p, vec2(12.9898, 78.233))) * 43758.5453);
}

void main() {
  float time = iTime * uSpeed;
  vec2 p = uScale * ((gl_FragCoord.xy - 0.5 * iResolution.xy) / iResolution.y) - 0.5;

  vec2 drift = vec2(0.0);
  if (uEnableMouse) {
    drift = (uMouse - 0.5) * uMouseStrength * 2.0;
  }
  p += drift;

  vec2 i = p;
  float c = 0.0;
  float r = length(p + vec2(sin(time), sin(time * 0.3 + 5.0)) * 0.5);
  float d = length(p);
  float rot = d + time + p.x * uSwirl;

  float cosRot = cos(rot);
  mat2 warp = mat2(cos(rot - sin(time / 5.0)), sin(rot), -sin(cosRot - time), cosRot) * uFold;
  float glowCore = uGlow * uCoreSize;

  for (float n = 0.0; n < 8.0; n++) {
    if (n >= uDetail) break;
    p *= warp;
    float t = r - time / (n + 3.0);
    i -= p + vec2(cos(t - i.x - r) + sin(t + i.y), sin(t - i.y) + cos(t + i.x) + r);
    c += glowCore / length(vec2(sin(i.x + t), cos(i.y + t)));
  }

  c /= 6.0;

  float intensity = max(c - uBlackPoint, 0.0) * uBrightness;

  float g = clamp(intensity, 0.0, 1.0);

  float mid = 0.5;
  if (uColorMode > 1.5) {
    mid = 0.65;
  } else if (uColorMode > 0.5) {
    mid = 0.35;
  }

  vec3 col = mix(uColor1, uColor2, smoothstep(0.0, mid, g));
  col = mix(col, uColor3, smoothstep(mid, 1.0, g));

  float a = g;
  if (uGrain > 0.5) {
    float gr = hash(gl_FragCoord.xy + iTime);
    a += (gr - 0.5) * uGrainIntensity;
  }
  a = clamp(a, 0.0, 1.0) * uOpacity;
  fragColor = vec4(col * a, a);
}
`;

export class MoltenMetal {
  constructor(container, options = {}) {
    if (!container) throw new Error('MoltenMetal: 需要容器元素');
    this.container = container;

    // 若容器内有 .molten-canvas-layer,canvas 放进该层(绝对定位,不撑开布局);
    // 否则直接放容器内,并给容器加 position:relative + overflow:hidden
    const layer = container.querySelector('.molten-canvas-layer');
    this.canvasHost = layer || container;
    if (!layer) {
      const cs = getComputedStyle(container);
      if (cs.position === 'static') container.style.position = 'relative';
      container.style.overflow = 'hidden';
    }

    // 默认参数
    this.options = Object.assign(
      {
        color1: '#5227FF',
        color2: '#FF9FFC',
        color3: '#FFFFFF',
        speed: 0.35,
        scale: 4,
        detail: 3,
        glow: 1.6,
        coreSize: 0.1,
        swirl: 1,
        fold: -0.2,
        blackPoint: 0.05,
        brightness: 1.3,
        colorMode: 'molten',
        grain: true,
        grainIntensity: 0.05,
        mouseInteraction: true,
        mouseStrength: 0.3,
        opacity: 1.0,
      },
      options
    );

    this.renderer = new Renderer({
      webgl: 2,
      alpha: true,
      premultipliedAlpha: true,
      antialias: false,
      dpr: Math.min(window.devicePixelRatio || 1, 2),
    });

    const gl = this.renderer.gl;
    gl.clearColor(0, 0, 0, 0);
    const canvas = gl.canvas;
    canvas.style.width = '100%';
    canvas.style.height = '100%';
    canvas.style.display = 'block';
    this.canvasHost.appendChild(canvas);

    this.geometry = new Triangle(gl);
    this.program = new Program(gl, {
      vertex,
      fragment,
      uniforms: {
        iTime: { value: 0 },
        iResolution: { value: new Float32Array([1, 1]) },
        uSpeed: { value: 0.35 },
        uScale: { value: 4 },
        uDetail: { value: 3 },
        uGlow: { value: 1.6 },
        uCoreSize: { value: 0.1 },
        uSwirl: { value: 1 },
        uFold: { value: -0.2 },
        uBlackPoint: { value: 0.05 },
        uBrightness: { value: 1.3 },
        uColorMode: { value: 0 },
        uGrain: { value: 1 },
        uGrainIntensity: { value: 0.05 },
        uOpacity: { value: 1.0 },
        uMouse: { value: new Float32Array([0.5, 0.5]) },
        uMouseStrength: { value: 0.3 },
        uEnableMouse: { value: true },
        uColor1: { value: new Float32Array([1, 1, 1]) },
        uColor2: { value: new Float32Array([1, 1, 1]) },
        uColor3: { value: new Float32Array([1, 1, 1]) },
      },
    });

    this.mesh = new Mesh(gl, { geometry: this.geometry, program: this.program });

    // 应用初始参数
    this.applyOptions(this.options);

    // 尺寸自适应:观察容器(而非 canvas),canvas 绝对定位铺满层,不参与文档流
    this.setSize = () => {
      const rect = container.getBoundingClientRect();
      const w = Math.max(1, Math.floor(rect.width));
      const h = Math.max(1, Math.floor(rect.height));
      // 防止异常放大(防御:限制在合理范围)
      if (h > 4000) return;
      this.renderer.setSize(w, h);
      const res = this.program.uniforms.iResolution.value;
      res[0] = gl.drawingBufferWidth;
      res[1] = gl.drawingBufferHeight;
      this.renderer.render({ scene: this.mesh });
    };

    this.ro = new ResizeObserver(() => this.setSize());
    this.ro.observe(this.canvasHost);
    this.setSize();

    // 鼠标交互
    this.targetMouse = [0.5, 0.5];
    this.currentMouse = [0.5, 0.5];

    this.handleMouseMove = (e) => {
      const rect = canvas.getBoundingClientRect();
      this.targetMouse[0] = (e.clientX - rect.left) / rect.width;
      this.targetMouse[1] = 1.0 - (e.clientY - rect.top) / rect.height;
    };
    this.handleMouseLeave = () => {
      this.targetMouse[0] = 0.5;
      this.targetMouse[1] = 0.5;
    };
    canvas.addEventListener('mousemove', this.handleMouseMove);
    canvas.addEventListener('mouseleave', this.handleMouseLeave);

    // 动画循环
    this.raf = 0;
    this.isVisible = true;
    this.isPageVisible = !document.hidden;
    this.t0 = performance.now();

    this.loop = (t) => {
      this.program.uniforms.iTime.value = (t - this.t0) * 0.001;
      this.currentMouse[0] += 0.05 * (this.targetMouse[0] - this.currentMouse[0]);
      this.currentMouse[1] += 0.05 * (this.targetMouse[1] - this.currentMouse[1]);
      this.program.uniforms.uMouse.value[0] = this.currentMouse[0];
      this.program.uniforms.uMouse.value[1] = this.currentMouse[1];
      this.renderer.render({ scene: this.mesh });
      this.raf = requestAnimationFrame(this.loop);
    };

    this.tryStart = () => {
      if (this.isVisible && this.isPageVisible && this.raf === 0) {
        this.raf = requestAnimationFrame(this.loop);
      }
    };
    this.tryStop = () => {
      if (this.raf !== 0) {
        cancelAnimationFrame(this.raf);
        this.raf = 0;
      }
    };

    this.io = new IntersectionObserver(
      ([entry]) => {
        this.isVisible = entry.isIntersecting;
        this.isVisible ? this.tryStart() : this.tryStop();
      },
      { threshold: 0 }
    );
    this.io.observe(container);

    this.onVisibility = () => {
      this.isPageVisible = !document.hidden;
      this.isPageVisible ? this.tryStart() : this.tryStop();
    };
    document.addEventListener('visibilitychange', this.onVisibility);

    this.tryStart();
  }

  applyOptions(options) {
    if (!this.program) return;
    const u = this.program.uniforms;
    const o = Object.assign(this.options, options);

    u.uSpeed.value = o.speed;
    u.uScale.value = o.scale;
    u.uDetail.value = o.detail;
    u.uGlow.value = o.glow;
    u.uCoreSize.value = Math.max(o.coreSize, 0.001);
    u.uSwirl.value = o.swirl;
    u.uFold.value = o.fold;
    u.uBlackPoint.value = o.blackPoint;
    u.uBrightness.value = o.brightness;
    u.uColorMode.value = colorModeToFloat(o.colorMode);
    u.uGrain.value = o.grain ? 1 : 0;
    u.uGrainIntensity.value = o.grainIntensity;
    u.uOpacity.value = o.opacity;
    u.uMouseStrength.value = o.mouseStrength;
    u.uEnableMouse.value = o.mouseInteraction;

    const c1 = hexToRgb(o.color1);
    const c2 = hexToRgb(o.color2);
    const c3 = hexToRgb(o.color3);
    const uc1 = u.uColor1.value;
    const uc2 = u.uColor2.value;
    const uc3 = u.uColor3.value;
    uc1[0] = c1[0]; uc1[1] = c1[1]; uc1[2] = c1[2];
    uc2[0] = c2[0]; uc2[1] = c2[1]; uc2[2] = c2[2];
    uc3[0] = c3[0]; uc3[1] = c3[1]; uc3[2] = c3[2];
  }

  setOptions(options) {
    this.applyOptions(options);
  }

  destroy() {
    if (!this.renderer) return;
    this.tryStop();
    this.ro.disconnect();
    this.io.disconnect();
    document.removeEventListener('visibilitychange', this.onVisibility);
    this.container.removeEventListener('mousemove', this.handleMouseMove);
    this.container.removeEventListener('mouseleave', this.handleMouseLeave);
    try {
      const canvas = this.renderer.gl.canvas;
      if (canvas && this.canvasHost.contains(canvas)) {
        this.canvasHost.removeChild(canvas);
      }
    } catch (e) {}
    try {
      this.renderer.gl.getExtension('WEBGL_lose_context')?.loseContext();
    } catch (e) {}
    this.renderer = null;
  }
}
