import streamlit as st
import re
import pandas as pd
from collections import Counter
from streamlit_option_menu import option_menu

# ==========================================
# 1. KONFIGURASI HALAMAN & ATURAN TOKEN
# ==========================================
st.set_page_config(page_title="Lexical Analyzer Simulator", page_icon="[ ]", layout="centered")

TOKEN_RULES = [
    ('KEYWORD', r'\b(int|float|string|if|else|while|for|return|void|bool|true|false|print|def|class|import|from|True|False|None|and|or|not|in|is|elif|pass|break|continue|lambda|with|as|try|except|finally|raise|input|len|range|type|str|list|dict|tuple|set)\b'),
    ('NUMBER', r'\b\d+(\.\d+)?\b'),
    ('STRING', r'"[^"]*"|\'[^\']*\''),
    ('IDENTIFIER', r'\b[a-zA-Z_][a-zA-Z0-9_]*\b'),
    ('OPERATOR', r'==|!=|<=|>=|\+=|-=|\*\*|[+\-\raw*/=<>!&|%^~]'),
    ('DELIMITER', r'[;,(){}[\]:]'),
    ('COMMENT', r'#[^\n]*|//[^\n]*'),
    ('WHITESPACE', r'\s+'),
]

COLORS = {
    'KEYWORD': '#FF6B6B',
    'IDENTIFIER': '#4ECDC4',
    'NUMBER': '#FFE66D',
    'STRING': '#A8E6CF',
    'OPERATOR': '#FF8B94',
    'DELIMITER': '#B4B4FF',
    'COMMENT': '#AAAAAA',
    'UNKNOWN': '#FF0000',
}

TYPE_DESCRIPTIONS = {
    'KEYWORD': '<b>Kata Kunci Utama</b> — Kata perintah bawaan yang sudah punya arti khusus di dalam bahasa pemrograman.<br><i>Contoh: int, if, else, while, return, print.</i>',
    'IDENTIFIER': '<b>Nama Buatan Programmer</b> — Nama yang kamu buat sendiri bebas untuk menandai variabel, fungsi, atau nama kelas.<br><i>Contoh: nama_user, nilai_x, total_biaya.</i>',
    'NUMBER': '<b>Nilai Angka</b> — Semua komponen data berbentuk angka, baik angka bulat maupun pecahan/desimal.<br><i>Contoh: 5, 12, 3.14, 100.</i>',
    'STRING': '<b>Data Teks</b> — Kumpulan huruf atau kalimat yang wajib diapit oleh tanda kutip tunggal (\') atau ganda (").<br><i>Contoh: "Halo Dunia", \'SMK Bisa\'.</i>',
    'OPERATOR': '<b>Simbol Operasi</b> — Simbol khusus untuk menghitung matematika, membandingkan nilai, atau logika.<br><i>Contoh: +, -, *, =, ==, !=.</i>',
    'DELIMITER': '<b>Tanda Baca Pembatas</b> — Tanda baca untuk memisahkan perintah atau pembuka dan penutup blok kode.<br><i>Contoh: ; , ( ) { } [ ] :</i>',
    'COMMENT': '<b>Catatan Coding</b> — Teks penjelasan yang sengaja diabaikan komputer dan digunakan sebagai catatan kamu sendiri.<br><i>Contoh: # Ini catatan rumus, // Logika utama.</i>',
    'UNKNOWN': '<b>Karakter Tidak Dikenal</b> — Simbol atau karakter asing yang tidak terdaftar dan dianggap eror oleh sistem.',
}

OPERATOR_MAP = {
    '+': 'Simbol operasi penjumlahan', '-': 'Simbol operasi pengurangan', '*': 'Simbol operasi perkalian', 
    '/': 'Simbol operasi pembagian', '=': 'Simbol untuk mengisi atau memasukkan nilai', '==': 'Simbol perbandingan sama dengan',
    '!=': 'Simbol perbandingan tidak sama dengan', '<': 'Simbol lebih kecil dari', '>': 'Simbol lebih besar dari',
    '<=': 'Simbol lebih kecil atau sama dengan', '>=': 'Simbol lebih besar atau sama dengan',
    '%': 'Simbol sisa bagi (modulo)', '**': 'Simbol perpangkatan', '+=': 'Simbol tambah sekaligus isi nilai',
    '-=': 'Simbol kurang sekaligus isi nilai',
}

KEYWORD_MAP = {
    'int': 'Kata kunci bawaan untuk tipe data angka bulat', 'float': 'Kata kunci bawaan untuk tipe data angka desimal', 'string': 'Kata kunci bawaan untuk tipe data teks',
    'str': 'Kata kunci bawaan untuk tipe data teks', 'bool': 'Kata kunci bawaan untuk tipe data benar/salah', 'void': 'Fungsi tanpa nilai balik',
    'if': 'Percabangan (Jika kondisi benar)', 'else': 'Percabangan (Selain kondisi di atas)', 'elif': 'Kondisi alternatif',
    'while': 'Perulangan (Selama kondisi terpenuhi)', 'for': 'Perulangan (Iterasi berurutan)', 'return': 'Mengembalikan nilai dari fungsi',
    'def': 'Mendefinisikan fungsi baru', 'print': 'Output untuk menampilkan teks ke layar', 'True': 'Kondonsi Benar', 'False': 'Kondisi Salah'
}

DELIMITER_MAP = {
    ';': 'Simbol pembatas / tanda akhir baris kode', ',': 'Pemisah elemen data', ':': 'Pembuka blok kode baru', '(': 'Buka kurung parameter',
    ')': 'Tutup kurung parameter', '{': 'Buka kurung kurawal fungsi', '}': 'Tutup kurung kurawal fungsi', '[': 'Buka kurung siku', ']': 'Tutup kurung siku'
}

# ==========================================
# 2. FUNGSI LOGIKA TOKENIZER
# ==========================================
def get_token_meaning(ttype, value):
    if ttype == 'NUMBER': return f'Komponen angka {"desimal" if "." in value else "bulat"}'
    if ttype == 'STRING': return f'Komponen data teks (string)'
    if ttype == 'IDENTIFIER': return f'Nama identitas (variabel) yang kamu buat sendiri'
    if ttype == 'COMMENT': return f'Catatan coding (komentar)'
    if ttype == 'OPERATOR': return OPERATOR_MAP.get(value, f'Simbol operasi: {value}')
    if ttype == 'KEYWORD': return KEYWORD_MAP.get(value, f'Kata kunci utama: {value}')
    if ttype == 'DELIMITER': return DELIMITER_MAP.get(value, f'Tanda baca pembatas')
    return f'Komponen: {value}'

def tokenize(code):
    tokens = []
    pos = 0
    while pos < len(code):
        match = None
        for token_type, pattern in TOKEN_RULES:
            regex = re.compile(pattern)
            match = regex.match(code, pos)
            if match:
                value = match.group(0)
                if token_type != 'WHITESPACE': tokens.append((token_type, value))
                pos = match.end()
                break
        if not match:
            tokens.append(('UNKNOWN', code[pos]))
            pos += 1
    return tokens

# ==========================================
# 3. INTERFACE MENU NAVIGASI
# ==========================================
selected = option_menu(
    menu_title=None,
    options=["Beranda", "Simulator Token", "Buku Panduan"],
    icons=["house-door", "cpu", "book-half"], 
    menu_icon="cast",
    default_index=0,
    orientation="horizontal",
    styles={
        "container": {"padding": "0!important", "background-color": "#f8fafc", "border-radius": "8px"},
        "icon": {"color": "#f59e0b", "font-size": "16px"}, 
        "nav-link": {"font-size": "15px", "text-align": "center", "margin":"0px", "--hover-color": "#f1f5f9", "font-weight": "500"},
        "nav-link-selected": {"background-color": "#4f46e5", "color": "white", "font-weight": "bold"},
    }
)

# Inisialisasi State Aplikasi
if 'code_input' not in st.session_state: st.session_state.code_input = ''
if 'show_result' not in st.session_state: st.session_state.show_result = False

# --- HALAMAN 1: BERANDA ---
if selected == "Beranda":
    st.markdown("<h2 style='text-align: center; color: #1e293b; font-weight: 800; margin-top: 15px; margin-bottom: 5px; letter-spacing: 0.5px;'>[ LEXICAL ANALYZER SIMULATOR ]</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #64748b; font-size: 15px; font-weight: 500; margin-bottom: 25px;'>Aplikasi seru untuk melihat bagaimana komputer membaca dan mengenali kode coding yang kamu ketik secara real-time.</p>", unsafe_allow_html=True)
    st.write("---")
    
    st.info(
        "**[ PANDUAN AWAL ]**\n\n"
        "Yuk, uji kode coding-mu di sini! Aplikasi ini siap membantu kamu melihat langsung bagaimana "
        "cara kerja komputer dalam memotong, membaca, dan mengenali setiap **baris kode** yang kamu ketik "
        "secara *real-time*. Selamat mencoba!"
    )
    
    st.markdown("### >> Apa yang Dilakukan Aplikasi Ini?")
    
    # Grid Layout 3 Kolom Menggunakan Teks Header Bergaya Dev
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""
        <div style='background-color: #f8fafc; padding: 15px; border-radius: 8px; border-top: 4px solid #4f46e5; height: 160px;'>
            <h4 style='margin: 0; font-size: 16px;'>[1] Potong Kode</h4>
            <p style='font-size: 13px; color: #64748b; margin-top: 8px;'>Aplikasi ini akan memotong-motong kode coding yang kamu ketik menjadi bagian-bagian paling kecil.</p>
        </div>
        """, unsafe_allow_html=True)
        
    with col2:
        st.markdown("""
        <div style='background-color: #f8fafc; padding: 15px; border-radius: 8px; border-top: 4px solid #4f46e5; height: 160px;'>
            <h4 style='margin: 0; font-size: 16px;'>[2] Beri Label</h4>
            <p style='font-size: 13px; color: #64748b; margin-top: 8px;'>Setiap potongan kode akan langsung diberi label atau nama jenis komponennya secara otomatis.</p>
        </div>
        """, unsafe_allow_html=True)
        
    with col3:
        st.markdown("""
        <div style='background-color: #f8fafc; padding: 15px; border-radius: 8px; border-top: 4px solid #4f46e5; height: 160px;'>
            <h4 style='margin: 0; font-size: 16px;'>[3] Warnai Otomatis</h4>
            <p style='font-size: 13px; color: #64748b; margin-top: 8px;'>Hasilnya akan ditampilkan dalam bentuk warna-warni agar kamu lebih mudah membedakan strukturnya.</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.write("")
    st.write("---")
    st.markdown("### [ TUTORIAL ] Cara Cepat Menggunakan Aplikasi")
    st.markdown("""
    * **[LANGKAH 1]** > Tulis atau tempel potongan kode coding kamu ke dalam simulator.
    * **[LANGKAH 2]** > Klik tombol jalankan analisis untuk memotong dan melabeli token.
    * **[LANGKAH 3]** > Lihat hasil warnanya atau buka menu **Buku Panduan** jika bingung arti warnanya.
    """)
    
    st.write("")
    if st.button("Mulai Simulator Sekarang >>", use_container_width=True, type="primary"):
        st.session_state.show_result = False
        st.info("Silakan klik menu 'Simulator Token' di bagian atas layar untuk memulai.")

# --- HALAMAN 2: SIMULATOR TOKEN ---
elif selected == "Simulator Token":
    st.markdown("<h3 style='color: #1e293b; font-weight: 700;'>Simulator Analisis Leksikal</h3>", unsafe_allow_html=True)
    st.write("Tulis atau tempel potongan kode coding kamu di kolom bawah ini. Kamu bisa pakai bahasa Python atau C!")
    
    code_input = st.text_area(
        "Masukkan Source Code:",
        height=180,
        placeholder='Contoh: int total = x + 5; atau print("Nilai optimal")',
        value=st.session_state.code_input,
        key=f"code_area_{st.session_state.get('_reset_key', 0)}",
        label_visibility="collapsed"
    )

    c1, c2 = st.columns(2)
    with c1:
        tokenize_btn = st.button("Jalankan Analisis Token", use_container_width=True, type="primary")
    with c2:
        reset_btn = st.button("Bersihkan Kolom", use_container_width=True)

    if reset_btn:
        st.session_state.code_input = ''
        st.session_state.show_result = False
        st.session_state['_reset_key'] = st.session_state.get('_reset_key', 0) + 1
        st.rerun()

    if tokenize_btn:
        if code_input.strip():
            st.session_state.show_result = True
            st.session_state.code_input = code_input

    if st.session_state.show_result and st.session_state.code_input.strip():
        tokens = tokenize(st.session_state.code_input)
        
        st.markdown("#### Hasil Visualisasi Potongan Token")
        html = ""
        for ttype, val in tokens:
            color = COLORS.get(ttype, '#ffffff')
            html += f'<span style="background:{color};padding:5px 11px;margin:4px;border-radius:6px;font-weight:bold;color:#1e293b;display:inline-block;font-size:14px;box-shadow: 1px 1px 2px rgba(0,0,0,0.1)">{val}</span>'
        st.markdown(html, unsafe_allow_html=True)

        st.markdown("#### Statistik Akumulasi Token")
        counts = Counter(t for t, v in tokens)
        stat_html = "<div style='display: flex; flex-wrap: wrap; gap: 10px; margin-bottom: 15px;'>"
        for ttype, count in counts.items():
            color = COLORS.get(ttype, '#ffffff')
            stat_html += f'<div style="background:#f8fafc; padding:6px 12px; border-radius:6px; border-left:4px solid {color}; font-size:13.5px; color:#334155;"><b>{ttype}</b>: {count} buah</div>'
        stat_html += "</div>"
        st.markdown(stat_html, unsafe_allow_html=True)

        st.markdown("#### Tabel Analisis Kamus Detail")
        table_data = []
        for i, (t, v) in enumerate(tokens):
            table_data.append({
                "No": i + 1, 
                "Karakter/Token": v, 
                "Jenis Komponen": t,
                "Kegunaan / Arti": get_token_meaning(t, v)
            })
        st.dataframe(pd.DataFrame(table_data), use_container_width=True, hide_index=True)
        
        unknowns = [v for t, v in tokens if t == 'UNKNOWN']
        if unknowns:
            st.error(f"Perhatian! Ditemukan {len(unknowns)} karakter tidak dikenal (Eror Coding): {', '.join(unknowns)}")
    else:
        st.caption("Menunggu input kode dimasukkan...")

# --- HALAMAN 3: BUKU PANDUAN MATERI ---
elif selected == "Buku Panduan":
    st.markdown("<h3 style='color: #1e293b; font-weight: 700;'>[ DOCS ] Buku Panduan & Kamus Referensi</h3>", unsafe_allow_html=True)
    st.write("Gunakan halaman ini sebagai panduan cepat memahami cara komputer membaca komponen coding.")
    st.write("---")
    
    # 1. PENGANTAR ALUR KERJA
    st.markdown("#### >> Bagaimana Cara Komputer Membaca Kodemu?")
    st.write("""
    Sebelum program bisa dijalankan, baris kode buatanmu wajib diterjemahkan oleh sistem penerjemah yang disebut **Kompiler (Compiler)**. 
    Proses paling awalnya dinamakan **Analisis Leksikal**, yaitu tugas memotong-motong kode menjadi bagian kecil yang disebut **Token**.
    """)
    st.markdown("""
    * **[1] Membaca** > Sistem membaca kode yang kamu ketik satu per satu dari kiri ke kanan.
    * **[2] Membersihkan** > Sistem otomatis membuang spasi kosong atau catatan komentar yang tidak penting bagi komputer.
    * **[3] Melabeli** > Potongan kode yang tersisa langsung diberi warna sesuai jenis komponennya.
    """)
        
    st.write("---")
    
    # 2. LEGENDA WARNA (KAMUS REFERENSI)
    st.markdown("#### >> Kamus Arti Warna Komponen")
    for ttype, desc in TYPE_DESCRIPTIONS.items():
        color = COLORS.get(ttype, '#ffffff')
        st.markdown(f"""
        <div style="border-left: 6px solid {color}; background-color: #f8fafc; padding: 12px; border-radius: 0px 8px 8px 0px; margin-bottom: 12px; box-shadow: 0 1px 3px rgba(0,0,0,0.05)">
            <span style="background:{color}; padding: 3px 10px; border-radius: 4px; font-weight: bold; color: #1e293b; font-size: 13px;">{ttype}</span>
            <div style="margin-top: 8px; font-size: 14px; color: #334155; line-height: 1.5;">{desc}</div>
        </div>
        """, unsafe_allow_html=True)

    st.write("---")

    # 3. KONTEN CHEAT SHEET: CONTOH KODE SIAP PAKAI
    st.markdown("#### >> Contoh Kode Siap Pakai (Salin & Tempel di Simulator)")
    st.write("Kamu bisa salin salah satu contoh kode di bawah ini untuk diuji langsung di menu Simulator Token:")
    
    st.markdown("**Contoh 1: Logika Percabangan (Bahasa Python)**")
    st.code("""# Menguji kondisi angka
nilai = 80
if nilai >= 75:
    print("Kamu Lulus!")
else:
    print("Remedial")""", language="python")

    st.markdown("**Contoh 2: Deklarasi Variabel & Hitungan (Bahasa C)**")
    st.code("""int alas = 10;
int tinggi = 5;
int luas = alas * tinggi / 2;""", language="c")

    st.write("---")

    # 4. KONTEN TROUBLESHOOTING: DETEKSI EROR
    st.markdown("#### >> Panduan Mengatasi Eror Leksikal (UNKNOWN)")
    st.write("""
    Jika saat menjalankan simulator kamu melihat warna merah menyala dengan label **UNKNOWN**, 
    artinya kamu memasukkan simbol atau karakter asing yang **tidak terdaftar** dalam aturan bahasa pemrograman teks tersebut.
    
    * **Penyebab Umum:** Mengetik simbol aneh di luar tanda kutip teks, seperti penggunaan karakter `@`, `$`, atau `~` secara sembarangan di baris kode kalkulasi matematika.
    * **Solusinya:** Pastikan semua simbol matematika dan tanda baca pembatas ditulis menggunakan karakter standar yang dikenali keyboard komputer (seperti `+`, `-`, `*`, `/`, `=`, `;`).
    """)

# ==========================================
# 4. WATERMARK / FOOTER (TEGAS & KONSISTEN)
# ==========================================
st.markdown("---")
st.markdown("<div style='text-align: center; color: #334155; font-size: 13px; font-weight: 500;'>Media Edukasi Teknik Kompilasi - Magang Berdampak Unipol 2026</div>", unsafe_allow_html=True)
