import subprocess
import sys
print("Web arayüzü başlatılıyor, lütfen tarayıcınızın açılmasını bekleyin...")
subprocess.run([sys.executable, "-m", "streamlit", "run", "frontend.py"])