/**
 * Shopping Adventure — postMessage Adapter Bridge
 * Connects the 3D Supermarket Adventure iframe with the SkillSpark learning platform.
 */

(function() {
  'use strict';

  const GAME_ID = 'shopping-adventure';
  let sessionId = null;
  let startTime = null;

  function sendToParent(data) {
    try {
      window.parent.postMessage({ ...data, gameId: GAME_ID }, '*');
    } catch (e) {
      console.warn('[Adapter] Failed to send message to parent:', e);
    }
  }

  // Listen for messages from parent
  window.addEventListener('message', function(event) {
    const data = event.data;
    if (!data || !data.type) return;

    switch (data.type) {
      case 'session:start':
        sessionId = data.sessionId;
        startTime = Date.now();
        console.log('[Adapter] Session started:', sessionId);
        break;
      case 'session:pause':
        console.log('[Adapter] Session paused');
        break;
      case 'session:resume':
        console.log('[Adapter] Session resumed');
        break;
      case 'session:stop':
        console.log('[Adapter] Session stopped by parent');
        break;
    }
  });

  // Signal ready
  sendToParent({ type: 'game:ready' });

  // Auto-detect game start
  let hasStarted = false;
  const checkStart = setInterval(function() {
    const canvas = document.querySelector('canvas');
    if (canvas && !hasStarted) {
      hasStarted = true;
      startTime = startTime || Date.now();
      sendToParent({
        type: 'game:started',
        difficulty: (window.list && window.list.level) || 'easy',
        timestamp: new Date().toISOString(),
      });
      clearInterval(checkStart);
    }
  }, 500);

  // Detect game completion by watching for receipt / summary screen
  let hasCompleted = false;
  const checkComplete = setInterval(function() {
    if (hasCompleted) return;

    const summaryEl = document.getElementById('summary');
    const isSummaryVisible = summaryEl && !summaryEl.classList.contains('hide');
    const allText = document.body ? document.body.innerText : '';

    if (isSummaryVisible || allText.includes('Shopping Adventure Completed') || allText.includes('Shopping Complete')) {
      hasCompleted = true;
      const duration = startTime ? Math.round((Date.now() - startTime) / 1000) : 60;
      const tracker = window.tracker || {};
      const wrongPick = tracker.wrongPick || 0;
      const wrongTalk = tracker.wrongTalk || 0;
      const talkOk = tracker.talkOk || 2;
      const talkTotal = tracker.talkTotal || 2;
      const score = Math.max(20, 100 - (wrongPick * 15) - (wrongTalk * 10));

      sendToParent({
        type: 'game:completed',
        metrics: {
          score: score,
          duration_seconds: duration,
          completed: true,
          wrong_picks: wrongPick,
          wrong_talk: wrongTalk,
          talk_ok: talkOk,
          talk_total: talkTotal,
          items_collected: (window.basket && typeof window.basket.count === 'function') ? window.basket.count() : 4,
          accuracy_pct: Math.round(Math.max(30, 100 - wrongPick * 20)),
          social_score: Math.round(talkTotal > 0 ? (talkOk / talkTotal) * 100 : 100),
        },
        duration: duration,
      });
      clearInterval(checkComplete);
    }
  }, 1000);

  console.log('[Adapter] Shopping Adventure / Supermarket Adventure bridge ready');
})();
