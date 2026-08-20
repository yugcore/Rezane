/**
 * Rezane AI Assistant — Dual-Wing State Manager
 * Keeps the central circular REZANE AI orb ALWAYS VISIBLE.
 * Opens left wing (Apps, Windows, Git) and right wing (Browser, Chat) on demand.
 */
class HUDManager {
  constructor() {
    this.viewport = document.querySelector('.app-viewport');
    this.leftWing = document.querySelector('.left-wing');
    this.rightWing = document.querySelector('.right-wing');

    this.activeLeftTab = null;
    this.activeRightTab = null;

    this._initEvents();
  }

  _initEvents() {
    // Left wing tabs
    document.querySelectorAll('.wing-tab-btn[data-wing="left"]').forEach(btn => {
      btn.addEventListener('click', () => {
        const tab = btn.getAttribute('data-tab');
        if (tab) this.openWing('left', tab);
      });
    });

    // Right wing tabs
    document.querySelectorAll('.wing-tab-btn[data-wing="right"]').forEach(btn => {
      btn.addEventListener('click', () => {
        const tab = btn.getAttribute('data-tab');
        if (tab) this.openWing('right', tab);
      });
    });

    // Wing close buttons [X]
    const leftClose = document.querySelector('#closeLeftWing');
    if (leftClose) {
      leftClose.addEventListener('click', () => this.closeWing('left'));
    }
    const rightClose = document.querySelector('#closeRightWing');
    if (rightClose) {
      rightClose.addEventListener('click', () => this.closeWing('right'));
    }

    // Bottom HUD dock buttons
    document.querySelectorAll('.hud-dock-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        const target = btn.getAttribute('data-target');
        if (!target) return;

        if (['quick_launch', 'apps'].includes(target)) {
          this.toggleWing('left', 'apps');
        } else if (target === 'windows') {
          this.toggleWing('left', 'windows');
        } else if (target === 'git') {
          this.toggleWing('left', 'git');
        } else if (target === 'browser') {
          this.toggleWing('right', 'browser');
        } else if (target === 'chat') {
          this.toggleWing('right', 'chat');
        } else if (target === 'dashboard') {
          this.toggleBothWings();
        }
      });
    });

    // Global keyboard shortcuts
    window.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') {
        this.closeAll();
      } else if (e.ctrlKey && e.key.toLowerCase() === 'b') {
        e.preventDefault();
        this.toggleWing('right', 'browser');
      } else if (e.ctrlKey && e.key.toLowerCase() === 'j') {
        e.preventDefault();
        this.toggleWing('right', 'chat');
      } else if (e.ctrlKey && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        this.toggleWing('left', 'apps');
      } else if (e.ctrlKey && e.key.toLowerCase() === 'w') {
        e.preventDefault();
        this.toggleWing('left', 'windows');
      } else if (e.ctrlKey && e.key.toLowerCase() === 'g') {
        e.preventDefault();
        this.toggleWing('left', 'git');
      } else if (e.ctrlKey && e.key.toLowerCase() === 'd') {
        e.preventDefault();
        this.toggleBothWings();
      }
    });
  }

  toggleWing(side, tab) {
    if (side === 'left') {
      if (this.viewport.classList.contains('left-open') && this.activeLeftTab === tab) {
        this.closeWing('left');
      } else {
        this.openWing('left', tab);
      }
    } else if (side === 'right') {
      if (this.viewport.classList.contains('right-open') && this.activeRightTab === tab) {
        this.closeWing('right');
      } else {
        this.openWing('right', tab);
      }
    }
  }

  toggleBothWings() {
    const isBothOpen = this.viewport.classList.contains('left-open') && this.viewport.classList.contains('right-open');
    if (isBothOpen) {
      this.closeAll();
    } else {
      this.openWing('left', this.activeLeftTab || 'apps');
      this.openWing('right', this.activeRightTab || 'browser');
    }
  }

  openWing(side, tab) {
    if (!this.viewport) return;

    if (side === 'left') {
      this.viewport.classList.add('left-open');
      this.activeLeftTab = tab;

      // Update tab buttons
      document.querySelectorAll('.wing-tab-btn[data-wing="left"]').forEach(btn => {
        btn.classList.toggle('active', btn.getAttribute('data-tab') === tab);
      });

      // Update panes
      document.querySelectorAll('#leftWingBody .tab-pane').forEach(pane => {
        pane.classList.toggle('active', pane.getAttribute('data-pane') === tab);
      });

      // Update dock button states
      document.querySelectorAll('.hud-dock-btn').forEach(btn => {
        const t = btn.getAttribute('data-target');
        if (['quick_launch', 'apps', 'windows', 'git'].includes(t)) {
          btn.classList.toggle('active', (t === tab || (t === 'quick_launch' && tab === 'apps')));
        }
      });
    } else if (side === 'right') {
      this.viewport.classList.add('right-open');
      this.activeRightTab = tab;

      // Update tab buttons
      document.querySelectorAll('.wing-tab-btn[data-wing="right"]').forEach(btn => {
        btn.classList.toggle('active', btn.getAttribute('data-tab') === tab);
      });

      // Update panes
      document.querySelectorAll('#rightWingBody .tab-pane').forEach(pane => {
        pane.classList.toggle('active', pane.getAttribute('data-pane') === tab);
      });

      // Focus input if chat or browser
      if (tab === 'chat') {
        const inp = document.querySelector('#chatInput');
        if (inp) setTimeout(() => inp.focus(), 150);
      } else if (tab === 'browser') {
        const urlInp = document.querySelector('#urlInput');
        if (urlInp) setTimeout(() => urlInp.focus(), 150);
      }

      // Update dock button states
      document.querySelectorAll('.hud-dock-btn').forEach(btn => {
        const t = btn.getAttribute('data-target');
        if (['browser', 'chat'].includes(t)) {
          btn.classList.toggle('active', t === tab);
        }
      });
    }
  }

  closeWing(side) {
    if (!this.viewport) return;

    if (side === 'left') {
      this.viewport.classList.remove('left-open');
      this.activeLeftTab = null;
      document.querySelectorAll('.hud-dock-btn').forEach(btn => {
        const t = btn.getAttribute('data-target');
        if (['quick_launch', 'apps', 'windows', 'git'].includes(t)) {
          btn.classList.remove('active');
        }
      });
    } else if (side === 'right') {
      this.viewport.classList.remove('right-open');
      this.activeRightTab = null;
      document.querySelectorAll('.hud-dock-btn').forEach(btn => {
        const t = btn.getAttribute('data-target');
        if (['browser', 'chat'].includes(t)) {
          btn.classList.remove('active');
        }
      });
    }
  }

  closeAll() {
    this.closeWing('left');
    this.closeWing('right');
  }

  navigateBrowser(url) {
    this.openWing('right', 'browser');

    const urlInput = document.querySelector('#urlInput');
    const frame = document.querySelector('#browserFrame');
    const frameView = document.querySelector('#browserFrameView');
    const shortcutsView = document.querySelector('#browserShortcutsView');
    const tabTitle = document.querySelector('#browserTabTitle');

    if (urlInput) urlInput.value = url;
    if (tabTitle) tabTitle.textContent = url.replace(/^https?:\/\//, '').split('/')[0];
    if (frame) frame.src = `/api/browser/proxy?url=${encodeURIComponent(url)}`;
    if (shortcutsView) shortcutsView.style.display = 'none';
    if (frameView) {
      frameView.style.display = 'flex';
      frameView.classList.add('active');
    }
  }
}

window.hudManager = new HUDManager();
