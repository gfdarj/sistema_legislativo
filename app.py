import os
import django
import streamlit as st
import pandas as pd
from datetime import datetime

# ==========================================
# 1. CONFIGURAÇÃO DO AMBIENTE DJANGO
# ==========================================
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'legislativo.settings')  # AJUSTE AQUI
django.setup()

from www.models import (  # AJUSTE AQUI
    TipoProposicao, Autor, Comissao, Proposicao, Reuniao, Tramitacao, Parecer
)

# ==========================================
# 2. CONFIGURAÇÃO DA PÁGINA STREAMLIT
# ==========================================
st.set_page_config(page_title="Sistema Legislativo CRUD", page_icon="🏛️", layout="wide")


def main():
    st.sidebar.title("🏛️ Menu do Sistema")
    menu = [
        "Dashboard",
        "Autores",
        "Comissões",
        "Proposições",
        "Reuniões",
        "Tramitações",
        "Pareceres"
    ]
    escolha = st.sidebar.selectbox("Módulo de Gestão", menu)

    if escolha == "Dashboard":
        mostrar_dashboard()
    elif escolha == "Autores":
        crud_autores()
    elif escolha == "Comissões":
        crud_comissoes()
    elif escolha == "Proposições":
        crud_proposicoes()
    elif escolha == "Reuniões":
        crud_reunioes()
    elif escolha == "Tramitações":
        crud_tramitacoes()
    elif escolha == "Pareceres":
        crud_pareceres()


# ==========================================
# 3. MÓDULOS CRUD
# ==========================================

def mostrar_dashboard():
    st.title("📊 Dashboard Legislativo")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Proposições", Proposicao.objects.count())
    col2.metric("Comissões Ativas", Comissao.objects.filter(ativa=True).count())
    col3.metric("Reuniões", Reuniao.objects.count())
    col4.metric("Pareceres Emitidos", Parecer.objects.count())


def crud_autores():
    st.title("✍️ Gestão de Autores")
    tab_listar, tab_cadastrar = st.tabs(["Listar / Excluir", "Cadastrar"])

    with tab_listar:
        autores = Autor.objects.all()
        if autores.exists():
            dados = [{"ID": a.id, "Nome": a.nome, "Sexo": a.get_sexo_display(), "Ativo": a.ativo} for a in autores]
            st.dataframe(pd.DataFrame(dados), use_container_width=True)

            st.markdown("### Excluir Autor")
            autor_del = st.selectbox("Selecione para excluir:", autores, format_func=lambda x: x.nome)
            if st.button("Deletar Autor", type="primary"):
                autor_del.delete()
                st.success("Autor excluído!")
                st.rerun()
        else:
            st.info("Nenhum autor cadastrado.")

    with tab_cadastrar:
        with st.form("form_autor"):
            nome = st.text_input("Nome do Autor")
            sexo = st.radio("Sexo", ["M", "F"], horizontal=True)
            ativo = st.checkbox("Ativo", value=True)
            if st.form_submit_button("Salvar Autor"):
                if nome:
                    Autor.objects.create(nome=nome, sexo=sexo, ativo=ativo)
                    st.success("Autor cadastrado!")
                    st.rerun()


def crud_comissoes():
    st.title("🏢 Gestão de Comissões")
    tab_listar, tab_cadastrar = st.tabs(["Listar", "Cadastrar"])

    with tab_listar:
        comissoes = Comissao.objects.all()
        if comissoes.exists():
            dados = [{"ID": c.id, "Sigla": c.sigla, "Nome": c.nome, "Ativa": c.ativa} for c in comissoes]
            st.dataframe(pd.DataFrame(dados), use_container_width=True)

            st.markdown("### Alterar Status")
            com_status = st.selectbox("Selecione a Comissão:", comissoes, format_func=lambda x: x.sigla)
            if st.button("Inverter Status (Ativar/Inativar)"):
                com_status.ativa = not com_status.ativa
                com_status.save()
                st.success(f"Status de {com_status.sigla} alterado!")
                st.rerun()

    with tab_cadastrar:
        with st.form("form_comissao"):
            sigla = st.text_input("Sigla (ex: CCJ)", max_chars=20)
            nome = st.text_input("Nome Completo")
            ativa = st.checkbox("Ativa", value=True)
            if st.form_submit_button("Salvar Comissão"):
                if sigla and nome:
                    Comissao.objects.create(sigla=sigla, nome=nome, ativa=ativa)
                    st.success("Comissão cadastrada!")
                    st.rerun()


def crud_proposicoes():
    st.title("📄 Gestão de Proposições")
    tab_listar, tab_cadastrar = st.tabs(["Listar", "Cadastrar Nova"])

    with tab_listar:
        proposicoes = Proposicao.objects.select_related('tipo').all()
        if proposicoes.exists():
            dados = [{
                "Número": p.numero,
                "Formatado": p.numero_formatado,
                "Tipo": p.tipo.sigla,
                "Publicação": p.data_publicacao
            } for p in proposicoes]
            st.dataframe(pd.DataFrame(dados), use_container_width=True)

    with tab_cadastrar:
        with st.form("form_proposicao"):
            tipos = list(TipoProposicao.objects.filter(ativo=True))
            if not tipos:
                st.warning("Cadastre um Tipo de Proposição primeiro (via Django Admin).")
                return

            col1, col2, col3 = st.columns(3)
            with col1:
                tipo_sel = st.selectbox("Tipo", tipos, format_func=lambda x: x.nome)
            with col2:
                numero = st.text_input("Número (ID)", max_chars=11)
            with col3:
                num_form = st.text_input("Número Formatado", max_chars=20)

            ementa = st.text_area("Ementa")
            data_pub = st.date_input("Data de Publicação")
            autores_sel = st.multiselect("Autores", list(Autor.objects.filter(ativo=True)),
                                         format_func=lambda x: x.nome)
            link = st.text_input("Link Externo (Opcional)")

            if st.form_submit_button("Salvar Proposição"):
                try:
                    prop = Proposicao.objects.create(
                        tipo=tipo_sel, numero=numero, numero_formatado=num_form,
                        ementa=ementa, data_publicacao=data_pub, link_proposicao=link
                    )
                    prop.autores.set(autores_sel)
                    st.success("Proposição cadastrada!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro: {e}")


def crud_reunioes():
    st.title("📅 Gestão de Reuniões")
    tab_listar, tab_cadastrar = st.tabs(["Listar", "Agendar Reunião"])

    with tab_listar:
        reunioes = Reuniao.objects.select_related('comissao').all()
        if reunioes.exists():
            dados = [{
                "Comissão": r.comissao.sigla,
                "Tipo": r.get_tipo_display(),
                "Nº/Ano": f"{r.numero}/{r.ano}",
                "Data": r.data,
                "Hora": r.hora
            } for r in reunioes]
            st.dataframe(pd.DataFrame(dados), use_container_width=True)

    with tab_cadastrar:
        with st.form("form_reuniao"):
            comissoes = list(Comissao.objects.filter(ativa=True))
            col1, col2 = st.columns(2)
            with col1:
                com_sel = st.selectbox("Comissão", comissoes, format_func=lambda x: x.nome)
                tipo = st.selectbox("Tipo", ["ORDINARIA", "EXTRAORDINARIA"])
                numero = st.number_input("Número da Reunião", min_value=1)
            with col2:
                ano = st.number_input("Ano", min_value=2000, value=datetime.now().year)
                data = st.date_input("Data")
                hora = st.time_input("Hora")

            pauta = st.text_area("Pauta (Opcional)")
            ata = st.text_area("Ata (Opcional)")

            if st.form_submit_button("Salvar Reunião"):
                try:
                    Reuniao.objects.create(
                        comissao=com_sel, tipo=tipo, numero=numero, ano=ano,
                        data=data, hora=hora, pauta=pauta, ata=ata
                    )
                    st.success("Reunião agendada!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro (verifique se já existe reunião com este número/ano na comissão): {e}")


def crud_tramitacoes():
    st.title("🛤️ Gestão de Tramitações")
    tab_listar, tab_cadastrar = st.tabs(["Listar", "Registrar Tramitação"])

    with tab_listar:
        trams = Tramitacao.objects.select_related('proposicao', 'comissao').all()
        if trams.exists():
            dados = [{
                "Proposição": t.proposicao.numero_formatado,
                "Comissão": t.comissao.sigla,
                "Entrada": t.data_entrada,
                "Saída": t.data_saida
            } for t in trams]
            st.dataframe(pd.DataFrame(dados), use_container_width=True)

    with tab_cadastrar:
        with st.form("form_tram"):
            prop_sel = st.selectbox("Proposição", list(Proposicao.objects.all()),
                                    format_func=lambda x: x.numero_formatado)
            com_sel = st.selectbox("Comissão de Destino", list(Comissao.objects.filter(ativa=True)),
                                   format_func=lambda x: x.nome)

            col1, col2 = st.columns(2)
            with col1:
                data_in = st.date_input("Data de Entrada")
            with col2:
                data_out = st.date_input("Data de Saída (Opcional)", value=None)

            obs = st.text_area("Observação")

            if st.form_submit_button("Registrar Tramitação"):
                Tramitacao.objects.create(
                    proposicao=prop_sel, comissao=com_sel,
                    data_entrada=data_in, data_saida=data_out, observacao=obs
                )
                st.success("Tramitação registrada!")
                st.rerun()


def crud_pareceres():
    st.title("⚖️ Gestão de Pareceres")
    tab_listar, tab_cadastrar = st.tabs(["Listar", "Emitir Parecer"])

    with tab_listar:
        pareceres = Parecer.objects.select_related('tramitacao', 'relator', 'reuniao').all()
        if pareceres.exists():
            dados = [{
                "Proposição": p.tramitacao.proposicao.numero_formatado,
                "Relator": p.relator.nome,
                "Tipo": p.get_tipo_display(),
                "Data": p.data_apresentacao,
                "Decisão": p.parecer
            } for p in pareceres]
            st.dataframe(pd.DataFrame(dados), use_container_width=True)

    with tab_cadastrar:
        with st.form("form_parecer"):
            tram_sel = st.selectbox("Tramitação Referente", list(Tramitacao.objects.all()),
                                    format_func=lambda x: f"{x.proposicao.numero_formatado} - {x.comissao.sigla}")
            reuniao_sel = st.selectbox("Reunião", list(Reuniao.objects.all()), format_func=lambda x: x.descricao)
            relator_sel = st.selectbox("Relator", list(Autor.objects.filter(ativo=True)), format_func=lambda x: x.nome)

            col1, col2 = st.columns(2)
            with col1:
                tipo = st.selectbox("Tipo de Parecer", ["RELATOR", "VENCIDO"])
                parecer_resumo = st.text_input("Parecer (Resumo/Decisão)", max_chars=200)
            with col2:
                data_apresentacao = st.date_input("Data de Apresentação")

            st.caption("Texto Completo (Markdown / HTML permitido)")
            texto = st.text_area("Texto do Parecer", height=200)

            if st.form_submit_button("Salvar Parecer"):
                Parecer.objects.create(
                    tramitacao=tram_sel, reuniao=reuniao_sel, relator=relator_sel,
                    tipo=tipo, parecer=parecer_resumo, texto=texto,
                    data_apresentacao=data_apresentacao
                )
                st.success("Parecer emitido com sucesso!")
                st.rerun()


if __name__ == "__main__":
    main()

