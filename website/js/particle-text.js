/**
 * ParticleText —— 纯 JS 版粒子文字(Canvas 2D,零依赖)
 * =================================================
 * 从 reactbits 的 React 组件改写为原生 JS,不依赖 React。
 * 文字从散开状态聚合成形,鼠标划过有斥力,粒子会呼吸漂移。
 *
 * 用法:
 *   import { ParticleText } from './js/particle-text.js';
 *   const pt = new ParticleText(containerEl, { text: '张君杰', ... });
 *   pt.destroy();
 */
export class ParticleText {
  constructor(container, options = {}) {
    if (!container) throw new Error('ParticleText: 需要容器元素');
    this.container = container;

    this.options = Object.assign(
      {
        text: '张君杰',
        particleSize: 2.2,
        density: 4,
        color: '#f8fafc',
        highlightColor: '#5b6bff',
        scatter: 190,
        gatherDuration: 1600,
        stagger: 420,
        pointerRepel: 42,
        repelRadius: 120,
        idleDrift: 0.8,
        trigger: 'mount',
        fontSize: 'clamp(2.5rem, 9vw, 6rem)',
        fontWeight: 800,
        fontFamily: 'inherit',
        glow: true,
      },
      options
    );

    // 创建 canvas
    this.canvas = document.createElement('canvas');
    this.canvas.className = 'particle-text__canvas';
    this.canvas.setAttribute('aria-hidden', 'true');
    this.container.appendChild(this.canvas);

    const ctx = this.canvas.getContext('2d');
    if (!ctx) {
      this.canvas.remove();
      throw new Error('ParticleText: 无法获取 2D 上下文');
    }
    this.ctx = ctx;

    // 状态
    this.particles = [];
    this.animationFrame = null;
    this.resizeFrame = null;
    this.buildId = 0;
    this.gathering = false;
    this.gatherStart = 0;
    this.reducedMotion =
      window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    this.width = 0;
    this.height = 0;
    this.dpr = 1;

    this.pointer = { active: false, x: 0, y: 0, smoothX: 0, smoothY: 0 };
    this.isVisible = true;
    this.isPageVisible = !document.hidden;

    this._startGather = this._startGather.bind(this);
    this._render = this._render.bind(this);
    this._sampleText = this._sampleText.bind(this);
    this._queueSample = this._queueSample.bind(this);
    this._handlePointerMove = this._handlePointerMove.bind(this);
    this._handlePointerLeave = this._handlePointerLeave.bind(this);
    this._handlePointerEnter = this._handlePointerEnter.bind(this);
    this._handleClick = this._handleClick.bind(this);
    this._onVisibility = this._onVisibility.bind(this);

    this._bindEvents();
    this._sampleText();
    this._tryStart();
  }

  /* ---------- 工具函数 ---------- */

  _hexToRgb(hex) {
    const clean = hex.replace('#', '').trim();
    if (!/^[0-9a-fA-F]{6}$/.test(clean)) return null;
    return {
      r: parseInt(clean.slice(0, 2), 16),
      g: parseInt(clean.slice(2, 4), 16),
      b: parseInt(clean.slice(4, 6), 16),
    };
  }

  _mixRgb(from, to, amount) {
    return {
      r: Math.round(from.r + (to.r - from.r) * amount),
      g: Math.round(from.g + (to.g - from.g) * amount),
      b: Math.round(from.b + (to.b - from.b) * amount),
    };
  }

  _rgbToCss(rgb) {
    return `rgb(${rgb.r}, ${rgb.g}, ${rgb.b})`;
  }

  _clamp(value, min, max) {
    return Math.min(Math.max(value, min), max);
  }

  _easeOutCubic(t) {
    return 1 - Math.pow(1 - t, 3);
  }

  _resolveFontSize(value) {
    if (typeof value === 'number') return value;
    const probe = document.createElement('span');
    probe.textContent = 'M';
    probe.style.position = 'absolute';
    probe.style.visibility = 'hidden';
    probe.style.pointerEvents = 'none';
    probe.style.fontSize = value;
    probe.style.fontWeight = String(this.options.fontWeight);
    probe.style.fontFamily = this.options.fontFamily === 'inherit'
      ? getComputedStyle(this.container).fontFamily
      : this.options.fontFamily;
    this.container.appendChild(probe);
    const size = parseFloat(window.getComputedStyle(probe).fontSize) || 96;
    probe.remove();
    return size;
  }

  async _waitForFonts(font) {
    if (!('fonts' in document)) return;
    try {
      await document.fonts.load(font);
    } catch (e) {}
    await document.fonts.ready;
  }

  /* ---------- 动画 ---------- */

  _startGather(fromScatter = true) {
    if (!this.particles.length) return;
    const now = performance.now();
    const spread = this.reducedMotion ? 0 : this.options.scatter;

    this.particles.forEach((p) => {
      if (fromScatter) {
        const angle = p.seed * Math.PI * 2;
        const distance = spread * (0.35 + p.depth * 0.75);
        p.x = p.targetX + Math.cos(angle) * distance + (p.depth - 0.5) * spread * 0.55;
        p.y = p.targetY + Math.sin(angle) * distance + (p.seed - 0.5) * spread * 0.55;
      }
      p.startX = p.x;
      p.startY = p.y;
      p.delay = this.reducedMotion ? 0 : p.seed * this.options.stagger;
    });

    this.gatherStart = now;
    this.gathering = true;
  }

  _drawParticle(p) {
    const size = p.size;
    this.ctx.fillStyle = p.color;
    if (size <= 2.1) {
      this.ctx.fillRect(p.x - size / 2, p.y - size / 2, size, size);
      return;
    }
    this.ctx.beginPath();
    this.ctx.arc(p.x, p.y, size / 2, 0, Math.PI * 2);
    this.ctx.fill();
  }

  _render(now) {
    const ctx = this.ctx;
    ctx.clearRect(0, 0, this.width, this.height);

    if (this.options.glow && !this.reducedMotion) {
      ctx.shadowBlur = this.options.particleSize * 3;
      ctx.shadowColor = this.options.highlightColor;
    } else {
      ctx.shadowBlur = 0;
    }

    const p = this.pointer;
    p.smoothX += (p.x - p.smoothX) * 0.18;
    p.smoothY += (p.y - p.smoothY) * 0.18;

    let complete = true;

    this.particles.forEach((particle) => {
      let baseX = particle.targetX;
      let baseY = particle.targetY;
      let progress = 1;

      if (this.gathering) {
        const local =
          (now - this.gatherStart - particle.delay) /
          Math.max(1, this.reducedMotion ? 1 : this.options.gatherDuration);
        progress = this._clamp(local, 0, 1);
        const eased = this._easeOutCubic(progress);
        baseX = particle.startX + (particle.targetX - particle.startX) * eased;
        baseY = particle.startY + (particle.targetY - particle.startY) * eased;
        if (progress < 1) complete = false;
      } else if (!this.reducedMotion && this.options.idleDrift > 0) {
        const driftTime = now * 0.001;
        baseX += Math.sin(driftTime * 0.9 + particle.seed * 10) * this.options.idleDrift * particle.depth;
        baseY += Math.cos(driftTime * 0.75 + particle.depth * 10) * this.options.idleDrift * particle.depth;
      }

      if (p.active && !this.reducedMotion && this.options.pointerRepel > 0 && this.options.repelRadius > 0) {
        const dx = baseX - p.smoothX;
        const dy = baseY - p.smoothY;
        const distance = Math.hypot(dx, dy);
        if (distance > 0 && distance < this.options.repelRadius) {
          const force =
            Math.pow(1 - distance / this.options.repelRadius, 2) * this.options.pointerRepel;
          baseX += (dx / distance) * force;
          baseY += (dy / distance) * force;
        }
      }

      const follow = this.reducedMotion ? 1 : 0.22;
      particle.x += (baseX - particle.x) * follow;
      particle.y += (baseY - particle.y) * follow;

      ctx.globalAlpha = this._clamp(0.6 + progress * 0.4, 0, 1);
      this._drawParticle(particle);
    });

    ctx.globalAlpha = 1;
    ctx.shadowBlur = 0;

    if (this.gathering && complete) {
      this.gathering = false;
    }

    this.animationFrame = window.requestAnimationFrame(this._render);
  }

  _tryStart() {
    if (this.isVisible && this.isPageVisible && this.animationFrame === null) {
      this.animationFrame = window.requestAnimationFrame(this._render);
    }
  }

  _tryStop() {
    if (this.animationFrame !== null) {
      window.cancelAnimationFrame(this.animationFrame);
      this.animationFrame = null;
    }
  }

  /* ---------- 采样(把文字变成粒子) ---------- */

  async _sampleText() {
    const currentBuild = ++this.buildId;
    const rect = this.container.getBoundingClientRect();
    this.width = Math.floor(rect.width);
    this.height = Math.floor(rect.height);
    if (this.width <= 0 || this.height <= 0) return;

    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    this.canvas.width = Math.max(1, Math.floor(this.width * dpr));
    this.canvas.height = Math.max(1, Math.floor(this.height * dpr));
    this.canvas.style.width = '100%';
    this.canvas.style.height = '100%';
    this.ctx.setTransform(dpr, 0, 0, dpr, 0, 0);

    const computed = window.getComputedStyle(this.container);
    const resolvedFamily =
      this.options.fontFamily === 'inherit' ? computed.fontFamily || 'sans-serif' : this.options.fontFamily;
    let resolvedSize = this._resolveFontSize(this.options.fontSize);
    let font = `${this.options.fontWeight} ${resolvedSize}px ${resolvedFamily}`;

    await this._waitForFonts(font);
    if (currentBuild !== this.buildId) return;

    const offscreen = document.createElement('canvas');
    const offCtx = offscreen.getContext('2d', { willReadFrequently: true });
    if (!offCtx) return;

    const content = String(this.options.text || ' ');
    const maxTextWidth = this.width * 0.92;
    offCtx.font = font;
    let metrics = offCtx.measureText(content);
    const measuredWidth = Math.max(1, metrics.width);
    if (measuredWidth > maxTextWidth) {
      resolvedSize = Math.max(18, resolvedSize * (maxTextWidth / measuredWidth));
      font = `${this.options.fontWeight} ${resolvedSize}px ${resolvedFamily}`;
      await this._waitForFonts(font);
      if (currentBuild !== this.buildId) return;
      offCtx.font = font;
      metrics = offCtx.measureText(content);
    }

    const left = Math.ceil(metrics.actualBoundingBoxLeft || 0);
    const right = Math.ceil(metrics.actualBoundingBoxRight || metrics.width);
    const ascent = Math.ceil(metrics.actualBoundingBoxAscent || resolvedSize * 0.78);
    const descent = Math.ceil(metrics.actualBoundingBoxDescent || resolvedSize * 0.22);
    const padding = Math.max(12, Math.ceil(resolvedSize * 0.08));
    const textWidth = Math.max(1, left + right);
    const textHeight = Math.max(1, ascent + descent);

    offscreen.width = textWidth + padding * 2;
    offscreen.height = textHeight + padding * 2;
    offCtx.clearRect(0, 0, offscreen.width, offscreen.height);
    offCtx.font = font;
    offCtx.textAlign = 'left';
    offCtx.textBaseline = 'alphabetic';
    offCtx.fillStyle = '#ffffff';
    offCtx.fillText(content, padding - left, padding + ascent);

    const imageData = offCtx.getImageData(0, 0, offscreen.width, offscreen.height);
    const targets = [];
    const step = Math.max(2, Math.floor(this.options.density));

    for (let y = 0; y < offscreen.height; y += step) {
      for (let x = 0; x < offscreen.width; x += step) {
        const alpha = imageData.data[(y * offscreen.width + x) * 4 + 3];
        if (alpha > 40) {
          targets.push({
            x: this.width / 2 - offscreen.width / 2 + x,
            y: this.height / 2 - offscreen.height / 2 + y,
            alpha: alpha / 255,
          });
        }
      }
    }

    const maxParticles = Math.max(900, Math.min(5200, Math.floor((this.width * this.height) / 90)));
    const stride = Math.max(1, Math.ceil(targets.length / maxParticles));
    const baseRgb = this._hexToRgb(this.options.color);
    const highlightRgb = this._hexToRgb(this.options.highlightColor);
    const selected = targets.filter((_, index) => index % stride === 0);

    this.particles = selected.map((target, index) => {
      const seed = ((index * 9301 + 49297) % 233280) / 233280;
      const depth = 0.45 + (((index * 233 + 97) % 1000) / 1000) * 0.9;
      // 颜色混合:大部分粒子保持主体色(白),仅少量随机粒子带高亮色点缀。
      // 原逻辑 target.x/width 使 blend 恒在 0.3~0.7,导致全部粒子偏蓝。
      const blend = baseRgb && highlightRgb
        ? (seed > 0.82 ? seed * 0.9 : 0)
        : 0;
      const particleColor = baseRgb && highlightRgb
        ? this._rgbToCss(this._mixRgb(baseRgb, highlightRgb, blend))
        : this.options.color;
      const angle = seed * Math.PI * 2;
      const distance = (this.reducedMotion ? 0 : this.options.scatter) * (0.35 + depth * 0.75);
      const startX = target.x + Math.cos(angle) * distance + (seed - 0.5) * this.options.scatter * 0.45;
      const startY = target.y + Math.sin(angle) * distance + (depth - 0.9) * this.options.scatter * 0.45;

      return {
        x: this.reducedMotion ? target.x : startX,
        y: this.reducedMotion ? target.y : startY,
        startX,
        startY,
        targetX: target.x,
        targetY: target.y,
        size: Math.max(0.6, this.options.particleSize * (0.75 + target.alpha * 0.45)),
        color: particleColor,
        seed,
        depth,
        delay: seed * this.options.stagger,
      };
    });

    this.pointer.x = this.width / 2;
    this.pointer.y = this.height / 2;
    this.pointer.smoothX = this.pointer.x;
    this.pointer.smoothY = this.pointer.y;

    if (this.reducedMotion) {
      this.particles.forEach((particle) => {
        particle.x = particle.targetX;
        particle.y = particle.targetY;
        particle.startX = particle.targetX;
        particle.startY = particle.targetY;
        particle.delay = 0;
      });
      this.gathering = false;
    } else {
      this._startGather(false);
    }

    this._tryStart();
  }

  _queueSample() {
    if (this.resizeFrame) window.cancelAnimationFrame(this.resizeFrame);
    this.resizeFrame = window.requestAnimationFrame(this._sampleText);
  }

  /* ---------- 事件 ---------- */

  _bindEvents() {
    this._handlePointerMove = this._handlePointerMove.bind(this);
    this._handlePointerLeave = this._handlePointerLeave.bind(this);
    this._handlePointerEnter = this._handlePointerEnter.bind(this);
    this._handleClick = this._handleClick.bind(this);
    this._onVisibility = this._onVisibility.bind(this);

    this.canvas.addEventListener('pointerenter', this._handlePointerEnter);
    this.canvas.addEventListener('pointermove', this._handlePointerMove);
    this.canvas.addEventListener('pointerleave', this._handlePointerLeave);
    this.canvas.addEventListener('click', this._handleClick);

    this.ro = new ResizeObserver(this._queueSample);
    this.ro.observe(this.container);

    this.io = new IntersectionObserver(
      ([entry]) => {
        this.isVisible = entry.isIntersecting;
        this.isVisible ? this._tryStart() : this._tryStop();
      },
      { threshold: 0 }
    );
    this.io.observe(this.container);

    document.addEventListener('visibilitychange', this._onVisibility);

    const mq = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)');
    if (mq && mq.addEventListener) {
      this._reduceMotionQuery = mq;
      this._handleReduceMotionChange = (e) => {
        this.reducedMotion = e.matches;
        this._sampleText();
      };
      mq.addEventListener('change', this._handleReduceMotionChange);
    }
  }

  _handlePointerMove(event) {
    const rect = this.canvas.getBoundingClientRect();
    this.pointer.x = event.clientX - rect.left;
    this.pointer.y = event.clientY - rect.top;
    this.pointer.active = true;
  }

  _handlePointerLeave() {
    this.pointer.active = false;
  }

  _handlePointerEnter(event) {
    this._handlePointerMove(event);
    if (this.options.trigger === 'hover') this._startGather(true);
  }

  _handleClick() {
    if (this.options.trigger === 'click') this._startGather(true);
  }

  _onVisibility() {
    this.isPageVisible = !document.hidden;
    this.isPageVisible ? this._tryStart() : this._tryStop();
  }

  /* ---------- 销毁 ---------- */

  destroy() {
    this.buildId += 1;
    this._tryStop();
    if (this.resizeFrame) window.cancelAnimationFrame(this.resizeFrame);
    this.ro.disconnect();
    this.io.disconnect();
    document.removeEventListener('visibilitychange', this._onVisibility);
    if (this._reduceMotionQuery && this._handleReduceMotionChange) {
      this._reduceMotionQuery.removeEventListener('change', this._handleReduceMotionChange);
    }
    this.canvas.removeEventListener('pointerenter', this._handlePointerEnter);
    this.canvas.removeEventListener('pointermove', this._handlePointerMove);
    this.canvas.removeEventListener('pointerleave', this._handlePointerLeave);
    this.canvas.removeEventListener('click', this._handleClick);
    try {
      if (this.canvas.parentNode) this.canvas.parentNode.removeChild(this.canvas);
    } catch (e) {}
  }
}

/**
 * 初始化所有 [data-particle-text] 容器(页面共用)
 */
export function initParticleText() {
  const els = document.querySelectorAll('[data-particle-text]');
  els.forEach((el) => {
    const d = el.dataset;
    try {
      new ParticleText(el, {
        text: d.text || '张君杰',
        particleSize: d.particleSize !== undefined ? parseFloat(d.particleSize) : 2.2,
        density: d.density !== undefined ? parseFloat(d.density) : 4,
        color: d.color || '#f8fafc',
        highlightColor: d.highlight || '#5b6bff',
        scatter: d.scatter !== undefined ? parseFloat(d.scatter) : 190,
        gatherDuration: d.gatherDuration !== undefined ? parseFloat(d.gatherDuration) : 1600,
        stagger: d.stagger !== undefined ? parseFloat(d.stagger) : 420,
        pointerRepel: d.pointerRepel !== undefined ? parseFloat(d.pointerRepel) : 42,
        repelRadius: d.repelRadius !== undefined ? parseFloat(d.repelRadius) : 120,
        idleDrift: d.idleDrift !== undefined ? parseFloat(d.idleDrift) : 0.8,
        trigger: d.trigger || 'mount',
        fontSize: d.fontSize || 'clamp(2.5rem, 9vw, 6rem)',
        fontWeight: d.fontWeight !== undefined ? parseInt(d.fontWeight, 10) : 800,
        fontFamily: d.fontFamily || 'inherit',
        glow: d.glow !== 'false',
      });
    } catch (e) {
      console.warn('[ParticleText] 初始化失败:', e);
    }
  });
}
