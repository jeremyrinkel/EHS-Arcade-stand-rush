"""Add a browser-native fullscreen control to Pygbag's generated HTML."""
from pathlib import Path
p=Path('game/build/web/index.html')
html=p.read_text(encoding='utf-8')
addon=r'''
<style id="stand-rush-fullscreen-style">
#stand-rush-fullscreen { position:fixed; top:12px; right:12px; z-index:2147483647;
  background:#1d202b; color:#f6ead0; border:2px solid #efb951;
  border-radius:8px; padding:10px 14px; font:bold 14px Arial,sans-serif;
  cursor:pointer; box-shadow:0 2px 12px #0008; }
#stand-rush-fullscreen:hover {background:#34374a}
:fullscreen {background:#11151f!important}
:fullscreen canvas { max-width:100vw!important; max-height:100vh!important;
  width:min(100vw, 151.351vh)!important;
  height:min(100vh, 66.0714vw)!important;
  object-fit:contain!important; }
</style>
<button id="stand-rush-fullscreen" type="button" title="Toggle game fullscreen">⛶ Fullscreen</button>
<script id="stand-rush-fullscreen-script">
(function () {
  const btn = document.getElementById('stand-rush-fullscreen');
  async function toggle() {
    try {
      if (document.fullscreenElement) await document.exitFullscreen();
      else await document.documentElement.requestFullscreen();
    } catch (error) { console.warn('Fullscreen was blocked:', error); }
  }
  btn.addEventListener('click', toggle);
  document.addEventListener('fullscreenchange', () => {
    btn.textContent = document.fullscreenElement ? '⛶ Exit fullscreen' : '⛶ Fullscreen';
  });
})();
</script>
'''
if 'stand-rush-fullscreen-script' not in html:
    html=html.replace('</body>',addon+'\n</body>')
p.write_text(html,encoding='utf-8')
