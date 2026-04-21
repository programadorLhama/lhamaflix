const API_BASE = ""; 
const ITEMS_PER_PAGE = 9;
let allVideos = [];
let currentPage = 1;
let hlsInstance = null;
let mediaRecoveryAttempts = 0;
let networkRecoveryAttempts = 0;

// ... Elementos do DOM (mantidos)
const movieGrid = document.getElementById('movie-grid');
const pagination = document.getElementById('pagination');
const catalogView = document.getElementById('catalog-view');
const playerView = document.getElementById('player-view');
const videoPlayer = document.getElementById('video-player');
const playingTitle = document.getElementById('playing-title');
const backButton = document.getElementById('back-button');

async function tryStartPlayback() {
    try {
        await videoPlayer.play();
        return;
    } catch (error) {
        console.warn("Autoplay padrão falhou, tentando modo muted:", error);
    }

    try {
        videoPlayer.muted = true;
        await videoPlayer.play();
    } catch (error) {
        console.warn("Falha ao iniciar reprodução:", error);
    }
}

// --- Inicialização do Google Cast ---
window.__onGCastApiAvailable = function(isAvailable) {
    if (isAvailable) {
        initializeCastApi();
    }
};

function initializeCastApi() {
    cast.framework.CastContext.getInstance().setOptions({
        receiverApplicationId: chrome.cast.media.DEFAULT_MEDIA_RECEIVER_APP_ID,
        autoJoinPolicy: chrome.cast.AutoJoinPolicy.ORIGIN_SCOPED
    });
}

// ... Funções init() e renderGrid() (mantidas do código anterior)
async function init() {
    try {
        const response = await fetch(`${API_BASE}/api/videos/hls`);
        const data = await response.json();
        allVideos = data.videos || [];
        renderGrid();
    } catch (error) {
        console.error("Erro:", error);
    }
}

function renderGrid() {
    movieGrid.innerHTML = "";
    const start = (currentPage - 1) * ITEMS_PER_PAGE;
    const end = start + ITEMS_PER_PAGE;
    const pageItems = allVideos.slice(start, end);

    pageItems.forEach(video => {
        const folderPath = video.playlist_url.substring(0, video.playlist_url.lastIndexOf('/'));
        const posterUrl = `${folderPath}/poster.jpg`;

        const card = document.createElement('div');
        card.className = 'movie-card';
        card.innerHTML = `
            <div class="card-header"><span class="card-title">${video.title}</span></div>
            <div class="card-thumb" style="background-image: url('${posterUrl}');">
                <div class="play-overlay"><span>▶</span></div>
            </div>
        `;
        card.onclick = () => openPlayer(video);
        movieGrid.appendChild(card);
    });
    renderPagination();
}

function renderPagination() {
    pagination.innerHTML = "";
    const totalPages = Math.ceil(allVideos.length / ITEMS_PER_PAGE);
    if (totalPages <= 1) return;
    for (let i = 1; i <= totalPages; i++) {
        const btn = document.createElement('button');
        btn.innerText = i;
        btn.className = `page-btn ${i === currentPage ? 'active' : ''}`;
        btn.onclick = (e) => {
            e.stopPropagation();
            currentPage = i;
            renderGrid();
            window.scrollTo({top: 0, behavior: 'smooth'});
        };
        pagination.appendChild(btn);
    }
}

function openPlayer(video) {
    catalogView.classList.add('hidden');
    playerView.classList.remove('hidden');
    window.scrollTo(0, 0);

    if (hlsInstance) {
        hlsInstance.destroy();
        hlsInstance = null;
    }
    mediaRecoveryAttempts = 0;
    networkRecoveryAttempts = 0;
    videoPlayer.pause();
    videoPlayer.removeAttribute("src");
    videoPlayer.load();

    // Evita playlist stale em cache quando um HLS acabou de ser regenerado.
    const playlistUrl = `${video.playlist_url}${video.playlist_url.includes("?") ? "&" : "?"}t=${Date.now()}`;

    // No mobile, o navegador Safari/Chrome detecta o HLS e oferece o Cast nativo no player
    if (Hls.isSupported()) {
        hlsInstance = new Hls();
        hlsInstance.attachMedia(videoPlayer);
        hlsInstance.on(Hls.Events.MEDIA_ATTACHED, () => {
            hlsInstance.loadSource(playlistUrl);
        });
        hlsInstance.on(Hls.Events.MANIFEST_PARSED, () => {
            tryStartPlayback();
        });
        hlsInstance.on(Hls.Events.ERROR, (_event, data) => {
            console.error("Erro no HLS:", data);
            if (data.fatal) {
                if (data.type === Hls.ErrorTypes.NETWORK_ERROR) {
                    networkRecoveryAttempts += 1;
                    if (networkRecoveryAttempts <= 2) {
                        hlsInstance.startLoad();
                    } else {
                        console.error("Falha de rede HLS persistente; encerrando player.");
                        hlsInstance.destroy();
                        hlsInstance = null;
                    }
                } else if (data.type === Hls.ErrorTypes.MEDIA_ERROR) {
                    mediaRecoveryAttempts += 1;
                    if (data.details === Hls.ErrorDetails.BUFFER_APPEND_ERROR && mediaRecoveryAttempts === 1) {
                        hlsInstance.swapAudioCodec();
                    }
                    if (mediaRecoveryAttempts <= 2) {
                        hlsInstance.recoverMediaError();
                    } else {
                        console.error("Falha de mídia HLS persistente; encerrando player.");
                        hlsInstance.destroy();
                        hlsInstance = null;
                    }
                } else {
                    hlsInstance.destroy();
                    hlsInstance = null;
                }
            }
        });
    } else if (videoPlayer.canPlayType('application/vnd.apple.mpegurl')) {
        videoPlayer.src = playlistUrl;
        tryStartPlayback();
    }
}

backButton.onclick = () => {
    if (hlsInstance) {
        hlsInstance.destroy();
        hlsInstance = null;
    }
    videoPlayer.pause();
    videoPlayer.removeAttribute("src");
    videoPlayer.load();
    playerView.classList.add('hidden');
    catalogView.classList.remove('hidden');
};

init();
