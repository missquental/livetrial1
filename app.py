import streamlit as st
import cv2
import threading
import time
from datetime import datetime

# Konfigurasi halaman
st.set_page_config(
    page_title="CCTV Stream to YouTube",
    layout="wide"
)

# Judul aplikasi
st.title("🎥 CCTV Stream to YouTube Live")
st.markdown("---")

# Sidebar untuk konfigurasi
with st.sidebar:
    st.header("⚙️ Konfigurasi")
    
    # Input URL CCTV
    cctv_url = st.text_input(
        "🔗 URL CCTV", 
        value="http://stream.cctv.malangkota.go.id/WebRTCApp/play.html?name=192932202274819493009134",
        help="Masukkan URL stream CCTV yang akan ditampilkan"
    )
    
    # Input RTMP Key
    rtmp_key = st.text_input(
        "🔑 RTMP Key YouTube", 
        type="password",
        help="RTMP key dari YouTube Studio untuk streaming live"
    )
    
    # Input Custom RTMP URL (opsional)
    custom_rtmp = st.text_input(
        "📡 Custom RTMP URL (Opsional)", 
        placeholder="rtmp://a.rtmp.youtube.com/live2/",
        help="Gunakan RTMP URL kustom jika tidak menggunakan YouTube"
    )
    
    # Tombol kontrol
    col1, col2 = st.columns(2)
    with col1:
        start_btn = st.button("▶️ Mulai Streaming", use_container_width=True)
    with col2:
        stop_btn = st.button("⏹️ Stop Streaming", use_container_width=True)
        
    st.markdown("---")
    st.info("💡 Pastikan RTMP Key sudah dimasukkan dengan benar di YouTube Studio")

# Inisialisasi session state
if 'streaming' not in st.session_state:
    st.session_state.streaming = False
    
if 'status_msg' not in st.session_state:
    st.session_state.status_msg = "Menunggu..."

# Kolom utama untuk video player
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("📹 Preview CCTV")
    video_placeholder = st.empty()
    status_placeholder = st.empty()

with col2:
    st.subheader("📊 Status Streaming")
    info_placeholder = st.empty()
    
    # Informasi teknis
    st.markdown("### 📋 Info Teknis:")
    st.write("- Resolusi: 1280x720 (HD)")
    st.write("- FPS: 30")
    st.write("- Codec: H.264")
    st.write("- Format Output: RTMP")
    
    st.markdown("---")
    st.markdown("### ℹ️ Cara Menggunakan:")
    st.markdown("1. Masukkan RTMP Key dari YouTube Studio")
    st.markdown("2. Klik tombol 'Mulai Streaming'")
    st.markdown("3. Preview akan muncul di layar kiri")
    st.markdown("4. Stream akan dikirim ke channel YouTube Anda")

# Fungsi untuk streaming
def start_stream(cctv_url, rtmp_key, custom_rtmp):
    try:
        # Tentukan RTMP URL
        if custom_rtmp:
            rtmp_url = f"{custom_rtmp}/{rtmp_key}" if rtmp_key else custom_rtmp
        else:
            rtmp_url = f"rtmp://a.rtmp.youtube.com/live2/{rtmp_key}"
            
        # Buka capture dari CCTV
        cap = cv2.VideoCapture(cctv_url)
        
        # Properti video
        frame_width = int(cap.get(3))
        frame_height = int(cap.get(4))
        fps = 30
        
        # Codec dan writer
        fourcc = cv2.VideoWriter_fourcc(*'H264')
        out = cv2.VideoWriter(
            rtmp_url,
            fourcc,
            fps,
            (frame_width, frame_height)
        )
        
        if not out.isOpened():
            st.error("Gagal membuka koneksi RTMP")
            return
            
        st.session_state.streaming = True
        
        while st.session_state.streaming:
            ret, frame = cap.read()
            if not ret:
                st.warning("Tidak dapat membaca frame dari CCTV")
                break
                
            # Resize frame untuk optimalisasi
            frame = cv2.resize(frame, (1280, 720))
            
            # Tambahkan watermark tanggal dan jam
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cv2.putText(
                frame, 
                timestamp, 
                (10, 30), 
                cv2.FONT_HERSHEY_SIMPLEX, 
                1, 
                (255, 255, 255), 
                2, 
                cv2.LINE_AA
            )
            
            # Tampilkan preview
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            video_placeholder.image(rgb_frame, channels="RGB", use_column_width=True)
            
            # Kirim frame ke RTMP
            out.write(frame)
            
            # Update status
            status_placeholder.success(f"Streaming aktif | {timestamp}")
            
        # Cleanup
        cap.release()
        out.release()
        status_placeholder.info("Streaming dihentikan")
        
    except Exception as e:
        st.error(f"Error saat streaming: {str(e)}")
        st.session_state.streaming = False

# Kontrol streaming
if start_btn and rtmp_key:
    if not st.session_state.streaming:
        st.session_state.thread = threading.Thread(
            target=start_stream, 
            args=(cctv_url, rtmp_key, custom_rtmp)
        )
        st.session_state.thread.start()
        st.session_state.status_msg = "Streaming dimulai..."
elif stop_btn:
    st.session_state.streaming = False
    if 'thread' in st.session_state and st.session_state.thread.is_alive():
        st.session_state.thread.join(timeout=1)
    st.session_state.status_msg = "Streaming dihentikan"

# Update informasi status
info_placeholder.info(st.session_state.status_msg)

# Footer
st.markdown("---")
st.caption("Developed with ❤️ using Streamlit | CCTV Malang Kota")
