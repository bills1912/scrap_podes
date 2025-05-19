import streamlit as st
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import streamlit.components.v1 as components
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import chromedriver_autoinstaller
from bs4 import BeautifulSoup
import pandas as pd
import time
import base64
import json

# chromedriver_autoinstaller.install()

st.set_page_config(layout="wide")
# Fungsi untuk scraping data dari website Aplicares (BPJS Kesehatan)
def scrape_aplicares(provinsi, jenis_faskes):
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    wait = WebDriverWait(driver, 15)

    try:
        url = "https://faskes.bpjs-kesehatan.go.id/aplicares/#/app/dashboard"
        driver.get(url)
        time.sleep(3)

        st.write("Debug: Mencari elemen di halaman...")
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        div_editable_elements = soup.find_all('div', attrs={'contenteditable': 'true'})
        st.write("Div contenteditable ditemukan:", [
            {'class': d.get('class'), 'name': d.get('name'), 'text': d.text[:50]} for d in div_editable_elements
        ])
        div_elements = soup.find_all('div', class_=['form-control', 'dropdown'])
        st.write("Div lain (form-control/dropdown) ditemukan:", [
            {'class': d.get('class'), 'name': d.get('name'), 'text': d.text[:50]} for d in div_elements
        ])
        select_elements = soup.find_all('select')
        st.write("Dropdown select ditemukan:", [
            {'class': s.get('class'), 'name': s.get('name'), 'options': [opt.text for opt in s.find_all('option')]} for s in select_elements
        ])
        button_elements = soup.find_all('button')
        st.write("Tombol ditemukan:", [
            {'text': b.text, 'class': b.get('class'), 'id': b.get('id')} for b in button_elements
        ])

        try:
            provinsi_div = wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "div[ng-model='combobox.propinsi.selected']"))
            )
            st.write("Div provinsi ditemukan (ng-model='combobox.propinsi.selected').")
            provinsi_div.click()
            st.write("Div provinsi diklik untuk mengaktifkan fokus.")
            driver.execute_script("arguments[0].innerText = ''", provinsi_div)
            st.write("Isi div provinsi dikosongkan.")
            provinsi_div.send_keys(provinsi)
            st.write(f"Provinsi '{provinsi}' diketik di div.")
            time.sleep(1)

            try:
                autocomplete_option = wait.until(
                    EC.element_to_be_clickable(
                        (By.XPATH, f"//div[contains(@class, 'autocomplete-item') and contains(text(), '{provinsi}')]")
                    )
                )
                autocomplete_option.click()
                st.write(f"Opsi autocomplete '{provinsi}' dipilih.")
            except:
                st.warning(f"Opsi autocomplete '{provinsi}' tidak ditemukan, mencoba opsi serupa...")
                autocomplete_options = driver.find_elements(By.CSS_SELECTOR, "div.autocomplete-item")
                option_texts = [opt.text for opt in autocomplete_options]
                st.write("Opsi autocomplete yang tersedia:", option_texts)
                for opt in autocomplete_options:
                    if provinsi.lower() in opt.text.lower():
                        opt.click()
                        st.write(f"Opsi autocomplete '{opt.text}' dipilih.")
                        break
                else:
                    st.warning("Tidak ada opsi autocomplete yang cocok.")
                    provinsi_div.send_keys(Keys.ENTER)
                    st.write("Enter ditekan sebagai fallback.")
            time.sleep(1)

        except Exception as e:
            st.error(f"Error saat mengisi div provinsi: {e}")
            try:
                st.warning("Mencoba fallback dengan JavaScript...")
                driver.execute_script(
                    f"arguments[0].innerText = '{provinsi}'; arguments[0].dispatchEvent(new Event('input'));",
                    provinsi_div
                )
                st.write(f"Provinsi '{provinsi}' diset melalui JavaScript.")
                time.sleep(1)
                driver.execute_script("arguments[0].dispatchEvent(new KeyboardEvent('keydown', {'key': 'Enter'}));", provinsi_div)
                st.write("Enter disimulasikan melalui JavaScript.")
                time.sleep(1)
            except Exception as js_e:
                st.error(f"Fallback JavaScript gagal: {js_e}")
                return None

        try:
            faskes_dropdown = Select(wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "select[name='faskes']"))
            ))
            st.write("Dropdown jenis faskes ditemukan (name='faskes').")
        except:
            st.warning("Name 'faskes' tidak ditemukan, mencoba class 'form-select'...")
            faskes_dropdown = Select(wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "select.form-control"))
            ))
            st.write("Dropdown jenis faskes ditemukan (class='form-select').")

        try:
            faskes_dropdown.select_by_visible_text(jenis_faskes)
        except:
            st.warning(f"Opsi '{jenis_faskes}' tidak ditemukan, mencoba opsi serupa...")
            options = [opt.text for opt in faskes_dropdown.options]
            st.write("Opsi jenis faskes yang tersedia:", options)
            for opt in options:
                if jenis_faskes.lower() in opt.lower():
                    faskes_dropdown.select_by_visible_text(opt)
                    break
            else:
                st.error("Jenis faskes tidak ditemukan di dropdown.")
                return None
        st.write(f"Jenis faskes '{jenis_faskes}' dipilih.")
        time.sleep(1)

        try:
            cari_button = wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button"))
            )
            st.write("Tombol cari ditemukan (class='btn-primary').")
        except:
            st.warning("Class 'btn-primary' tidak ditemukan, mencoba tombol dengan teks 'Cari'...")
            cari_button = wait.until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Cari')]"))
            )
            st.write("Tombol cari ditemukan (teks 'Cari').")
        cari_button.click()
        st.write("Tombol cari diklik.")
        time.sleep(3)

        soup = BeautifulSoup(driver.page_source, 'html.parser')
        marker_elements = soup.find_all(['div'], class_=['faskes-item', 'marker'])
        if not marker_elements:
            st.warning("Elemen marker/div dengan class 'faskes-item' atau 'marker' tidak ditemukan.")
            marker_elements = soup.find_all(['marker'])
            st.write("Mencoba semua div/marker")
            if not marker_elements:
                st.error("Tidak ada elemen berulang ditemukan.")
                return None

        data = []
        headers = None
        for marker in marker_elements:
            row = {}
            name = marker.find('div', class_='name') or marker.find('span', class_='name')
            address = marker.find('div', class_='address') or marker.find('span', class_='address')
            faskes_type = marker.find('div', class_='type') or marker.find('span', class_='type')
            if name:
                row['Name'] = name.text.strip()
            if address:
                row['Address'] = address.text.strip()
            if faskes_type:
                row['Type'] = faskes_type.text.strip()
            if row:
                data.append(row)
            if not headers and row:
                headers = list(row.keys())

        if not data:
            st.error("Tidak ada data yang dapat diekstrak dari elemen marker/div.")
            return None

        df = pd.DataFrame(data, columns=headers or ['Name', 'Address', 'Type'])
        return df

    except Exception as e:
        st.error(f"Error saat scraping: {e}")
        return None
    finally:
        driver.quit()

# Fungsi untuk scraping data dari website Kemdikbud
def scrape_kemdikbud(kode_kabkot, fasilitas_pendidikan):
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument("--disable-infobars")
    options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    wait = WebDriverWait(driver, 15)

    try:
        url = f"https://sekolah.data.kemdikbud.go.id/index.php/Cpetasebaran/index/{kode_kabkot}/{fasilitas_pendidikan}"
        driver.get(url)
        st.write("Memuat halaman...")
        time.sleep(5)  # Tunggu halaman dinamis dimuat
        
        markers = wait.until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".leaflet-marker-icon, div.marker, span.marker"))
        )
        st.write(f"Ditemukan {len(markers)} marker di peta.")
        
        data = []
        for index, marker in enumerate(markers):
            try:
                # Klik marker untuk membuka pop-up
                driver.execute_script("arguments[0].click();", marker)  # Gunakan JavaScript untuk klik jika tidak interactable
                # st.write(f"Mengklik marker ke-{index + 1}...")
                time.sleep(1)  # Tunggu pop-up muncul

                # Tunggu hingga pop-up muncul
                popup = wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".leaflet-popup-content, .popup, div.popup-content"))
                )
                # st.write("Pop-up ditemukan.")

                # Ambil konten pop-up
                soup = BeautifulSoup(popup.get_attribute('innerHTML'), 'html.parser')
                row = {}

                # Ekstrak data dari pop-up (sesuaikan dengan struktur HTML)
                data_sekolah = soup.find('ul', {'class':'list-group list-group-unbordered'}).find_all('li')
                npsn = data_sekolah[0]
                nama = data_sekolah[1].find('a')
                alamat = data_sekolah[2]

                if npsn:
                    row['NPSN'] = npsn.text.strip()
                if nama:
                    row['Nama Sekolan'] = nama.text.strip()
                if alamat:
                    row['Alamat'] = alamat.text.strip()

                if row:
                    data.append(row)
                else:
                    st.warning(f"Tidak ada data valid di pop-up marker ke-{index + 1}.")

            except Exception as e:
                st.warning(f"Gagal memproses marker ke-{index + 1}: {e}")
                continue

        if not data:
            st.error("Tidak ada data yang dapat diekstrak dari pop-up marker.")
            return None

        df = pd.DataFrame(data)
        return df

    except Exception as e:
        st.error(f"Error saat scraping: {e}")
        return None
    finally:
        driver.quit()
        
def scrape_dapodik(kode_prov):
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    wait = WebDriverWait(driver, 15)

    try:
        url = f"https://dapo.dikdasmen.go.id/sp/1/{kode_prov}"
        driver.get(url)
        st.write("Memuat halaman...")
        time.sleep(5)  # Tunggu halaman dinamis dimuat
        
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        table = soup.find('table', {'id':'DataTables_Table_0'})
        table_header = table.find('thead')
        table_body = table.find('tbody')
        rows = table_body.find_all('tr')
        # st.write(f"{rows}")
        
        data = {}
        for row in rows:
            try:
                micro_data = {}
                
                wilayah = row.find_all('td')[1].find('a')
                # Data TK
                total_tk = row.find_all('td')[5]
                total_tk_n = row.find_all('td')[6]
                total_tk_s = row.find_all('td')[7]
                
                # Data KB
                total_kb = row.find_all('td')[8]
                total_kb_n = row.find_all('td')[9]
                total_kb_s = row.find_all('td')[10]
                
                # Data TPA
                total_tpa = row.find_all('td')[11]
                total_tpa_n = row.find_all('td')[12]
                total_tpa_s = row.find_all('td')[13]
                
                # Data SPS
                total_sps = row.find_all('td')[14]
                total_sps_n = row.find_all('td')[15]
                total_sps_s = row.find_all('td')[16]
                
                # Data PKBM
                total_pkbm = row.find_all('td')[17]
                total_pkbm_n = row.find_all('td')[18]
                total_pkbm_s = row.find_all('td')[19]
                
                # Data SKB
                total_skb = row.find_all('td')[20]
                total_skb_n = row.find_all('td')[21]
                total_skb_s = row.find_all('td')[22]
                
                # Data SD
                total_sd = row.find_all('td')[23]
                total_sd_n = row.find_all('td')[24]
                total_sd_s = row.find_all('td')[25]
                
                # Data SMP
                total_smp = row.find_all('td')[26]
                total_smp_n = row.find_all('td')[27]
                total_smp_s = row.find_all('td')[28]
                
                # Data SMA
                total_sma = row.find_all('td')[29]
                total_sma_n = row.find_all('td')[30]
                total_sma_s = row.find_all('td')[31]
                
                # Data SMK
                total_smk = row.find_all('td')[32]
                total_smk_n = row.find_all('td')[33]
                total_smk_s = row.find_all('td')[34]
                
                # Data SLB
                total_slb = row.find_all('td')[35]
                total_slb_n = row.find_all('td')[36]
                total_slb_s = row.find_all('td')[37]
                
                
                micro_data['TK'] = {'Total': total_tk.text.strip(), 'Negeri': total_tk_n.text.strip(), 'Swasta': total_tk_s.text.strip()}
                micro_data['KB'] = {'Total': total_kb.text.strip(), 'Negeri': total_kb_n.text.strip(), 'Swasta': total_kb_s.text.strip()}
                micro_data['TPA'] = {'Total': total_tpa.text.strip(), 'Negeri': total_tpa_n.text.strip(), 'Swasta': total_tpa_s.text.strip()}
                micro_data['SPS'] = {'Total': total_sps.text.strip(), 'Negeri': total_sps_n.text.strip(), 'Swasta': total_sps_s.text.strip()}
                micro_data['PKBM'] = {'Total': total_pkbm.text.strip(), 'Negeri': total_pkbm_n.text.strip(), 'Swasta': total_pkbm_s.text.strip()}
                micro_data['SKB'] = {'Total': total_skb.text.strip(), 'Negeri': total_skb_n.text.strip(), 'Swasta': total_skb_s.text.strip()}
                micro_data['SD'] = {'Total': total_sd.text.strip(), 'Negeri': total_sd_n.text.strip(), 'Swasta': total_sd_s.text.strip()}
                micro_data['SMP'] = {'Total': total_smp.text.strip(), 'Negeri': total_smp_n.text.strip(), 'Swasta': total_smp_s.text.strip()}
                micro_data['SMA'] = {'Total': total_sma.text.strip(), 'Negeri': total_sma_n.text.strip(), 'Swasta': total_sma_s.text.strip()}
                micro_data['SMK'] = {'Total': total_smk.text.strip(), 'Negeri': total_smk_n.text.strip(), 'Swasta': total_smk_s.text.strip()}
                micro_data['SLB'] = {'Total': total_slb.text.strip(), 'Negeri': total_slb_n.text.strip(), 'Swasta': total_slb_s.text.strip()}
                if micro_data:
                    data[wilayah.text.strip()] = {
                        'TK':micro_data['TK'], 
                        'KB':micro_data['KB'], 
                        'TPA':micro_data['TPA'], 
                        'SPS':micro_data['SPS'], 
                        'PKBM':micro_data['PKBM'], 
                        'SKB':micro_data['SKB'], 
                        'SD':micro_data['SD'], 
                        'SMP':micro_data['SMP'], 
                        'SMA':micro_data['SMA'], 
                        'SMK':micro_data['SMK'], 
                        'SLB':micro_data['SLB']
                        }
                else:
                    st.warning(f"Tidak ada data valid yang di-scrape.")

            except Exception as e:
                st.warning(f"Gagal memproses tabel")
                continue

        if not data:
            st.error("Tidak ada data yang dapat diekstrak dari pop-up marker.")
            return None

        return data

    except Exception as e:
        st.error(f"Error saat scraping: {e}")
        return None
    finally:
        driver.quit()
        

# Aplikasi Streamlit dengan Menu di Sidebar
st.sidebar.title("Menu Scraping")
with st.sidebar:
    page = st.radio("Pilih Halaman", [
        # "Fasilitas Kesehatan", 
        "Fasilitas Pendidikan dari Kemendikbud",
        #   "Perbankan"
        ])

if page == "Fasilitas Kesehatan":
    st.title("Scraping Data Falisilitas Kesehatan dari website BPJS")
    with st.form("form_faskes"):
        st.write("Pilih parameter pencarian:")
        provinsi = st.text_input("Provinsi", value="Jawa Barat")
        jenis_faskes = st.selectbox("Jenis Faskes", ["Rumah Sakit", "Puskesmas", "Klinik Pratama", "Dokter Umum"])
        submit_button = st.form_submit_button("Cari Faskes")

    if submit_button:
        with st.spinner("Mengambil data dari Aplicares..."):
            result_df = scrape_aplicares(provinsi, jenis_faskes)
            if result_df is not None and not result_df.empty:
                st.success("Data berhasil diambil!")
                st.dataframe(result_df)
            else:
                st.error("Gagal mengambil data atau data tidak tersedia.")

elif page == "Fasilitas Pendidikan dari Kemendikbud":
    def download_button(object_to_download, download_filename):
        """
        Generates a link to download the given object_to_download.
        Params:
        ------
        object_to_download:  The object to be downloaded.
        download_filename (str): filename and extension of file. e.g. mydata.csv,
        Returns:
        -------
        (str): the anchor tag to download object_to_download
        """
        if isinstance(object_to_download, pd.DataFrame):
            object_to_download = object_to_download.to_csv(index=False)

        # Try JSON encode for everything else
        else:
            object_to_download = json.dumps(object_to_download)

        try:
            # some strings <-> bytes conversions necessary here
            b64 = base64.b64encode(object_to_download.encode()).decode()

        except AttributeError as e:
            b64 = base64.b64encode(object_to_download).decode()

        dl_link = f"""
        <html>
        <head>
        <title>Start Auto Download file</title>
        <script src="http://code.jquery.com/jquery-3.2.1.min.js"></script>
        <script>
        $('<a href="data:text/csv;base64,{b64}" download="{download_filename}">')[0].click()
        </script>
        </head>
        </html>
        """
        return dl_link


    def download_df(data, filename):
        # df = pd.DataFrame(st.session_state.col_values, columns=[st.session_state.col_name])
        components.html(
            download_button(data, filename),
            height=0,
        )
            
    st.title("Scraping Data Fasilitas Pendidikan dari Kemendikbud")
    tab1, tab2 = st.tabs(["Website Sekolah Kita", "Website Dapodik"])
    with tab1:
        col1, col2 = st.columns([2, 2])
        with col1:
            st.subheader("Pencarian Fasilitas Pendidikan")
            with st.form("form_sekolah_kita"):
                st.write("Masukkan Parameter Pencarian:")
                kabkot = st.text_input("Kode Kabupaten/Kota", placeholder="Contoh: 003000", help="Untuk kode dengan 5 digit, tambahkan 0 di depan.")
                jenis_faspend = st.selectbox("Jenis Fasilitas Pendidikan", ["SD", "MI", "SMP", "MTS", "SMA", "MA", "SMK", "SDLB", "SMPLB", 
                                                            "SMALB", "SLB", "TK", "KB", "TPA", "SPS", "PKMB", "Kursus", "SKB"])
                submit_button = st.form_submit_button("Cari Fasilitas Pendidikan")
        with col2:
            st.subheader("Referensi Kode")
            referensi_kode = pd.read_csv("https://raw.githubusercontent.com/bills1912/scrap_podes/refs/heads/main/master-kab-kota.csv", sep=";")
            st.dataframe(referensi_kode)
            

        if submit_button:
            with st.spinner("Mengambil data dari Sekolah Kita..."):
                result_df = scrape_kemdikbud(kabkot, jenis_faspend)
                if result_df is not None and not result_df.empty:
                    st.success("Data berhasil diambil!")
                    st.dataframe(result_df)
                    st.download_button(
                        f"Unduh Data {jenis_faspend}",
                        result_df.to_csv(index=False).encode('utf-8'),
                        f"{kabkot}_{jenis_faspend}.csv",
                        "text/csv",
                        key='download-csv'
                    )
                else:
                    st.error("Gagal mengambil data atau data tidak tersedia.")
    with tab2:
        col1, col2 = st.columns([2, 2])
        with col1:
            st.subheader("Pencarian Fasilitas Pendidikan")
            with st.form("form_dapodik"):
                st.write("Masukkan Parameter Pencarian:")
                prov = st.text_input("Kode Provinsi", placeholder="Contoh: 003000", help="Untuk kode dengan 5 digit, tambahkan 0 di depan.")
                submit_button = st.form_submit_button("Cari Fasilitas Pendidikan")
        with col2:
            st.subheader("Referensi Kode")
            referensi_kode = pd.read_csv("https://raw.githubusercontent.com/bills1912/scrap_podes/refs/heads/main/master-kab-kota.csv", sep=";")
            st.dataframe(referensi_kode)
            

        if submit_button:
            with st.spinner("Mengambil data dari Sekolah Kita..."):
                result_df = scrape_dapodik(prov)
                if result_df:
                    st.success("Data berhasil diambil!")
                    st.download_button(
                        label="Download Data",
                        data=json.dumps(result_df).encode('utf-8'),
                        file_name="data.json",
                        mime="application/json",
                        icon=":material/download:",
                    )
                else:
                    st.error("Gagal mengambil data atau data tidak tersedia.")

# Petunjuk Umum
# st.markdown("""
# **Petunjuk jika Scraping Gagal:**
# 1. Buka website target, klik kanan pada elemen data (tabel, daftar, dll.), lalu pilih "Inspect".
# 2. Catat `class`, `id`, atau atribut lain. Contoh:
#    - Faskes: `<div class="faskes-item"><div class="name">RS Umum</div></div>`
#    - Sekolah: `<table class="table-striped"><tr><td>SDN 01</td></tr></table>`
# 3. Perbarui selector di kode:
#    - Faskes: `By.CSS_SELECTOR, "div.faskes-item"`
#    - Sekolah: `By.CSS_SELECTOR, "table.table-striped"`
# 4. Jika data dimuat via JavaScript, tambah waktu tunggu (`time.sleep(5)` ke `time.sleep(10)`).
# 5. Salin HTML elemen dari Developer Tools untuk bantuan lebih lanjut.

# **Alternatif Resmi untuk Sekolah:**
# - Unduh dataset dari [Portal Data Kemendikdasmen](https://data.dikdasmen.go.id/) (CSV/XLSV, diperbarui harian).
# - Contoh: Data satuan pendidikan mencakup nama, alamat, jenjang, dan status.

# **Legalitas:**
# - Scraping mungkin melanggar ketentuan layanan. Hubungi BPJS Kesehatan atau Kemendikbud untuk akses resmi.
# """)
