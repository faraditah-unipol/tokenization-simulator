import streamlit as st
import re
import pandas as pd
from collections import Counter
from streamlit_option_menu import option_menu

# ==========================================
# 1. KONFIGURASI HALAMAN & ATURAN TOKEN
# ==========================================
st.set_page_config(page_title="Lexical Analyzer Simulator", page_icon="🔤", layout="centered")

TOKEN_RULES = [
    ('KEYWORD', r'\b(int|float|string|if|else|while|for|return|void|bool|true|false|print|def|class|import|from|True|False|None|and|or|not|in|is|elif|pass|break|continue|lambda|with|as|try|except|finally|raise|input|len|range|type|str|list|dict|tuple|set)\b'),
    ('NUMBER', r'\b\d+(\.\d+)?\b'),
    ('STRING', r'"[^"]*"|\'[^\']*\''),
    ('IDENTIFIER', r'\b[a-zA-Z_][a-zA-Z0-9_]*\b'),
    ('OPERATOR', r'==|!=|<=|>=|\+=|-=|\*\*|[+\-\*/=<>!&|%^~]'),
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
    'KEYWORD': '<b>Kata Kunci Resmi (Reserved Words)</b> — Kata bawaan yang sudah dipesan oleh bahasa pemrograman dan memiliki arti khusus bagi komputer.<br><i>Contoh: int, if, else, while, return, print.</i>',
    'IDENTIFIER': '<b>Identitas / Nama Buatan</b> — Nama yang diciptakan oleh programmer untuk menandai sebuah variabel, fungsi, atau nama kelas.<br><i>Contoh: nama_user, nilai_x, total_biaya, hitung_eoq.</i>',
    'NUMBER': '<b>Konstanta Angka (Literal Numerik)</b> — Semua jenis data berbentuk nilai angka konstanta, baik bilangan bulat (integer) maupun desimal (float).<br><i>Contoh: 5, 12, 3.14, 100.</i>',
    'STRING': '<b>Literal Teks (String)</b> — Kumpulan karakter huruf atau kalimat yang wajib diapit oleh tanda kutip tunggal (\') atau tanda kutip ganda (").<br><i>Contoh: "Halo Dunia", \'Timah Solder\'.</i>',
    'OPERATOR': '<b>Simbol Operasi (Operator)</b> — Karakter khusus yang digunakan untuk melakukan proses perhitungan matematika, perbandingan nilai, atau logika.<br><i>Contoh: +, -, *, =, ==, !=, <=.</i>',
    'DELIMITER': '<b>Pembatas Kode (Delimiter)</b> — Tanda baca pemisah antar perintah, penanda pembuka/penutup blok kode, ataupun argumen fungsi.<br><i>Contoh: ; , ( ) { } [ ] :</i>',
    'COMMENT': '<b>Catatan Programmer (Komentar)</b> — Teks penjelasan di dalam baris kode yang sengaja diabaikan oleh mesin komputer saat proses kompilasi.<br><i>Contoh: # Ini fungsi hitung, // Variabel utama.</i>',
    'UNKNOWN': '<b>⚠️ Karakter Tidak Dikenal</b> — Karakter asing atau simbol ilegal yang tidak terdaftar ke dalam aturan bahasa pemrograman teks tersebut.',
}

OPERATOR_MAP = {
    '+': 'Operator penjumlahan', '-': 'Operator pengurangan', '*': 'Operator perkalian', 
    '/': 'Operator pembagian', '=': 'Operator penugasan (assignment)', '==': 'Operator perbandingan sama dengan',
    '!=': 'Operator perbandingan tidak sama dengan', '<': 'Operator lebih kecil dari', '>': 'Operator lebih besar dari',
    '<=': 'Operator lebih kecil atau sama dengan', '>=': 'Operator lebih besar atau sama dengan',
    '%': 'Operator sisa bagi (modulo)', '**': 'Operator perpangkatan', '+=': 'Operator tambah sekaligus assign',
    '-=': 'Operator kurang sekaligus assign',
}

KEYWORD_MAP = {
    'int': 'Tipe data bilangan bulat', 'float': 'Tipe data bilangan desimal', 'string': 'Tipe data teks',
    'str': 'Tipe data teks (Python)', 'bool': 'Tipe data boolean', 'void': 'Fungsi tanpa nilai balik',
    'if': 'Percabangan (Jika)', 'else': 'Percabangan (Selain itu)', 'elif': 'Kondisi alternatif',
    'while': 'Perulangan (Selama)', 'for': 'Perulangan (Iterasi)', 'return': 'Mengembalikan nilai',
    'def': 'Mendefinisikan fungsi', 'print': 'Output teks ke layar', 'True': 'Boolean Benar', 'False': 'Boolean Salah'
}

DELIMITER_MAP = {
    ';': 'Akhir pernyataan koding', ',': 'Pemisah elemen data', ':': 'Pembuka blok kode baru', '(': 'Buka kurung parameter',
    ')': 'Tutup kurung parameter', '{': 'Buka kurung kurawal fungsi', '}': 'Tutup kurung kurawal fungsi', '[': 'Buka kurung siku array', ']': 'Tutup kurung siku array'
}

# ==========================================
# 2. FUNGSI LOGIKA TOKENIZER
# ==========================================
def get_token_meaning(ttype, value):
    if ttype == 'NUMBER': return f'Bilangan {"desimal" if "." in value else "bulat (integer)"}: {value}'
    if ttype == 'STRING': return f'Data teks (string): {value}'
    if ttype == 'IDENTIFIER': return f'Nama variabel/fungsi buatan: {value}'
    if ttype == 'COMMENT': return f'Komentar program: {value}'
    if ttype == 'OPERATOR': return OPERATOR_MAP.get(value, f'Operator: {value}')
    if ttype == 'KEYWORD': return KEYWORD_MAP.get(value, f'Kata kunci: {value}')
    if ttype == 'DELIMITER': return DELIMITER_MAP.get(value, f'Delimiter: {value}')
    return f'Token: {value}'

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
# 3. INTERFACE MENU NAVIGASI (PROFESIONAL)
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
    st.markdown("<p style='text-align: center; color: #64748b; font-size: 13px; font-weight: 700; letter-spacing: 2px; margin-bottom: 0px;'>KKN MAGANG BERDAMPAK UNIPOL 2026</p>", unsafe_allow_html=True)
    st.markdown("<h2 style='text-align: center; color: #1e293b; font-weight: 800; margin-top: 5px; margin-bottom: 20px; letter-spacing: 0.5px;'>LEXICAL ANALYZER SIMULATOR</h2>", unsafe_allow_html=True)
    st.write("---")
    
    st.markdown("""
    <div style="background-color: #f8fafc; padding: 20px; border-radius: 12px; border: 1px solid #e2e8f0; margin-bottom: 20px;">
        <h4 style="color: #1e293b; margin-top: 0px;">👋 Selamat Datang!</h4>
        <p style="color: #475569; font-size: 14.5px; line-height: 1.6; margin-bottom: 0px;">
            Media edukasi digital ini dikembangkan untuk membantu siswa memahami mata pelajaran <b>Teknik Kompilasi</b>, khususnya pada tahap awal yaitu <b>Analisis Leksikal</b>.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    st.info("🎯 **Tujuan Aplikasi:** Membedah setiap baris kode pemrograman menjadi komponen terkecil (Token) sehingga struktur bahasa dapat dipahami oleh komputer secara otomatis.")
    
    st.markdown("### 🚀 Petunjuk Penggunaan:")
    st.markdown("""
    1. Pilih menu **Simulator Token** di atas untuk mulai menguji dan menganalisis kode pemrogramanmu.
    2. Pilih menu **Buku Panduan** untuk melihat referensi teori materi dan arti dari setiap warna token.
    """)

# --- HALAMAN 2: SIMULATOR TOKEN ---
elif selected == "Simulator Token":
    st.markdown("<h3 style='color: #1e293b; font-weight: 700;'>🤖 Simulator Analisis Leksikal</h3>", unsafe_allow_html=True)
    st.write("Ketik atau tempel kode pemrograman (Python / C) kamu di bawah ini untuk dibedah secara otomatis.")
    
    code_input = st.text_area(
        "Masukkan Source Code:",
        height=180,
        placeholder='Contoh: int total = x + 5; atau print("Nilai optimal")',
        value=st.session_state.code_input,
        key=f"code_area_{st.session_state.get('_reset_key', 0)}"
    )

    c1, c2 = st.columns(2)
    with c1:
        tokenize_btn = st.button("Jalankan Analisis Token ▶", use_container_width=True, type="primary")
    with c2:
        reset_btn = st.button("🔄 Bersihkan Kolom", use_container_width=True)

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
        
        st.markdown("#### 🧩 Visualisasi Hasil Potongan Token")
        html = ""
        for ttype, val in tokens:
            color = COLORS.get(ttype, '#ffffff')
            html += f'<span style="background:{color};padding:5px 11px;margin:4px;border-radius:6px;font-weight:bold;color:#1e293b;display:inline-block;font-size:14px;box-shadow: 1px 1px 2px rgba(0,0,0,0.1)">{val}</span>'
        st.markdown(html, unsafe_allow_html=True)

        st.markdown("#### 📊 Tabel Analisis Kamus Detail")
        table_data = []
        for i, (t, v) in enumerate(tokens):
            table_data.append({
                "No": i + 1, "Karakter/Token": v, "Kategori Tipe": t,
                "Arti Fungsional Kata": get_token_meaning(t, v)
            })
        st.dataframe(pd.DataFrame(table_data), use_container_width=True, hide_index=True)
        
        unknowns = [v for t, v in tokens if t == 'UNKNOWN']
        if unknowns:
            st.error(f"⚠️ Perhatian! Ditemukan {len(unknowns)} karakter tidak dikenal (Error Leksikal): {', '.join(unknowns)}")
    else:
        st.caption("Menunggu input source code dimasukkan...")

# --- HALAMAN 3: BUKU PANDUAN MATERI ---
elif selected == "Buku Panduan":
    st.markdown("<h3 style='color: #1e293b; font-weight: 700;'>📘 Buku Panduan & Kamus Referensi</h3>", unsafe_allow_html=True)
    st.write("Gunakan halaman ini sebagai modul belajar memahami klasifikasi komponen dalam pemrograman.")
    st.write("---")
    
    col_a, col_b = st.columns([1.1, 0.9])
    
    with col_a:
        st.markdown("#### 🧠 Pengantar Teori Kompilasi")
        st.write("""
        Sebelum sebuah software/aplikasi dijalankan oleh komputer, baris kode buatan programmer wajib diterjemahkan terlebih dahulu oleh sistem penelaah yang disebut **Kompiler (Compiler)**.
        
        Proses penerjemahan paling awal ini dinamakan **Analisis Leksikal (Lexical Analysis)** atau *Tokenizer*.
        """)
        
        st.markdown("##### ⚙️ Alur Kerja Sistem Tokenizer:")
        st.markdown("""
        1. **Scanning (Pemindaian):** Karakter kode dibaca dari kiri ke kanan.
        2. **Filtering (Penyaringan):** Karakter tidak penting (seperti spasi kosong & catatan komentar) dibuang dari antrean.
        3. **Labeling (Pelabelan):** Kata yang tersisa dicocokkan dengan aturan baku matematika logika (**Regular Expression**) lalu dikelompokkan ke kategori tipenya masing-masing.
        """)
        st.info("💡 **Tips Belajar:** Jalankan simulasi kodinganmu di menu kedua, lalu lihat statistik akumulasi jenis kata yang paling sering kamu gunakan di kolom sebelah kanan ini!")

    with col_b:
        st.markdown("#### 📈 Statistik Pengujian")
        if st.session_state.show_result and st.session_state.code_input:
            tokens = tokenize(st.session_state.code_input)
            counts = Counter(t for t, v in tokens)
            
            stat_html = "<ul>"
            for ttype, count in counts.items():
                color = COLORS.get(ttype, '#ffffff')
                stat_html += f'<li style="margin-bottom:8px;"><span style="background:{color};padding:3px 10px;border-radius:12px;font-weight:bold;color:#1e293b;font-size:13px;display:inline-block;width:110px;text-align:center;">{ttype}</span> : {count} buah kata</li>'
            stat_html += "</ul>"
            st.markdown(stat_html, unsafe_allow_html=True)
        else:
            st.caption("Belum ada data pengujian. Silakan jalankan simulasi kode terlebih dahulu di menu Simulator Token.")
            
    st.write("---")
    st.markdown("#### 🏷️ Legenda Klasifikasi Warna & Tipe Token")
    
    for ttype, desc in TYPE_DESCRIPTIONS.items():
        color = COLORS.get(ttype, '#ffffff')
        st.markdown(f"""
        <div style="border-left: 6px solid {color}; background-color: #f8fafc; padding: 12px; border-radius: 0px 8px 8px 0px; margin-bottom: 12px; box-shadow: 0 1px 3px rgba(0,0,0,0.05)">
            <span style="background:{color}; padding: 3px 10px; border-radius: 4px; font-weight: bold; color: #1e293b; font-size: 13px;">{ttype}</span>
            <div style="margin-top: 8px; font-size: 14px; color: #334155; line-height: 1.5;">{desc}</div>
        </div>
        """, unsafe_allow_html=True)

# Footer Watermark Hak Cipta Proker
st.markdown("---")
st.markdown("<div style='text-align: center; color: #cbd5e1; font-size: 11px; font-weight:500;'>© 2026 Media Edukasi Teknik Kompilasi - Magang Berdampak UNIPOL</div>", unsafe_allow_html=True)
