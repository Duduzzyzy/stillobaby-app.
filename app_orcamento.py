"""
MOTOR DE GERAÇÃO DE PDF - STTILLOBABY MASTER EDITION
Layout Executivo de Alta Precisão (100% blindado contra sobreposição de palavras).
QR Code Oficial do Banco Central (EMVCo Pix Copia e Cola) que abre direto no app do banco.
"""

import os
import re
import tempfile
import unicodedata
from datetime import datetime

import qrcode
from fpdf import FPDF


def limpar_texto(texto):
    if not texto:
        return ""
    return str(texto).replace("•", "-")


def crc16_ccitt(payload: str) -> str:
    """Calcula o CRC16-CCITT exigido pela especificação oficial do Banco Central do Brasil."""
    crc = 0xFFFF
    for c in payload:
        crc ^= ord(c) << 8
        for _ in range(8):
            if crc & 0x8000:
                crc = (crc << 1) ^ 0x1021
            else:
                crc = crc << 1
            crc &= 0xFFFF
    return f"{crc:04X}"


def format_pix_field(id_str: str, val_str: str) -> str:
    return f"{id_str}{len(val_str):02d}{val_str}"


def gerar_payload_pix_oficial(
    chave: str,
    nome_beneficiario: str = "Sebastião Carlos Pinto Da Silva",
    cidade: str = "SAO PAULO",
    valor: float = 0.0,
    txid: str = "***",
) -> str:
    """
    Gera a string oficial Pix Padrão Banco Central do Brasil (EMVCo BR Code).
    Qualquer banco (Nubank, Itaú, Bradesco, Inter, Santander, etc.) reconhece e abre a tela de transferência.
    """
    chave_limpa = str(chave).strip()
    nums = re.sub(r"\D", "", chave_limpa)
    if "@" in chave_limpa:
        # Chave e-mail mantém como está
        chave_limpa = chave_limpa.lower()
    elif len(nums) == 11:
        # Se for celular (ex: 11999998888), o Bacen exige +55.
        # Mas se for CPF (11 dígitos), a chave Pix é apenas os 11 dígitos numéricos.
        # Se começar com formato padrão de celular (ex: DDD + 9 dígitos), verifica se já tem +55:
        if chave_limpa.startswith("+55"):
            chave_limpa = f"+{nums}"
        else:
            # Em chaves padrão tipo telefone celular sem +55:
            chave_limpa = f"+55{nums}"
    elif len(nums) == 10:
        # Celular ou fixo antigo com DDD
        if not chave_limpa.startswith("+55"):
            chave_limpa = f"+55{nums}"
        else:
            chave_limpa = f"+{nums}"
    elif len(nums) == 14:
        # CNPJ: apenas números
        chave_limpa = nums
    # Chave aleatória (EVP / UUID) mantém intacta

    # 00: Format Indicator
    p00 = format_pix_field("00", "01")
    # 26: Merchant Account Info (GUI + Pix Key)
    gui = format_pix_field("00", "BR.GOV.BCB.PIX")
    key = format_pix_field("01", chave_limpa)
    p26 = format_pix_field("26", gui + key)
    # 52: Merchant Category Code (0000 = Geral)
    p52 = format_pix_field("52", "0000")
    # 53: Transaction Currency (986 = BRL)
    p53 = format_pix_field("53", "986")

    # 54: Transaction Amount
    p54 = ""
    if valor and valor > 0:
        p54 = format_pix_field("54", f"{valor:.2f}")

    # 58: Country Code
    p58 = format_pix_field("58", "BR")
    # 59: Merchant Name (máx 25)
    nome_norm = (
        unicodedata.normalize("NFKD", str(nome_beneficiario))
        .encode("ASCII", "ignore")
        .decode("ASCII")
    )
    nome_beneficiario_limpo = re.sub(r"[^A-Za-z0-9 ]", "", nome_norm).strip().upper()[:25]
    if not nome_beneficiario_limpo:
        nome_beneficiario_limpo = "SEBASTIAO CARLOS"
    p59 = format_pix_field("59", nome_beneficiario_limpo)

    # 60: Merchant City (máx 15)
    cid_norm = (
        unicodedata.normalize("NFKD", str(cidade))
        .encode("ASCII", "ignore")
        .decode("ASCII")
    )
    cidade_limpa = re.sub(r"[^A-Za-z0-9 ]", "", cid_norm).strip().upper()[:15]
    if not cidade_limpa:
        cidade_limpa = "SAO PAULO"
    p60 = format_pix_field("60", cidade_limpa)

    # 62: Additional Data Field (txid / Identificador da transferência)
    txid_limpo = re.sub(r"[^A-Za-z0-9]", "", txid).strip()[:25]
    if not txid_limpo:
        txid_limpo = "***"
    p62_tx = format_pix_field("05", txid_limpo)
    p62 = format_pix_field("62", p62_tx)

    payload_sem_crc = p00 + p26 + p52 + p53 + p54 + p58 + p59 + p60 + p62 + "6304"
    crc = crc16_ccitt(payload_sem_crc)
    return payload_sem_crc + crc


class PDFSttilloMaster(FPDF):
    def __init__(
        self,
        nome_empresa="STTILLOBABY",
        contato="(11) 97697-5525",
        cnpj="66.192.622/0001-77",
        numero_os="",
    ):
        super().__init__()
        self.nome_empresa = nome_empresa
        self.contato = contato
        self.cnpj = cnpj
        self.numero_os = numero_os

    def header(self):
        # 1. BARRAS CORPORATIVAS
        self.set_fill_color(10, 25, 47)
        self.rect(0, 0, 210, 38, "F")

        # Friso Dourado
        self.set_fill_color(197, 160, 89)
        self.rect(0, 38, 210, 2.5, "F")

        # 2. BRANDING OFICIAL DA MARCA (STTILLOBABY)
        self.set_font("Helvetica", "B", 20)
        self.set_text_color(255, 255, 255)
        self.set_xy(14, 8)
        self.cell(110, 9, self.nome_empresa, ln=False)

        # Badge da OS
        if self.numero_os:
            self.set_fill_color(197, 160, 89)
            self.rect(138, 8, 58, 8, "F")
            self.set_font("Helvetica", "B", 9.5)
            self.set_text_color(10, 25, 47)
            self.set_xy(138, 8)
            self.cell(
                58, 8, f"ORDEM DE SERVICO #{limpar_texto(self.numero_os)}", align="C"
            )

        self.set_font("Helvetica", "", 9)
        self.set_text_color(200, 215, 235)
        self.set_xy(14, 18)
        self.cell(
            110,
            5,
            "Centro Tecnico de Restauracao, Manutencao e Higienizacao de Carrinhos",
            ln=True,
        )

        self.set_font("Helvetica", "", 8.5)
        self.set_text_color(180, 200, 220)
        self.set_xy(14, 25)
        linha_topo = f"WhatsApp: {self.contato} | Sao Paulo - SP"
        if self.cnpj:
            linha_topo += f" | CNPJ: {self.cnpj}"
        self.cell(0, 5, linha_topo, ln=True)
        self.ln(13)

    def footer(self):
        self.set_y(-24)
        self.set_draw_color(210, 215, 225)
        self.set_line_width(0.3)
        self.line(14, self.get_y(), 196, self.get_y())
        self.ln(2)

        self.set_font("Helvetica", "B", 7.5)
        self.set_text_color(90, 100, 115)
        self.cell(
            0,
            3.5,
            f"{self.nome_empresa} - CENTRO TECNICO ESPECIALIZADO EM CARRINHOS PREMIUM",
            align="C",
            ln=True,
        )

        self.set_font("Helvetica", "", 7)
        self.set_text_color(130, 135, 145)
        self.cell(
            0,
            3.5,
            "Garantia legal de 90 dias conforme Art. 26 do Codigo de Defesa do Consumidor (Lei 8.078/90).",
            align="C",
            ln=True,
        )
        self.cell(
            0,
            3.5,
            f"Documento oficial emitido em {datetime.now().strftime('%d/%m/%Y as %H:%M')} | Validade da proposta: 7 dias corridos.",
            align="C",
        )


def criar_pdf_bytes(
    nome_cliente,
    modelo_carrinho,
    lista_servicos,
    forma_pagamento,
    prazo_dias,
    nome_empresa="STTILLOBABY",
    contato_empresa="(11) 97697-5525",
    cnpj="66.192.622/0001-77",
    chave_pix="",
    numero_os="",
    telefone_cliente="",
    status_documento="AGUARDANDO APROVACAO",
):
    pdf = PDFSttilloMaster(nome_empresa, contato_empresa, cnpj, numero_os)
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=26)

    # -------------------------------------------------------------------------
    # 1. BLOCO DADOS DO CLIENTE & EQUIPAMENTO (COORDENADAS SEPARADAS - SEM COLISÃO)
    # -------------------------------------------------------------------------
    pdf.ln(2)
    y_bloco_cli = pdf.get_y()

    # Caixa de fundo
    pdf.set_fill_color(248, 250, 253)
    pdf.rect(14, y_bloco_cli, 182, 30, "F")
    pdf.set_draw_color(215, 222, 235)
    pdf.set_line_width(0.4)
    pdf.rect(14, y_bloco_cli, 182, 30, "D")

    # Faixa do topo do card
    pdf.set_fill_color(235, 240, 248)
    pdf.rect(14, y_bloco_cli, 182, 6, "F")
    pdf.set_xy(17, y_bloco_cli + 1)
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_text_color(10, 25, 47)
    pdf.cell(85, 4, "INFORMACOES DO CLIENTE")
    pdf.set_xy(110, y_bloco_cli + 1)
    pdf.cell(82, 4, "DADOS DO EQUIPAMENTO", align="R", ln=True)

    # Linha 1: Cliente (Coluna 1) | Equipamento (Coluna 2)
    pdf.set_xy(17, y_bloco_cli + 8)
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_text_color(100, 110, 125)
    pdf.cell(20, 5, "Cliente:")
    pdf.set_font("Helvetica", "B", 8.5)
    pdf.set_text_color(20, 30, 45)
    pdf.cell(65, 5, limpar_texto(nome_cliente)[:28])

    pdf.set_xy(108, y_bloco_cli + 8)
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_text_color(100, 110, 125)
    pdf.cell(28, 5, "Equipamento:")
    pdf.set_font("Helvetica", "B", 8.5)
    pdf.set_text_color(20, 30, 45)
    pdf.cell(58, 5, limpar_texto(modelo_carrinho)[:28], ln=True)

    # Linha 2: Contato (Coluna 1) | Data Entrada (Coluna 2)
    pdf.set_xy(17, y_bloco_cli + 15)
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_text_color(100, 110, 125)
    pdf.cell(20, 5, "Contato:")
    pdf.set_font("Helvetica", "", 8.5)
    pdf.set_text_color(40, 50, 65)
    tel_exibir = (
        limpar_texto(telefone_cliente) if telefone_cliente else "Registrado em Sistema"
    )
    pdf.cell(65, 5, tel_exibir[:28])

    pdf.set_xy(108, y_bloco_cli + 15)
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_text_color(100, 110, 125)
    pdf.cell(28, 5, "Data Entrada:")
    pdf.set_font("Helvetica", "", 8.5)
    pdf.set_text_color(40, 50, 65)
    pdf.cell(58, 5, datetime.now().strftime("%d/%m/%Y"), ln=True)

    # Linha 3: Status (Coluna 1) | Laudo Tecnico (Coluna 2)
    pdf.set_xy(17, y_bloco_cli + 22)
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_text_color(100, 110, 125)
    pdf.cell(20, 5, "Status:")
    pdf.set_font("Helvetica", "B", 8)

    # Cor dinâmica para o Status
    texto_status = limpar_texto(status_documento).upper()
    if "APROVADO" in texto_status:
        pdf.set_text_color(27, 94, 32)  # Verde elegante para aprovado
    else:
        pdf.set_text_color(197, 160, 89)  # Dourado nobre para aguardando / análise

    pdf.cell(65, 5, texto_status[:30])

    pdf.set_xy(108, y_bloco_cli + 22)
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_text_color(100, 110, 125)
    pdf.cell(28, 5, "Laudo Tecnico:")
    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(40, 50, 65)
    pdf.cell(58, 5, "Pecas Originais / Higienizacao Atoxica", ln=True)

    pdf.set_y(y_bloco_cli + 34)

    # -------------------------------------------------------------------------
    # 2. TABELA DE SERVIÇOS & PEÇAS
    # -------------------------------------------------------------------------
    pdf.set_font("Helvetica", "B", 9.5)
    pdf.set_text_color(10, 25, 47)
    pdf.cell(0, 6, "DISCRIMINACAO DOS SERVICOS E PECAS APROVADAS", ln=True)

    pdf.set_fill_color(10, 25, 47)
    pdf.set_font("Helvetica", "B", 8.5)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(10, 7, " Item", border=0, fill=True, align="C")
    pdf.cell(132, 7, " Descricao do Servico Tecnico Especializado", border=0, fill=True)
    pdf.cell(40, 7, "Valor (R$)  ", border=0, fill=True, align="R", ln=True)

    subtotal = 0.0
    for idx, item in enumerate(lista_servicos, 1):
        nome_item = limpar_texto(item["nome"])
        preco = float(item["preco"])
        subtotal += preco

        if idx % 2 == 1:
            pdf.set_fill_color(255, 255, 255)
        else:
            pdf.set_fill_color(248, 250, 253)

        pdf.set_font("Helvetica", "B", 8.5)
        pdf.set_text_color(120, 130, 145)
        pdf.cell(10, 7, f" {idx:02d}", border="B", fill=True, align="C")

        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(40, 45, 55)
        pdf.cell(132, 7, f" {nome_item}", border="B", fill=True)

        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(20, 30, 45)
        preco_formatado = (
            f"R$ {preco:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        )
        pdf.cell(
            40, 7, f"{preco_formatado}  ", border="B", align="R", fill=True, ln=True
        )

    pdf.ln(2)

    tem_desconto = "5% de desconto" in forma_pagamento or "5%" in forma_pagamento

    if tem_desconto:
        desconto_valor = subtotal * 0.05
        total_final = subtotal - desconto_valor

        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(100, 110, 125)
        pdf.cell(142, 5, "Subtotal Geral dos Servicos:", align="R")
        sub_str = (
            f"R$ {subtotal:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        )
        pdf.cell(40, 5, f"{sub_str}  ", align="R", ln=True)

        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(180, 45, 45)
        pdf.cell(142, 5, "Bonificacao / Desconto Promocional a Vista (-5%):", align="R")
        desc_str = (
            f"- R$ {desconto_valor:,.2f}".replace(",", "X")
            .replace(".", ",")
            .replace("X", ".")
        )
        pdf.cell(40, 5, f"{desc_str}  ", align="R", ln=True)
    else:
        total_final = subtotal

    # Box do Total Final
    pdf.set_fill_color(232, 245, 233)
    pdf.set_draw_color(165, 214, 167)
    pdf.set_line_width(0.5)
    pdf.rect(14, pdf.get_y() + 1, 182, 11, "DF")

    pdf.set_xy(18, pdf.get_y() + 2)
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(27, 94, 32)
    pdf.cell(130, 9, "VALOR TOTAL LIQUIDO APROVADO:")

    total_str = (
        f"R$ {total_final:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    )
    pdf.set_font("Helvetica", "B", 13)
    pdf.cell(44, 9, f"{total_str}  ", align="R", ln=True)
    pdf.ln(6)

    # -------------------------------------------------------------------------
    # 3. CONDIÇÕES COMERCIAIS & QR CODE PIX OFICIAL DO BANCO CENTRAL
    # -------------------------------------------------------------------------
    y_cond = pdf.get_y()
    chave_pix_final = chave_pix.strip() if chave_pix else "66.192.622/0001-77"

    # Valor da transferência que vai embutido no Pix
    if "50%" in forma_pagamento:
        valor_pix_embutido = round(total_final / 2, 2)
        rotulo_pix_qr = "PIX ENTRADA 50%"
    else:
        valor_pix_embutido = round(total_final, 2)
        rotulo_pix_qr = "PAGUE VIA PIX"

    # Gera a string oficial EMVCo BR Code (Padrão Banco Central do Brasil)
    payload_pix_brcode = gerar_payload_pix_oficial(
        chave=chave_pix_final,
        nome_beneficiario="Sebastião Carlos Pinto Da Silva",
        cidade="SAO PAULO",
        valor=valor_pix_embutido,
        txid=numero_os if numero_os else "***",
    )

    # Gera QR Code oficial escaneável por QUALQUER banco em alta resolução
    qr = qrcode.QRCode(
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=12,
        border=2,
    )
    qr.add_data(payload_pix_brcode)
    qr.make(fit=True)
    img_qr = qr.make_image(fill_color="black", back_color="white")

    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tf:
        temp_qr_path = tf.name
        img_qr.save(temp_qr_path)

    largura_txt_box = 136
    altura_cond = 50

    pdf.set_fill_color(248, 250, 253)
    pdf.rect(14, y_cond, 182, altura_cond, "F")
    pdf.set_draw_color(215, 222, 235)
    pdf.set_line_width(0.4)
    pdf.rect(14, y_cond, 182, altura_cond, "D")

    # Cabeçalho da seção de condições
    pdf.set_fill_color(235, 240, 248)
    pdf.rect(14, y_cond, 182, 6, "F")
    pdf.set_xy(17, y_cond + 1)
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_text_color(10, 25, 47)
    pdf.cell(largura_txt_box, 4, "CONDICOES DE PAGAMENTO E TERMOS DE EXECUCAO", ln=True)

    # Linha 1: Condição Pagamento
    pdf.set_xy(17, y_cond + 8)
    pdf.set_font("Helvetica", "B", 8.5)
    pdf.set_text_color(10, 25, 47)
    pdf.cell(38, 4.5, "- Condicao Pagamento:")
    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(40, 50, 65)
    texto_forma = limpar_texto(forma_pagamento)[:60]
    pdf.cell(largura_txt_box - 38, 4.5, f" {texto_forma}", ln=True)

    # Linha 1.1: Detalhe dos 50% + 50%
    if "50%" in forma_pagamento:
        metade = total_final / 2
        metade_str = (
            f"R$ {metade:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        )
        pdf.set_x(17)
        pdf.set_font("Helvetica", "I", 7.8)
        pdf.set_text_color(180, 130, 40)
        pdf.cell(
            largura_txt_box,
            4,
            f"  * Divisao: {metade_str} no inicio dos servicos + {metade_str} na retirada",
            ln=True,
        )
    else:
        pdf.ln(1)

    # Linha 2: Chave Pix
    pdf.set_x(17)
    pdf.set_font("Helvetica", "B", 8.5)
    pdf.set_text_color(10, 25, 47)
    pdf.cell(38, 4.5, "- Chave PIX Oficial:")
    pdf.set_font("Helvetica", "B", 8.5)
    pdf.set_text_color(27, 94, 32)
    pdf.cell(
        largura_txt_box - 38,
        4.5,
        f" {limpar_texto(chave_pix_final)} (Sebastião Carlos Pinto Da Silva)",
        ln=True,
    )

    # Linha 3: Prazo
    pdf.set_x(17)
    pdf.set_font("Helvetica", "B", 8.5)
    pdf.set_text_color(10, 25, 47)
    pdf.cell(38, 4.5, "- Prazo Entrega:")
    pdf.set_font("Helvetica", "", 8.5)
    pdf.set_text_color(40, 50, 65)
    pdf.cell(largura_txt_box - 38, 4.5, f" {limpar_texto(prazo_dias)}", ln=True)

    # Linha 4: Garantia Legal
    pdf.set_x(17)
    pdf.set_font("Helvetica", "B", 8.5)
    pdf.set_text_color(10, 25, 47)
    pdf.cell(38, 4.5, "- Garantia Legal:")
    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(40, 50, 65)
    pdf.cell(
        largura_txt_box - 38,
        4.5,
        " 90 dias conforme Art. 26 do Codigo de Defesa do Consumidor.",
        ln=True,
    )

    # Linha 5: Segurança e Laudo
    pdf.set_x(17)
    pdf.set_font("Helvetica", "B", 8.5)
    pdf.set_text_color(10, 25, 47)
    pdf.cell(38, 4.5, "- Seguranca:")
    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(40, 50, 65)
    pdf.cell(
        largura_txt_box - 38,
        4.5,
        " Higienizacao atoxica hospitalar, segura para a saude do bebe.",
        ln=True,
    )

    # Box com QR Code Oficial
    # Dimensões da caixinha: largura 38, altura 41
    # Imagem QR: 30x30 posicionada em Y = y_cond + 7
    # Texto do rótulo: posicionado em Y = y_cond + 38 (CLARAMENTE ABAIXO DO QR, NUNCA EM CIMA!)
    pdf.set_fill_color(255, 255, 255)
    pdf.set_draw_color(200, 210, 225)
    pdf.rect(154, y_cond + 6, 38, 41, "DF")
    pdf.image(temp_qr_path, x=158, y=y_cond + 7.5, w=30, h=30)
    pdf.set_xy(154, y_cond + 38.5)
    pdf.set_font("Helvetica", "B", 7)
    pdf.set_text_color(10, 25, 47)
    pdf.cell(38, 7, rotulo_pix_qr, align="C")

    try:
        os.remove(temp_qr_path)
    except:
        pass

    # -------------------------------------------------------------------------
    # 4. CHAVE PIX COPIA E COLA OFICIAL (EMVCo BR CODE) + CHAVE DIRETA
    # -------------------------------------------------------------------------
    pdf.set_y(y_cond + altura_cond + 3)
    y_pix_box = pdf.get_y()

    pdf.set_fill_color(243, 245, 249)
    pdf.set_draw_color(215, 222, 235)
    pdf.rect(14, y_pix_box, 182, 19, "DF")

    # Cabeçalho da caixa copia e cola
    pdf.set_xy(17, y_pix_box + 1.5)
    pdf.set_font("Helvetica", "B", 7.5)
    pdf.set_text_color(10, 25, 47)
    pdf.cell(95, 3.5, "CHAVE PIX DIRETA (FAVORECIDO: SEBASTIAO CARLOS PINTO DA SILVA):")
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_text_color(27, 94, 32)
    pdf.cell(80, 3.5, f"{limpar_texto(chave_pix_final)}", align="R", ln=True)

    # Linha divisória fina interna
    pdf.set_draw_color(225, 230, 240)
    pdf.line(17, y_pix_box + 5.8, 193, y_pix_box + 5.8)

    # Código Pix Copia e Cola completo (BR Code oficial)
    pdf.set_xy(17, y_pix_box + 7)
    pdf.set_font("Helvetica", "B", 6.5)
    pdf.set_text_color(80, 90, 105)
    pdf.cell(
        0,
        3,
        "CODIGO PIX COPIA E COLA (COPIE E COLE DIRETAMENTE NO SEU BANCO):",
        ln=True,
    )

    pdf.set_x(17)
    pdf.set_font("Courier", "B", 6.5)
    pdf.set_text_color(40, 50, 65)
    pdf.multi_cell(176, 3, payload_pix_brcode)

    return bytes(pdf.output())
