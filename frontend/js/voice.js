/**
 * Rezane AI Assistant — Advanced Voice-to-Text (STT) & Real-Time Voice Controller
 */
class VoiceController {
  constructor() {
    this.recognition = null;
    this.isListening = false;
    this.mediaRecorder = null;
    this.audioChunks = [];
    this.silenceTimer = null;
    this.lastInterimText = "";

    // DOM Elements
    this.listeningPill = document.querySelector('.listening-pill') || document.querySelector('#listeningPill');
    this.listeningText = document.querySelector('.listening-text') || document.querySelector('#telemetryText');
    this.micPing = document.querySelector('.mic-ping');
    this.voiceWave = document.querySelector('.voice-wave');
    this.micBtn = document.querySelector('#micToggleBtn') || document.querySelector('.ctrl-btn');

    this._initSpeechRecognition();
    this._initEvents();
  }

  _initSpeechRecognition() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRecognition) {
      this.recognition = new SpeechRecognition();
      this.recognition.continuous = true;
      this.recognition.interimResults = true;
      this.recognition.lang = 'en-US';

      this.recognition.onstart = () => {
        this.isListening = true;
        this._updateUIState('LISTENING', 'Listening...');
      };

      this.recognition.onresult = (event) => {
        let interimTranscript = '';
        let finalTranscript = '';

        for (let i = event.resultIndex; i < event.results.length; ++i) {
          const transcript = event.results[i][0].transcript;
          if (event.results[i].isFinal) {
            finalTranscript += transcript;
          } else {
            interimTranscript += transcript;
          }
        }

        const displayText = finalTranscript || interimTranscript;
        if (displayText) {
          this.lastInterimText = displayText;
          this._showLiveTranscription(displayText);
          
          clearTimeout(this.silenceTimer);
          if (finalTranscript) {
            this._handleRecognizedCommand(finalTranscript.trim());
          } else {
            this.silenceTimer = setTimeout(() => {
              if (this.lastInterimText.trim()) {
                this._handleRecognizedCommand(this.lastInterimText.trim());
                this.lastInterimText = "";
              }
            }, 1200);
          }
        }
      };

      this.recognition.onerror = (event) => {
        console.debug('Speech recognition event:', event.error);
        if (event.error === 'not-allowed') {
          // If browser mic permission is not granted, fallback to Whisper audio capture
          this._startWhisperRecording();
        }
      };

      this.recognition.onend = () => {
        if (this.isListening) {
          try {
            this.recognition.start();
          } catch (e) {}
        }
      };
    } else {
      console.warn('Web Speech API not available. Using Whisper backend fallback.');
    }
  }

  _initEvents() {
    // Click on listening pill or mic button to toggle voice recognition
    if (this.listeningPill) {
      this.listeningPill.addEventListener('click', () => this.toggleListening());
    }
    if (this.micBtn) {
      this.micBtn.addEventListener('click', () => this.toggleListening());
    }

    // Keyboard shortcut: Ctrl + Space or M to toggle listening
    window.addEventListener('keydown', (e) => {
      if ((e.ctrlKey && e.code === 'Space') || (e.key === 'm' && document.activeElement.tagName !== 'INPUT')) {
        e.preventDefault();
        this.toggleListening();
      }
    });
  }

  toggleListening() {
    if (this.isListening) {
      this.stopListening();
    } else {
      this.startListening();
    }
  }

  startListening() {
    this.isListening = true;
    this._updateUIState('LISTENING', 'Listening...');
    if (window.orbController) {
      window.orbController.updateState({ current_state: 'LISTENING', status_text: 'Listening...' });
    }

    fetch('/api/assistant/state', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ state: 'LISTENING', status_text: 'Listening...' })
    }).catch(() => {});

    if (this.recognition) {
      try {
        this.recognition.start();
      } catch (e) {}
    } else {
      this._startWhisperRecording();
    }
  }

  stopListening() {
    this.isListening = false;
    clearTimeout(this.silenceTimer);
    this._updateUIState('IDLE', 'Ready and waiting for instructions.');
    if (window.orbController) {
      window.orbController.updateState({ current_state: 'IDLE', status_text: 'Ready' });
    }

    fetch('/api/assistant/state', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ state: 'IDLE', status_text: 'Ready' })
    }).catch(() => {});

    if (this.recognition) {
      try {
        this.recognition.stop();
      } catch (e) {}
    }
    this._stopWhisperRecording();
  }

  _updateUIState(state, text) {
    if (this.listeningText) {
      this.listeningText.textContent = text;
    }
    if (this.listeningPill) {
      if (state === 'LISTENING') {
        this.listeningPill.classList.add('active');
        this.listeningPill.style.borderColor = '#ffffff';
      } else {
        this.listeningPill.classList.remove('active');
        this.listeningPill.style.borderColor = '#333333';
      }
    }
    if (this.micBtn) {
      if (state === 'LISTENING') {
        this.micBtn.classList.add('active');
      } else {
        this.micBtn.classList.remove('active');
      }
    }
  }

  _showLiveTranscription(text) {
    if (this.listeningText) {
      this.listeningText.textContent = `"${text}"`;
      this.listeningText.style.color = '#ffffff';
    }
  }

  async _handleRecognizedCommand(text) {
    if (!text) return;
    console.log('Voice Command Recognized:', text);
    
    // Switch orb to thinking state
    if (window.orbController) {
      window.orbController.updateState({ current_state: 'THINKING', status_text: `Analyzing: "${text}"` });
    }
    this._showLiveTranscription(`Command: "${text}"`);

    // 1. Check for immediate local client-side UI popup actions
    const handledLocally = this._handleLocalUIIntent(text);

    // 2. Post to backend voice command endpoint for backend orchestration / tools
    try {
      const response = await fetch('/api/voice/command', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text })
      });
      const data = await response.json();
      
      // If not already handled locally, process parsed intent
      if (!handledLocally && data.parsed) {
        this._dispatchParsedIntent(data.parsed);
      }
    } catch (err) {
      console.debug('Voice command API error:', err);
    }
  }

  _handleLocalUIIntent(text) {
    const t = text.toLowerCase();
    
    // Close / Hide wings back to clean Orb view
    if (t.includes('close left') || t.includes('hide left')) {
      if (window.hudManager) window.hudManager.closeWing('left');
      return true;
    }
    if (t.includes('close right') || t.includes('hide right') || t.includes('close browser') || t.includes('close chat')) {
      if (window.hudManager) window.hudManager.closeWing('right');
      return true;
    }
    if (t.includes('close all') || t.includes('hide all') || t.includes('minimize') || t.includes('dismiss') || t.includes('back to orb') || t.includes('clear screen') || t === 'close' || t === 'hide') {
      if (window.hudManager) {
        window.hudManager.closeAll();
      }
      setTimeout(() => {
        if (window.orbController) {
          window.orbController.updateState({ current_state: 'IDLE', status_text: 'Ready' });
        }
      }, 500);
      return true;
    }

    // Open Browser (Right Wing)
    if (t.includes('browser') || t.includes('youtube') || t.includes('google') || t.includes('search web') || t.includes('search for') || t.includes('open web')) {
      if (window.hudManager) {
        window.hudManager.openWing('right', 'browser');
        if (t.includes('search youtube for')) {
          const q = t.split('search youtube for')[1].trim();
          window.hudManager.navigateBrowser(`https://www.youtube.com/results?search_query=${encodeURIComponent(q)}`);
        } else if (t.includes('search google for')) {
          const q = t.split('search google for')[1].trim();
          window.hudManager.navigateBrowser(`https://www.google.com/search?q=${encodeURIComponent(q)}`);
        }
      }
      return true;
    }

    // Open Quick Launch / Apps (Left Wing)
    if (t.includes('quick launch') || t.includes('apps') || t.includes('launchpad') || t.includes('show launch')) {
      if (window.hudManager) window.hudManager.openWing('left', 'apps');
      return true;
    }

    // Open Active Windows (Left Wing)
    if (t.includes('active windows') || t.includes('windows') || t.includes('task manager')) {
      if (window.hudManager) window.hudManager.openWing('left', 'windows');
      return true;
    }

    // Open Git (Left Wing)
    if (t.includes('git') || t.includes('repository') || t.includes('commits')) {
      if (window.hudManager) window.hudManager.openWing('left', 'git');
      return true;
    }

    // Open Chat / AI Output (Right Wing)
    if (t.includes('chat') || t.includes('conversation') || t.includes('assistant') || t.includes('output') || t.includes('talk to rezane')) {
      if (window.hudManager) window.hudManager.openWing('right', 'chat');
      return true;
    }

    // Open Full Dashboard
    if (t.includes('dashboard') || t.includes('expand all') || t.includes('everything')) {
      if (window.hudManager) window.hudManager.toggleBothWings();
      return true;
    }

    return false;
  }

  _dispatchParsedIntent(parsed) {
    if (!parsed) return;
    if (parsed.intent === 'OPEN_PANEL' && window.hudManager) {
      window.hudManager.openPopup(parsed.panel);
    } else if (parsed.intent === 'CLOSE_PANELS' && window.hudManager) {
      window.hudManager.closeAllPopups();
    }
  }

  // --- Whisper Audio Recording Fallback ---
  async _startWhisperRecording() {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      this.audioChunks = [];
      this.mediaRecorder = new MediaRecorder(stream);
      this.mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) this.audioChunks.push(e.data);
      };
      this.mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(this.audioChunks, { type: 'audio/webm' });
        const formData = new FormData();
        formData.append('file', audioBlob, 'voice.webm');
        
        try {
          if (window.orbController) {
            window.orbController.updateState({ current_state: 'THINKING', status_text: 'Transcribing speech with Whisper...' });
          }
          const res = await fetch('/api/voice/transcribe', {
            method: 'POST',
            body: formData
          });
          const data = await res.json();
          if (data.text) {
            this._showLiveTranscription(data.text);
            this._handleRecognizedCommand(data.text);
          }
        } catch (err) {
          console.debug('Whisper transcribe error:', err);
        }
      };
      this.mediaRecorder.start();
    } catch (e) {
      console.warn('Microphone recording error:', e);
    }
  }

  _stopWhisperRecording() {
    if (this.mediaRecorder && this.mediaRecorder.state !== 'inactive') {
      this.mediaRecorder.stop();
    }
  }
}

window.voiceController = new VoiceController();
