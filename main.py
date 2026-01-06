import streamlit as st
import google.generativeai as genai
import tools  
import os
import re


st.set_page_config(
    page_title="Market Agent Pro",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("💰 Market Agent AI")
st.caption("🚀 Agent financiar autonom & personalizat")


if "portfolio_checked" not in st.session_state:
    with st.spinner("🔄 Îți verific portofoliul personal..."):
        try:
            #
            if hasattr(tools, 'check_portfolio_updates'):
                update_msg = tools.check_portfolio_updates()
                if update_msg:
                    st.info(update_msg, icon="🔔")
            else:
                st.warning("⚠️ Funcția 'check_portfolio_updates' lipsește din tools.py")
        except Exception as e:
            
            st.error(f"Eroare la încărcarea portofoliului: {e}")
            
    st.session_state.portfolio_checked = True


with st.sidebar:
    st.header(" Configurare")
    
    
    api_key = st.text_input(" Google API Key", type="password", help="Cheia ta de la Google AI Studio")
    
    st.divider() 

   
    st.subheader(" Unelte Active")
    st.success(" Căutare Web (DuckDuckGo)")
    st.success(" Date Financiare (Yahoo)")
    st.success(" Grafice (Matplotlib)")
    
    st.divider()

    
    st.subheader(" Portofoliul Meu")
    
    col1, col2 = st.columns([2, 1])
    with col1:
        new_ticker = st.text_input("Simbol", placeholder="ex: PLTR", label_visibility="collapsed")
    with col2:
        add_btn = st.button("Adaugă")

    if add_btn and new_ticker:
        with st.spinner("Verific..."):
            try:
                rezultat = tools.add_stock_to_portfolio(new_ticker)
                if "Am adăugat" in rezultat:
                    st.toast(rezultat, icon="Am adăugat") 
                    st.success(rezultat)
                else:
                    st.error(rezultat)
            except Exception as e:
                st.error(f"Eroare: {e}")

    st.divider()
    
   
    if st.button(" Șterge Conversația", type="primary"): 
        st.session_state.messages = []
        st.session_state.chat_session = None
        st.rerun()


if "messages" not in st.session_state:
    st.session_state.messages = []


if api_key:
    try:
        genai.configure(api_key=api_key)
        
        my_tools = [tools.search_internet, tools.get_financial_data, tools.generate_price_chart]
        
        system_instruction = """
        Ești un Analist Financiar Expert (Market Agent 2.0).
        Obiectivul tău este să răspunzi COMPLET la întrebările utilizatorului folosind uneltele disponibile.

        REGULI CRITICE:
        1. NU răspunde doar descriind ce vrei să faci. FĂ-O efectiv apelând funcția și SPUNE REZULTATUL.
        2. Dacă utilizatorul cere o comparație (ex: Coca-Cola vs Pepsi), folosește `get_financial_data` pentru AMBELE companii.
        3. Citește cu atenție datele primite de la unelte. Prezintă datele JSON într-un format ușor de citit.
        4. Dacă generezi un grafic, confirmă utilizatorului că a fost salvat fișierul (ex: AMZN_chart.png).
Exemplu de flux corect:
User: "Compară KO și PEP"
Tu: Apelezi get_financial_data("KO") -> primești datele -> Apelezi get_financial_data("PEP") -> primești datele.
Răspuns final: "Iată comparația: Coca-Cola are un dividend de X%, iar Pepsi de Y%..."
        """
        
        if "chat_session" not in st.session_state or st.session_state.chat_session is None:
            model = genai.GenerativeModel(
                model_name='gemini-2.5-flash-lite',
                tools=my_tools,
                system_instruction=system_instruction
            )
            st.session_state.chat_session = model.start_chat(enable_automatic_function_calling=True)
            
    except Exception as e:
        st.error(f"Eroare la configurare API: {e}")

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if "image" in message:
            st.image(message["image"])


if prompt := st.chat_input("Ce analizăm astăzi? (ex: Compară Apple cu Microsoft)"):
    if not api_key:
        st.warning("Te rog introdu cheia API în bara din stânga pentru a începe.")
        st.stop()

  
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

  
    with st.chat_message("assistant"):
        with st.spinner("Agentul analizează piețele..."):
            try:
                response = st.session_state.chat_session.send_message(prompt)
                text_response = response.text
                
                
                image_file = None
                match = re.search(r"(\w+_chart\.png)", text_response)
                
                st.markdown(text_response)
                
                if match:
                    filename = match.group(1)
                    if os.path.exists(filename):
                        st.image(filename)
                        image_file = filename
                    else:
                        st.warning(f"Graficul {filename} a fost generat, dar nu îl găsesc pe disc.")

                
                message_data = {"role": "assistant", "content": text_response}
                if image_file:
                    message_data["image"] = image_file
                
                st.session_state.messages.append(message_data)
                
                
                st.rerun()

            except Exception as e:
                st.error(f"A apărut o eroare: {e}")


if st.session_state.messages and st.session_state.messages[-1]["role"] == "assistant":
    st.markdown("---")
    col1, col2 = st.columns([1, 4])
    
    with col1:
        if st.button("📄 Generează Raport PDF"):
            last_msg = st.session_state.messages[-1]
            text_content = last_msg["content"]
            img_content = last_msg.get("image") 
            
            with st.spinner("Generez documentul PDF..."):
                
                try:
                    pdf_path = tools.generate_pdf_report(text_content, img_content)
                    
                    if pdf_path and os.path.exists(pdf_path):
                        
                        with open(pdf_path, "rb") as f:
                            pdf_data = f.read()
                        
                        
                        st.download_button(
                            label="⬇️ Descarcă Raportul Final",
                            data=pdf_data,
                            file_name="Raport_Investitii.pdf",
                            mime="application/pdf"
                        )
                        st.success("PDF generat! Apasă pe butonul de mai sus pentru download.")
                    else:
                        st.error("Eroare: Nu s-a putut crea fișierul PDF.")
                except AttributeError:
                    st.error("Eroare: Funcția 'generate_pdf_report' lipsește din tools.py. Verifică fișierul tools.")