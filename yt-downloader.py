import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import yt_dlp
import threading
import queue
import os
import json

# ─── Configurações persistentes ───────────────────────────────────────────────
CONFIG_FILE = "yt_downloader_config.json"

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
        except:
            pass
    return {"download_path": os.path.join(os.path.expanduser("~"), "Downloads")}

def save_config(cfg):
    with open(CONFIG_FILE, "w") as f:
        json.dump(cfg, f)

config = load_config()

# ─── Estado global ─────────────────────────────────────────────────────────────
log_queue = queue.Queue()
is_running = False
video_info = None
available_formats = []

# ══════════════════════════════════════════════════════════════════════════════
# CORES & FONTES
# ══════════════════════════════════════════════════════════════════════════════
BG        = "#0D0D0D"
CARD      = "#141414"
CARD2     = "#1A1A1A"
BORDER    = "#2A2A2A"
ACCENT    = "#FF0033"      # vermelho YouTube
ACCENT2   = "#FF4D6A"
TEXT      = "#F0F0F0"
SUBTEXT   = "#888888"
SUCCESS   = "#00C896"
WARNING   = "#FFB347"
DANGER    = "#FF4444"
FONT_MAIN = ("Segoe UI", 10)
FONT_BOLD = ("Segoe UI", 10, "bold")
FONT_LG   = ("Segoe UI", 13, "bold")
FONT_XL   = ("Segoe UI", 18, "bold")
FONT_MONO = ("Consolas", 9)

# ══════════════════════════════════════════════════════════════════════════════
# JANELA PRINCIPAL
# ══════════════════════════════════════════════════════════════════════════════
root = tk.Tk()
root.title("YT Downloader")
root.geometry("760x820")
root.minsize(720, 700)
root.configure(bg=BG)

# Centralizar
root.update_idletasks()
x = (root.winfo_screenwidth()  - 760) // 2
y = (root.winfo_screenheight() - 820) // 2
root.geometry(f"760x820+{x}+{y}")

# ══════════════════════════════════════════════════════════════════════════════
# HELPERS DE WIDGET
# ══════════════════════════════════════════════════════════════════════════════
def card(parent, **kw):
    return tk.Frame(parent, bg=CARD, **kw)

def label(parent, text, font=FONT_MAIN, fg=TEXT, **kw):
    return tk.Label(parent, text=text, font=font, fg=fg, bg=parent["bg"], **kw)

def sep(parent):
    return tk.Frame(parent, bg=BORDER, height=1)

# ══════════════════════════════════════════════════════════════════════════════
# SCROLL CANVAS PRINCIPAL
# ══════════════════════════════════════════════════════════════════════════════
outer = tk.Frame(root, bg=BG)
outer.pack(fill=tk.BOTH, expand=True)

canvas = tk.Canvas(outer, bg=BG, highlightthickness=0)
scrollbar = tk.Scrollbar(outer, orient="vertical", command=canvas.yview)
canvas.configure(yscrollcommand=scrollbar.set)

scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

scroll_frame = tk.Frame(canvas, bg=BG)
scroll_window = canvas.create_window((0, 0), window=scroll_frame, anchor="nw")

def on_frame_configure(e):
    canvas.configure(scrollregion=canvas.bbox("all"))

def on_canvas_configure(e):
    canvas.itemconfig(scroll_window, width=e.width)

scroll_frame.bind("<Configure>", on_frame_configure)
canvas.bind("<Configure>", on_canvas_configure)
canvas.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(-1*(e.delta//120), "units"))

# ══════════════════════════════════════════════════════════════════════════════
# CABEÇALHO
# ══════════════════════════════════════════════════════════════════════════════
header = tk.Frame(scroll_frame, bg=BG, pady=20)
header.pack(fill=tk.X, padx=30)

# Logo + título
logo_row = tk.Frame(header, bg=BG)
logo_row.pack(fill=tk.X)

logo_box = tk.Frame(logo_row, bg=ACCENT, width=38, height=28)
logo_box.pack(side=tk.LEFT, anchor="center")
logo_box.pack_propagate(False)
tk.Label(logo_box, text="▶", font=("Segoe UI", 14, "bold"), fg="white", bg=ACCENT).place(relx=.5, rely=.5, anchor="center")

tk.Frame(logo_row, bg=BG, width=10).pack(side=tk.LEFT)
label(logo_row, "YT Downloader", font=FONT_XL, fg=TEXT).pack(side=tk.LEFT, anchor="center")

# Botão ⚙ settings — canto direito
btn_settings = tk.Button(logo_row, text="⚙  Configurações", font=FONT_MAIN,
                          bg=CARD2, fg=SUBTEXT, relief="flat", cursor="hand2",
                          activebackground=BORDER, activeforeground=TEXT,
                          padx=12, pady=6, bd=0)
btn_settings.pack(side=tk.RIGHT, anchor="center")

label(header, "Baixe vídeos, áudios e legendas do YouTube com facilidade",
      fg=SUBTEXT).pack(anchor=tk.W, pady=(4, 0))

# ══════════════════════════════════════════════════════════════════════════════
# SEÇÃO 1 — URL
# ══════════════════════════════════════════════════════════════════════════════
sec_url = card(scroll_frame)
sec_url.pack(fill=tk.X, padx=30, pady=(0, 12))

inner_url = tk.Frame(sec_url, bg=CARD, padx=20, pady=18)
inner_url.pack(fill=tk.X)

label(inner_url, "URL do Vídeo", font=FONT_BOLD, fg=SUBTEXT).pack(anchor=tk.W)

url_row = tk.Frame(inner_url, bg=CARD)
url_row.pack(fill=tk.X, pady=(8, 0))

entry_url = tk.Entry(url_row, font=("Segoe UI", 11), bg=CARD2, fg=TEXT,
                     insertbackground=TEXT, relief="flat",
                     highlightthickness=1, highlightcolor=ACCENT,
                     highlightbackground=BORDER)
entry_url.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=9, ipadx=10)
entry_url.focus_set()

tk.Frame(url_row, bg=CARD, width=8).pack(side=tk.LEFT)

btn_fetch = tk.Button(url_row, text="Analisar  →", font=FONT_BOLD,
                      bg=ACCENT, fg="white", relief="flat", cursor="hand2",
                      activebackground=ACCENT2, activeforeground="white",
                      padx=18, pady=0, bd=0)
btn_fetch.pack(side=tk.LEFT, ipady=9)

# ══════════════════════════════════════════════════════════════════════════════
# SEÇÃO 2 — INFO DO VÍDEO (oculta até analisar)
# ══════════════════════════════════════════════════════════════════════════════
sec_info = card(scroll_frame)
# não empacotado ainda

inner_info = tk.Frame(sec_info, bg=CARD, padx=20, pady=16)
inner_info.pack(fill=tk.X)

info_title_var = tk.StringVar(value="")
info_dur_var   = tk.StringVar(value="")

lbl_video_title = label(inner_info, "", font=FONT_LG, fg=TEXT)
lbl_video_title.pack(anchor=tk.W)
lbl_video_title["textvariable"] = info_title_var

lbl_dur = label(inner_info, "", fg=SUBTEXT)
lbl_dur.pack(anchor=tk.W, pady=(2, 0))
lbl_dur["textvariable"] = info_dur_var

# ══════════════════════════════════════════════════════════════════════════════
# SEÇÃO 3 — TIPO DE DOWNLOAD
# ══════════════════════════════════════════════════════════════════════════════
sec_type = card(scroll_frame)
# não empacotado ainda

inner_type = tk.Frame(sec_type, bg=CARD, padx=20, pady=18)
inner_type.pack(fill=tk.X)

label(inner_type, "O que deseja baixar?", font=FONT_BOLD, fg=SUBTEXT).pack(anchor=tk.W, pady=(0,10))

download_type = tk.StringVar(value="video")

type_row = tk.Frame(inner_type, bg=CARD)
type_row.pack(fill=tk.X)

TYPE_OPTIONS = [
    ("🎬  Vídeo",   "video"),
    ("🎵  Áudio",   "audio"),
    ("📄  Legenda", "subtitle"),
]

type_buttons = {}

def select_type(val):
    download_type.set(val)
    for v, btn in type_buttons.items():
        if v == val:
            btn.configure(bg=ACCENT, fg="white", relief="flat")
        else:
            btn.configure(bg=CARD2, fg=SUBTEXT, relief="flat")
    update_format_section()

for txt, val in TYPE_OPTIONS:
    b = tk.Button(type_row, text=txt, font=FONT_BOLD, bg=CARD2, fg=SUBTEXT,
                  relief="flat", cursor="hand2", padx=20, pady=8, bd=0,
                  activebackground=ACCENT, activeforeground="white",
                  command=lambda v=val: select_type(v))
    b.pack(side=tk.LEFT, padx=(0, 8))
    type_buttons[val] = b

# select_type("video") é chamado após a seção 4 ser criada

# ══════════════════════════════════════════════════════════════════════════════
# SEÇÃO 4 — OPÇÕES DE FORMATO
# ══════════════════════════════════════════════════════════════════════════════
sec_fmt = card(scroll_frame)
# não empacotado ainda

inner_fmt = tk.Frame(sec_fmt, bg=CARD, padx=20, pady=18)
inner_fmt.pack(fill=tk.X)

label(inner_fmt, "Formato & Qualidade", font=FONT_BOLD, fg=SUBTEXT).pack(anchor=tk.W, pady=(0,12))

# --- Vídeo ---
fmt_video_frame = tk.Frame(inner_fmt, bg=CARD)

lbl_res = label(fmt_video_frame, "Resolução", fg=SUBTEXT)
lbl_res.grid(row=0, column=0, sticky="w", pady=4)
res_var = tk.StringVar()
combo_res = ttk.Combobox(fmt_video_frame, textvariable=res_var, state="readonly",
                         font=FONT_MAIN, width=28)
combo_res.grid(row=0, column=1, sticky="w", padx=(12, 0), pady=4)

lbl_vfmt = label(fmt_video_frame, "Contêiner", fg=SUBTEXT)
lbl_vfmt.grid(row=1, column=0, sticky="w", pady=4)
vfmt_var = tk.StringVar()
combo_vfmt = ttk.Combobox(fmt_video_frame, textvariable=vfmt_var, state="readonly",
                           font=FONT_MAIN, width=28)
combo_vfmt.grid(row=1, column=1, sticky="w", padx=(12, 0), pady=4)

fmt_video_frame.configure(bg=CARD)
for w in fmt_video_frame.winfo_children():
    if isinstance(w, tk.Label):
        w.configure(bg=CARD)

# --- Áudio ---
fmt_audio_frame = tk.Frame(inner_fmt, bg=CARD)

lbl_abr = label(fmt_audio_frame, "Qualidade", fg=SUBTEXT)
lbl_abr.grid(row=0, column=0, sticky="w", pady=4)
abr_var = tk.StringVar()
combo_abr = ttk.Combobox(fmt_audio_frame, textvariable=abr_var, state="readonly",
                          font=FONT_MAIN, width=28)
combo_abr.grid(row=0, column=1, sticky="w", padx=(12, 0), pady=4)

lbl_afmt = label(fmt_audio_frame, "Formato", fg=SUBTEXT)
lbl_afmt.grid(row=1, column=0, sticky="w", pady=4)
afmt_var = tk.StringVar()
combo_afmt = ttk.Combobox(fmt_audio_frame, textvariable=afmt_var, state="readonly",
                           font=FONT_MAIN, width=28,
                           values=["mp3", "m4a", "opus", "wav", "flac"])
combo_afmt.set("mp3")
combo_afmt.grid(row=1, column=1, sticky="w", padx=(12, 0), pady=4)

fmt_audio_frame.configure(bg=CARD)
for w in fmt_audio_frame.winfo_children():
    if isinstance(w, tk.Label):
        w.configure(bg=CARD)

# --- Legenda ---
fmt_sub_frame = tk.Frame(inner_fmt, bg=CARD)

lbl_slang = label(fmt_sub_frame, "Idioma", fg=SUBTEXT)
lbl_slang.grid(row=0, column=0, sticky="w", pady=4)
slang_var = tk.StringVar()
combo_slang = ttk.Combobox(fmt_sub_frame, textvariable=slang_var, state="readonly",
                             font=FONT_MAIN, width=28)
combo_slang.grid(row=0, column=1, sticky="w", padx=(12, 0), pady=4)

lbl_sfmt = label(fmt_sub_frame, "Formato", fg=SUBTEXT)
lbl_sfmt.grid(row=1, column=0, sticky="w", pady=4)
sfmt_var = tk.StringVar()
combo_sfmt = ttk.Combobox(fmt_sub_frame, textvariable=sfmt_var, state="readonly",
                            font=FONT_MAIN, width=28,
                            values=["srt", "vtt", "ass", "json3"])
combo_sfmt.set("srt")
combo_sfmt.grid(row=1, column=1, sticky="w", padx=(12, 0), pady=4)

fmt_sub_frame.configure(bg=CARD)
for w in fmt_sub_frame.winfo_children():
    if isinstance(w, tk.Label):
        w.configure(bg=CARD)

def update_format_section():
    fmt_video_frame.pack_forget()
    fmt_audio_frame.pack_forget()
    fmt_sub_frame.pack_forget()
    t = download_type.get()
    if t == "video":
        fmt_video_frame.pack(fill=tk.X)
    elif t == "audio":
        fmt_audio_frame.pack(fill=tk.X)
    else:
        fmt_sub_frame.pack(fill=tk.X)

# Agora que update_format_section existe, inicializa o estado dos botões
select_type("video")

# ══════════════════════════════════════════════════════════════════════════════
# SEÇÃO 5 — BARRA DE PROGRESSO + BOTÃO DOWNLOAD
# ══════════════════════════════════════════════════════════════════════════════
sec_dl = card(scroll_frame)
# não empacotado ainda

inner_dl = tk.Frame(sec_dl, bg=CARD, padx=20, pady=18)
inner_dl.pack(fill=tk.X)

# Destino
dest_row = tk.Frame(inner_dl, bg=CARD)
dest_row.pack(fill=tk.X, pady=(0, 12))

label(dest_row, "Salvar em:", fg=SUBTEXT).pack(side=tk.LEFT)
tk.Frame(dest_row, bg=CARD, width=8).pack(side=tk.LEFT)

lbl_path = label(dest_row, config["download_path"], fg=TEXT)
lbl_path.pack(side=tk.LEFT, fill=tk.X, expand=True)

# Progress
progress_var = tk.DoubleVar(value=0)
style = ttk.Style()
style.theme_use("clam")
style.configure("Red.Horizontal.TProgressbar",
                troughcolor=CARD2, background=ACCENT,
                lightcolor=ACCENT, darkcolor=ACCENT,
                bordercolor=CARD2, troughrelief="flat")

progress_bar = ttk.Progressbar(inner_dl, variable=progress_var, maximum=100,
                                style="Red.Horizontal.TProgressbar", length=400)
progress_bar.pack(fill=tk.X, pady=(0, 6))

progress_label = label(inner_dl, "Aguardando...", fg=SUBTEXT)
progress_label.pack(anchor=tk.W)

tk.Frame(inner_dl, bg=BORDER, height=1).pack(fill=tk.X, pady=12)

btn_download = tk.Button(inner_dl, text="⬇  Iniciar Download", font=("Segoe UI", 12, "bold"),
                          bg=ACCENT, fg="white", relief="flat", cursor="hand2",
                          activebackground=ACCENT2, activeforeground="white",
                          padx=30, pady=12, bd=0)
btn_download.pack(fill=tk.X)

# ══════════════════════════════════════════════════════════════════════════════
# SEÇÃO 6 — LOG
# ══════════════════════════════════════════════════════════════════════════════
sec_log = card(scroll_frame)
# não empacotado ainda

inner_log = tk.Frame(sec_log, bg=CARD, padx=20, pady=16)
inner_log.pack(fill=tk.X)

log_header = tk.Frame(inner_log, bg=CARD)
log_header.pack(fill=tk.X, pady=(0, 8))

label(log_header, "Log do Processo", font=FONT_BOLD, fg=SUBTEXT).pack(side=tk.LEFT)

btn_clear_log = tk.Button(log_header, text="Limpar", font=("Segoe UI", 9),
                           bg=CARD2, fg=SUBTEXT, relief="flat", cursor="hand2",
                           activebackground=BORDER, activeforeground=TEXT,
                           padx=10, pady=3, bd=0)
btn_clear_log.pack(side=tk.RIGHT)

log_text = tk.Text(inner_log, wrap=tk.WORD, font=FONT_MONO, bg="#0A0A0A",
                   fg="#CCCCCC", relief="flat", state="disabled",
                   height=10, insertbackground=TEXT,
                   highlightthickness=1, highlightbackground=BORDER)
log_text.pack(fill=tk.X)

log_text.tag_configure("success", foreground=SUCCESS)
log_text.tag_configure("error",   foreground=DANGER)
log_text.tag_configure("warn",    foreground=WARNING)
log_text.tag_configure("info",    foreground="#4FC3F7")
log_text.tag_configure("normal",  foreground="#CCCCCC")

# Rodapé
tk.Frame(scroll_frame, bg=BG, height=20).pack()

# ══════════════════════════════════════════════════════════════════════════════
# LÓGICA — LOG
# ══════════════════════════════════════════════════════════════════════════════
def log(msg, tag="normal"):
    def _do():
        log_text.config(state="normal")
        log_text.insert(tk.END, msg + "\n", tag)
        log_text.see(tk.END)
        log_text.config(state="disabled")
    root.after(0, _do)

def clear_log():
    log_text.config(state="normal")
    log_text.delete("1.0", tk.END)
    log_text.config(state="disabled")

btn_clear_log.configure(command=clear_log)

# ══════════════════════════════════════════════════════════════════════════════
# LÓGICA — ANALISAR VÍDEO
# ══════════════════════════════════════════════════════════════════════════════
def show_sections():
    for sec in (sec_info, sec_type, sec_fmt, sec_dl, sec_log):
        sec.pack(fill=tk.X, padx=30, pady=(0, 12))

def fetch_info():
    global video_info, available_formats

    url = entry_url.get().strip()
    if not url:
        messagebox.showwarning("Aviso", "Cole uma URL primeiro.")
        return
    if not url.startswith(("http://", "https://")):
        messagebox.showwarning("Aviso", "A URL deve começar com http:// ou https://")
        return

    btn_fetch.configure(state="disabled", text="Analisando...")
    log("🔍 Analisando vídeo...", "info")

    def _fetch():
        global video_info, available_formats
        try:
            ydl_opts = {"quiet": True, "no_warnings": True, "skip_download": True}
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                video_info = info
                available_formats = info.get("formats", [])

            root.after(0, on_fetch_success)
        except Exception as e:
            root.after(0, lambda: on_fetch_error(str(e)))

    threading.Thread(target=_fetch, daemon=True).start()

def on_fetch_success():
    global video_info

    info = video_info
    title    = info.get("title", "Sem título")
    duration = info.get("duration", 0)
    mins, secs = divmod(int(duration), 60)
    hrs,  mins = divmod(mins, 60)

    info_title_var.set(title[:70] + ("…" if len(title) > 70 else ""))
    if hrs:
        info_dur_var.set(f"⏱  {hrs}h {mins:02d}m {secs:02d}s")
    else:
        info_dur_var.set(f"⏱  {mins}m {secs:02d}s")

    # Preencher combos de vídeo
    res_set  = {}
    fmt_set  = set()
    abr_list = []

    for f in available_formats:
        vcodec = f.get("vcodec", "none")
        acodec = f.get("acodec", "none")
        height = f.get("height")
        ext    = f.get("ext", "")
        abr    = f.get("abr")

        if vcodec and vcodec != "none" and height:
            key = f"{height}p"
            if key not in res_set:
                res_set[key] = []
            if ext not in res_set[key]:
                res_set[key].append(ext)
                fmt_set.add(ext)

        if acodec and acodec != "none" and abr and vcodec in (None, "none"):
            abr_list.append(f"{int(abr)} kbps ({ext})")

    resolutions = sorted(res_set.keys(), key=lambda x: int(x[:-1]), reverse=True)
    if not resolutions:
        resolutions = ["Melhor disponível"]
    combo_res["values"] = resolutions
    combo_res.set(resolutions[0])

    containers = sorted(fmt_set)
    if not containers:
        containers = ["mp4", "webm"]
    combo_vfmt["values"] = containers
    combo_vfmt.set("mp4" if "mp4" in containers else containers[0])

    # Combos de áudio
    if not abr_list:
        abr_list = ["Melhor disponível"]
    combo_abr["values"] = abr_list
    combo_abr.set(abr_list[0])

    # Combos de legenda
    subs = info.get("subtitles", {})
    auto = info.get("automatic_captions", {})
    langs = list(subs.keys()) + [f"{k} (auto)" for k in auto.keys() if k not in subs]
    if not langs:
        langs = ["Nenhuma legenda disponível"]
    combo_slang["values"] = langs
    combo_slang.set(langs[0])

    show_sections()
    update_format_section()

    log(f"✅ Vídeo encontrado: {info_title_var.get()}", "success")
    btn_fetch.configure(state="normal", text="Analisar  →")

def on_fetch_error(err):
    log(f"❌ Erro ao analisar: {err}", "error")
    btn_fetch.configure(state="normal", text="Analisar  →")

btn_fetch.configure(command=fetch_info)
entry_url.bind("<Return>", lambda e: fetch_info())

# ══════════════════════════════════════════════════════════════════════════════
# LÓGICA — DOWNLOAD
# ══════════════════════════════════════════════════════════════════════════════
def update_progress(pct, msg=""):
    root.after(0, lambda: progress_var.set(pct))
    if msg:
        root.after(0, lambda: progress_label.configure(text=msg))

def build_ydl_opts():
    t    = download_type.get()
    dest = config["download_path"]
    tmpl = os.path.join(dest, "%(title)s.%(ext)s")

    def hook(d):
        if d["status"] == "downloading":
            pct_str = d.get("_percent_str", "0%").strip().replace("%", "")
            try:
                pct = float(pct_str)
            except:
                pct = 0
            speed = d.get("_speed_str", "").strip()
            eta   = d.get("_eta_str", "").strip()
            update_progress(pct, f"Baixando… {pct:.1f}%  |  {speed}  |  ETA {eta}")
        elif d["status"] == "finished":
            update_progress(100, "Finalizando…")

    opts = {
        "outtmpl": tmpl,
        "quiet": True,
        "no_warnings": True,
        "progress_hooks": [hook],
        "socket_timeout": 30,
    }

    if t == "video":
        res = res_var.get().replace("p", "")
        fmt = vfmt_var.get()
        if res.isdigit():
            opts["format"] = f"bestvideo[height<={res}][ext={fmt}]+bestaudio/bestvideo[height<={res}]+bestaudio/best"
        else:
            opts["format"] = "bestvideo+bestaudio/best"
        opts["merge_output_format"] = fmt if fmt else "mp4"

    elif t == "audio":
        afmt = afmt_var.get()
        opts["format"]            = "bestaudio/best"
        opts["postprocessors"] = [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": afmt,
            "preferredquality": "192",
        }]

    else:  # subtitle
        lang = slang_var.get().replace(" (auto)", "")
        sfmt = sfmt_var.get()
        opts["skip_download"]          = True
        opts["writesubtitles"]         = True
        opts["writeautomaticsub"]      = True
        opts["subtitleslangs"]         = [lang]
        opts["subtitlesformat"]        = sfmt
        opts["postprocessors"]         = [{"key": "FFmpegSubtitlesConvertor",
                                           "format": sfmt}]

    return opts

def iniciar_download():
    global is_running
    if is_running:
        messagebox.showwarning("Aviso", "Já há um download em andamento.")
        return
    if video_info is None:
        messagebox.showwarning("Aviso", "Analise um vídeo primeiro.")
        return

    url = entry_url.get().strip()
    is_running = True
    btn_download.configure(state="disabled", text="⏳  Baixando…")
    progress_var.set(0)
    progress_label.configure(text="Iniciando…")
    log("🚀 Iniciando download…", "info")

    def _run():
        global is_running
        try:
            opts = build_ydl_opts()
            with yt_dlp.YoutubeDL(opts) as ydl:
                ydl.download([url])
            log(f"✅ Download concluído! Salvo em: {config['download_path']}", "success")
            root.after(0, lambda: progress_label.configure(text="Concluído!"))
        except Exception as e:
            log(f"❌ Erro: {e}", "error")
            root.after(0, lambda: progress_label.configure(text="Erro no download."))
        finally:
            is_running = False
            root.after(0, lambda: btn_download.configure(state="normal", text="⬇  Iniciar Download"))

    threading.Thread(target=_run, daemon=True).start()

btn_download.configure(command=iniciar_download)

# ══════════════════════════════════════════════════════════════════════════════
# JANELA DE CONFIGURAÇÕES
# ══════════════════════════════════════════════════════════════════════════════
def open_settings():
    win = tk.Toplevel(root)
    win.title("Configurações")
    win.geometry("500x280")
    win.resizable(False, False)
    win.configure(bg=BG)
    win.grab_set()

    # Centralizar
    win.update_idletasks()
    wx = root.winfo_x() + (760 - 500) // 2
    wy = root.winfo_y() + (820 - 280) // 2
    win.geometry(f"500x280+{wx}+{wy}")

    p = tk.Frame(win, bg=BG, padx=30, pady=24)
    p.pack(fill=tk.BOTH, expand=True)

    label(p, "Configurações", font=FONT_XL, fg=TEXT).pack(anchor=tk.W)
    sep(p).pack(fill=tk.X, pady=12)

    # Pasta de download
    label(p, "Pasta de Downloads", font=FONT_BOLD, fg=SUBTEXT).pack(anchor=tk.W)

    path_row = tk.Frame(p, bg=BG)
    path_row.pack(fill=tk.X, pady=(6, 0))

    path_var = tk.StringVar(value=config["download_path"])

    path_entry = tk.Entry(path_row, textvariable=path_var, font=FONT_MAIN,
                          bg=CARD2, fg=TEXT, insertbackground=TEXT, relief="flat",
                          highlightthickness=1, highlightcolor=ACCENT,
                          highlightbackground=BORDER, state="readonly")
    path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=8, ipadx=8)

    tk.Frame(path_row, bg=BG, width=8).pack(side=tk.LEFT)

    def choose_folder():
        folder = filedialog.askdirectory(title="Selecionar pasta de download",
                                          initialdir=path_var.get())
        if folder:
            path_var.set(folder)

    tk.Button(path_row, text="📁  Escolher", font=FONT_MAIN,
              bg=CARD2, fg=TEXT, relief="flat", cursor="hand2",
              activebackground=BORDER, activeforeground=TEXT,
              padx=12, pady=0, bd=0,
              command=choose_folder).pack(side=tk.LEFT, ipady=8)

    sep(p).pack(fill=tk.X, pady=16)

    btn_row = tk.Frame(p, bg=BG)
    btn_row.pack(fill=tk.X)

    def save_and_close():
        config["download_path"] = path_var.get()
        save_config(config)
        lbl_path.configure(text=config["download_path"])
        log(f"⚙  Pasta de download atualizada: {config['download_path']}", "info")
        win.destroy()

    tk.Button(btn_row, text="Cancelar", font=FONT_MAIN,
              bg=CARD2, fg=SUBTEXT, relief="flat", cursor="hand2",
              activebackground=BORDER, activeforeground=TEXT,
              padx=20, pady=8, bd=0,
              command=win.destroy).pack(side=tk.RIGHT, padx=(8, 0))

    tk.Button(btn_row, text="Salvar", font=FONT_BOLD,
              bg=ACCENT, fg="white", relief="flat", cursor="hand2",
              activebackground=ACCENT2, activeforeground="white",
              padx=20, pady=8, bd=0,
              command=save_and_close).pack(side=tk.RIGHT)

btn_settings.configure(command=open_settings)

# ══════════════════════════════════════════════════════════════════════════════
# LOOP
# ══════════════════════════════════════════════════════════════════════════════
root.mainloop()
