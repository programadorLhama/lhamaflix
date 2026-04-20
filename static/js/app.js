/**
 * Player HLS para o vídeo Corrente_do_Mal (videos/Corrente_do_Mal.mp4).
 * Usa a mesma origem que a página (ex.: http://localhost:8001).
 */
const VIDEO_ID = "Corrente_do_Mal";

const statusEl = document.getElementById("status");
const btnPrepare = document.getElementById("btnPrepare");
const btnPlay = document.getElementById("btnPlay");
const videoEl = document.getElementById("video");

let hlsInstance = null;
let playlistUrl = "";

function setStatus(text, variant) {
  statusEl.textContent = text;
  statusEl.classList.remove("is-error", "is-ok");
  if (variant === "error") statusEl.classList.add("is-error");
  if (variant === "ok") statusEl.classList.add("is-ok");
}

function destroyHls() {
  if (hlsInstance) {
    hlsInstance.destroy();
    hlsInstance = null;
  }
}

function attachNative(src) {
  destroyHls();
  videoEl.src = src;
}

function attachHlsJs(src) {
  destroyHls();
  if (typeof Hls === "undefined" || !Hls.isSupported()) {
    setStatus("hls.js não está disponível neste browser.", "error");
    return;
  }
  hlsInstance = new Hls({
    enableWorker: true,
    lowLatencyMode: false,
  });
  hlsInstance.loadSource(src);
  hlsInstance.attachMedia(videoEl);
  hlsInstance.on(Hls.Events.MANIFEST_PARSED, () => {
    setStatus("Manifesto carregado. Pode reproduzir.", "ok");
  });
  hlsInstance.on(Hls.Events.ERROR, (_, data) => {
    if (data.fatal) {
      setStatus(`Erro HLS: ${data.type} — ${data.details}`, "error");
    }
  });
}

function loadPlaylist() {
  const src = playlistUrl.startsWith("http") ? playlistUrl : `${window.location.origin}${playlistUrl}`;

  if (videoEl.canPlayType("application/vnd.apple.mpegurl")) {
    setStatus("A usar reprodução HLS nativa.", "ok");
    attachNative(src);
    return;
  }

  setStatus("A usar hls.js para reprodução.", "ok");
  attachHlsJs(src);
}

async function prepareHls() {
  btnPrepare.disabled = true;
  btnPlay.disabled = true;
  setStatus("A gerar HLS (pode demorar)…");

  try {
    const res = await fetch(`/api/videos/${encodeURIComponent(VIDEO_ID)}/hls`, {
      method: "POST",
    });
    const body = await res.json().catch(() => ({}));

    if (!res.ok) {
      const detail = body.detail ?? JSON.stringify(body);
      throw new Error(typeof detail === "string" ? detail : "Pedido falhou");
    }

    if (!body.playlist_url) {
      throw new Error("Resposta sem playlist_url.");
    }

    playlistUrl = body.playlist_url;
    setStatus(body.message || "HLS pronto.", "ok");
    btnPlay.disabled = false;
  } catch (e) {
    setStatus(e.message || String(e), "error");
  } finally {
    btnPrepare.disabled = false;
  }
}

function play() {
  if (!playlistUrl) {
    setStatus("Prepare o HLS primeiro.", "error");
    return;
  }
  loadPlaylist();
  videoEl.play().catch(() => {
    setStatus("Reprodução bloqueada pelo browser (interaja com a página).", "error");
  });
}

btnPrepare.addEventListener("click", () => {
  void prepareHls();
});

btnPlay.addEventListener("click", () => {
  play();
});
