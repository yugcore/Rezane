/**
 * Central AI Indicator & Orb Visual Controller (Circular Gradient Core)
 */
class OrbController {
  constructor() {
    this.orbWrap = document.querySelector('.orb-wrap');
    this.orbGlow = document.querySelector('.orb-glow');
    this.orbRing = document.querySelector('.orb-ring');
    this.orbCore = document.querySelector('.orb-core');
    this.listeningPill = document.querySelector('.listening-pill');
    this.listeningText = document.querySelector('.listening-text');
    this.micPing = document.querySelector('.mic-ping');
    this.currentState = 'IDLE';

    this._initEvents();
  }

  _initEvents() {
    if (this.listeningPill) {
      this.listeningPill.addEventListener('click', () => {
        if (window.voiceController) {
          window.voiceController.toggleListening();
        }
      });
    }

    if (this.orbWrap) {
      this.orbWrap.addEventListener('click', () => {
        if (window.voiceController) {
          window.voiceController.toggleListening();
        }
      });
    }
  }

  updateState(statusData) {
    const state = (statusData.current_state || 'IDLE').toUpperCase();
    this.currentState = state;
    const text = statusData.status_text || state;

    if (this.listeningText) {
      this.listeningText.textContent = text;
    }

    if (!this.orbGlow || !this.orbRing) return;

    switch (state) {
      case 'LISTENING':
        this.orbGlow.style.background = 'radial-gradient(circle, rgba(255,255,255,0.22), rgba(255,255,255,0) 70%)';
        this.orbRing.style.background = 'conic-gradient(from 0deg, rgba(255,255,255,0.06), #ffffff, rgba(255,255,255,0.06) 45%)';
        this.orbRing.style.animationDuration = '3.5s';
        if (this.listeningPill) {
          this.listeningPill.style.borderColor = '#ffffff';
          this.listeningText.style.color = '#ffffff';
        }
        if (this.micPing) this.micPing.style.borderColor = '#ffffff';
        break;

      case 'THINKING':
      case 'PLANNING':
        this.orbGlow.style.background = 'radial-gradient(circle, rgba(255,255,255,0.28), rgba(255,255,255,0) 70%)';
        this.orbRing.style.background = 'conic-gradient(from 0deg, rgba(255,255,255,0.1), #ffffff, rgba(255,255,255,0.1) 30%)';
        this.orbRing.style.animationDuration = '1.8s';
        if (this.listeningPill) {
          this.listeningPill.style.borderColor = '#ffffff';
          this.listeningText.style.color = '#ffffff';
        }
        if (this.micPing) this.micPing.style.borderColor = '#ffffff';
        break;

      case 'EXECUTING':
        this.orbGlow.style.background = 'radial-gradient(circle, rgba(255,255,255,0.2), rgba(255,255,255,0) 70%)';
        this.orbRing.style.background = 'conic-gradient(from 0deg, rgba(255,255,255,0.05), rgba(255,255,255,0.92), rgba(255,255,255,0.05) 50%)';
        this.orbRing.style.animationDuration = '1.4s';
        if (this.listeningPill) {
          this.listeningPill.style.borderColor = '#cccccc';
          this.listeningText.style.color = '#cccccc';
        }
        if (this.micPing) this.micPing.style.borderColor = '#cccccc';
        break;

      case 'SPEAKING':
        this.orbGlow.style.background = 'radial-gradient(circle, rgba(255,255,255,0.25), rgba(255,255,255,0) 70%)';
        this.orbRing.style.background = 'conic-gradient(from 0deg, rgba(255,255,255,0.08), #ffffff, rgba(255,255,255,0.08) 40%)';
        this.orbRing.style.animationDuration = '2.8s';
        if (this.listeningPill) {
          this.listeningPill.style.borderColor = '#ffffff';
          this.listeningText.style.color = '#ffffff';
        }
        if (this.micPing) this.micPing.style.borderColor = '#ffffff';
        break;

      case 'ERROR':
        this.orbGlow.style.background = 'radial-gradient(circle, rgba(255,255,255,0.08), rgba(255,255,255,0) 70%)';
        this.orbRing.style.background = 'conic-gradient(from 0deg, rgba(255,255,255,0.02), #666666, rgba(255,255,255,0.02) 20%)';
        this.orbRing.style.animationDuration = '6s';
        if (this.listeningPill) {
          this.listeningPill.style.borderColor = '#555555';
          this.listeningText.style.color = '#777777';
        }
        if (this.micPing) this.micPing.style.borderColor = '#777777';
        break;

      case 'IDLE':
      default:
        this.orbGlow.style.background = 'radial-gradient(circle, rgba(255,255,255,0.12), rgba(255,255,255,0) 70%)';
        this.orbRing.style.background = 'conic-gradient(from 0deg, rgba(255,255,255,0.03), rgba(255,255,255,0.95), rgba(255,255,255,0.03) 40%)';
        this.orbRing.style.animationDuration = '7s';
        if (this.listeningPill) {
          this.listeningPill.style.borderColor = '#333333';
          this.listeningText.style.color = '#ffffff';
        }
        if (this.micPing) this.micPing.style.borderColor = '#ffffff';
        break;
    }
  }
}

window.orbController = new OrbController();
