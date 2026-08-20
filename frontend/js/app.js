/**
 * Main Application Orchestrator for Rezane AI Dashboard
 */
document.addEventListener('DOMContentLoaded', () => {
  const ws = window.eventClient;
  const orb = window.orbController;

  // DOM Elements
  const windowsListEl = document.getElementById('windowsList');
  const windowsCountEl = document.getElementById('windowsCount');
  const gitBranchEl = document.getElementById('gitBranch');
  const gitAheadEl = document.getElementById('gitAhead');
  const gitBehindEl = document.getElementById('gitBehind');
  const gitFilesContainerEl = document.getElementById('gitFilesContainer');
  const gitChangesSummaryEl = document.getElementById('gitChangesSummary');
  const stageAllBtn = document.getElementById('stageAllBtn');
  const commitBtn = document.getElementById('commitBtn');

  const chatScrollEl = document.getElementById('chatScroll');
  const chatInputEl = document.getElementById('chatInput');
  const sendBtn = document.getElementById('sendBtn');

  // ---------- WebSocket Event Subscriptions ----------

  ws.on('initial_sync', (data) => {
    console.log('[Rezane App] Received initial sync', data);
    if (data.status) orb.updateState(data.status);
    if (data.git) renderGitStatus(data.git);
    if (data.windows) renderActiveWindows(data.windows);
    if (data.history) renderChatHistory(data.history);
  });

  ws.on('state_change', (status) => {
    orb.updateState(status);
  });

  ws.on('windows_update', (data) => {
    if (data.windows) {
      renderActiveWindows(data.windows);
      if (windowsCountEl) windowsCountEl.textContent = `${data.total_count || data.windows.length} windows active`;
    }
  });

  ws.on('git_update', (gitData) => {
    renderGitStatus(gitData);
  });

  ws.on('chat_message', (msg) => {
    appendChatMessage(msg);
  });

  ws.on('checklist_update', (data) => {
    updateChecklist(data.msg_id, data.checklist);
  });

  // Connect WebSocket
  ws.connect();

  // Initial HTTP Fetch Fallback
  fetchInitialData();

  // ---------- Renderers ----------

  function renderActiveWindows(windows) {
    if (!windowsListEl) return;
    if (!windows || windows.length === 0) {
      windowsListEl.innerHTML = '<div style="padding:12px; color:var(--text-tertiary); font-size:12px;">No active application windows detected.</div>';
      return;
    }

    windowsListEl.innerHTML = windows.map(w => {
      const iconBg = getAppBgClass(w.category, w.process_name);
      return `
        <div class="window-row" data-hwnd="${w.hwnd}">
          <div class="win-icon ${iconBg}">
            ${getWindowIcon(w.category)}
          </div>
          <div class="win-info">
            <div class="win-title" title="${escapeHtml(w.title)}">${escapeHtml(w.title)}</div>
            <div class="win-path" title="${escapeHtml(w.process_path || '')}">${escapeHtml(w.process_path || w.process_name)}</div>
          </div>
          <div class="win-tag">${escapeHtml(w.category)}</div>
        </div>
      `;
    }).join('');

    // Attach click to focus
    windowsListEl.querySelectorAll('.window-row').forEach(row => {
      row.addEventListener('click', () => {
        const hwnd = parseInt(row.getAttribute('data-hwnd'));
        if (hwnd) {
          fetch('/api/windows/focus', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ hwnd })
          });
        }
      });
    });
  }

  function renderGitStatus(git) {
    const gitUrl = git?.remote_url || 'https://github.com/yugcore';
    if (!git || !git.is_git) {
      if (gitBranchEl) {
        gitBranchEl.innerHTML = `
          <svg viewBox="0 0 24 24" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="6" y1="3" x2="6" y2="15"/><circle cx="18" cy="6" r="3"/><circle cx="6" cy="18" r="3"/><path d="M18 9a9 9 0 0 1-9 9"/></svg>
          yugcore (connected)
        `;
        gitBranchEl.setAttribute('href', gitUrl);
      }
      if (gitFilesContainerEl) gitFilesContainerEl.innerHTML = '<div style="padding:10px; color:var(--text-tertiary); font-size:12px;">Connected to github.com/yugcore. Working tree clean.</div>';
      return;
    }

    if (gitBranchEl) {
      gitBranchEl.innerHTML = `
        <svg viewBox="0 0 24 24" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="6" y1="3" x2="6" y2="15"/><circle cx="18" cy="6" r="3"/><circle cx="6" cy="18" r="3"/><path d="M18 9a9 9 0 0 1-9 9"/></svg>
        ${escapeHtml(git.branch || 'main')}
      `;
      gitBranchEl.setAttribute('href', gitUrl);
      gitBranchEl.setAttribute('target', '_blank');
      gitBranchEl.setAttribute('title', `Open repository: ${gitUrl}`);
    }

    if (gitAheadEl) gitAheadEl.textContent = `AHEAD ${git.ahead || 0}`;
    if (gitBehindEl) gitBehindEl.textContent = `BEHIND ${git.behind || 0}`;

    let html = '';
    
    if (git.modified && git.modified.length > 0) {
      html += '<div class="git-section-label">Modified</div>';
      html += git.modified.map(f => `
        <div class="git-file-row">
          <div class="git-file-name" title="${escapeHtml(f.path)}">
            <svg viewBox="0 0 24 24" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 18 15 12 9 6"/></svg>
            ${escapeHtml(f.path)}
          </div>
          <div class="git-badge badge-m">${escapeHtml(f.badge || 'M')}</div>
        </div>
      `).join('');
    }

    if (git.untracked && git.untracked.length > 0) {
      html += '<div class="git-section-label">Untracked</div>';
      html += git.untracked.map(f => `
        <div class="git-file-row">
          <div class="git-file-name" title="${escapeHtml(f.path)}">
            <svg viewBox="0 0 24 24" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 18 15 12 9 6"/></svg>
            ${escapeHtml(f.path)}
          </div>
          <div class="git-badge badge-untracked">${escapeHtml(f.badge || '??')}</div>
        </div>
      `).join('');
    }

    if (git.staged && git.staged.length > 0) {
      html += '<div class="git-section-label">Staged</div>';
      html += git.staged.map(f => `
        <div class="git-file-row">
          <div class="git-file-name" title="${escapeHtml(f.path)}">
            <svg viewBox="0 0 24 24" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 18 15 12 9 6"/></svg>
            ${escapeHtml(f.path)}
          </div>
          <div class="git-badge badge-staged">${escapeHtml(f.badge || 'A')}</div>
        </div>
      `).join('');
    }

    if (!html) {
      html = '<div style="padding:14px 4px; color:var(--text-secondary); font-size:12px;">Working tree clean. Repository synced with yugcore.</div>';
    }

    if (gitFilesContainerEl) gitFilesContainerEl.innerHTML = html;
    if (gitChangesSummaryEl) {
      gitChangesSummaryEl.innerHTML = `Changes <span class="plus">+${git.additions || 0}</span> <span class="minus">-${git.deletions || 0}</span>`;
    }
  }

  function renderChatHistory(messages) {
    if (!chatScrollEl) return;
    chatScrollEl.innerHTML = '';
    messages.forEach(m => appendChatMessage(m, false));
    scrollToBottom();
  }

  function appendChatMessage(msg, scroll = true) {
    if (!chatScrollEl) return;
    const existing = document.getElementById(msg.id);
    if (existing) {
      existing.remove();
    }

    const isYou = msg.role === 'you';
    const roleLabel = isYou ? 'You' : 'Assistant';
    const roleClass = isYou ? 'role-you' : 'role-assistant';

    let checklistHtml = '';
    if (msg.checklist && msg.checklist.length > 0) {
      checklistHtml = `
        <div class="checklist">
          ${msg.checklist.map(item => `
            <div class="check-item ${item.status === 'running' ? 'active' : ''}">
              <div class="check-icon ${item.status === 'done' ? 'check-done' : ''}">
                ${item.status === 'done' 
                  ? '<svg viewBox="0 0 24 24" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><polyline points="8 12.5 11 15.5 16 9"/></svg>'
                  : item.status === 'running' 
                    ? '<div class="spinner"></div>'
                    : '<div style="width:5px; height:5px; background:var(--text-tertiary)"></div>'
                }
              </div>
              <span>${escapeHtml(item.label)}</span>
            </div>
          `).join('')}
        </div>
      `;
    }

    let resultPathHtml = '';
    if (msg.result_path) {
      resultPathHtml = `
        <div class="result-path mono">${escapeHtml(msg.result_path)}</div>
        <br>
        <div class="open-folder-btn" onclick="openPath('${escapeHtml(msg.result_path)}')">
          <svg viewBox="0 0 24 24" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2Z"/></svg>
          Open Results
        </div>
      `;
    }

    const msgDiv = document.createElement('div');
    msgDiv.className = 'msg';
    msgDiv.id = msg.id;
    msgDiv.innerHTML = `
      <div class="msg-meta">
        <span class="msg-time">${msg.timestamp || ''}</span>
        <span class="msg-role ${roleClass}">${roleLabel}</span>
      </div>
      <div class="msg-text">${escapeHtml(msg.text).replace(/\\n/g, '<br>')}</div>
      ${checklistHtml}
      ${resultPathHtml}
    `;

    chatScrollEl.appendChild(msgDiv);
    if (scroll) scrollToBottom();
  }

  function updateChecklist(msgId, checklist) {
    const msgEl = document.getElementById(msgId);
    if (!msgEl) return;
    const checklistEl = msgEl.querySelector('.checklist');
    if (!checklistEl) return;

    checklistEl.innerHTML = checklist.map(item => `
      <div class="check-item ${item.status === 'running' ? 'active' : ''}">
        <div class="check-icon ${item.status === 'done' ? 'check-done' : ''}">
          ${item.status === 'done' 
            ? '<svg viewBox="0 0 24 24" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><polyline points="8 12.5 11 15.5 16 9"/></svg>'
            : item.status === 'running' 
              ? '<div class="spinner"></div>'
              : '<div style="width:5px; height:5px; background:var(--text-tertiary)"></div>'
          }
        </div>
        <span>${escapeHtml(item.label)}</span>
      </div>
    `).join('');
  }

  function scrollToBottom() {
    if (chatScrollEl) {
      chatScrollEl.scrollTop = chatScrollEl.scrollHeight;
    }
  }

  // ---------- User Chat Interaction ----------

  async function handleSend() {
    if (!chatInputEl) return;
    const text = chatInputEl.value.trim();
    if (!text) return;
    chatInputEl.value = '';

    try {
      await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text })
      });
    } catch (e) {
      console.error('Failed to send chat message:', e);
    }
  }

  if (sendBtn) sendBtn.addEventListener('click', handleSend);
  if (chatInputEl) {
    chatInputEl.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        e.preventDefault();
        handleSend();
      }
    });
  }

  // ---------- Quick Launch & Actions ----------

  document.querySelectorAll('.app-icon-wrap').forEach(wrap => {
    wrap.addEventListener('click', () => {
      const label = wrap.querySelector('.app-label')?.textContent?.trim() || '';
      triggerQuickLaunch(label);
    });
  });

  document.querySelectorAll('.qa-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const text = btn.textContent.trim().toLowerCase();
      if (text.includes('terminal')) triggerQuickLaunch('terminal');
      else if (text.includes('file')) triggerQuickLaunch('vscode');
      else if (text.includes('screenshot')) triggerQuickLaunch('screenshot');
      else if (text.includes('note')) triggerQuickLaunch('notepad');
    });
  });

  if (stageAllBtn) {
    stageAllBtn.addEventListener('click', async () => {
      await fetch('/api/tools/execute', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ tool_name: 'git_stage_all' })
      });
      fetchGit();
    });
  }

  if (commitBtn) {
    commitBtn.addEventListener('click', async () => {
      const msg = prompt('Enter commit message:', 'Update workspace files');
      if (msg) {
        await fetch('/api/tools/execute', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            tool_name: 'git_commit',
            parameters: { message: msg },
            user_confirmed: true
          })
        });
        fetchGit();
      }
    });
  }

  function triggerQuickLaunch(action) {
    fetch('/api/quicklaunch/action', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action })
    }).catch(e => console.error('Quick launch error:', e));
  }

  // ==========================================
  // ---------- Embedded Browser Component ----
  // ==========================================

  class EmbeddedBrowser {
    constructor() {
      this.shortcutsView = document.getElementById('browserShortcutsView');
      this.frameView = document.getElementById('browserFrameView');
      this.iframe = document.getElementById('browserFrame');
      this.urlInput = document.getElementById('browserUrlInput');
      this.goBtn = document.getElementById('browserGoBtn');
      this.nativeBtn = document.getElementById('browserNativeBtn');
      this.backBtn = document.getElementById('browserBackBtn');
      this.forwardBtn = document.getElementById('browserForwardBtn');
      this.refreshBtn = document.getElementById('browserRefreshBtn');
      this.homeBtn = document.getElementById('browserHomeBtn');
      this.tabRow = document.getElementById('browserTabRow');
      this.addTabBtn = document.getElementById('browserAddTabBtn');
      this.progress = document.getElementById('browserProgress');

      this.tabs = [
        { id: 'tab-1', title: 'New Tab', url: null, history: [], historyIdx: -1 }
      ];
      this.activeTabId = 'tab-1';

      this._init();
    }

    _init() {
      // Nav buttons
      if (this.goBtn) this.goBtn.addEventListener('click', () => this.navigateFromInput());
      if (this.nativeBtn) this.nativeBtn.addEventListener('click', () => this.launchNative());
      if (this.urlInput) {
        this.urlInput.addEventListener('keydown', (e) => {
          if (e.key === 'Enter') {
            e.preventDefault();
            this.navigateFromInput();
          }
        });
      }

      if (this.backBtn) this.backBtn.addEventListener('click', () => this.goBack());
      if (this.forwardBtn) this.forwardBtn.addEventListener('click', () => this.goForward());
      if (this.refreshBtn) this.refreshBtn.addEventListener('click', () => this.reload());
      if (this.homeBtn) this.homeBtn.addEventListener('click', () => this.showHome());
      if (this.addTabBtn) this.addTabBtn.addEventListener('click', () => this.addTab());

      // Shortcut cards
      document.querySelectorAll('.browser-shortcuts-view .shortcut-card').forEach(card => {
        card.addEventListener('click', () => {
          if (card.id === 'browserAddShortcutBtn') {
            const customUrl = prompt('Enter website URL or documentation link:');
            if (customUrl) this.navigate(customUrl);
          } else {
            const url = card.getAttribute('data-url');
            if (url) {
              const label = card.querySelector('.shortcut-label')?.textContent?.trim();
              this.navigate(url, label);
            }
          }
        });
      });

      // Iframe load listener
      if (this.iframe) {
        this.iframe.addEventListener('load', () => {
          this._hideProgress();
        });
      }

      this._renderTabs();
    }

    getActiveTab() {
      return this.tabs.find(t => t.id === this.activeTabId) || this.tabs[0];
    }

    navigateFromInput() {
      const inputVal = this.urlInput?.value?.trim();
      if (!inputVal) return;
      this.navigate(inputVal);
    }

    navigate(rawTarget, titleHint) {
      let target = rawTarget.trim();
      let title = titleHint || target;

      // Handle search queries and plain text vs domain
      if (!target.startsWith('http://') && !target.startsWith('https://')) {
        if (target.includes('.') && !target.includes(' ')) {
          target = 'https://' + target;
        } else {
          // Regular Google Search
          title = `Google: ${target}`;
          target = `https://www.google.com/search?q=${encodeURIComponent(target)}`;
        }
      }

      // Proxy url to eliminate iframe blocking (X-Frame-Options, CSP)
      const proxyUrl = `/api/browser/proxy?url=${encodeURIComponent(target)}`;

      const tab = this.getActiveTab();
      if (tab.historyIdx === -1 || tab.history[tab.historyIdx] !== target) {
        tab.history = tab.history.slice(0, tab.historyIdx + 1);
        tab.history.push(target);
        tab.historyIdx = tab.history.length - 1;
      }
      tab.url = target;
      tab.title = this._extractHostname(target) || title;

      if (this.urlInput) this.urlInput.value = target;

      this._showProgress();
      this._showFrameView();

      if (this.iframe) {
        this.iframe.src = proxyUrl;
      }

      this._updateNavButtons();
      this._renderTabs();
    }

    async launchNative(targetUrl) {
      let target = (targetUrl || this.urlInput?.value?.trim() || this.getActiveTab()?.url || 'https://www.youtube.com/').trim();
      if (!target.startsWith('http://') && !target.startsWith('https://')) {
        if (target.includes('.') && !target.includes(' ')) {
          target = 'https://' + target;
        } else {
          target = `https://www.google.com/search?q=${encodeURIComponent(target)}`;
        }
      }
      try {
        await fetch('/api/browser/native', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ url: target })
        });
      } catch (err) {
        console.error('Failed to launch native browser window:', err);
      }
    }

    showHome() {
      const tab = this.getActiveTab();
      tab.url = null;
      tab.title = 'New Tab';

      if (this.urlInput) this.urlInput.value = '';
      if (this.iframe) this.iframe.src = 'about:blank';

      this._showShortcutsView();
      this._updateNavButtons();
      this._renderTabs();
    }

    goBack() {
      const tab = this.getActiveTab();
      if (tab.historyIdx > 0) {
        tab.historyIdx--;
        const prevUrl = tab.history[tab.historyIdx];
        this.navigate(prevUrl);
      } else {
        this.showHome();
      }
    }

    goForward() {
      const tab = this.getActiveTab();
      if (tab.historyIdx < tab.history.length - 1) {
        tab.historyIdx++;
        const nextUrl = tab.history[tab.historyIdx];
        this.navigate(nextUrl);
      }
    }

    reload() {
      const tab = this.getActiveTab();
      if (tab.url) {
        this._showProgress();
        if (this.iframe) {
          const currentSrc = this.iframe.src;
          this.iframe.src = 'about:blank';
          setTimeout(() => { this.iframe.src = currentSrc; }, 60);
        }
      }
    }

    addTab(url = null) {
      const newId = `tab-${Date.now()}`;
      this.tabs.push({
        id: newId,
        title: 'New Tab',
        url: url,
        history: url ? [url] : [],
        historyIdx: url ? 0 : -1
      });
      this.switchTab(newId);
    }

    closeTab(tabId, e) {
      if (e) e.stopPropagation();
      if (this.tabs.length <= 1) {
        this.showHome();
        return;
      }
      const idx = this.tabs.findIndex(t => t.id === tabId);
      this.tabs = this.tabs.filter(t => t.id !== tabId);

      if (this.activeTabId === tabId) {
        const nextTab = this.tabs[Math.max(0, idx - 1)];
        this.switchTab(nextTab.id);
      } else {
        this._renderTabs();
      }
    }

    switchTab(tabId) {
      this.activeTabId = tabId;
      const tab = this.getActiveTab();

      if (tab.url) {
        if (this.urlInput) this.urlInput.value = tab.url;
        this._showFrameView();
        const proxyUrl = `/api/browser/proxy?url=${encodeURIComponent(tab.url)}`;
        if (this.iframe && this.iframe.src !== proxyUrl) {
          this.iframe.src = proxyUrl;
        }
      } else {
        if (this.urlInput) this.urlInput.value = '';
        this._showShortcutsView();
      }

      this._updateNavButtons();
      this._renderTabs();
    }

    _showShortcutsView() {
      if (this.shortcutsView) this.shortcutsView.style.display = 'flex';
      if (this.frameView) this.frameView.classList.remove('active');
    }

    _showFrameView() {
      if (this.shortcutsView) this.shortcutsView.style.display = 'none';
      if (this.frameView) this.frameView.classList.add('active');
    }

    _showProgress() {
      if (this.progress) this.progress.style.display = 'block';
    }

    _hideProgress() {
      if (this.progress) this.progress.style.display = 'none';
    }

    _updateNavButtons() {
      const tab = this.getActiveTab();
      if (this.backBtn) this.backBtn.disabled = (tab.historyIdx <= 0 && !tab.url);
      if (this.forwardBtn) this.forwardBtn.disabled = (tab.historyIdx >= tab.history.length - 1);
    }

    _extractHostname(url) {
      try {
        const u = new URL(url);
        return u.hostname.replace('www.', '');
      } catch {
        return null;
      }
    }

    _renderTabs() {
      if (!this.tabRow) return;
      const tabsHtml = this.tabs.map(t => {
        const isActive = t.id === this.activeTabId;
        return `
          <div class="tab ${isActive ? 'active' : ''}" data-tab-id="${t.id}">
            <span class="tab-dot"></span>
            <span class="tab-title">${escapeHtml(t.title || 'New Tab')}</span>
            ${this.tabs.length > 1 ? `<span class="tab-close" data-close-id="${t.id}">&times;</span>` : ''}
          </div>
        `;
      }).join('');

      this.tabRow.innerHTML = `
        ${tabsHtml}
        <div class="tab-add" id="browserAddTabBtn" title="New Tab">
          <svg viewBox="0 0 24 24" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
        </div>
      `;

      // Rebind tab clicks
      this.tabRow.querySelectorAll('.tab').forEach(el => {
        el.addEventListener('click', () => {
          const id = el.getAttribute('data-tab-id');
          if (id) this.switchTab(id);
        });
      });

      this.tabRow.querySelectorAll('.tab-close').forEach(btn => {
        btn.addEventListener('click', (e) => {
          const id = btn.getAttribute('data-close-id');
          if (id) this.closeTab(id, e);
        });
      });

      const newAddBtn = document.getElementById('browserAddTabBtn');
      if (newAddBtn) {
        newAddBtn.addEventListener('click', () => this.addTab());
      }
    }
  }

  // Initialize browser controller
  window.browserController = new EmbeddedBrowser();

  // Helper for opening links directly into the browser panel
  window.openInAssistantBrowser = function(url, title) {
    if (window.browserController) {
      window.browserController.navigate(url, title);
    }
  };

  async function fetchInitialData() {
    try {
      const [statusRes, winRes, gitRes, chatRes] = await Promise.all([
        fetch('/api/status').then(r => r.json()),
        fetch('/api/windows').then(r => r.json()),
        fetch('/api/git').then(r => r.json()),
        fetch('/api/chat/history').then(r => r.json())
      ]);

      if (statusRes) orb.updateState(statusRes);
      if (winRes && winRes.windows) renderActiveWindows(winRes.windows);
      if (gitRes) renderGitStatus(gitRes);
      if (chatRes && chatRes.messages) renderChatHistory(chatRes.messages);
    } catch (err) {
      console.debug('Initial HTTP fetch:', err);
    }
  }

  async function fetchGit() {
    try {
      const git = await fetch('/api/git').then(r => r.json());
      renderGitStatus(git);
    } catch (e) {}
  }

  // Helpers
  function getAppBgClass(category, pname) {
    const p = (pname || '').toLowerCase();
    if (p.includes('code') || p.includes('devenv')) return 'bg-vscode';
    if (p.includes('wt') || p.includes('powershell') || p.includes('cmd')) return 'bg-terminal';
    if (p.includes('godot')) return 'bg-godot';
    if (p.includes('unreal')) return 'bg-unreal';
    if (category === 'Engine') return 'bg-zegfx';
    return 'bg-files';
  }

  function getWindowIcon(cat) {
    if (cat === 'Code') {
      return '<svg viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M17 3 7 12l10 9 3-1.5V4.5L17 3Z"/><path d="M7 12 3 9v6l4-3Z"/></svg>';
    }
    if (cat === 'Terminal') {
      return '<svg viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="4 6 9 12 4 18"/><line x1="12" y1="18" x2="20" y2="18"/></svg>';
    }
    if (cat === 'Engine') {
      return '<svg viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="1.8"><circle cx="12" cy="12" r="8.5"/><path d="M6 13c1-3 2.5-5 3.5-5s.7 3 1 5 1 5 1.8 5S14 15 15 12s2-4.2 3-4" stroke-linecap="round"/></svg>';
    }
    return '<svg viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M3 7a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V7Z"/></svg>';
  }

  function escapeHtml(str) {
    if (!str) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  window.openPath = function(path) {
    fetch('/api/tools/execute', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ tool_name: 'open_folder', parameters: { path: path } })
    });
  };
});
