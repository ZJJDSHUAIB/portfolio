/**
 * MoltenMetal 页面初始化脚本(三个页面共用)
 * =================================================
 * 用法:在页面 <head> 里配置 importmap 指向 ogl CDN,
 * 在页面末尾加载本脚本 + molten-metal.js。
 *
 * HTML 结构约定:
 *   <div class="molten-hero" data-molten>  ... hero 内容 ... </div>
 *   <!-- 脚本在 </body> 前 -->
 *   <script type="importmap"> ... </script>
 *   <script type="module">
 *     import { initMolten } from './js/molten-init.js';
 *     initMolten();
 *   </script>
 */
import { MoltenMetal } from './molten-metal.js';

const DEFAULT_OPTS = {
  color1: '#5B6BFF',   // Halo 靛蓝
  color2: '#3DD7E5',   // Halo info 青
  color3: '#F2F4F8',   // Halo 亮白
  speed: 0.3,
  scale: 2.5,
  detail: 3,
  glow: 2.2,
  coreSize: 0.15,
  swirl: 1,
  fold: -0.2,
  blackPoint: 0.0,
  brightness: 2.5,
  colorMode: 'molten',
  grain: true,
  grainIntensity: 0.05,
  mouseInteraction: true,
  mouseStrength: 0.3,
  opacity: 1.0,
};

export function initMolten() {
  const containers = document.querySelectorAll('.molten-hero');
  if (!containers.length) return;

  // 每个容器都会初始化一个实例
  containers.forEach((container) => {
    // 读取 data-molten 上的配置(可覆盖默认)
    const data = container.dataset;
    const opts = Object.assign({}, DEFAULT_OPTS, {
      color1: data.color1 || DEFAULT_OPTS.color1,
      color2: data.color2 || DEFAULT_OPTS.color2,
      color3: data.color3 || DEFAULT_OPTS.color3,
      speed: data.speed !== undefined ? parseFloat(data.speed) : DEFAULT_OPTS.speed,
      detail: data.detail !== undefined ? parseFloat(data.detail) : DEFAULT_OPTS.detail,
      opacity: data.opacity !== undefined ? parseFloat(data.opacity) : DEFAULT_OPTS.opacity,
    });

    try {
      new MoltenMetal(container, opts);
      container.dataset.moltenOk = 'true';
    } catch (e) {
      // 降级:CDN 加载失败或 WebGL 不可用,静默失败,保留静态背景
      console.warn('[MoltenMetal] 初始化失败,使用静态背景:', e);
      container.dataset.moltenError = String(e && e.message ? e.message : e);
      container.classList.add('molten-fallback');
    }
  });
}
