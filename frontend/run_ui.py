import subprocess
import sys
import os


def main():
    # run_ui.py dosyasının bulunduğu klasörün tam yolunu otomatik bul
    current_dir = os.path.dirname(os.path.abspath(__file__))
    frontend_file = os.path.join(current_dir, "frontend.py")

    # frontend.py dosyasının var olup olmadığını kontrol et
    if not os.path.exists(frontend_file):
        print(
            f"❌ Hata: '{frontend_file}' dosyası bulunamadı! Lütfen frontend dosyanızın adını ve konumunu kontrol edin.")
        sys.exit(1)

    print("🚀 Streamlit web arayüzü başlatılıyor, lütfen tarayıcınızın açılmasını bekleyin...")

    try:
        # Subprocess ile streamlit uygulamasını çalıştır
        subprocess.run([sys.executable, "-m", "streamlit", "run", frontend_file], check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Arayüz çalıştırılırken bir hata oluştu: {e}")
        sys.exit(e.returncode)
    except KeyboardInterrupt:
        print("\n👋 Web arayüzü kullanıcı tarafından sonlandırıldı. İyi günler!")
        sys.exit(0)


if __name__ == "__main__":
    main()