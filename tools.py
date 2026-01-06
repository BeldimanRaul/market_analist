import json  
import time
import yfinance as yf
import matplotlib.pyplot as plt
from duckduckgo_search import DDGS
from fpdf import FPDF
import os



PORTFOLIO_FILE = "portfolio.json"

def load_portfolio():
    """Citește portofoliul din fișierul JSON."""
    if not os.path.exists(PORTFOLIO_FILE):
        return {}
    try:
        with open(PORTFOLIO_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_portfolio(data):
    """Salvează portofoliul în fișierul JSON."""
    with open(PORTFOLIO_FILE, "w") as f:
        json.dump(data, f, indent=4)

def add_stock_to_portfolio(ticker):
    """Adaugă o acțiune în portofoliu și îi salvează prețul curent."""
    ticker = ticker.upper().strip()
    data = load_portfolio()
    
    
    try:
        stock = yf.Ticker(ticker)
        price = stock.info.get('currentPrice') or stock.info.get('regularMarketPrice')
        
        if price:
            data[ticker] = price
            save_portfolio(data)
            return f" Am adăugat {ticker} în portofoliu la prețul ${price}."
        else:
            return f" Nu am găsit preț pentru {ticker}."
    except Exception as e:
        return f"Eroare la adăugare: {e}"

def check_portfolio_updates():
    """
    Verifică portofoliul și compară prețurile curente cu cele salvate.
    Returnează un mesaj de bun venit personalizat.
    """
    data = load_portfolio()
    if not data:
        return None 

    message = "###  Update Portofoliu:\n"
    updates_found = False

    for ticker, old_price in data.items():
        try:
            stock = yf.Ticker(ticker)
            current_price = stock.info.get('currentPrice') or stock.info.get('regularMarketPrice')
            
            if current_price:
                
                diff = current_price - old_price
                percent = (diff / old_price) * 100
                
                
                icon = "🟢" if diff >= 0 else "🔴"
                msg_part = f"{icon} **{ticker}**: ${current_price} ({percent:+.2f}% de la ultima vizită)\n"
                message += msg_part
                
               
                data[ticker] = current_price
                updates_found = True
        except:
            continue
    
    
    if updates_found:
        save_portfolio(data)
        return message
    else:
        return "Nu am putut actualiza datele portofoliului."

def search_internet(query: str):
    """
    Caută pe internet știri și informații.
    Încearcă să obțină rezultate proaspete și gestionează erorile de conexiune.
    """
    print(f"\n[SISTEM]  Caut pe web: '{query}'...")
    
    
    max_retries = 2
    
    for attempt in range(max_retries):
        try:
           
            time.sleep(2)
            
           
            results = DDGS().text(query, region='wt-wt', safesearch='off', timelimit='w', max_results=5, backend='html')
            
            
            if not results:
                if attempt < max_retries - 1:
                    print(f"[DEBUG] Reîncercare căutare ({attempt+1}/{max_retries})...")
                    continue 
                return "SISTEM: Nu am găsit rezultate relevante (lista goală)."
            
            
            final_text = f"### Rezultate căutare pentru '{query}':\n\n"
            for i, res in enumerate(results, 1):
                title = res.get('title', 'Fără titlu')
                body = res.get('body', 'Fără descriere')
                link = res.get('href', '#')
                date = res.get('date', '') 
                
                final_text += f"**{i}. {title}**\n"
                if date:
                    final_text += f"   (Data: {date})\n"
                final_text += f"   {body}\n"
                final_text += f"   Surse: {link}\n\n"
                
            return final_text

        except Exception as e:
            print(f"[EROARE SEARCH] Încercarea {attempt+1}: {e}")
            if attempt < max_retries - 1:
                time.sleep(3) 
            else:
                return f"Eroare critică la căutare: {e}"


def get_financial_data(ticker: str):
    """
    Obține date financiare LIVE.
    Versiune BLINDATĂ pentru procente.
    """
    print(f"\n[SISTEM]  Descarc date pentru: {ticker}...")
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        current_price = info.get('currentPrice') or info.get('regularMarketPrice')
        if not current_price:
             return "EROARE: Simbol invalid (ex: folosește 'BTC-USD' pt Bitcoin)."

       
        raw_div = info.get('dividendYield') 
        
        if raw_div is None:
            div_formatted = "0% (N/A)"
        else:
           
            
            if raw_div > 0.20: 
               
                if raw_div > 1: 
                   
                    div_formatted = f"{raw_div:.2f}%"
                else:
                  
                    div_formatted = f"{raw_div * 100:.2f}%"
            else:
               
                div_formatted = f"{raw_div * 100:.2f}%"

        data = {
            "Nume": info.get('shortName'),
            "Preț": f"${current_price}",
            "Dividend": div_formatted, 
            "P/E Ratio": info.get('forwardPE') or "N/A",
            "Recomandare": info.get('recommendationKey', "N/A").upper(),
            "Target Preț": f"${info.get('targetMeanPrice', 'N/A')}"
        }
        return str(data)
    except Exception as e:
        return f"Eroare date: {e}"


def generate_price_chart(ticker: str):
    """Generează grafic pe 1 an."""
    filename = f"{ticker}_chart.png"
    print(f"\n[SISTEM]  Generez grafic: {filename}...")
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="1y")
        if hist.empty: return "Fără date istorice."

        plt.figure(figsize=(10, 5))
        plt.plot(hist.index, hist['Close'], label='Preț')
        plt.title(f"Evoluția {ticker} (1 An)")
        plt.grid(True)
        plt.savefig(filename)
        plt.close() 
        return f"Grafic salvat: {filename}"
    except Exception as e:
        return f"Eroare grafic: {e}"
    

    




def clean_text_for_pdf(text):
    """
    FPDF standard nu suportă emoji-uri sau unele diacritice complexe direct.
    Această funcție curăță textul pentru a evita erorile de encodare 'Latin-1'.
    """
    
    replacements = {
        'ă': 'a', 'â': 'a', 'î': 'i', 'ș': 's', 'ț': 't',
        'Ă': 'A', 'Â': 'A', 'Î': 'I', 'Ș': 'S', 'Ț': 'T',
        '–': '-', '”': '"', '„': '"', '’': "'"
    }
    for k, v in replacements.items():
        text = text.replace(k, v)
    
    
    text = text.replace('**', '').replace('##', '').replace('###', '')
    return text

def generate_pdf_report(analysis_text, chart_filename=None):
    """
    Generează un raport PDF cu analiza text și graficul (dacă există).
    Returnează numele fișierului PDF generat.
    """
    pdf_filename = "Raport_Investitii.pdf"
    print(f"\n[SISTEM]  Generez PDF: {pdf_filename}...")

    try:
        pdf = FPDF()
        pdf.add_page()
        
       
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(0, 10, "Raport Analiza Financiara (AI Agent)", ln=True, align='C')
        pdf.ln(10) 

        
        pdf.set_font("Arial", size=12)
        clean_body = clean_text_for_pdf(analysis_text)
        
        pdf.multi_cell(0, 10, clean_body)
        pdf.ln(10)

       
        if chart_filename and os.path.exists(chart_filename):
           
            pdf.image(chart_filename, x=30, w=150)
        
        pdf.output(pdf_filename)
        return pdf_filename

    except Exception as e:
        print(f"Eroare generare PDF: {e}")
        return None