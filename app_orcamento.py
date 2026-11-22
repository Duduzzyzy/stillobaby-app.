import streamlit as st
from datetime import datetime
import re
from gerador_luxo import criar_pdf_bytes

# Configurações de layout Mobile-First e UI Limpa
st.set_page_config(
    page_title="Stillobaby - Orçamentos",
    page_icon="👶",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Estilização CSS Corporativa de Alto Padrão
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #0D1B2A 0%, #1B263B 100%);
        padding: 22px;
        border-radius: 12px;
        text-align: center;
        margin-bottom: 25px;
        border-bottom: 3px solid #C5A059;
    }
    .main-title {
        font-size: 2rem;
        font-weight: 800;
        color: #FFFFFF !important;
        margin: 0;
        letter-spacing: 1px;
    }
    .sub-title {
        font-size: 0.95rem;
        color: #E0E1DD !important;
        margin-top: 5px;
        font-weight: 400;
    }
    .stButton>button {
        background: linear-gradient(180deg, #0D1B2A 0%, #1B263B 100%);
        color: white;
        border-radius: 8px;
        font-weight: 700;
        border: none;
        height: 50px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        transition: all 0.2s ease;
    }
    .stButton>button:hover {
        background: #1B263B;
        color: #C5A059;
        transform: translateY(-1px);
    }
</style>
""", unsafe_allow_html=True)

# Topo Visual Profissional
st.markdown("""
<div class="main-header">
    <p class="main-title">👶 STILLOBABY</p>
    <p class="sub-title">Centro Técnico Especializado em Carrinhos de Bebê</p>
</div>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# CONTROLE DE ACESSO E SEGURANÇA (LOGIN STILLOBABY)
# -----------------------------------------------------------------------------
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False

if not st.session_state.autenticado:
    st.markdown("### 🔐 Acesso Restrito à Equipe")
    st.info("Insira suas credenciais de atendimento da Stillobaby para acessar o sistema:")
    
    with st.form("form_login"):
        user_input = st.text_input("Usuário:", placeholder="Ex: seu usuário")
        pass_input = st.text_input("Senha de Acesso:", type="password", placeholder="••••••••")
        btn_login = st.form_submit_button("🔓 ENTRAR NO SISTEMA")
        
        if btn_login:
            if user_input.strip() == "daniela1607" and pass_input.strip() == "jw347618":
                st.session_state.autenticado = True
                st.success("✅ Acesso liberado com sucesso!")
                st.rerun()
            else:
                st.error("❌ Usuário ou senha incorretos! Tente novamente.")
                
    st.stop() # Bloqueia qualquer execução abaixo até logar com sucesso!

# Se estiver logado, exibe botão discreto para sair se quiser
c_head1, c_head2 = st.columns([8, 2])
with c_head2:
    if st.button("🚪 Sair"):
        st.session_state.autenticado = False
        st.rerun()

# Funções de Tratamento e Autocorreção Inteligente
def auto_corrigir_texto(texto):
    if not texto:
        return ""
    texto = re.sub(r'\s+', ' ', texto.strip())
    if len(texto) > 1:
        texto = texto[0].upper() + texto[1:]
    elif len(texto) == 1:
        texto = texto.upper()
    return texto

def tratar_preco_inteligente(valor_str):
    if not valor_str:
        return 0.0
    val_limpo = str(valor_str).replace("R$", "").replace(" ", "").replace(".", "").replace(",", ".")
    try:
        return float(val_limpo)
    except:
        return 0.0

# 1. CONFIGURAÇÕES DA EMPRESA (CNPJ + PIX + CONTATO)
with st.expander("⚙️ Dados da Stillobaby (CNPJ, Chave Pix e WhatsApp)", expanded=False):
    nome_empresa = st.text_input("Nome da Empresa:", value="STILLOBABY")
    cnpj_empresa = st.text_input("CNPJ da Empresa:", value="66.192.622/0001-77")
    contato_empresa = st.text_input("WhatsApp de Atendimento:", value="(11) 97697-5525")
    chave_pix_padrao = st.text_input("Chave Pix Padrão:", value="(11) 97697-5525")
    numero_os = st.text_input("Número da OS:", value=f"{datetime.now().strftime('%d%m%H%M')}")
    status_opcoes = [
        "AGUARDANDO APROVACAO",
        "ORCAMENTO APROVADO"
    ]
    status_orcamento = st.selectbox("Status do Documento:", status_opcoes, index=0)

# 2. DADOS DO CLIENTE & CARRINHO
st.markdown("### 1. Dados do Cliente e Carrinho")
col_cli, col_tel = st.columns(2)
with col_cli:
    nome_cliente_raw = st.text_input("Nome do Cliente:", placeholder="Ex: Mariana Silva")
    nome_cliente = auto_corrigir_texto(nome_cliente_raw)
with col_tel:
    telefone_cliente = st.text_input("WhatsApp do Cliente (opcional):", placeholder="Ex: (11) 98888-7777")

col_car, col_car_mod = st.columns(2)
with col_car:
    marcas = [
        "Cybex (Priam, Balios, Mios)",
        "Bugaboo (Fox, Bee, Cameleon, Donkey)",
        "Mima Xari",
        "UPPAbaby (Vista, Cruz)",
        "Stokke (Xplory, Trailz)",
        "Maxi-Cosi",
        "Chicco / Burigotto",
        "Outro modelo (digitar manual)"
    ]
    escolha_car = st.selectbox("Marca / Modelo:", marcas)
with col_car_mod:
    if "Outro" in escolha_car:
        modelo_carrinho = auto_corrigir_texto(st.text_input("Digite o modelo:", placeholder="Ex: Maclaren Quest"))
    else:
        modelo_carrinho = escolha_car

# 3. LANÇAMENTO TOTALMENTE PERSONALIZADO DE SERVIÇOS
st.markdown("### 2. Serviços e Peças (Totalmente Personalizado)")

sugestoes_texto = [
    "Digitar serviço livremente...",
    "Higienização Completa Antibacteriana e Impermeabilização",
    "Revisão Geral e Restauração da Trava do Freio",
    "Troca de Espumas e Revestimento da Manopla",
    "Manutenção e Lubrificação dos Rolamentos e Eixos",
    "Ajuste, Alinhamento e Solda de Chassi",
    "Reforma e Costura da Capota e Tecidos"
]

escolha_sugestao = st.selectbox("💡 Sugestões de texto rápido (opcional):", sugestoes_texto)

c_desc, c_val, c_btn = st.columns([6, 3, 2])
with c_desc:
    texto_padrao = "" if escolha_sugestao == "Digitar serviço livremente..." else escolha_sugestao
    servico_input = st.text_input("Descrição do Serviço / Peça:", value=texto_padrao, placeholder="Ex: Troca da trava direita")
with c_val:
    preco_input = st.text_input("Preço (R$):", placeholder="Ex: 650,00 ou 650")
with c_btn:
    st.write("")
    st.write("")
    btn_add = st.button("➕ Inserir")

# Inicializa sessão
if "itens" not in st.session_state:
    st.session_state.itens = []

if btn_add:
    desc_tratada = auto_corrigir_texto(servico_input)
    preco_tratado = tratar_preco_inteligente(preco_input)
    
    if not desc_tratada:
        st.warning("Digite a descrição do serviço!")
    elif preco_tratado <= 0:
        st.warning("Digite um valor válido maior que zero (ex: 350 ou 350,00)!")
    else:
        st.session_state.itens.append({
            "nome": desc_tratada,
            "preco": preco_tratado
        })
        st.rerun()

# Listagem dos Itens Lançados
if st.session_state.itens:
    st.write("---")
    st.write("**Itens adicionados no orçamento:**")
    subtotal = 0.0
    for i, it in enumerate(st.session_state.itens):
        c_i_nom, c_i_prc, c_i_del = st.columns([6, 3, 1])
        c_i_nom.write(f"• **{it['nome']}**")
        c_i_prc.write(f"R$ {it['preco']:,.2f}")
        if c_i_del.button("❌", key=f"del_{i}"):
            st.session_state.itens.pop(i)
            st.rerun()
        subtotal += it["preco"]
else:
    subtotal = 0.0
    st.info("Nenhum serviço inserido ainda. Digite a descrição e o preço acima!")

# 4. CONDIÇÕES DE PAGAMENTO (50% + 50% OU 5% DE DESCONTO À VISTA)
st.markdown("### 3. Condições Comerciais e Prazo")
col_cond_pag, col_cond_prz = st.columns(2)

with col_cond_pag:
    formas = [
        "50% de entrada no início + 50% na retirada do carrinho (Padrão)",
        "Pagamento integral à vista no Pix com 5% de desconto promocional",
        "Pagamento integral na entrega / retirada",
        "Até 3x sem juros no cartão de crédito",
        "Até 6x no cartão de crédito"
    ]
    forma_pagamento = st.selectbox("Forma de Pagamento:", formas)

with col_cond_prz:
    prazos = [
        "3 a 5 dias úteis",
        "2 a 3 dias úteis",
        "Serviço Expresso (Pronto em até 24h)",
        "Aguardando peças de reposição (7 a 10 dias úteis)",
        "Digitar prazo manual..."
    ]
    escolha_prazo = st.selectbox("Prazo de Execução:", prazos)
    if "Digitar prazo manual" in escolha_prazo:
        prazo_final = auto_corrigir_texto(st.text_input("Digite o prazo combinado:", placeholder="Ex: Até sexta-feira às 15h"))
    else:
        prazo_final = escolha_prazo

# Chave Pix visível diretamente na tela principal para troca rápida se quiser
chave_pix = st.text_input(
    "🔑 Chave Pix do Orçamento (Já vem o número padrão, mas pode apagar e trocar na hora):",
    value=chave_pix_padrao,
    help="Pode ser o celular, CPF, CNPJ, e-mail ou chave aleatória. O QR Code do PDF se ajusta na hora!"
)

# Exibição de Resumo Financeiro Inteligente
if subtotal > 0:
    st.write("---")
    tem_desc = "5% de desconto" in forma_pagamento
    if tem_desc:
        val_desconto = subtotal * 0.05
        total_a_pagar = subtotal - val_desconto
        c_tot1, c_tot2, c_tot3 = st.columns(3)
        c_tot1.metric("Subtotal", f"R$ {subtotal:,.2f}")
        c_tot2.metric("Desconto (5%)", f"- R$ {val_desconto:,.2f}")
        c_tot3.metric("Total Final com Desconto", f"R$ {total_a_pagar:,.2f}")
    else:
        total_a_pagar = subtotal
        if "50%" in forma_pagamento:
            metade = total_a_pagar / 2
            c_m1, c_m2 = st.columns(2)
            c_m1.metric("Valor Total do Serviço", f"R$ {total_a_pagar:,.2f}")
            c_m2.metric("Entrada (50%) + Retirada (50%)", f"2x de R$ {metade:,.2f}")
        else:
            st.success(f"### Valor Total a Pagar: R$ {total_a_pagar:,.2f}")

# 5. BOTÃO GERAR PDF COM QR CODE E CNPJ
st.write("")
if st.button("📄 GERAR ORÇAMENTO EM PDF"):
    if not nome_cliente:
        st.error("Por favor, preencha o nome do cliente!")
    elif not st.session_state.itens:
        st.error("Insira pelo menos um serviço no orçamento!")
    elif not prazo_final:
        st.error("Por favor, preencha o prazo de execução!")
    else:
        pdf_bytes = criar_pdf_bytes(
            nome_cliente=nome_cliente,
            modelo_carrinho=modelo_carrinho,
            lista_servicos=st.session_state.itens,
            forma_pagamento=forma_pagamento,
            prazo_dias=prazo_final,
            nome_empresa=nome_empresa,
            contato_empresa=contato_empresa,
            cnpj=cnpj_empresa,
            chave_pix=chave_pix,
            numero_os=numero_os,
            telefone_cliente=telefone_cliente,
            status_documento=status_orcamento
        )
        
        nome_arquivo = f"Orcamento_{nome_cliente.replace(' ', '_')}.pdf"
        st.balloons()
        st.success("✅ Orçamento oficial da Stillobaby gerado com sucesso!")
        
        st.download_button(
            label="⬇️ BAIXAR PDF PRONTO PARA ENVIAR NO WHATSAPP",
            data=pdf_bytes,
            file_name=nome_arquivo,
            mime="application/pdf"
        )
