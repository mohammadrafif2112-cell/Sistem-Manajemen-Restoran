import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
import os

# ===============================
#  THEME / COLOR CONFIG
# ===============================
COLOR_BG = "#f0f7ff"
COLOR_FRAME = "#e3efff"
COLOR_HEADER = "#005bbb"
COLOR_TEXT = "#003f7d"

COLOR_BTN_PRIMARY = "#4b9cff"
COLOR_BTN_SUCCESS = "#48c774"
COLOR_BTN_WARNING = "#ffdd57"
COLOR_BTN_DANGER = "#ff6b6b"

# ===============================
#  SAMPLE DATA & CLASSES
# ===============================
nama_restoran = "Burjo Tubagus"
rating_restoran = 4.9
waktu_buka = "10:00"
waktu_tutup = "22:00"

class MenuItem:
    def __init__(self, id, nama, kategori, harga, stok):
        self.id = id
        self.nama = nama
        self.kategori = kategori
        self.harga = harga
        self.stok = stok

    def get_info(self):
        return f"{self.nama} - Rp {self.harga:,} (Stok: {self.stok})"

    def kurangi_stok(self, jumlah):
        if self.stok >= jumlah:
            self.stok -= jumlah
            return True
        return False

    def tambah_stok(self, jumlah):
        self.stok += jumlah

class Makanan(MenuItem):
    def __init__(self, id, nama, harga, stok, tingkat_kepedasan=0):
        super().__init__(id, nama, "makanan", harga, stok)
        self.tingkat_kepedasan = tingkat_kepedasan

    def get_info(self):
        pedas = " 🌶" * self.tingkat_kepedasan
        return f"🍽️ {self.nama}{pedas} - Rp {self.harga:,} (Stok: {self.stok})"

class Minuman(MenuItem):
    def __init__(self, id, nama, harga, stok, ukuran="regular", dingin=True):
        super().__init__(id, nama, "minuman", harga, stok)
        self.ukuran = ukuran
        self.dingin = dingin

    def get_info(self):
        suhu = "❄️" if self.dingin else "☕"
        return f"🥤 {self.nama} {suhu} - Rp {self.harga:,} (Stok: {self.stok})"

class Meja:
    def __init__(self, nomor, kapasitas=2):
        self.nomor = nomor
        self.kapasitas = kapasitas
        self.status = "kosong"
        self.pesanan = None

class Pesanan:
    def __init__(self, id_pesanan, nomor_meja):
        self.id_pesanan = id_pesanan
        self.nomor_meja = nomor_meja
        self.items = []
        self.status = "aktif"  # aktif -> sedang makan / menunggu, selesai -> sudah diproses
        self.total_harga = 0
        self.waktu_buat = datetime.now()
        self.waktu_selesai = None

    def tambah_item(self, menu_item, jumlah, catatan=""):
        if menu_item.kurangi_stok(jumlah):
            subtotal = menu_item.harga * jumlah
            self.items.append({"menu_item": menu_item, "jumlah": jumlah, "catatan": catatan, "subtotal": subtotal})
            self.total_harga += subtotal
            return True
        return False

    def hapus_item_terakhir(self, menu_item_nama, jumlah):
        """
        Coba hapus item terakhir yang sesuai nama dan jumlah.
        Kembalikan True + subtotal jika berhasil, otherwise False.
        """
        for i in range(len(self.items)-1, -1, -1):
            it = self.items[i]
            if it['menu_item'].nama == menu_item_nama and it['jumlah'] == jumlah:
                subtotal = it['subtotal']
                # restore stok
                it['menu_item'].tambah_stok(it['jumlah'])
                # hapus
                self.total_harga -= subtotal
                self.items.pop(i)
                return True, subtotal
        return False, 0

    def get_info_pesanan(self):
        teks = f"Pesanan #{self.id_pesanan} - Meja {self.nomor_meja}\nStatus: {self.status}\n"
        teks += f"Dibuat: {self.waktu_buat.strftime('%Y-%m-%d %H:%M:%S')}\n"
        if self.waktu_selesai:
            teks += f"Selesai: {self.waktu_selesai.strftime('%Y-%m-%d %H:%M:%S')}\n"
        teks += "-"*36 + "\n"
        for i, it in enumerate(self.items, start=1):
            teks += f"{i}. {it['menu_item'].nama} x{it['jumlah']} - Rp {it['subtotal']:,}\n"
            if it['catatan']:
                teks += f"   Catatan: {it['catatan']}\n"
        teks += "-"*36 + "\n"
        teks += f"TOTAL: Rp {self.total_harga:,}\n"
        return teks

    def get_nota_text(self):
        # Lebih terstruktur untuk nota/receipt
        lines = []
        lines.append(f"{nama_restoran}")
        lines.append(f"Waktu: {self.waktu_buat.strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"Pesanan: #{self.id_pesanan}    Meja: {self.nomor_meja}")
        lines.append("-"*36)
        for it in self.items:
            lines.append(f"{it['menu_item'].nama} x{it['jumlah']}  Rp {it['subtotal']:,}")
            if it['catatan']:
                lines.append(f"  (Catatan: {it['catatan']})")
        lines.append("-"*36)
        lines.append(f"TOTAL: Rp {self.total_harga:,}")
        if self.waktu_selesai:
            lines.append(f"Selesai: {self.waktu_selesai.strftime('%Y-%m-%d %H:%M:%S')}")
        return "\n".join(lines)

# ===============================
#  Manajer Restoran (data & logika)
# ===============================
class ManajerRestoran:
    def __init__(self):
        self.menu_items = []
        self.meja = []
        self.pesanan = []

        # Tambahan: struktur data Stack & Queue
        self.riwayat_aksi = []    # STACK (list, push/pop dari akhir)
        self.antrian_pesanan = [] # QUEUE (list, enqueue di akhir, dequeue di index 0)

        self.load_sample_data()

    def load_sample_data(self):
        # Meja 1-10
        for i in range(1, 11):
            kapasitas = 2 if i <= 5 else 4
            self.meja.append(Meja(i, kapasitas))

        # Menu
        self.menu_items.extend([
            Makanan(1, "Ayam Balap", 15000, 15, 2),
            Makanan(2, "Ayam Bali", 15000, 10, 1),
            Makanan(3, "Mie Dok Dok", 18000, 8, 0),
            Minuman(101, "Es Teh Manis", 5000, 20),
            Minuman(102, "Jus Jeruk", 12000, 15),
            Minuman(103, "Kopi Latte", 18000, 12, "large", False)
        ])

    def buat_pesanan(self, nomor_meja):
        id_pesanan = len(self.pesanan) + 1
        pesanan_baru = Pesanan(id_pesanan, nomor_meja)
        self.pesanan.append(pesanan_baru)
        meja = self.meja[nomor_meja - 1]
        meja.status = "terisi"
        meja.pesanan = pesanan_baru
        return pesanan_baru

    def get_menu_by_kategori(self, kategori):
        return [m for m in self.menu_items if m.kategori == kategori]

    def get_laporan_penjualan(self):
        total_penjualan = sum(p.total_harga for p in self.pesanan if p.status == "selesai")
        jumlah = sum(1 for p in self.pesanan if p.status == "selesai")
        return {"total_penjualan": total_penjualan, "jumlah_pesanan": jumlah, "rata_rata": (total_penjualan / jumlah) if jumlah else 0}

    # ------------------
    # STACK (riwayat aksi)
    # ------------------
    def push_aksi(self, aksi):
        # aksi: string yang menjelaskan aksi, misal "Tambah Ayam Balap x2" atau "Buat pesanan #3"
        self.riwayat_aksi.append(aksi)

    def pop_aksi(self):
        if len(self.riwayat_aksi) > 0:
            return self.riwayat_aksi.pop()
        return None

    # ------------------
    # QUEUE (antrian pesanan untuk dapur)
    # ------------------
    def enqueue_pesanan(self, pesanan):
        self.antrian_pesanan.append(pesanan)

    def dequeue_pesanan(self):
        if len(self.antrian_pesanan) > 0:
            return self.antrian_pesanan.pop(0)
        return None

# ===============================
#  GUI Application
# ===============================
class AplikasiRestoran:
    def __init__(self, root):
        self.root = root
        self.root.title("Sistem Manajemen Restoran - Berwarna")
        self.root.geometry("1000x700")
        self.root.configure(bg=COLOR_BG)

        self.manajer = ManajerRestoran()
        self.pesanan_aktif = None

        self.setup_gui()

    def setup_gui(self):
        style = ttk.Style()
        style.theme_use('default')

        notebook = ttk.Notebook(self.root)
        notebook.pack(expand=True, fill='both')

        frame_beranda = tk.Frame(notebook, bg=COLOR_BG)
        frame_pesanan = tk.Frame(notebook, bg=COLOR_BG)
        frame_menu = tk.Frame(notebook, bg=COLOR_BG)
        frame_meja = tk.Frame(notebook, bg=COLOR_BG)
        frame_nota = tk.Frame(notebook, bg=COLOR_BG)
        frame_antrian = tk.Frame(notebook, bg=COLOR_BG)

        notebook.add(frame_beranda, text="🏠 Beranda")
        notebook.add(frame_pesanan, text="🧾 Pesanan")
        notebook.add(frame_menu, text="🍽 Menu")
        notebook.add(frame_meja, text="🪑 Meja")
        notebook.add(frame_nota, text="🧾 Nota")  # <-- mengganti Laporan menjadi Nota
        notebook.add(frame_antrian, text="🛎 Antrian")

        self.setup_beranda(frame_beranda)
        self.setup_pesanan(frame_pesanan)
        self.setup_menu(frame_menu)
        self.setup_meja(frame_meja)
        self.setup_nota(frame_nota)
        self.setup_antrian(frame_antrian)

    def setup_beranda(self, frame):
        tk.Label(frame, text=f"Selamat Datang di {nama_restoran}", font=("Arial", 20, "bold"), bg=COLOR_BG, fg=COLOR_HEADER).pack(pady=12)

        stats_frame = tk.LabelFrame(frame, text="Statistik Hari Ini", bg=COLOR_FRAME, fg=COLOR_TEXT, padx=10, pady=10)
        stats_frame.pack(fill='x', padx=20, pady=8)

        tk.Label(stats_frame, text=f"Total Meja: {len(self.manajer.meja)}", bg=COLOR_FRAME, fg=COLOR_TEXT).pack(anchor='w')
        tk.Label(stats_frame, text=f"Total Menu: {len(self.manajer.menu_items)}", bg=COLOR_FRAME, fg=COLOR_TEXT).pack(anchor='w')
        tk.Label(stats_frame, text=f"Rating: {rating_restoran} ⭐", bg=COLOR_FRAME, fg=COLOR_TEXT).pack(anchor='w')

    def setup_pesanan(self, frame):
        input_frame = tk.Frame(frame, bg=COLOR_BG)
        input_frame.pack(pady=10, padx=20, anchor='w')

        tk.Label(input_frame, text="Nomor Meja:", bg=COLOR_BG, fg=COLOR_TEXT).grid(row=0, column=0, padx=5)
        self.entry_meja = tk.Entry(input_frame, width=8)
        self.entry_meja.grid(row=0, column=1, padx=5)

        btn_buat = tk.Button(input_frame, text="Buat Pesanan", bg=COLOR_BTN_PRIMARY, fg='white', command=self.buat_pesanan_baru)
        btn_buat.grid(row=0, column=2, padx=8)

        # Pilih menu
        menu_frame = tk.LabelFrame(frame, text="Tambah Item ke Pesanan", bg=COLOR_FRAME, padx=10, pady=10)
        menu_frame.pack(fill='both', padx=20, pady=10)

        tk.Label(menu_frame, text="Pilih Menu:", bg=COLOR_FRAME).grid(row=0, column=0, sticky='w')
        self.combo_menu = ttk.Combobox(menu_frame, width=60)
        self.refresh_menu_values()
        self.combo_menu.grid(row=1, column=0, columnspan=3, pady=5, sticky='w')

        tk.Label(menu_frame, text="Jumlah:", bg=COLOR_FRAME).grid(row=2, column=0, sticky='w')
        self.entry_jumlah = tk.Entry(menu_frame, width=8)
        self.entry_jumlah.grid(row=2, column=1, sticky='w')
        self.entry_jumlah.insert(0, "1")

        tk.Label(menu_frame, text="Catatan:", bg=COLOR_FRAME).grid(row=3, column=0, sticky='w')
        self.entry_catatan = tk.Entry(menu_frame, width=40)
        self.entry_catatan.grid(row=3, column=1, columnspan=2, pady=5, sticky='w')

        btn_tambah = tk.Button(menu_frame, text="Tambah ke Pesanan", bg=COLOR_BTN_SUCCESS, fg='white', command=self.tambah_item_pesanan)
        btn_tambah.grid(row=4, column=0, pady=8, sticky='w')

        btn_undo = tk.Button(menu_frame, text="Undo Aksi Terakhir", bg=COLOR_BTN_WARNING, fg='black', command=self.undo_aksi)
        btn_undo.grid(row=4, column=1, pady=8, sticky='w')

        self.text_pesanan = tk.Text(frame, height=12)
        self.text_pesanan.pack(fill='both', padx=20, pady=10)

    def setup_menu(self, frame):
        tk.Label(frame, text="Daftar Menu", font=("Arial", 14, "bold"), bg=COLOR_BG, fg=COLOR_HEADER).pack(pady=8)
        menu_list = tk.Frame(frame, bg=COLOR_BG)
        menu_list.pack(fill='both', padx=20)

        for item in self.manajer.menu_items:
            tk.Label(menu_list, text=item.get_info(), bg=COLOR_BG, fg=COLOR_TEXT).pack(anchor='w', pady=2)

    def setup_meja(self, frame):
        tk.Label(frame, text="Status Meja", font=("Arial", 14, "bold"), bg=COLOR_BG, fg=COLOR_HEADER).pack(pady=8)
        self.grid_meja = tk.Frame(frame, bg=COLOR_BG)
        self.grid_meja.pack(padx=20, pady=10)
        self.render_meja_buttons()

    def render_meja_buttons(self):
        # Hapus semua widget di grid_meja dan buat ulang (dipakai saat update)
        for widget in self.grid_meja.winfo_children():
            widget.destroy()

        for i, meja in enumerate(self.manajer.meja):
            if meja.status == 'kosong':
                warna = COLOR_BTN_SUCCESS
                teks_warna = 'white'
            elif meja.status == 'terisi':
                warna = COLOR_BTN_DANGER
                teks_warna = 'white'
            else:
                warna = COLOR_BTN_WARNING
                teks_warna = 'black'

            btn = tk.Button(self.grid_meja, text=f"Meja {meja.nomor}\n{meja.status}", bg=warna, fg=teks_warna, width=12, height=4,
                            command=lambda m=meja: self.tampilkan_info_meja(m))
            btn.grid(row=i//5, column=i%5, padx=6, pady=6)

    # ==================== NOTA (pengganti Laporan) ====================
    def setup_nota(self, frame):
        tk.Label(frame, text="Daftar Nota (Pesanan Selesai)", font=("Arial", 14, "bold"), bg=COLOR_BG, fg=COLOR_HEADER).pack(pady=8)
        self.list_nota = tk.Listbox(frame, width=80, height=18)
        self.list_nota.pack(padx=20, pady=10)

        btn_frame = tk.Frame(frame, bg=COLOR_BG)
        btn_frame.pack(pady=6)

        tk.Button(btn_frame, text="Refresh Nota", bg=COLOR_BTN_PRIMARY, fg='white', command=self.refresh_nota).grid(row=0, column=0, padx=6)
        tk.Button(btn_frame, text="Tampilkan Nota", bg=COLOR_BTN_SUCCESS, fg='white', command=self.tampilkan_nota).grid(row=0, column=1, padx=6)
        tk.Button(btn_frame, text="Simpan Nota ke File", bg=COLOR_BTN_WARNING, fg='black', command=self.simpan_nota_file).grid(row=0, column=2, padx=6)

        self.refresh_nota()

    def refresh_nota(self):
        self.list_nota.delete(0, tk.END)
        for p in self.manajer.pesanan:
            if p.status == "selesai":
                waktu = p.waktu_selesai.strftime('%Y-%m-%d %H:%M:%S') if p.waktu_selesai else "-"
                self.list_nota.insert(tk.END, f"#{p.id_pesanan} - Meja {p.nomor_meja} - Total Rp {p.total_harga:,} - {waktu}")

    def tampilkan_nota(self):
        sel = self.list_nota.curselection()
        if not sel:
            messagebox.showinfo("Nota", "Pilih nota terlebih dahulu.")
            return
        idx = sel[0]
        # cari pesanan selesai ke idx
        selesai = [p for p in self.manajer.pesanan if p.status == "selesai"]
        if idx >= len(selesai):
            messagebox.showerror("Error", "Indeks nota tidak valid.")
            return
        p = selesai[idx]
        messagebox.showinfo(f"Nota #{p.id_pesanan}", p.get_nota_text())

    def simpan_nota_file(self):
        sel = self.list_nota.curselection()
        if not sel:
            messagebox.showinfo("Simpan Nota", "Pilih nota terlebih dahulu.")
            return
        idx = sel[0]
        selesai = [p for p in self.manajer.pesanan if p.status == "selesai"]
        if idx >= len(selesai):
            messagebox.showerror("Error", "Indeks nota tidak valid.")
            return
        p = selesai[idx]

        # default filename
        default_name = f"nota_{p.id_pesanan}_{p.waktu_selesai.strftime('%Y%m%d_%H%M%S') if p.waktu_selesai else datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        filepath = filedialog.asksaveasfilename(defaultextension=".txt", initialfile=default_name,
                                                filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")])
        if not filepath:
            return
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(p.get_nota_text())
            messagebox.showinfo("Simpan Nota", f"Nota disimpan ke:\n{filepath}")
        except Exception as e:
            messagebox.showerror("Error", f"Gagal menyimpan nota: {e}")

    # ==================== ANTRIAN (Queue) UI ====================
    def setup_antrian(self, frame):
        tk.Label(frame, text="Antrian Pesanan - Untuk Dapur", font=("Arial", 14, "bold"), bg=COLOR_BG, fg=COLOR_HEADER).pack(pady=8)
        self.list_antrian = tk.Listbox(frame, width=60, height=15)
        self.list_antrian.pack(pady=10)

        btn_frame = tk.Frame(frame, bg=COLOR_BG)
        btn_frame.pack()

        tk.Button(btn_frame, text="Refresh Antrian", bg=COLOR_BTN_PRIMARY, fg='white', command=self.refresh_antrian).grid(row=0, column=0, padx=6)
        tk.Button(btn_frame, text="Proses Pesanan", bg=COLOR_BTN_SUCCESS, fg='white', command=self.proses_pesanan_dequeue).grid(row=0, column=1, padx=6)
        tk.Button(btn_frame, text="Lihat Riwayat Aksi", bg=COLOR_BTN_WARNING, fg='black', command=self.tampilkan_riwayat).grid(row=0, column=2, padx=6)

        self.refresh_antrian()

    def refresh_antrian(self):
        self.list_antrian.delete(0, tk.END)
        for p in self.manajer.antrian_pesanan:
            self.list_antrian.insert(tk.END, f"#{p.id_pesanan} - Meja {p.nomor_meja} - Items: {len(p.items)} - Total Rp {p.total_harga:,}")

    # ==================== Actions ====================
    def buat_pesanan_baru(self):
        try:
            nomor_meja = int(self.entry_meja.get())
            if not (1 <= nomor_meja <= len(self.manajer.meja)):
                raise ValueError
        except Exception:
            messagebox.showerror('Error', 'Nomor meja tidak valid')
            return

        meja = self.manajer.meja[nomor_meja - 1]
        if meja.status == "terisi":
            messagebox.showerror('Error', f"Meja {nomor_meja} sudah terisi.")
            return

        self.pesanan_aktif = self.manajer.buat_pesanan(nomor_meja)
        # masukkan ke antrian (queue) untuk diproses dapur
        self.manajer.enqueue_pesanan(self.pesanan_aktif)
        # catat ke riwayat (stack)
        self.manajer.push_aksi(f"Buat pesanan #{self.pesanan_aktif.id_pesanan}")

        messagebox.showinfo('Sukses', f'Pesanan dibuat untuk meja {nomor_meja}\nID Pesanan: #{self.pesanan_aktif.id_pesanan}')
        self.update_tampilan_pesanan()
        self.refresh_antrian()
        self.render_meja_buttons()
        self.refresh_menu_values()

    def tambah_item_pesanan(self):
        if not self.pesanan_aktif:
            messagebox.showerror('Error', 'Buat pesanan terlebih dahulu')
            return

        selected = self.combo_menu.current()
        if selected == -1:
            messagebox.showerror('Error', 'Pilih menu terlebih dahulu')
            return

        try:
            jumlah = int(self.entry_jumlah.get())
            if jumlah <= 0:
                raise ValueError
        except Exception:
            messagebox.showerror('Error', 'Masukkan jumlah valid (angka > 0)')
            return

        menu_item = self.manajer.menu_items[selected]
        catatan = self.entry_catatan.get()

        is_ok = self.pesanan_aktif.tambah_item(menu_item, jumlah, catatan)
        if not is_ok:
            messagebox.showerror('Error', 'Stok tidak mencukupi')
            return

        # catat aksi ke stack (misal: "Tambah Ayam Balap x2")
        self.manajer.push_aksi(f"Tambah {menu_item.nama} x{jumlah}")

        messagebox.showinfo('Sukses', f'{menu_item.nama} x{jumlah} ditambahkan ke pesanan')
        self.update_tampilan_pesanan()
        self.refresh_antrian()
        self.refresh_menu_values()

    def update_tampilan_pesanan(self):
        if not self.pesanan_aktif:
            self.text_pesanan.delete('1.0', tk.END)
            return
        self.text_pesanan.delete('1.0', tk.END)
        self.text_pesanan.insert(tk.END, self.pesanan_aktif.get_info_pesanan())

    def tampilkan_info_meja(self, meja):
        info = f"Meja {meja.nomor}\nStatus: {meja.status}"
        if meja.pesanan:
            info += f"\nPesanan ID: {meja.pesanan.id_pesanan}\nItems: {len(meja.pesanan.items)}\nTotal: Rp {meja.pesanan.total_harga:,}\nStatus Pesanan: {meja.pesanan.status}"
        messagebox.showinfo(f'Info Meja {meja.nomor}', info)

    # ------------------ Stack (Undo) ------------------
    def undo_aksi(self):
        aksi = self.manajer.pop_aksi()
        if not aksi:
            messagebox.showinfo("Undo", "Tidak ada aksi untuk di-undo")
            return

        # Kita coba handling dua pola aksi: "Tambah {nama} x{jumlah}" dan "Buat pesanan #{id}"
        if aksi.startswith("Tambah "):
            # contoh: "Tambah Ayam Balap x2"
            try:
                # split by ' x' dari kanan
                left, xpart = aksi.rsplit(" x", 1)
                jumlah = int(xpart)
                _, nama_item = left.split(" ", 1)  # remove "Tambah "
            except Exception:
                messagebox.showinfo("Undo", f"Aksi dibatalkan: {aksi}\n(Tidak dapat melakukan undo otomatis detail item)")
                return

            # coba hapus item terakhir yang cocok pada pesanan aktif (atau di meja terkait)
            # Preferensi: jika pesanan aktif punya item cocok -> hapus sana, else cari pesanan terakhir
            berhasil = False
            subtotal = 0
            if self.pesanan_aktif:
                ok, subtotal = self.pesanan_aktif.hapus_item_terakhir(nama_item, jumlah)
                berhasil = ok
            if not berhasil:
                # cari di semua pesanan (reverse order)
                for p in reversed(self.manajer.pesanan):
                    ok, subtotal = p.hapus_item_terakhir(nama_item, jumlah)
                    if ok:
                        berhasil = True
                        break

            if berhasil:
                messagebox.showinfo("Undo", f"Aksi undo berhasil: {aksi}\nSubtotal dikembalikan: Rp {subtotal:,}")
                self.update_tampilan_pesanan()
                self.refresh_antrian()
                self.refresh_menu_values()
                self.render_meja_buttons()
                return
            else:
                messagebox.showinfo("Undo", f"Aksi dibatalkan: {aksi}\n(Tidak menemukan item yang cocok untuk di-undo)")
                return

        elif aksi.startswith("Buat pesanan #"):
            # contoh: "Buat pesanan #3"
            try:
                parts = aksi.split("#", 1)
                id_p = int(parts[1])
            except Exception:
                messagebox.showinfo("Undo", f"Aksi dibatalkan: {aksi}\n(Tidak dapat memproses undo)")
                return

            # cari pesanan dengan id tersebut
            target = None
            for p in self.manajer.pesanan:
                if p.id_pesanan == id_p:
                    target = p
                    break
            if not target:
                messagebox.showinfo("Undo", f"Aksi dibatalkan: {aksi}\n(Tidak menemukan pesanan #{id_p})")
                return

            # hanya bisa undo jika pesanan masih aktif dan belum selesai & masih di antrian
            if target.status != "aktif":
                messagebox.showinfo("Undo", f"Tidak bisa undo pesanan #{id_p} karena statusnya bukan aktif ({target.status})")
                return

            # Cek apakah pesanan masih ada di antrian
            if target in self.manajer.antrian_pesanan:
                try:
                    self.manajer.antrian_pesanan.remove(target)
                except ValueError:
                    pass

            # restore stok untuk semua item yang ada di pesanan (jika ada)
            for it in target.items:
                it['menu_item'].tambah_stok(it['jumlah'])

            # ubah meja jadi kosong jika meja itu merujuk pada pesanan ini
            meja = self.manajer.meja[target.nomor_meja - 1]
            if meja.pesanan == target:
                meja.pesanan = None
                meja.status = "kosong"

            # hapus dari daftar pesanan
            try:
                self.manajer.pesanan.remove(target)
            except ValueError:
                pass

            messagebox.showinfo("Undo", f"Pesanan #{id_p} dibatalkan dan stok dikembalikan.")
            # update UI
            if self.pesanan_aktif and self.pesanan_aktif.id_pesanan == id_p:
                self.pesanan_aktif = None
                self.update_tampilan_pesanan()
            self.refresh_antrian()
            self.refresh_menu_values()
            self.render_meja_buttons()
            return

        else:
            # aksi lain — kita hanya memberitahu dan tidak membalikkan otomatis
            messagebox.showinfo("Undo", f"Aksi dibatalkan: {aksi}\n(Tidak ada handler undo otomatis untuk tipe aksi ini)")
            return

    def tampilkan_riwayat(self):
        if not self.manajer.riwayat_aksi:
            messagebox.showinfo("Riwayat Aksi", "Belum ada riwayat aksi.")
            return
        teks = "Riwayat Aksi (Top = terakhir):\n\n"
        for i, a in enumerate(reversed(self.manajer.riwayat_aksi), start=1):
            teks += f"{i}. {a}\n"
        messagebox.showinfo("Riwayat Aksi", teks)

    # ------------------ Queue processing ------------------
    def proses_pesanan_dequeue(self):
        pesanan = self.manajer.dequeue_pesanan()
        if not pesanan:
            messagebox.showinfo("Proses Antrian", "Tidak ada pesanan dalam antrian.")
            return

        # tandai pesanan sebagai selesai
        pesanan.status = "selesai"
        pesanan.waktu_selesai = datetime.now()
        # kamar/meja: kosongkan meja setelah pesanan selesai
        meja = self.manajer.meja[pesanan.nomor_meja - 1]
        if meja.pesanan == pesanan:
            meja.pesanan = None
            meja.status = "kosong"

        # catat aksi bahwa pesanan diproses (opsional)
        self.manajer.push_aksi(f"Proses pesanan #{pesanan.id_pesanan}")

        messagebox.showinfo("Proses Antrian", f"Pesanan #{pesanan.id_pesanan} diproses dan ditandai selesai.\nTotal: Rp {pesanan.total_harga:,}")
        self.refresh_antrian()
        self.render_meja_buttons()
        # update nota list
        self.refresh_nota()
        # jika pesanan yang sedang ditampilkan adalah pesanan ini, update tampilan
        if self.pesanan_aktif and self.pesanan_aktif.id_pesanan == pesanan.id_pesanan:
            self.update_tampilan_pesanan()

    # ==================== Utility ====================
    def refresh_menu_values(self):
        # refresh data values di combobox menu (agar stok terbaru terlihat)
        values = [item.get_info() for item in self.manajer.menu_items]
        self.combo_menu['values'] = values

    # ==================== Run helpers / finalizations ====================
    def run(self):
        self.root.mainloop()

# ===============================
#  RUN
# ===============================
if __name__ == '__main__':
    root = tk.Tk()
    app = AplikasiRestoran(root)
    app.run()  
