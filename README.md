# Lhamaflix - Streaming HLS com FastAPI

Sistema de streaming de videos com backend em FastAPI e frontend estatico, focado em converter arquivos `.mp4` e `.mkv` para HLS (`.m3u8` + segmentos `.ts`) e reproduzir no navegador.

## Visao geral do sistema

- Backend:
  - API REST em FastAPI para listar videos, iniciar conversao HLS e consultar status.
  - Banco SQLite para registrar estado dos jobs de conversao.
  - Exposicao de arquivos HLS via rota estatica `/hls`.
- Frontend:
  - Interface em `static/` com catalogo de filmes em cards.
  - Consome a API em `/api/videos/hls` para montar o catalogo.
  - Reproduz HLS com `hls.js` (ou suporte nativo do navegador).

## Estrutura de pastas principal

- `videos/`: entrada dos arquivos fonte `.mp4` e `.mkv`.
- `hls/`: saida da transcodificacao HLS.
  - Exemplo: `hls/Meu_Filme/playlist.m3u8` e `segment_001.ts`.
- `static/`: frontend (HTML, CSS, JS).
- `data/`: banco SQLite (`app.db`).
- `app/`: codigo backend (rotas, controllers, models, configuracoes).

## Fluxo completo: da pasta `videos` ate assistir

1. Adicione um arquivo `.mp4` ou `.mkv` em `videos/`.
   - Exemplo: `videos/filme_teste.mp4` ou `videos/filme_teste.mkv`.
2. O sistema reconhece esse arquivo pela rota de fontes:
   - `GET /api/videos/sources`
3. Inicie a geracao HLS para o video:
   - `POST /api/videos/filme_teste/hls`
4. O backend executa `ffmpeg` e cria os arquivos em:
   - `hls/filme_teste/playlist.m3u8`
   - `hls/filme_teste/segment_*.ts`
5. Opcionalmente consulte o status:
   - `GET /api/videos/filme_teste/hls/status`
6. Quando o HLS estiver pronto, o catalogo aparece em:
   - `GET /api/videos/hls`
7. Abra a aplicacao no navegador (`/`) e clique no card do filme.
8. O player carrega `playlist_url` (ex.: `/hls/filme_teste/playlist.m3u8`) e inicia a reproducao.

## Como executar

## Requisitos

- Python 3.10+ (recomendado)
- `ffmpeg` instalado e disponivel no PATH

## Execucao local

1. Instale dependencias:
   - `pip install -r requirements.txt`
2. Suba a API:
   - `python3 run.py`
3. Acesse no navegador:
   - `http://localhost:8001/`

Observacao: ao iniciar, a aplicacao cria automaticamente as pastas configuradas e o banco SQLite, se nao existirem.

## Variaveis de ambiente (opcionais)

- `VIDEOS_DIR` (padrao: `./videos`)
- `HLS_DIR` (padrao: `./hls`)
- `STATIC_DIR` (padrao: `./static`)
- `DB_PATH` (padrao: `./data/app.db`)
- `FFMPEG_BIN` (padrao: `ffmpeg`)
- `HOST` (padrao: `0.0.0.0`)
- `PORT` (padrao: `8001`)
- `RELOAD` (padrao: `true`)

## Rotas do sistema

## Rotas da API

Base da API: `/api`

- `GET /api/health`
  - Health check da aplicacao.

- `GET /api/videos`
  - Lista videos HLS prontos (equivalente ao catalogo principal).

- `GET /api/videos/hls`
  - Lista videos HLS prontos para o frontend.
  - Retorna itens com `id`, `title` e `playlist_url`.

- `GET /api/videos/sources`
  - Lista arquivos `.mp4` e `.mkv` encontrados na pasta de origem (`videos/`).

- `POST /api/videos/{video_id}/hls`
  - Gera HLS para o video indicado (`{video_id}.mp4` ou `{video_id}.mkv`).
  - Se `playlist.m3u8` ja existir, retorna pronto sem reconverter.

- `GET /api/videos/{video_id}/hls/status`
  - Consulta status do job no SQLite e existencia da playlist.
  - Estados tipicos: `none`, `processing`, `ready`, `error`.

## Rotas estaticas

- `GET /`
  - Serve a interface web de `static/index.html`.

- `GET /hls/{video_id}/playlist.m3u8`
  - Entrega a playlist HLS.

- `GET /hls/{video_id}/segment_*.ts`
  - Entrega os segmentos de video HLS.

## Funcionamento interno (resumo tecnico)

- Validacao de `video_id`:
  - Permitido apenas padrao seguro (`a-z`, `A-Z`, `0-9`, `.`, `_`, `-`).
- Conversao HLS:
  - Codec de video: `libx264`
  - Codec de audio: `aac`
  - Segmentacao: `6s`
  - Modo playlist: `vod`
- Persistencia:
  - Tabela `video_jobs` guarda status e mensagens de erro.
- Frontend:
  - Renderiza cards com poster (`poster.jpg` dentro da pasta do HLS, quando existir).
  - Reproducao via `hls.js` com fallback nativo para navegadores compativeis.

## Exemplo rapido com cURL

1. Listar fontes:
   - `curl http://localhost:8001/api/videos/sources`
2. Gerar HLS:
   - `curl -X POST http://localhost:8001/api/videos/filme_teste/hls`
3. Ver status:
   - `curl http://localhost:8001/api/videos/filme_teste/hls/status`
4. Listar catalogo:
   - `curl http://localhost:8001/api/videos/hls`

## Observação final

Caso queira alterar o arquivo de mkv para .mp4:
    - `ffmpeg -i input.mkv -c copy output.mp4`
