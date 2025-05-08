import streamlit as st
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import pandas as pd
import time

# Fungsi untuk scraping data dari website Aplicares
def scrape_aplicares(provinsi, jenis_faskes):
    # Konfigurasi Selenium WebDriver
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')  # Menjalankan browser tanpa UI
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    wait = WebDriverWait(driver, 15)  # Tunggu hingga 15 detik

    try:
        # Buka halaman dashboard
        url = "https://faskes.bpjs-kesehatan.go.id/aplicares/#/app/dashboard"
        driver.get(url)
        time.sleep(3)  # Tunggu halaman dimuat

        # Debug: Cetak elemen div contenteditable, div lain, select, dan button
        st.write("Debug: Mencari elemen di halaman...")
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        div_editable_elements = soup.find_all('div', attrs={'contenteditable': 'true'})
        st.write("Div contenteditable ditemukan:", [
            {
                'class': d.get('class'),
                'name': d.get('name'),
                'text': d.text[:50]
            } for d in div_editable_elements
        ])
        div_elements = soup.find_all('div', class_=['form-control', 'dropdown'])
        st.write("Div lain (form-control/dropdown) ditemukan:", [
            {
                'class': d.get('class'),
                'name': d.get('name'),
                'text': d.text[:50]
            } for d in div_elements
        ])
        select_elements = soup.find_all('select')
        st.write("Dropdown select ditemukan:", [
            {
                'class': s.get('class'),
                'name': s.get('name'),
                'options': [opt.text for opt in s.find_all('option')]
            } for s in select_elements
        ])
        button_elements = soup.find_all('button')
        st.write("Tombol ditemukan:", [
            {
                'text': b.text,
                'class': b.get('class'),
                'id': b.get('id')
            } for b in button_elements
        ])

        # Simulasi pemilihan form
        try:
            
            # Ketik provinsi di div contenteditable
            # Ketik provinsi di div dengan attribute ng-model='combobox.propinsi.selected'
            try:
                # Tunggu hingga elemen div dengan ng-model='combobox.propinsi.selected' dapat diklik
                provinsi_div = wait.until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "div[ng-model='combobox.propinsi.selected']"))
                )
                st.write("Div provinsi ditemukan (ng-model='combobox.propinsi.selected').")
                
                # Klik div untuk memastikan elemen aktif (fokus)
                provinsi_div.click()
                st.write("Div provinsi diklik untuk mengaktifkan fokus.")
                
                # Kosongkan isi div menggunakan JavaScript (lebih andal untuk div contenteditable)
                driver.execute_script("arguments[0].innerText = ''", provinsi_div)
                st.write("Isi div provinsi dikosongkan.")
                
                # Kirim teks provinsi ke div
                provinsi_div.send_keys(provinsi)
                st.write(f"Provinsi '{provinsi}' diketik di div.")
                time.sleep(1)  # Tunggu sebentar untuk munculnya autocomplete
                
                # Pilih opsi autocomplete (jika ada)
                try:
                    # Cari elemen autocomplete yang cocok dengan provinsi
                    autocomplete_option = wait.until(
                        EC.element_to_be_clickable(
                            (By.XPATH, f"//div[contains(@class, 'autocomplete-item') and contains(text(), '{provinsi}')]")
                        )
                    )
                    autocomplete_option.click()
                    st.write(f"Opsi autocomplete '{provinsi}' dipilih.")
                except:
                    st.warning(f"Opsi autocomplete '{provinsi}' tidak ditemukan, mencoba opsi serupa...")
                    # Cari semua elemen autocomplete
                    autocomplete_options = driver.find_elements(By.CSS_SELECTOR, "div.autocomplete-item")
                    option_texts = [opt.text for opt in autocomplete_options]
                    st.write("Opsi autocomplete yang tersedia:", option_texts)
                    
                    # Pilih opsi yang cocok
                    for opt in autocomplete_options:
                        if provinsi.lower() in opt.text.lower():
                            opt.click()
                            st.write(f"Opsi autocomplete '{opt.text}' dipilih.")
                            break
                    else:
                        st.warning("Tidak ada opsi autocomplete yang cocok.")
                        # Fallback: Tekan Enter untuk mengonfirmasi input
                        provinsi_div.send_keys(Keys.ENTER)
                        st.write("Enter ditekan sebagai fallback.")
                time.sleep(1)  # Tunggu proses selesai

            except Exception as e:
                st.error(f"Error saat mengisi div provinsi: {e}")
                # Coba fallback dengan JavaScript jika elemen tidak dapat diinteraksikan
                try:
                    st.warning("Mencoba fallback dengan JavaScript...")
                    driver.execute_script(
                        f"arguments[0].innerText = '{provinsi}'; arguments[0].dispatchEvent(new Event('input'));", 
                        provinsi_div
                    )
                    st.write(f"Provinsi '{provinsi}' diset melalui JavaScript.")
                    time.sleep(1)
                    # Tekan Enter melalui JavaScript untuk mengonfirmasi
                    driver.execute_script("arguments[0].dispatchEvent(new KeyboardEvent('keydown', {'key': 'Enter'}));", provinsi_div)
                    st.write("Enter disimulasikan melalui JavaScript.")
                    time.sleep(1)
                except Exception as js_e:
                    st.error(f"Fallback JavaScript gagal: {js_e}")
                    return None
            # Pilih jenis faskes (menggunakan select)
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
            # Coba pilih opsi
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

            # Klik tombol cari
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
            time.sleep(3)  # Tunggu hasil dimuat
        except Exception as e:
            st.error(f"Error saat memilih form: {e}")
            return None

        # Ambil konten halaman setelah interaksi
        soup = BeautifulSoup(driver.page_source, 'html.parser')

        # Ekstrak data dari elemen marker berulang
        marker_elements = soup.find_all(['div'], class_=['faskes-item', 'marker'])
        if not marker_elements:
            st.warning("Elemen marker/div dengan class 'faskes-item' atau 'marker' tidak ditemukan.")
            # Coba tanpa class spesifik
            marker_elements = soup.find_all(['marker'])
            st.write("Mencoba semua div/marker")
            if not marker_elements:
                st.error("Tidak ada elemen berulang ditemukan.")
                return None

        # Parsing data ke DataFrame
        data = []
        headers = None
        for marker in marker_elements:
            # Asumsikan setiap marker berisi sub-elemen seperti name, address, type
            row = {}
            row['Name'] = marker.title.strip()
            # address = marker.find('div', class_='address') or marker.find('span', class_='address')
            # faskes_type = marker.find('div', class_='type') or marker.find('span', class_='type')
            
            # if name:
            #     row['Name'] = name.text.strip()
            # if address:
            #     row['Address'] = address.text.strip()
            # if faskes_type:
            #     row['Type'] = faskes_type.text.strip()
            
            if row:
                data.append(row)
            
            # Tentukan header dari elemen pertama
            if not headers and row:
                headers = list(row.keys())

        if not data:
            st.error("Tidak ada data yang dapat diekstrak dari elemen marker/div.")
            return None

        # Buat DataFrame
        df = pd.DataFrame(data, columns=headers or ['Name', 'Address', 'Type'])
        return df

    except Exception as e:
        st.error(f"Error saat scraping: {e}")
        return None
    finally:
        driver.quit()

# Aplikasi Streamlit
st.title("Scraping Faskes BPJS Kesehatan")

# Form input di Streamlit
with st.form("form_faskes"):
    st.write("Pilih parameter pencarian:")
    provinsi = st.text_input("Provinsi", value="Jawa Barat")  # Input teks untuk provinsi
    jenis_faskes = st.selectbox("Jenis Faskes", ["Rumah Sakit", "Puskesmas", "Klinik Pratama", "Dokter Umum"])
    submit_button = st.form_submit_button("Cari Faskes")

# Proses scraping saat form disubmit
if submit_button:
    with st.spinner("Mengambil data dari Aplicares..."):
        result_df = scrape_aplicares(provinsi, jenis_faskes)
        if result_df is not None and not result_df.empty:
            st.success("Data berhasil diambil!")
            st.dataframe(result_df)
        else:
            st.error("Gagal mengambil data atau data tidak tersedia.")

# Petunjuk untuk menemukan elemen
st.markdown("""
**Petunjuk jika gagal:**
1. Buka website, klik kanan pada div provinsi, daftar autocomplete, jenis faskes, tombol cari, dan elemen data (marker/div), lalu pilih "Inspect".
2. Catat `class`, `name`, atau atribut lain. Contoh:
   - Provinsi: `<div class="form-control" name="provinsi" contenteditable="true">`
   - Autocomplete: `<div class="autocomplete-item">Jawa Barat</div>`
   - Jenis faskes: `<select class="form-select" name="faskes">`
   - Tombol: `<button class="btn btn-primary">Cari</button>`
   - Data: `<marker class="faskes-item"><div class="name">RS Umum</div></marker>`
3. Periksa output debug untuk melihat `div contenteditable`, `select`, `button`, dan `marker/div`.
4. Perbarui kode dengan selector yang sesuai:
   - Contoh: `By.CSS_SELECTOR, "div[name='provinsi'][contenteditable='true']"`
   - Contoh: `By.XPATH, "//div[contains(@class, 'faskes-item')]"`
5. Jika `<marker>` bukan elemen yang benar (misalnya, `<div>` atau `<li>`), salin HTML untuk penyesuaian.
6. Salin HTML elemen dari Developer Tools untuk bantuan lebih lanjut.
**Legalitas**: Pastikan Anda memiliki izin untuk scraping. Hubungi BPJS Kesehatan untuk akses API resmi.
""")