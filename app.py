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
    resolution = st.selectbox("Resolusi", ["1280x720", "1920x1080", "854x480"])
    bitrate = st.slider("Bitrate (kbps)", 500, 5000, 2500)
    
    # Tombol kontrol
    col1, col2 = st.columns(2)
    with col1:
        start_btn = st.button("▶️ Mulai Streaming", use_container_width=True)
    with col2:
        stop_btn = st.button("⏹️ Stop Streaming", use_container_width=True)
        
    st.markdown("---")
    st.info("💡 Pastikan semua dependensi terinstal:\n- ffmpeg\n- streamlink")

# Inisialisasi session state
if 'streaming' not in st.session_state:
    st.session_state.streaming = False
if 'process' not in st.session_state:
    st.session_state.process = None

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
    st.markdown("1. Pastikan **ffmpeg** dan **streamlink** sudah terinstal")
    st.markdown("2. Masukkan RTMP Key dari YouTube Studio")
    st.markdown("3. Klik tombol **Mulai Streaming**")
    st.markdown("4. Cek status streaming di panel kanan")

with col2:
    st.subheader("📊 Status Streaming")
    status_placeholder = st.empty()
    
    if st.session_state.streaming:
        status_placeholder.success("🟢 Streaming Aktif")
    else:
        status_placeholder.warning("🔴 Streaming Tidak Aktif")
    
    # Log streaming
    st.subheader("📝 Log")
    log_area = st.empty()
    log_text = st.empty()
    
    # Informasi teknis
    st.markdown("### ⚙️ Info Teknis:")
    st.write(f"- Resolusi: {resolution}")
    st.write(f"- Bitrate: {bitrate} kbps")
    st.write("- Codec: H.264")
    st.write("- Format Output: RTMP")
    
    st.markdown("---")
    st.markdown("### ⚠️ Perhatian:")
    st.warning("WebRTC stream membutuhkan proses konversi khusus. Pastikan server memiliki resource CPU yang cukup.")

# Fungsi untuk streaming dengan ffmpeg
def start_ffmpeg_stream(cctv_url, rtmp_key, custom_rtmp, resolution, bitrate):
    try:
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
            '-i', cctv_url,  # Input URL
            '-f', 'flv',     # Format output
            '-vcodec', 'libx264',  # Codec video
            '-preset', 'ultrafast',  # Preset encoding
            '-pix_fmt', 'yuv420p',   # Format pixel
            '-s', f'{width}x{height}',  # Resolusi
            '-b:v', f'{bitrate}k',   # Bitrate video
            '-bufsize', f'{bitrate*2}k',  # Buffer size
            '-maxrate', f'{bitrate}k',    # Max rate
            '-g', '60',          # GOP size
            '-acodec', 'aac',    # Codec audio
            '-b:a', '128k',      # Bitrate audio
            '-ar', '44100',      # Sample rate audio
            '-f', 'flv',         # Format container
            rtmp_url             # RTMP output
        ]
        
        # Jalankan proses
        st.session_state.process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )
        
        st.session_state.streaming = True
        log_text.text("🔄 Memulai streaming...")
        
        # Monitor proses
        while st.session_state.streaming and st.session_state.process.poll() is None:
            time.sleep(1)
            
        if st.session_state.process.returncode is not None:
            log_text.text(f"❌ Streaming berhenti dengan kode: {st.session_state.process.returncode}")
            
    except Exception as e:
        log_text.text(f"❌ Error: {str(e)}")
        st.session_state.streaming = False

# Fungsi alternatif dengan streamlink
def start_streamlink_stream(cctv_url, rtmp_key, custom_rtmp, resolution, bitrate):
    try:
        # Tentukan RTMP URL
        if custom_rtmp:
            rtmp_url = f"{custom_rtmp}/{rtmp_key}" if rtmp_key else custom_rtmp
        else:
            rtmp_url = f"rtmp://a.rtmp.youtube.com/live2/{rtmp_key}"
            
        # Command streamlink + ffmpeg pipeline
        cmd = [
            'streamlink',
            '--stdout',
            cctv_url,
            'best'
        ]
        
        # Jalankan streamlink
        streamlink_process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Command ffmpeg untuk re-encode
        width, height = resolution.split('x')
        ffmpeg_cmd = [
            'ffmpeg',
            '-i', 'pipe:0',      # Input dari stdin
            '-f', 'flv',
            '-vcodec', 'libx264',
            '-preset', 'ultrafast',
            '-pix_fmt', 'yuv420p',
            '-s', f'{width}x{height}',
            '-b:v', f'{bitrate}k',
            '-bufsize', f'{bitrate*2}k',
            '-maxrate', f'{bitrate}k',
            '-g', '60',
            '-acodec', 'aac',
            '-b:a', '128k',
            '-ar', '44100',
            '-f', 'flv',
            rtmp_url
        ]
        
        # Jalankan ffmpeg dengan input dari streamlink
        st.session_state.process = subprocess.Popen(
            ffmpeg_cmd,
            stdin=streamlink_process.stdout,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )
        
        st.session_state.streaming = True
        log_text.text("🔄 Memulai streaming dengan Streamlink...")
        
        # Monitor proses
        while st.session_state.streaming and st.session_state.process.poll() is None:
            time.sleep(1)
            
    except Exception as e:
        log_text.text(f"❌ Error: {str(e)}")
        st.session_state.streaming = False

# Kontrol streaming
if start_btn and rtmp_key:
    if not st.session_state.streaming:
        # Coba metode pertama
        log_text.text("🚀 Mencoba metode streaming...")
        
        # Jalankan streaming di thread terpisah
        streaming_thread = threading.Thread(
            target=start_ffmpeg_stream,
            args=(cctv_url, rtmp_key, custom_rtmp, resolution, bitrate)
        )
        streaming_thread.daemon = True
        streaming_thread.start()
        
elif stop_btn:
    st.session_state.streaming = False
    if st.session_state.process:
        st.session_state.process.terminate()
        st.session_state.process.wait()
    log_text.text("⏹️ Streaming dihentikan")

# Footer
st.markdown("---")
st.caption("🛠️ Troubleshooting: Jika streaming tidak berjalan, pastikan:")
st.markdown("- `ffmpeg` dan `streamlink` sudah terinstal")
st.markdown("- URL CCTV dapat diakses")
st.markdown("- RTMP key valid")
st.markdown("- Firewall tidak memblokir koneksi")
