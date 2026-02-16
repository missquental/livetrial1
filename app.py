import streamlit as st
import subprocess
import threading
import time
import os
from datetime import datetime

# Konfigurasi halaman
st.set_page_config(
    page_title="CCTV Stream to YouTube",
    layout="wide"
)

# Inisialisasi session state
if 'streaming' not in st.session_state:
    st.session_state.streaming = False
if 'process' not in st.session_state:
    st.session_state.process = None
if 'log_messages' not in st.session_state:
    st.session_state.log_messages = []
if 'status' not in st.session_state:
    st.session_state.status = "🔴 Tidak Aktif"

# Fungsi untuk menambah log dengan aman
def add_log(message):
    timestamp = datetime.now().strftime("%H:%M:%S")
    st.session_state.log_messages.append(f"[{timestamp}] {message}")
    # Batasi jumlah log
    if len(st.session_state.log_messages) > 50:
        st.session_state.log_messages = st.session_state.log_messages[-20:]

# Judul aplikasi
st.title("🎥 CCTV WebRTC Stream to YouTube Live")
st.markdown("---")

# Sidebar untuk konfigurasi
with st.sidebar:
    st.header("⚙️ Konfigurasi")
    
    # Input URL CCTV
    cctv_url = st.text_input(
        "🔗 URL CCTV WebRTC", 
        value="http://stream.cctv.malangkota.go.id/WebRTCApp/play.html?name=192932202274819493009134",
        help="URL WebRTC CCTV yang akan ditampilkan"
    )
    
    # Input RTMP Key
    rtmp_key = st.text_input(
        "🔑 RTMP Key YouTube", 
        type="password",
        help="RTMP key dari YouTube Studio"
    )
    
    # Input Custom RTMP URL (opsional)
    custom_rtmp = st.text_input(
        "📡 Custom RTMP URL (Opsional)", 
        placeholder="rtmp://a.rtmp.youtube.com/live2/",
        help="Gunakan RTMP URL kustom jika tidak menggunakan YouTube"
    )
    
    # Resolusi dan kualitas
    st.subheader("📺 Kualitas Video")
    resolution = st.selectbox("Resolusi", ["1280x720", "1920x1080", "854x480"], key="res_select")
    bitrate = st.slider("Bitrate (kbps)", 500, 5000, 2500, key="bitrate_slider")
    
    # Tombol kontrol
    col1, col2 = st.columns(2)
    with col1:
        start_btn = st.button("▶️ Mulai Streaming", use_container_width=True, key="start_btn")
    with col2:
        stop_btn = st.button("⏹️ Stop Streaming", use_container_width=True, key="stop_btn")
        
    st.markdown("---")
    st.info("💡 Pastikan ffmpeg sudah terinstal di sistem")

# Kolom utama
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("📹 Preview & Info")
    if not st.session_state.streaming:
        st.info("Preview akan muncul saat streaming dimulai")
        st.image("https://placehold.co/800x450/CCCCCC/333333?text=CCTV+Preview", 
                 caption="Preview CCTV", use_column_width=True)
    else:
        st.success("✅ Streaming sedang berjalan!")
        st.image("https://placehold.co/800x450/4CAF50/FFFFFF?text=LIVE+STREAMING", 
                 caption="Live Streaming", use_column_width=True)
    
    st.markdown("### 📋 Petunjuk Penggunaan:")
    st.markdown("1. Pastikan **ffmpeg** sudah terinstal di sistem")
    st.markdown("2. Masukkan RTMP Key dari YouTube Studio")
    st.markdown("3. Klik tombol **Mulai Streaming**")
    st.markdown("4. Monitor log di panel kanan")

with col2:
    st.subheader("📊 Status Streaming")
    
    # Status streaming
    status_display = st.empty()
    status_display.markdown(f"### {st.session_state.status}")
    
    # Log streaming
    st.subheader("📝 Log")
    log_container = st.container()
    
    # Tampilkan log terbaru
    with log_container:
        for log_msg in st.session_state.log_messages[-10:]:  # Tampilkan 10 log terakhir
            st.text(log_msg)
    
    # Informasi teknis
    st.markdown("### ⚙️ Info Teknis:")
    st.write(f"- Resolusi: {resolution}")
    st.write(f"- Bitrate: {bitrate} kbps")
    st.write("- Codec: H.264")
    st.write("- Format Output: RTMP")

# Fungsi untuk streaming dengan ffmpeg (dijalankan di thread terpisah)
def start_ffmpeg_stream(cctv_url, rtmp_key, custom_rtmp, resolution, bitrate):
    try:
        add_log("🔄 Memulai proses streaming...")
        
        # Parse resolusi
        width, height = resolution.split('x')
        
        # Tentukan RTMP URL
        if custom_rtmp:
            rtmp_url = f"{custom_rtmp}/{rtmp_key}" if rtmp_key else custom_rtmp
        else:
            rtmp_url = f"rtmp://a.rtmp.youtube.com/live2/{rtmp_key}"
            
        # Command ffmpeg untuk konversi WebRTC ke RTMP
        cmd = [
            'ffmpeg',
            '-re',  # Read input at native frame rate
            '-i', cctv_url,
            '-c:v', 'libx264',
            '-preset', 'ultrafast',
            '-pix_fmt', 'yuv420p',
            '-s', f'{width}x{height}',
            '-b:v', f'{bitrate}k',
            '-maxrate', f'{bitrate}k',
            '-bufsize', f'{bitrate*2}k',
            '-g', '60',
            '-c:a', 'aac',
            '-b:a', '128k',
            '-ar', '44100',
            '-f', 'flv',
            rtmp_url
        ]
        
        # Jalankan proses
        st.session_state.process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )
        
        add_log("✅ Proses ffmpeg dimulai")
        st.session_state.status = "🟢 Aktif"
        
        # Monitor proses
        while st.session_state.streaming and st.session_state.process.poll() is None:
            time.sleep(1)
            
        if st.session_state.process.returncode == 0:
            add_log("⏹️ Streaming selesai dengan normal")
        elif st.session_state.process.returncode is not None:
            add_log(f"❌ Streaming berhenti dengan kode: {st.session_state.process.returncode}")
            
    except Exception as e:
        add_log(f"❌ Error dalam thread: {str(e)}")
        st.session_state.streaming = False
        st.session_state.status = "🔴 Error"
    finally:
        st.session_state.streaming = False

# Kontrol streaming dengan fungsi wrapper yang aman
def safe_start_streaming():
    if not rtmp_key:
        add_log("❌ RTMP Key harus diisi!")
        return
        
    if st.session_state.streaming:
        add_log("⚠️ Streaming sudah berjalan!")
        return
        
    add_log("🚀 Memulai streaming...")
    st.session_state.streaming = True
    st.session_state.status = "🟡 Memulai..."
    
    # Jalankan streaming di thread terpisah
    streaming_thread = threading.Thread(
        target=start_ffmpeg_stream,
        args=(cctv_url, rtmp_key, custom_rtmp, resolution, bitrate),
        daemon=True
    )
    streaming_thread.start()

def safe_stop_streaming():
    if st.session_state.streaming and st.session_state.process:
        add_log("⏹️ Menghentikan streaming...")
        st.session_state.process.terminate()
        try:
            st.session_state.process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            st.session_state.process.kill()
        st.session_state.streaming = False
        st.session_state.status = "🔴 Dihentikan"
        add_log("✅ Streaming dihentikan")
    elif st.session_state.streaming:
        st.session_state.streaming = False
        st.session_state.status = "🔴 Dihentikan"
        add_log("✅ Streaming dihentikan")
    else:
        add_log("⚠️ Tidak ada streaming yang aktif")

# Kontrol button actions
if start_btn:
    safe_start_streaming()

if stop_btn:
    safe_stop_streaming()

# Footer
st.markdown("---")
st.caption("🛠️ Troubleshooting:")
st.markdown("- Pastikan `ffmpeg` terinstal: `ffmpeg -version`")
st.markdown("- Cek koneksi internet dan firewall")
st.markdown("- Verifikasi RTMP key dan URL")
