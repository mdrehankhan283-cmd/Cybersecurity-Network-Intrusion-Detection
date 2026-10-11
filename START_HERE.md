# NetGuard — pehle yeh padho

Yeh **complete Python Data Science project** hai: trained models, real dataset,
local dashboard, evaluation report, notebook, source code aur tests included hain.

## Windows par kaise chalaye

1. ZIP download karo. Right-click → **Extract All**. ZIP ke andar se run mat karo.
2. Python **3.12** install karo: https://www.python.org/downloads/ . Installer mein
   **Add Python to PATH** aur Python launcher select karo.
3. Extracted `netguard` folder mein **START_WINDOWS.bat** double-click karo.
4. Pehli baar internet chahiye: Python packages install honge. Command window khuli rakho.
5. Browser mein dashboard open hoga. Nahi khule to http://127.0.0.1:8501 kholo.
6. **Load real-data demo** dabao. Phir kisi row ka **Inspect** button try karo.
7. **Model evidence** tab mein actual test results dekho. **Export results** se CSV milega.

Model pehle se trained hai. Demo chalane ke liye training ya API key ki zarurat nahi.
Pehli successful setup ke baad dashboard bina internet ke chal sakta hai.

## Agar problem aaye

- `py` nahi mil raha: Python 3.12 ka official installer dobara chalao aur launcher enable karo.
- Port already in use: app ki doosri window band karo; ya terminal mein
  `.venv\Scripts\python.exe app.py --port 8502` chalao.
- Browser mein code/file dikhe: HTML file directly mat kholo; launcher chalao.
- `Missing required columns`: `data/samples/demo_flows.csv` wala format use karo.
- Installed package version conflict: is project ka `.venv` environment use karo.

## GitHub par kya upload karna hai

Suggested repository: **netguard-intrusion-detection**.

Extracted `netguard` folder ke **andar ka content** repository root mein upload karo,
taaki `README.md` seedha main page par dikhe. `.venv`, `__pycache__` aur uncompressed
`data/raw/RT_IOT2022` upload mat karo. `models/netguard.joblib` aur sample CSVs include karo.
Raw dataset online download karne ka script diya hai; uski ZIP upload karna zaroori nahi.

**GitHub Pages Python models run nahi karta.** README/screenshot GitHub par dikhenge;
interactive inference ke liye yeh Python app computer par run karna hoga. Is package
mein public hosted URL nahi hai.

## Interview ke liye

`docs/INTERVIEW_GUIDE.md` aur `reports/RESULTS.md` padho. Sirf high accuracy mat bolo:
duplicate leakage, false-positive rate, rare classes aur lab-to-real-network gap samjhao.
CV mein wahi claim karo jo tum samajh kar explain kar sakte ho.
