"""Dompet Pintar - Aplikasi Pencatat Keuangan Pribadi (Multi-User Streamlit)."""
import os
from datetime import date, timedelta

import pandas as pd
import streamlit as st
from streamlit_option_menu import option_menu

# Konfigurasi Tampilan Halaman Web
st.set_page_config(page_title="Dompet Pintar", page_icon="💰", layout="wide")

# ---------------------------------------------------------------- Konfigurasi Folder & File User
DATA_DIR = "data"
OS_USERS_FILE = os.path.join(DATA_DIR, "users.csv")
os.makedirs(DATA_DIR, exist_ok=True)


# --- Fungsi Manajemen Akun (Login & Register) ---
def load_users():
    if os.path.exists(OS_USERS_FILE):
        return pd.read_csv(OS_USERS_FILE, dtype=str)
    else:
        # User default pertama kali
        df_default = pd.DataFrame({"username": ["admin"], "password": ["admin123"]})
        df_default.to_csv(OS_USERS_FILE, index=False)
        return df_default


def register_user(username, password):
    df_users = load_users()
    if username in df_users["username"].values:
        return False  # Username sudah terdaftar
    
    baru = pd.DataFrame({"username": [username], "password": [password]})
    df_users = pd.concat([df_users, baru], ignore_index=True)
    df_users.to_csv(OS_USERS_FILE, index=False)
    return True


# --- Fungsi Data Keuangan Berdasarkan User yang Login ---
def get_user_files():
    user = st.session_state.get("user", "default")
    file_trx = os.path.join(DATA_DIR, f"transaksi_{user}.csv")
    file_anggaran = os.path.join(DATA_DIR, f"anggaran_{user}.csv")
    file_target = os.path.join(DATA_DIR, f"target_{user}.csv")
    return file_trx, file_anggaran, file_target


KOLOM_TRX = ["tanggal", "jenis", "kategori", "jumlah", "catatan"]
KATEGORI = {
    "Pemasukan": ["Uang Saku/Gaji", "Bonus", "Lainnya"],
    "Pengeluaran": [
        "Makan & Minum", "Transportasi", "Belanja",
        "Tagihan", "Hiburan", "Pendidikan", "Lainnya",
    ],
}


def rupiah(angka):
    return "Rp " + f"{angka:,.0f}".replace(",", ".")


def load_trx():
    file_trx, _, _ = get_user_files()
    if os.path.exists(file_trx):
        df = pd.read_csv(file_trx)
    else:
        df = pd.DataFrame(columns=KOLOM_TRX)
    df["tanggal"] = pd.to_datetime(df["tanggal"])
    df["jumlah"] = pd.to_numeric(df["jumlah"])
    df["catatan"] = df["catatan"].fillna("")
    df["bulan"] = df["tanggal"].dt.strftime("%Y-%m")
    return df


def save_trx(df):
    file_trx, _, _ = get_user_files()
    df[KOLOM_TRX].to_csv(file_trx, index=False)


def tambah_trx(tanggal, jenis, kategori, jumlah, catatan=""):
    df = load_trx()
    baru = pd.DataFrame(
        [{
            "tanggal": pd.to_datetime(tanggal),
            "jenis": jenis,
            "kategori": kategori,
            "jumlah": jumlah,
            "catatan": catatan,
        }]
    )
    df = baru if df.empty else pd.concat([df[KOLOM_TRX], baru], ignore_index=True)
    save_trx(df)


def load_anggaran():
    _, file_anggaran, _ = get_user_files()
    if os.path.exists(file_anggaran):
        df = pd.read_csv(file_anggaran)
        return dict(zip(df["kategori"], df["batas"]))
    return {}


def load_target():
    _, _, file_target = get_user_files()
    if os.path.exists(file_target):
        return pd.read_csv(file_target)
    return pd.DataFrame(columns=["nama", "target", "terkumpul"])


def isi_contoh():
    """Mengisi data contoh otomatis agar dashboard tidak kosong."""
    hari_ini = date.today()
    contoh = [
        (0, "Pemasukan", "Uang Saku/Gaji", 2500000, "Kiriman bulanan"),
        (1, "Pengeluaran", "Makan & Minum", 35000, "Makan siang"),
        (2, "Pengeluaran", "Transportasi", 20000, "Ojek online"),
        (3, "Pengeluaran", "Belanja", 150000, "Belanja bulanan"),
        (4, "Pengeluaran", "Hiburan", 60000, "Nonton bioskop"),
        (7, "Pemasukan", "Bonus", 300000, "Freelance"),
    ]
    for hari_lalu, jenis, kat, jml, cat in contoh:
        tambah_trx(hari_ini - timedelta(days=hari_lalu), jenis, kat, jml, cat)


# ------------------------------------------------------------------- Halaman Login & Register
def halaman_login():
    st.title("💰 Dompet Pintar")
    st.caption("Catat keuanganmu, kendalikan pengeluaranmu.")
    
    tab_login, tab_register = st.tabs(["Masuk (Login)", "Daftar Akun Baru (Register)"])
    
    with tab_login:
        with st.form("form_login"):
            user = st.text_input("Username")
            pwd = st.text_input("Password", type="password")
            masuk = st.form_submit_button("Masuk")
        if masuk:
            df_users = load_users()
            user_row = df_users[df_users["username"] == user]
            if not user_row.empty and user_row.iloc[0]["password"] == pwd:
                st.session_state.login = True
                st.session_state.user = user
                st.success("Berhasil masuk!")
                st.rerun()
            else:
                st.error("Username atau password salah.")

    with tab_register:
        with st.form("form_register"):
            new_user = st.text_input("Buat Username Baru")
            new_pwd = st.text_input("Buat Password Baru", type="password")
            daftar = st.form_submit_button("Daftar Akun")
        if daftar:
            if not new_user.strip() or not new_pwd.strip():
                st.error("Username dan password tidak boleh kosong.")
            else:
                sukses = register_user(new_user.strip(), new_pwd.strip())
                if sukses:
                    st.success("Akun berhasil dibuat! Silakan pindah ke tab 'Masuk (Login)'.")
                else:
                    st.error("Username sudah digunakan, silakan pilih nama lain.")


# ------------------------------------------------------------------- Halaman Menu Utama
def halaman_dashboard():
    st.header(f"📊 Dashboard ({st.session_state.user})")
    df = load_trx()

    if df.empty:
        st.info("Belum ada transaksi. Mulai dari menu **Catat Transaksi**, atau isi data contoh.")
        if st.button("Isi data contoh"):
            isi_contoh()
            st.rerun()
        return

    bulan_ini = date.today().strftime("%Y-%m")
    bln = df[df["bulan"] == bulan_ini]
    masuk = bln.loc[bln["jenis"] == "Pemasukan", "jumlah"].sum()
    keluar = bln.loc[bln["jenis"] == "Pengeluaran", "jumlah"].sum()
    saldo = (
        df.loc[df["jenis"] == "Pemasukan", "jumlah"].sum()
        - df.loc[df["jenis"] == "Pengeluaran", "jumlah"].sum()
    )

    c1, c2, c3 = st.columns(3)
    c1.metric("Saldo total", rupiah(saldo))
    c2.metric("Pemasukan bulan ini", rupiah(masuk))
    c3.metric("Pengeluaran bulan ini", rupiah(keluar))

    kiri, kanan = st.columns(2)
    with kiri:
        st.subheader("Pengeluaran per kategori (bulan ini)")
        per_kat = bln[bln["jenis"] == "Pengeluaran"].groupby("kategori")["jumlah"].sum()
        if per_kat.empty:
            st.caption("Belum ada pengeluaran bulan ini.")
        else:
            st.bar_chart(per_kat)
    with kanan:
        st.subheader("Tren harian (bulan ini)")
        if bln.empty:
            st.caption("Belum ada transaksi bulan ini.")
        else:
            tren = bln.groupby(["tanggal", "jenis"])["jumlah"].sum().unstack(fill_value=0)
            st.line_chart(tren)

    st.subheader("5 transaksi terakhir")
    terakhir = df.sort_values("tanggal", ascending=False).head(5).copy()
    terakhir["tanggal"] = terakhir["tanggal"].dt.strftime("%d-%m-%Y")
    st.dataframe(
        terakhir[KOLOM_TRX],
        hide_index=True,
        column_config={"jumlah": st.column_config.NumberColumn("Jumlah", format="Rp %d")},
    )


def halaman_catat():
    st.header("📝 Catat Transaksi")
    jenis = st.radio("Jenis", ["Pengeluaran", "Pemasukan"], horizontal=True)
    with st.form("form_trx", clear_on_submit=True):
        tanggal = st.date_input("Tanggal", value=date.today())
        kategori = st.selectbox("Kategori", KATEGORI[jenis])
        jumlah = st.number_input("Jumlah (Rp)", min_value=0, step=1000)
        catatan = st.text_input("Catatan (opsional)")
        simpan = st.form_submit_button("Simpan Transaksi")

    if simpan:
        if jumlah <= 0:
            st.error("Jumlah harus lebih dari 0.")
        else:
            tambah_trx(tanggal, jenis, kategori, jumlah, catatan.strip())
            st.success(f"{jenis} {rupiah(jumlah)} untuk '{kategori}' berhasil tersimpan!")


def halaman_belanja():
    st.header("🛒 Hitung Belanja")
    st.caption("Isi daftar belanjaan, total dihitung otomatis, lalu simpan sebagai pengeluaran.")
    awal = pd.DataFrame({"Barang": [""], "Jumlah": [1], "Harga Satuan": [0]})
    edit = st.data_editor(
        awal,
        num_rows="dynamic",
        key="tabel_belanja",
        column_config={
            "Jumlah": st.column_config.NumberColumn(min_value=1, step=1),
            "Harga Satuan": st.column_config.NumberColumn(min_value=0, step=500, format="Rp %d"),
        },
    )
    edit = edit.copy()
    edit["Jumlah"] = pd.to_numeric(edit["Jumlah"], errors="coerce").fillna(0)
    edit["Harga Satuan"] = pd.to_numeric(edit["Harga Satuan"], errors="coerce").fillna(0)
    edit["Total"] = edit["Jumlah"] * edit["Harga Satuan"]
    total = edit["Total"].sum()
    st.metric("Total belanja", rupiah(total))

    if st.button("Simpan sebagai pengeluaran"):
        if total <= 0:
            st.error("Total masih 0. Isi barang dan harganya dulu.")
        else:
            barang = [b for b in edit["Barang"].astype(str) if b.strip()]
            catatan = "Belanja: " + ", ".join(barang) if barang else "Belanja"
            tambah_trx(date.today(), "Pengeluaran", "Belanja", total, catatan[:200])
            st.success("Berhasil tersimpan sebagai pengeluaran kategori Belanja!")


def halaman_anggaran():
    st.header("💼 Anggaran Bulanan")
    batas = load_anggaran()

    st.subheader("Atur batas per kategori")
    with st.form("form_anggaran"):
        kolom = st.columns(2)
        input_batas = {}
        for i, kat in enumerate(KATEGORI["Pengeluaran"]):
            with kolom[i % 2]:
                input_batas[kat] = st.number_input(
                    kat, min_value=0, value=int(batas.get(kat, 0)),
                    step=50000, key=f"anggaran_{kat}",
                )
        simpan = st.form_submit_button("Simpan Anggaran")
    if simpan:
        _, file_anggaran, _ = get_user_files()
        pd.DataFrame({"kategori": list(input_batas), "batas": list(input_batas.values())}) \
            .to_csv(file_anggaran, index=False)
        st.success("Anggaran berhasil disimpan.")

    st.subheader("Pemakaian bulan ini")
    df = load_trx()
    bln = df[(df["bulan"] == date.today().strftime("%Y-%m")) & (df["jenis"] == "Pengeluaran")]
    terpakai = bln.groupby("kategori")["jumlah"].sum().to_dict()

    ada = False
    for kat in KATEGORI["Pengeluaran"]:
        limit = batas.get(kat, 0)
        if limit <= 0:
            continue
        ada = True
        pakai = terpakai.get(kat, 0)
        persen = pakai / limit if limit > 0 else 0
        st.write(f"**{kat}**: {rupiah(pakai)} dari {rupiah(limit)} ({persen * 100:.0f}%)")
        st.progress(min(persen, 1.0))
        if persen > 1:
            st.error(f"Anggaran {kat} sudah terlampaui {rupiah(pakai - limit)}!")
        elif persen >= 0.8:
            st.warning(f"Anggaran {kat} hampir habis.")
    if not ada:
        st.info("Belum ada batas anggaran yang diatur.")


def halaman_target():
    st.header("🎯 Target Tabungan")
    df = load_target()
    _, _, file_target = get_user_files()

    with st.expander("➕ Tambah target baru", expanded=df.empty):
        with st.form("form_target", clear_on_submit=True):
            nama = st.text_input("Nama target (mis. Laptop baru)")
            target = st.number_input("Jumlah target (Rp)", min_value=0, step=100000)
            kirim = st.form_submit_button("Simpan Target")
        if kirim:
            if not nama.strip() or target <= 0:
                st.error("Isi nama target dan jumlah lebih dari 0.")
            elif not df.empty and nama.strip() in df["nama"].tolist():
                st.error("Nama target sudah ada.")
            else:
                baru = pd.DataFrame([{"nama": nama.strip(), "target": target, "terkumpul": 0}])
                df = baru if df.empty else pd.concat([df, baru], ignore_index=True)
                df.to_csv(file_target, index=False)
                st.success("Target berhasil disimpan.")
                st.rerun()

    if df.empty:
        st.info("Belum ada target tabungan.")
        return

    st.subheader("Tambah setoran")
    with st.form("form_setoran", clear_on_submit=True):
        pilih = st.selectbox("Target", df["nama"].tolist())
        setor = st.number_input("Jumlah setoran (Rp)", min_value=0, step=10000)
        kirim = st.form_submit_button("Setor")
    if kirim:
        if setor <= 0:
            st.error("Setoran harus lebih dari 0.")
        else:
            df.loc[df["nama"] == pilih, "terkumpul"] += setor
            df.to_csv(file_target, index=False)
            st.success(f"Setoran {rupiah(setor)} berhasil ditambahkan!")
            st.rerun()

    st.subheader("Progres")
    for _, r in df.iterrows():
        persen = min(r["terkumpul"] / r["target"], 1.0) if r["target"] > 0 else 0
        st.write(f"**{r['nama']}**: {rupiah(r['terkumpul'])} dari {rupiah(r['target'])} ({persen * 100:.0f}%)")
        st.progress(persen)
        if persen >= 1:
            st.success("Target tercapai! 🎉")

    with st.expander("🗑️ Hapus target"):
        hapus = st.selectbox("Pilih target", df["nama"].tolist(), key="hapus_target")
        if st.button("Hapus target ini"):
            df[df["nama"] != hapus].to_csv(file_target, index=False)
            st.rerun()


def halaman_laporan():
    st.header("📈 Laporan Keuangan")
    df = load_trx()
    if df.empty:
        st.info("Belum ada data untuk dilaporkan.")
        return

    c1, c2 = st.columns(2)
    bulan_opsi = ["Semua"] + sorted(df["bulan"].unique(), reverse=True)
    bulan = c1.selectbox("Bulan", bulan_opsi)
    jenis = c2.selectbox("Jenis", ["Semua", "Pemasukan", "Pengeluaran"])

    f = df.copy()
    if bulan != "Semua":
        f = f[f["bulan"] == bulan]
    if jenis != "Semua":
        f = f[f["jenis"] == jenis]
    f = f.sort_values("tanggal", ascending=False)

    if f.empty:
        st.warning("Tidak ada transaksi untuk filter ini.")
        return

    masuk = f.loc[f["jenis"] == "Pemasukan", "jumlah"].sum()
    keluar = f.loc[f["jenis"] == "Pengeluaran", "jumlah"].sum()
    m1, m2, m3 = st.columns(3)
    m1.metric("Total pemasukan", rupiah(masuk))
    m2.metric("Total pengeluaran", rupiah(keluar))
    m3.metric("Selisih", rupiah(masuk - keluar))

    st.subheader("Total per kategori")
    st.bar_chart(f.groupby("kategori")["jumlah"].sum())

    st.subheader("Riwayat transaksi")
    tampil = f[KOLOM_TRX].copy()
    tampil["tanggal"] = tampil["tanggal"].dt.strftime("%d-%m-%Y")
    st.dataframe(
        tampil,
        hide_index=True,
        column_config={"jumlah": st.column_config.NumberColumn("Jumlah", format="Rp %d")},
    )
    st.download_button(
        "⬇️ Unduh CSV",
        data=tampil.to_csv(index=False).encode("utf-8"),
        file_name="laporan_keuangan.csv",
        mime="text/csv",
    )

    with st.expander("🗑️ Hapus transaksi"):
        label = {
            i: f"{r.tanggal.strftime('%d-%m-%Y')} | {r.kategori} | {rupiah(r.jumlah)} | {r.catatan}"
            for i, r in f.iterrows()
        }
        if label:
            pilih = st.selectbox("Pilih transaksi", list(label), format_func=lambda i: label[i])
            if st.button("Hapus transaksi ini"):
                save_trx(df.drop(index=pilih))
                st.rerun()


# ---------------------------------------------------------------------- Main Program Flow
if "login" not in st.session_state:
    st.session_state.login = False

if not st.session_state.login:
    halaman_login()
    st.stop()

# Sidebar Menu Setelah Berhasil Login
with st.sidebar:
    st.markdown("## 💰 Dompet Pintar")
    st.write(f"👤 Login sebagai: **{st.session_state.user}**")
    pilihan = option_menu(
        "Menu",
        ["Dashboard", "Catat Transaksi", "Hitung Belanja",
         "Anggaran", "Target Tabungan", "Laporan"],
        icons=["speedometer2", "pencil-square", "calculator",
               "wallet2", "piggy-bank", "graph-up"],
        menu_icon="list",
        default_index=0,
    )
    if st.button("Logout"):
        st.session_state.login = False
        st.session_state.user = ""
        st.rerun()
    st.caption("PEMROGRAMAN PYTHON")

HALAMAN = {
    "Dashboard": halaman_dashboard,
    "Catat Transaksi": halaman_catat,
    "Hitung Belanja": halaman_belanja,
    "Anggaran": halaman_anggaran,
    "Target Tabungan": halaman_target,
    "Laporan": halaman_laporan,
}
HALAMAN[pilihan]()