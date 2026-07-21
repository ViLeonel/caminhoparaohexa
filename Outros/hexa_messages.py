"""Mensagens operacionais e estados vazios compartilhados da interface."""

from __future__ import annotations

from hexa_taticas import LIMITE_RESERVAS, LIMITE_TITULARES

__all__ = [
    "ANALISE_SEM_AVALIACOES",
    "AVISO_PERSISTENCIA",
    "CONFLITO_PERSISTENCIA",
    "DADOS_EXTERNOS_AUSENTES",
    "DOSSIE_CAMPO_AUSENTE",
    "FEEDBACK_MENSAGEM_OBRIGATORIA",
    "FEEDBACK_PREPARADO",
    "MERCADO_ATLETA_AUSENTE",
    "MERCADO_SEM_DADOS",
    "NAO_INFORMADO_FONTE",
    "PERFIL_VAZIO",
    "REPOSITORIO_OCUPADO",
    "ROSTER_SEM_RESULTADOS",
    "SEM_BASE_CALCULO",
    "SEM_REGISTRO_EDITORIAL",
    "SUCESSO_CADASTRO",
    "convocacao_completa",
    "resumo_convocacao",
]


SEM_DADO = "Sem dado"
NAO_INFORMADO_FONTE = "Não informado pela fonte"
NAO_PESQUISADO = "Ainda não pesquisado"
NAO_APLICAVEL = "Não aplicável"
SEM_BASE_CALCULO = "Sem base suficiente"
SEM_REGISTRO_EDITORIAL = "Ainda não registrado"

PERFIL_VAZIO = (
    "Busque por nome e selecione um atleta para abrir a ficha individual. "
    "A pesquisa começa vazia para evitar escolhas acidentais."
)
ROSTER_SEM_RESULTADOS = (
    "Nenhum atleta corresponde aos filtros atuais. Ajuste a busca, a posição "
    "ou o grupo para visualizar outros resultados."
)
ANALISE_SEM_AVALIACOES = (
    "Ainda não há atletas com as duas notas editoriais preenchidas. "
    "Consensos e divergências aparecerão quando Vini e Roberto tiverem avaliado o mesmo atleta."
)
MERCADO_SEM_DADOS = (
    "Ainda não há valores de mercado utilizáveis. Isso significa dado não pesquisado "
    "ou não informado pela fonte, e não valor igual a zero."
)
DADOS_EXTERNOS_AUSENTES = (
    "Os dados externos deste atleta ainda não foram pesquisados ou cadastrados."
)
MERCADO_ATLETA_AUSENTE = (
    "O valor de mercado deste atleta ainda não foi pesquisado ou informado pela fonte."
)
DOSSIE_CAMPO_AUSENTE = "Este tópico editorial ainda não foi registrado."

CONFLITO_PERSISTENCIA = (
    "A base foi atualizada por outra sessão desde que esta página foi carregada. "
    "Recarregue a aplicação para receber a versão mais recente antes de salvar novamente."
)
REPOSITORIO_OCUPADO = (
    "Outra gravação da base está em andamento. Aguarde a conclusão e tente novamente."
)

AVISO_PERSISTENCIA = (
    "O JSON é a fonte canônica temporária. Em execução local, o cadastro é escrito no arquivo. "
    "No Streamlit Community Cloud, alterações feitas pela interface podem ser perdidas em reinícios "
    "ou novos deploys; para permanência, versione o JSON atualizado no GitHub."
)
SUCESSO_CADASTRO = (
    "{nome} foi incluído no JSON desta execução. Confirme e versione a alteração no GitHub "
    "para torná-la permanente no ambiente publicado."
)
FEEDBACK_PREPARADO = (
    "O botão apenas abre o aplicativo de e-mail do dispositivo com a mensagem preenchida. "
    "O envio só acontece após sua confirmação no cliente de e-mail."
)
FEEDBACK_MENSAGEM_OBRIGATORIA = "Descreva a sugestão antes de preparar o e-mail."


def resumo_convocacao(total_titulares: int, total_reservas: int) -> str:
    """Retorna um resumo textual das vagas ocupadas e restantes."""
    titulares = max(0, min(int(total_titulares), LIMITE_TITULARES))
    reservas = max(0, min(int(total_reservas), LIMITE_RESERVAS))
    faltam_titulares = LIMITE_TITULARES - titulares
    vagas_reservas = LIMITE_RESERVAS - reservas

    if faltam_titulares:
        situacao = f"Faltam {faltam_titulares} titular(es) para completar o time."
    else:
        situacao = "Time titular completo."

    return (
        f"Titulares: {titulares}/{LIMITE_TITULARES} · "
        f"Reservas: {reservas}/{LIMITE_RESERVAS} · "
        f"{situacao} Banco disponível: {vagas_reservas} vaga(s)."
    )


def convocacao_completa(total_titulares: int) -> bool:
    return int(total_titulares) >= LIMITE_TITULARES
