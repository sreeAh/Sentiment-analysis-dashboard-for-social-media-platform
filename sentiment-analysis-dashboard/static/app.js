const $ = (selector) => document.querySelector(selector);
const platformFilter = $('#platform-filter');
const sentimentFilter = $('#sentiment-filter');

function relativeTime(post) {
  if (post.minutes_ago === 0) return 'Just now';
  if (post.minutes_ago < 60) return `${post.minutes_ago}m ago`;
  const hours = Math.floor(post.minutes_ago / 60);
  return hours < 24 ? `${hours}h ago` : `${Math.floor(hours / 24)}d ago`;
}

function platformIcon(platform) {
  const icons = { X: '𝕏', Instagram: '◎', Reddit: '◉', TikTok: '♪' };
  return icons[platform] || '•';
}

function renderPosts(posts) {
  const tbody = $('#posts-table');
  tbody.innerHTML = posts.slice(0, 7).map((post) => `
    <tr><td><div class="post-cell"><div class="post-avatar avatar-${post.id % 5}">${escapeHtml(post.author.replace(/^[@u/]+/, '').slice(0, 2).toUpperCase())}</div><div class="post-copy"><strong>${escapeHtml(post.author)}</strong><span>${escapeHtml(post.text)}</span></div></div></td>
      <td><span class="platform-name"><i class="platform-mark mark-${post.platform.toLowerCase()}">${platformIcon(post.platform)}</i>${escapeHtml(post.platform)}</span></td>
      <td><span class="sentiment-badge ${post.sentiment.toLowerCase()}"><i></i>${post.sentiment}</span></td><td class="time-cell">${relativeTime(post)}</td><td><button class="row-more" aria-label="More post options">···</button></td></tr>`).join('');
  $('#empty-state').hidden = posts.length > 0;
}

function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, (character) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[character]);
}

function render(data) {
  $('#total-stat').textContent = data.total.toLocaleString();
  $('#positive-stat').innerHTML = `${data.positive_rate}<small>%</small>`;
  $('#neutral-stat').textContent = data.neutral.toLocaleString();
  $('#negative-stat').textContent = data.negative.toLocaleString();
  $('#live-count').textContent = data.all_posts;
  $('#donut-total').textContent = data.total.toLocaleString();
  $('#breakdown-positive').textContent = data.positive;
  $('#breakdown-neutral').textContent = data.neutral;
  $('#breakdown-negative').textContent = data.negative;
  const total = Math.max(data.positive + data.neutral + data.negative, 1);
  const positive = data.positive / total * 100;
  const neutral = data.neutral / total * 100;
  $('#donut-chart').style.background = `conic-gradient(#7169e8 0% ${positive}%, #f1b84c ${positive}% ${positive + neutral}%, #f07972 ${positive + neutral}% 100%)`;
  const known = new Set([...platformFilter.options].map((option) => option.value));
  data.platforms.forEach((platform) => {
    if (!known.has(platform)) platformFilter.add(new Option(platform, platform));
  });
  renderPosts(data.posts);
}

async function loadData() {
  const params = new URLSearchParams({ platform: platformFilter.value, sentiment: sentimentFilter.value });
  const response = await fetch(`/api/summary?${params}`);
  render(await response.json());
}

platformFilter.addEventListener('change', loadData);
sentimentFilter.addEventListener('change', loadData);
$('#refresh-button').addEventListener('click', (event) => {
  const button = event.currentTarget;
  button.classList.add('spinning');
  loadData().finally(() => setTimeout(() => button.classList.remove('spinning'), 450));
});
$('#export-button').addEventListener('click', () => {
  const params = new URLSearchParams({ platform: platformFilter.value, sentiment: sentimentFilter.value });
  window.location.href = `/api/export.csv?${params}`;
});
$('#analyzer-form').addEventListener('submit', async (event) => {
  event.preventDefault();
  const button = event.currentTarget.querySelector('button[type="submit"]');
  const text = $('#post-text').value.trim();
  if (!text) return;
  button.disabled = true;
  button.innerHTML = 'Analyzing…';
  try {
    const response = await fetch('/api/analyze', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text, platform: $('#analyzer-platform').value, author: '@you' }),
    });
    const result = await response.json();
    if (!response.ok) throw new Error(result.error || 'Could not analyze this post.');
    const post = result.post;
    $('#analysis-result').innerHTML = `<span class="sentiment-badge ${post.sentiment.toLowerCase()}"><i></i>${post.sentiment}</span><span>Keyword score: <strong>${post.score > 0 ? '+' : ''}${post.score}</strong></span><span class="result-added">Added to recent mentions</span>`;
    $('#post-text').value = '';
    platformFilter.value = 'All'; sentimentFilter.value = 'All';
    render(result.summary);
  } catch (error) {
    $('#analysis-result').textContent = error.message;
  } finally {
    button.disabled = false;
    button.innerHTML = 'Analyze post <span>↗</span>';
  }
});

loadData();
