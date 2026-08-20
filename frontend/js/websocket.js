/**
 * Resilient WebSocket Client for Rezane AI Real-Time Events
 */
class RezaneEventClient {
  constructor(url) {
    this.url = url || this._getDefaultWsUrl();
    this.ws = null;
    this.listeners = new Map();
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 50;
    this.reconnectDelay = 1500;
    this.isConnected = false;
  }

  _getDefaultWsUrl() {
    const loc = window.location;
    const protocol = loc.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = loc.host && loc.host !== '' ? loc.host : '127.0.0.1:8000';
    return `${protocol}//${host}/events`;
  }

  connect() {
    try {
      this.ws = new WebSocket(this.url);
      
      this.ws.onopen = () => {
        console.log('[Rezane WS] Connected to', this.url);
        this.isConnected = true;
        this.reconnectAttempts = 0;
        this._emit('connection_status', { connected: true });
      };

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          const eventType = data.event_type;
          const payload = data.payload || {};
          this._emit(eventType, payload);
          this._emit('*', { eventType, payload });
        } catch (err) {
          console.error('[Rezane WS] Failed to parse message:', err);
        }
      };

      this.ws.onclose = (event) => {
        this.isConnected = false;
        this._emit('connection_status', { connected: false });
        console.warn('[Rezane WS] Connection closed. Reconnecting...');
        this._scheduleReconnect();
      };

      this.ws.onerror = (err) => {
        console.error('[Rezane WS] Error:', err);
        this.ws.close();
      };
    } catch (e) {
      console.error('[Rezane WS] Exception initiating WebSocket:', e);
      this._scheduleReconnect();
    }
  }

  _scheduleReconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      const delay = Math.min(10000, this.reconnectDelay * Math.min(this.reconnectAttempts, 4));
      setTimeout(() => this.connect(), delay);
    }
  }

  on(eventType, callback) {
    if (!this.listeners.has(eventType)) {
      this.listeners.set(eventType, []);
    }
    this.listeners.get(eventType).push(callback);
    return () => this.off(eventType, callback);
  }

  off(eventType, callback) {
    if (!this.listeners.has(eventType)) return;
    const filtered = this.listeners.get(eventType).filter(cb => cb !== callback);
    this.listeners.set(eventType, filtered);
  }

  _emit(eventType, payload) {
    const cbs = this.listeners.get(eventType) || [];
    cbs.forEach(cb => {
      try {
        cb(payload);
      } catch (e) {
        console.error(`[Rezane WS] Error in listener for ${eventType}:`, e);
      }
    });
  }

  send(data) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(typeof data === 'string' ? data : JSON.stringify(data));
    }
  }
}

window.eventClient = new RezaneEventClient();
