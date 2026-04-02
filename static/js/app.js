const videoUrl = document.getElementById('videoUrl');
const platform = document.getElementById('platform');
const aiModel = document.getElementById('aiModel');
const processBtn = document.getElementById('processBtn');
const progressSection = document.getElementById('progressSection');
const progressFill = document.getElementById('progressFill');
const progressPercent = document.getElementById('progressPercent');
const statusText = document.getElementById('statusText');
const resultsSection = document.getElementById('resultsSection');
const clipsList = document.getElementById('clipsList');
const momentsSection = document.getElementById('momentsSection');
const momentsList = document.getElementById('momentsList');
const configToggle = document.getElementById('configToggle');
const configContent = document.getElementById('configContent');
const openaiKey = document.getElementById('openaiKey');
const saveConfig = document.getElementById('saveConfig');

let currentJobId = null;
let pollInterval = null;

configToggle.addEventListener('click', () => {
    configContent.style.display = configContent.style.display === 'none' ? 'block' : 'none';
});

saveConfig.addEventListener('click', async () => {
    await fetch('/api/config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ openai_key: openaiKey.value })
    });
    alert('Settings saved!');
});

async function loadConfig() {
    try {
        const res = await fetch('/api/config');
        const config = await res.json();
        if (config.openai_key) {
            openaiKey.value = config.openai_key;
        }
    } catch (e) {
        console.log('No config found');
    }
}

processBtn.addEventListener('click', async () => {
    if (!videoUrl.value) {
        alert('Please enter a YouTube URL');
        return;
    }

    const useLocal = aiModel.value === 'local';
    
    processBtn.disabled = true;
    processBtn.querySelector('.btn-text').style.display = 'none';
    processBtn.querySelector('.btn-loading').style.display = 'flex';
    
    progressSection.style.display = 'block';
    resultsSection.style.display = 'none';
    momentsSection.style.display = 'none';
    
    try {
        const res = await fetch('/api/process', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                video_url: videoUrl.value,
                platform: platform.value,
                use_local: useLocal
            })
        });
        
        const data = await res.json();
        currentJobId = data.job_id;
        
        startPolling();
    } catch (e) {
        alert('Error starting process: ' + e.message);
        resetUI();
    }
});

function startPolling() {
    pollInterval = setInterval(checkStatus, 2000);
}

function checkStatus() {
    if (!currentJobId) return;
    
    fetch(`/api/status/${currentJobId}`)
        .then(res => res.json())
        .then(job => {
            progressFill.style.width = job.progress + '%';
            progressPercent.textContent = job.progress + '%';
            
            const statusMessages = {
                'queued': 'Waiting to start...',
                'downloading': 'Downloading video...',
                'transcribing': 'Transcribing audio...',
                'extracting_moments': 'Finding key moments...',
                'clipping': 'Creating clips...',
                'completed': 'Processing complete!',
                'error': 'Error: ' + (job.error || 'Unknown error')
            };
            
            statusText.textContent = statusMessages[job.status] || job.status;
            
            if (job.status === 'completed') {
                stopPolling();
                showResults(job);
            } else if (job.status === 'error') {
                stopPolling();
                alert('Error: ' + (job.error || 'Unknown error'));
                resetUI();
            }
        })
        .catch(e => {
            console.error('Polling error:', e);
        });
}

function stopPolling() {
    if (pollInterval) {
        clearInterval(pollInterval);
        pollInterval = null;
    }
}

function showResults(job) {
    resetUI();
    
    if (job.moments && job.moments.length > 0) {
        momentsSection.style.display = 'block';
        momentsList.innerHTML = job.moments.map(m => `
            <div class="moment-item">
                <div class="moment-time">${formatTime(m.start)}</div>
                <div class="moment-text">${m.title}</div>
            </div>
        `).join('');
    }
    
    if (job.clips && job.clips.length > 0) {
        resultsSection.style.display = 'block';
        
        const clipsByIndex = {};
        job.clips.forEach(clip => {
            if (!clipsByIndex[clip.index]) {
                clipsByIndex[clip.index] = {
                    title: clip.title,
                    start: clip.start,
                    end: clip.end,
                    platforms: []
                };
            }
            clipsByIndex[clip.index].platforms.push({
                name: clip.platform,
                path: clip.path
            });
        });
        
        clipsList.innerHTML = Object.values(clipsByIndex).map((clip, i) => `
            <div class="clip-card">
                <div class="clip-header">
                    <div class="clip-title">Clip ${i + 1}: ${clip.title}</div>
                    <div class="clip-time">${formatTime(clip.start)} - ${formatTime(clip.end)}</div>
                </div>
                <div class="clip-downloads">
                    ${clip.platforms.map(p => `
                        <a href="/api/download/${currentJobId}/${job.clips.find(c => c.platform === p.name && c.index === i)?.index || 0}?platform=${p.name}" 
                           class="download-btn" download>
                            Download ${formatPlatform(p.name)}
                        </a>
                    `).join('')}
                </div>
            </div>
        `).join('');
    }
}

function formatTime(seconds) {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
}

function formatPlatform(platform) {
    const names = {
        'youtube': 'YouTube (16:9)',
        'youtube_shorts': 'YouTube Shorts',
        'instagram_reels': 'Instagram Reels',
        'instagram_stories': 'Instagram Stories',
        'facebook': 'Facebook',
        'tiktok': 'TikTok'
    };
    return names[platform] || platform;
}

function resetUI() {
    processBtn.disabled = false;
    processBtn.querySelector('.btn-text').style.display = 'flex';
    processBtn.querySelector('.btn-loading').style.display = 'none';
}

loadConfig();
