import streamlit as st
import google.generativeai as genai
import tools  
import os
from dotenv import load_dotenv
import re

load_dotenv("api.env")
api_key = os.getenv("API_KEY")

st.set_page_config(
    page_title="Market Agent Pro",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("BFinance")

if "portfolio_results" not in st.session_state:
    with st.spinner(" Îți verific portofoliul personal..."):
        try:
            if hasattr(tools, 'check_portfolio_updates'):
                update_msg = tools.check_portfolio_updates()
                
                st.session_state.portfolio_results = update_msg if update_msg else "Nu sunt modificări recente în portofoliu."
            else:
                st.session_state.portfolio_results = "⚠️ Funcția de actualizare lipsește."
        except Exception as e:
            st.session_state.portfolio_results = f"Eroare la actualizare: {e}"


with st.sidebar:
    st.header(" Configurare")
    # AM ELIMINAT api_key = "" CARE SUPRASCRIA CHEIA DIN .ENV
    st.divider() 

    st.subheader(" Adaugă în Portofoliu")
    col1, col2 = st.columns([2, 1])
    with col1:
        new_ticker = st.text_input("Simbol", placeholder="ex: TSLA", label_visibility="collapsed")
    with col2:
        if st.button("Adaugă"):
            if new_ticker:
                rezultat = tools.add_stock_to_portfolio(new_ticker)
                st.toast(rezultat)
                if "Am adăugat" in rezultat:
                    st.rerun()

    st.divider()
    if st.button(" Șterge Conversația", type="primary"): 
        st.session_state.messages = []
        st.session_state.chat_session = None
        st.rerun()

if api_key:
    try:
        genai.configure(api_key=api_key)
        my_tools = [tools.search_internet, tools.get_financial_data, tools.generate_price_chart,tools.generate_pdf_report]
        
        if "chat_session" not in st.session_state or st.session_state.chat_session is None:
            model = genai.GenerativeModel(
                model_name='gemini-2.5-flash-lite',
                tools=my_tools,
                system_instruction="""Ești un Analist Financiar Expert (Market Agent 2.0).
        Obiectivul tău este să răspunzi COMPLET la întrebările utilizatorului folosind uneltele disponibile.

        REGULI CRITICE:
        1. NU răspunde doar descriind ce vrei să faci. FĂ-O efectiv apelând funcția și SPUNE REZULTATUL.
        2. Dacă utilizatorul cere o comparație (ex: Coca-Cola vs Pepsi), folosește `get_financial_data` pentru AMBELE companii.
        3. Citește cu atenție datele primite de la unelte. Prezintă datele JSON într-un format ușor de citit.
        4. Dacă generezi un grafic, confirmă utilizatorului că a fost salvat fișierul (ex: AMZN_chart.png).
        5. NU lipi cuvintele între ele, chiar dacă folosești diacritice (ș, ț, ă, î, â).
        6. Când folosești cifre sau simboluri (ex: $43.29), pune un spațiu înainte și după ele.
        7. Formatează datele LIVE folosind uneltele disponibile.
        Exemplu de flux corect:
User: "Compară KO și PEP"
Tu: Apelezi get_financial_data("KO") -> primești datele -> Apelezi get_financial_data("PEP") -> primești datele.
Răspuns final: "Iată comparația: Coca-Cola are un dividend de X%, iar Pepsi de Y%..."""
        
            )
            st.session_state.chat_session = model.start_chat(enable_automatic_function_calling=True)
    except Exception as e:
        st.error(f"Eroare API: {e}")


tab_chat, tab_portofoliu = st.tabs([" Conversație", " Portofoliul Meu"])

with tab_chat:
    if "messages" not in st.session_state:
        st.session_state.messages = []

    
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            img_path = message.get("image")
            if img_path and os.path.exists(img_path):
                st.image(img_path)

    if prompt := st.chat_input("Analizează o companie..."):
        if not api_key:
            st.warning("Cheia API lipsește din fișierul api.env.")
        else:
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                with st.spinner("Agentul analizează..."):
                    try:
                        response = st.session_state.chat_session.send_message(prompt)
                        text_response = response.text
                        
                        image_file = None
                        match = re.search(r"(\w+_chart\.png)", text_response)
                        
                        st.markdown(text_response)
                        
                        if match:
                            potential_path = match.group(1)
                            if os.path.exists(potential_path):
                                st.image(potential_path)
                                image_file = potential_path
                        
                        message_data = {"role": "assistant", "content": text_response}
                        if image_file:
                            message_data["image"] = image_file
                        
                        st.session_state.messages.append(message_data)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Eroare: {e}")
if st.session_state.messages and st.session_state.messages[-1]["role"] == "assistant":
        st.divider()
        col_pdf, _ = st.columns([1, 4])
        with col_pdf:
            if st.button(" Generează Raport PDF"):
                last_msg = st.session_state.messages[-1]
                text_content = last_msg["content"]
                img_content = last_msg.get("image") # Poate fi None dacă nu există grafic
                
                with st.spinner("Se creează PDF-ul..."):
                    try:
                        pdf_path = tools.generate_pdf_report(text_content, img_content)
                        if pdf_path and os.path.exists(pdf_path):
                            with open(pdf_path, "rb") as f:
                                st.download_button(
                                    label=" Descarcă Raportul",
                                    data=f,
                                    file_name="Raport_BFinance.pdf",
                                    mime="application/pdf"
                                )
                            st.success("Raportul este gata!")
                        else:
                            st.error("Nu s-a putut genera fișierul.")
                    except Exception as e:
                        st.error(f"Eroare PDF: {e}")
with tab_portofoliu:
    st.header(" Evoluția Portofoliului")
    if st.session_state.get("portfolio_results"):
        st.markdown(st.session_state.portfolio_results)
    
    st.divider()
    st.subheader(" Detalii Portofoliu")
    portofoliu_data = tools.load_portfolio()
    if portofoliu_data:
        st.table(portofoliu_data)
    else:
        st.info("Portofoliul este gol.")