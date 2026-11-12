"""
graficos.py
===========
Módulo de GERAÇÃO DE GRÁFICOS do projeto (biblioteca Matplotlib).

Papel deste módulo no projeto
-----------------------------
Este módulo NÃO faz cálculos físicos. Ele recebe, via main.py, os resultados
já calculados por calculos.py e apenas:
    - separa os valores em listas para os eixos x e y;
    - desenha as curvas, com título, eixos, unidades, legenda e grade;
    - salva cada figura como PNG em resultados/graficos;
    - exibe as figuras na tela, se o usuário pedir.

Como os gráficos recebem os resultados
--------------------------------------
Os resultados chegam em dois formatos (os mesmos usados em dados.py):
    1. Lista de dicionários (Experimentos A, B, C, convergência e desafio):
       cada dicionário é um ponto do gráfico. A função extrair_coluna()
       percorre a lista e monta uma lista só com os valores de uma chave.
           [{"velocidade": 1, "distancia_total": 0.9}, ...]
           -> extrair_coluna(registros, "velocidade") -> [1, 2, 3, ...]
    2. Dicionário de listas (simulação de Euler-Cromer e trajetória analítica):
       as listas já estão prontas: simulacao["tempo"], simulacao["posicao"] ...

Estrutura do módulo
-------------------
Há UMA função genérica de desenho, gerar_grafico(), que recebe uma lista de
"séries" e desenha todas na mesma figura. As demais funções apenas montam
essas séries (escolhem chaves, rótulos e títulos) e chamam gerar_grafico().
É a mesma ideia de reutilização aplicada em calculos.py.

Formato de uma série (dicionário):
    {"x": [...], "y": [...], "rotulo": "texto da legenda",
     "estilo": "-" (opcional), "marcador": "o" (opcional)}
"""

from pathlib import Path

import matplotlib.pyplot as plt

# Cores fixas para que o mesmo tipo de curva tenha sempre a mesma cor em
# todas as figuras (ex.: dtotal sempre azul, analítico sempre cinza escuro).
CORES = {
    "total": "#1f5fa8",
    "reacao": "#e08a1e",
    "frenagem": "#2a9d5c",
    "analitico": "#333333",
    "numerico": "#c4372f",
    "referencia": "#7a7a7a",
    "series": ["#1f5fa8", "#e08a1e", "#2a9d5c", "#8e44ad"],
}


def configurar_estilo():
    """
    Ajusta o estilo padrão do Matplotlib (fonte, tamanho, grade) para todas as
    figuras. É chamada uma vez por main.py antes de gerar os gráficos.
    """
    plt.rcParams.update({
        "figure.figsize": (8, 5),
        "figure.dpi": 100,
        "font.size": 11,
        "axes.titlesize": 13,
        "axes.titleweight": "bold",
        "axes.labelsize": 11,
        "legend.fontsize": 10,
        "axes.grid": True,
        "grid.alpha": 0.35,
        "grid.linestyle": "--",
        "savefig.dpi": 150,
    })


def extrair_coluna(registros, chave):
    """
    Converte uma lista de dicionários em uma lista simples de valores.

    Exemplo: extrair_coluna([{"m": 20}, {"m": 30}], "m") -> [20, 30]

    Não há cálculo aqui: é só uma seleção dos valores para o eixo do gráfico.
    """
    return [registro[chave] for registro in registros]


def gerar_grafico(series, titulo, rotulo_x, rotulo_y, caminho,
                  linhas_verticais=None, linhas_horizontais=None,
                  escala_log=False):
    """
    Função GENÉRICA de desenho: cria uma figura, desenha todas as séries,
    identifica a figura e a salva em arquivo.

    Parâmetros
    ----------
    series : lista de dict
        Curvas a desenhar (formato descrito no topo do módulo).
    titulo, rotulo_x, rotulo_y : str
        Título da figura e nomes dos eixos (com unidades).
    caminho : str ou Path
        Arquivo PNG de saída.
    linhas_verticais / linhas_horizontais : lista de (valor, rótulo) ou None
        Linhas de referência tracejadas (ex.: instante tr, posição do obstáculo).
        Elas apenas marcam valores de entrada no gráfico.
    escala_log : bool
        Se True, usa escala logarítmica nos dois eixos (gráfico de convergência).

    Retorna
    -------
    A figura do Matplotlib (fica aberta para poder ser exibida depois por
    exibir_graficos(), ou fechada por fechar_graficos()).
    """
    fig, ax = plt.subplots()

    for i, serie in enumerate(series):
        ax.plot(serie["x"], serie["y"],
                linestyle=serie.get("estilo", "-"),
                marker=serie.get("marcador", None),
                color=serie.get("cor", CORES["series"][i % len(CORES["series"])]),
                linewidth=serie.get("espessura", 2),
                markersize=6,
                label=serie.get("rotulo"))

    for valor, rotulo in (linhas_verticais or []):
        ax.axvline(valor, color=CORES["referencia"], linestyle=":", linewidth=1.5, label=rotulo)
    for valor, rotulo in (linhas_horizontais or []):
        ax.axhline(valor, color=CORES["referencia"], linestyle="-.", linewidth=1.5, label=rotulo)

    if escala_log:
        ax.set_xscale("log")
        ax.set_yscale("log")

    ax.set_title(titulo)
    ax.set_xlabel(rotulo_x)
    ax.set_ylabel(rotulo_y)
    # A legenda só é desenhada se houver pelo menos um rótulo.
    if any(s.get("rotulo") for s in series) or linhas_verticais or linhas_horizontais:
        ax.legend(loc="best")

    fig.tight_layout()
    fig.savefig(caminho, bbox_inches="tight")
    # Mostra o caminho relativo à pasta atual (mais curto), quando possível.
    try:
        caminho_exibido = Path(caminho).resolve().relative_to(Path.cwd())
    except ValueError:
        caminho_exibido = caminho
    print(f"  [gráfico salvo] {caminho_exibido}")
    return fig


# =============================================================================
# FUNÇÕES ESPECÍFICAS (apenas montam as séries e chamam gerar_grafico)
# =============================================================================

def grafico_distancia_vs_parametro(registros, chave_x, rotulo_x, titulo, caminho):
    """
    Gráfico usado pelos Experimentos A, B e C: distância de parada em função
    do parâmetro variado.

    Parâmetros
    ----------
    registros : lista de dict produzida por calculos.executar_varredura(calcular_parada, ...)
    chave_x : str  -> chave do parâmetro variado ("velocidade", "massa" ou "tempo_resposta")
    rotulo_x : str -> nome do eixo x com unidade
    titulo, caminho : título e arquivo de saída

    Séries desenhadas: dtotal (linha cheia) e, para identificar as duas
    etapas do modelo, dr e db (linhas tracejadas).
    """
    x = extrair_coluna(registros, chave_x)
    series = [
        {"x": x, "y": extrair_coluna(registros, "distancia_total"),
         "rotulo": "Distância total (dtotal)", "marcador": "o", "cor": CORES["total"],
         "espessura": 2.5},
        {"x": x, "y": extrair_coluna(registros, "distancia_reacao"),
         "rotulo": "Distância de reação (dr)", "marcador": "s", "estilo": "--",
         "cor": CORES["reacao"], "espessura": 1.5},
        {"x": x, "y": extrair_coluna(registros, "distancia_frenagem"),
         "rotulo": "Distância de frenagem (db)", "marcador": "^", "estilo": "--",
         "cor": CORES["frenagem"], "espessura": 1.5},
    ]
    return gerar_grafico(series, titulo, rotulo_x, "Distância (m)", caminho)


def grafico_trajetoria(simulacao, analitico, chave_y, rotulo_y, titulo, caminho,
                       tempo_resposta, linha_horizontal=None):
    """
    Gráfico de uma grandeza em função do tempo (Experimento D): compara a
    simulação de Euler-Cromer com a solução analítica.

    Parâmetros
    ----------
    simulacao : dict de calculos.simular_euler_cromer() (listas "tempo", "posicao", ...)
    analitico : dict de calculos.calcular_trajetoria_analitica() (mesmo formato)
    chave_y : "posicao" ou "velocidade"
    rotulo_y, titulo, caminho : textos e arquivo de saída
    tempo_resposta : float [s] -> marcado como linha vertical (fim da Etapa 1)
    linha_horizontal : (valor, rótulo) opcional (ex.: posição do obstáculo)
    """
    dt = simulacao["passo_tempo"]
    series = [
        {"x": analitico["tempo"], "y": analitico[chave_y],
         "rotulo": "Solução analítica", "cor": CORES["analitico"], "espessura": 3},
        {"x": simulacao["tempo"], "y": simulacao[chave_y],
         "rotulo": f"Euler-Cromer (dt = {dt:g} s)", "estilo": "--",
         "cor": CORES["numerico"], "espessura": 1.8},
    ]
    verticais = [(tempo_resposta, f"Início da frenagem (t = tr = {tempo_resposta:g} s)")]
    horizontais = [linha_horizontal] if linha_horizontal else None
    return gerar_grafico(series, titulo, "Tempo (s)", rotulo_y, caminho,
                         linhas_verticais=verticais, linhas_horizontais=horizontais)


def grafico_comparacao_passos(simulacoes, analitico, caminho):
    """
    Sobrepõe as curvas x(t) obtidas com diferentes dt e a curva analítica.

    Parâmetros
    ----------
    simulacoes : lista de dicts de simular_euler_cromer (um por dt)
    analitico : dict de calcular_trajetoria_analitica
    """
    series = [{"x": analitico["tempo"], "y": analitico["posicao"],
               "rotulo": "Solução analítica", "cor": CORES["analitico"], "espessura": 3.5}]
    estilos = ["--", "-.", ":"]
    for i, sim in enumerate(simulacoes):
        series.append({"x": sim["tempo"], "y": sim["posicao"],
                       "rotulo": f"Euler-Cromer, dt = {sim['passo_tempo']:g} s",
                       "estilo": estilos[i % len(estilos)],
                       "cor": CORES["series"][i % len(CORES["series"])], "espessura": 1.8})
    return gerar_grafico(series, "Experimento D - Posição x(t) para diferentes passos de tempo",
                         "Tempo (s)", "Posição (m)", caminho)


def grafico_convergencia(registros, caminho):
    """
    Gráfico log-log do erro absoluto (|numérico - analítico|) da distância
    total em função do passo de tempo dt.

    Parâmetros: registros = lista de dict de calculos.comparar_simulacao_analitica().
    """
    series = [{"x": extrair_coluna(registros, "passo_tempo"),
               "y": extrair_coluna(registros, "erro_absoluto_distancia"),
               "rotulo": "Erro absoluto em dtotal", "marcador": "o",
               "cor": CORES["numerico"]}]
    return gerar_grafico(series, "Experimento D - Erro da simulação em função de dt",
                         "Passo de tempo dt (s)", "|dtotal numérico - dtotal analítico| (m)",
                         caminho, escala_log=True)


def grafico_velocidade_maxima_vs_massa(registros, caminho):
    """
    Desafio de engenharia: v_max e v_recomendada em função da massa total.

    Parâmetros: registros = lista de dict de
    calculos.executar_varredura(calcular_desafio, "massa", ...).
    """
    x = extrair_coluna(registros, "massa")
    fator = registros[0]["fator_seguranca"]
    series = [
        {"x": x, "y": extrair_coluna(registros, "velocidade_maxima"),
         "rotulo": "Velocidade máxima segura (v_max)", "marcador": "o", "cor": CORES["total"]},
        {"x": x, "y": extrair_coluna(registros, "velocidade_recomendada"),
         "rotulo": f"Velocidade recomendada ({fator:g} × v_max)", "marcador": "s",
         "estilo": "--", "cor": CORES["frenagem"]},
    ]
    return gerar_grafico(series, "Desafio - Velocidade máxima segura em função da massa",
                         "Massa total (kg)", "Velocidade (m/s)", caminho)


# =============================================================================
# EXIBIÇÃO
# =============================================================================

def exibir_graficos():
    """Abre na tela todas as figuras geradas (bloqueia até as janelas serem fechadas)."""
    plt.show()


def fechar_graficos():
    """Fecha todas as figuras abertas, liberando memória (os PNGs já estão salvos)."""
    plt.close("all")
