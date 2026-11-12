"""
dados.py
========
Módulo de ENTRADA E SAÍDA DE DADOS do projeto.

Papel deste módulo no projeto
-----------------------------
Este módulo NÃO faz cálculos físicos e NÃO desenha gráficos. Ele apenas:
    - pergunta valores ao usuário (entrada);
    - mostra parâmetros, tabelas e resultados no terminal (saída);
    - grava as tabelas em arquivos CSV (exportação);
    - cria as pastas de resultados.

Como os dados chegam aqui
-------------------------
main.py recebe os resultados de calculos.py e os repassa para as funções
deste módulo. Os resultados chegam em dois formatos:
    - um dicionário  (ex.: resultado de calcular_balanco_energetico);
    - uma lista de dicionários (ex.: resultado de executar_varredura),
      em que cada dicionário é UMA LINHA da tabela.

Como uma tabela é descrita
--------------------------
Cada tabela é definida por uma lista de COLUNAS no formato:
    (chave, rótulo, casas_decimais)
    - chave: nome da chave no dicionário de resultado (ex.: "distancia_total");
    - rótulo: texto do cabeçalho, com unidade (ex.: "dtotal (m)");
    - casas_decimais: quantas casas exibir/gravar ("e" = notação científica).
A mesma definição de colunas é usada para a tela e para o CSV, garantindo
que os dois mostrem exatamente as mesmas informações.
"""

import csv
from pathlib import Path

# -----------------------------------------------------------------------------
# Configuração de formato numérico
# -----------------------------------------------------------------------------
# Separadores no padrão brasileiro: o Excel/LibreOffice em português abre o
# CSV diretamente em colunas quando o separador de campos é ';' e a vírgula é
# o separador decimal.
SEPARADOR_CSV = ";"
SEPARADOR_DECIMAL = ","

# -----------------------------------------------------------------------------
# Definições das colunas de cada tabela: (chave, rótulo com unidade, casas)
# -----------------------------------------------------------------------------
COLUNAS_PARADA = [   # Experimentos A, B e C (saída de calcular_parada)
    ("massa", "m (kg)", 1),
    ("velocidade", "v0 (m/s)", 2),
    ("tempo_resposta", "tr (s)", 2),
    ("forca_frenagem", "Fb (N)", 1),
    ("distancia_reacao", "dr (m)", 3),
    ("distancia_frenagem", "db (m)", 3),
    ("distancia_total", "dtotal (m)", 3),
    ("tempo_total", "t parada (s)", 3),
]

COLUNAS_CONVERGENCIA = [   # Experimento D - comparação de dt
    ("passo_tempo", "dt (s)", 3),
    ("numero_passos", "Passos", 0),
    ("distancia_total_numerica", "dtotal num. (m)", 5),
    ("distancia_total_analitica", "dtotal anal. (m)", 5),
    ("erro_absoluto_distancia", "Erro abs. (m)", 5),
    ("erro_relativo_distancia", "Erro rel. (%)", 4),
    ("tempo_parada_numerico", "t num. (s)", 4),
    ("tempo_parada_analitico", "t anal. (s)", 4),
    ("erro_absoluto_tempo", "Erro t (s)", 4),
]

COLUNAS_TRAJETORIA = [   # Experimento D - registro passo a passo da simulação
    ("tempo", "t (s)", 4),
    ("posicao", "x (m)", 6),
    ("velocidade", "v (m/s)", 6),
    ("aceleracao", "a (m/s²)", 4),
]

COLUNAS_DESAFIO = [   # Desafio de engenharia (saída de calcular_desafio)
    ("massa", "m (kg)", 1),
    ("velocidade_maxima", "v_max (m/s)", 4),
    ("velocidade_recomendada", "v_rec (m/s)", 4),
    ("distancia_total_vmax", "dtotal(v_max) (m)", 4),
    ("distancia_total_vrec", "dtotal(v_rec) (m)", 4),
    ("residuo_equacao", "Resíduo (m)", "e"),
]

# Linhas do balanço energético: (chave, descrição, unidade, casas decimais)
LINHAS_BALANCO = [
    ("aceleracao_frenagem", "Aceleração de frenagem a = -Fb/m", "m/s²", 4),
    ("tempo_frenagem", "Tempo de frenagem tb = -v0/a", "s", 4),
    ("distancia_frenagem_dinamica", "db pelo método da dinâmica", "m", 6),
    ("distancia_frenagem_energia", "db pelo teorema trabalho-energia", "m", 6),
    ("diferenca_distancia_frenagem", "Diferença db(dinâmica) - db(energia)", "m", "e"),
    ("energia_cinetica_inicial", "Energia cinética inicial Ki", "J", 4),
    ("energia_cinetica_final", "Energia cinética final Kf", "J", 4),
    ("variacao_energia_cinetica", "Variação ΔK = Kf - Ki", "J", 4),
    ("trabalho_reacao", "Trabalho na etapa de resposta", "J", 4),
    ("trabalho_frenagem", "Trabalho da frenagem Wb = -Fb·db", "J", 4),
    ("diferenca_trabalho_energia", "Diferença Wb - ΔK", "J", "e"),
]

# Rótulos dos parâmetros de entrada: chave -> (descrição, unidade)
ROTULOS_PARAMETROS = {
    "massa_robo": ("Massa do robô vazio", "kg"),
    "massa_carga": ("Massa da carga", "kg"),
    "massa": ("Massa total", "kg"),
    "velocidade": ("Velocidade inicial", "m/s"),
    "distancia_obstaculo": ("Distância até o obstáculo", "m"),
    "tempo_resposta": ("Tempo de resposta", "s"),
    "forca_frenagem": ("Força de frenagem", "N"),
    "gravidade": ("Gravidade", "m/s²"),
    "forca_peso": ("Força peso (m·g)", "N"),
}

# Parâmetros que o usuário pode alterar (a massa total e o peso NÃO estão
# aqui porque são calculados em calculos.montar_parametros).
PARAMETROS_EDITAVEIS = ["massa_robo", "massa_carga", "velocidade", "tempo_resposta",
                        "forca_frenagem", "distancia_obstaculo", "gravidade"]


# =============================================================================
# FORMATAÇÃO
# =============================================================================

def formatar_numero(valor, casas=3):
    """
    Converte um número em texto com 'casas' casas decimais e vírgula decimal.

    Casos especiais:
            - casas == "e": notação científica (ex.: 1,23e-15). Usada nas colunas
          de diferença/resíduo, para que diferenças de arredondamento muito
          pequenas não apareçam simplesmente como "0,000".
        - textos são devolvidos sem alteração; booleanos viram "Sim"/"Não".

    Retorna: str.
    """
    if isinstance(valor, bool):
        return "Sim" if valor else "Não"
    if not isinstance(valor, (int, float)):
        return str(valor)
    if casas == "e":
        texto = f"{valor:.2e}"
    else:
        texto = f"{valor:.{casas}f}"
    return texto.replace(".", SEPARADOR_DECIMAL)


def imprimir_cabecalho(titulo, simbolo="="):
    """Imprime um título entre duas linhas, para separar as seções na tela."""
    linha = simbolo * max(70, len(titulo) + 4)
    print(f"\n{linha}\n  {titulo}\n{linha}")


# =============================================================================
# SAÍDA NO TERMINAL
# =============================================================================

def exibir_parametros(parametros, titulo="PARÂMETROS UTILIZADOS"):
    """
    Mostra os parâmetros-base em formato de lista "descrição: valor unidade".

    Parâmetros: parametros = dict produzido por calculos.montar_parametros().
    Não retorna nada.
    """
    imprimir_cabecalho(titulo)
    for chave, (descricao, unidade) in ROTULOS_PARAMETROS.items():
        if chave in parametros:
            print(f"  {descricao:<30} {formatar_numero(parametros[chave], 2):>10} {unidade}")


def exibir_tabela(registros, colunas, titulo=None):
    """
    Exibe uma lista de dicionários como tabela alinhada no terminal.

    Processamento:
        1. converte cada valor em texto com formatar_numero();
        2. calcula a largura de cada coluna (maior texto entre cabeçalho e valores);
        3. imprime cabeçalho, linha separadora e linhas de dados.

    Parâmetros
    ----------
    registros : lista de dict   (cada dict = uma linha)
    colunas : lista de (chave, rótulo, casas)
    titulo : str opcional
    """
    if titulo:
        imprimir_cabecalho(titulo, "-")

    cabecalhos = [rotulo for _, rotulo, _ in colunas]
    linhas = [[formatar_numero(reg[chave], casas) for chave, _, casas in colunas]
              for reg in registros]

    larguras = [max(len(cabecalhos[i]), *(len(l[i]) for l in linhas)) if linhas
                else len(cabecalhos[i]) for i in range(len(colunas))]

    print("  " + " | ".join(c.rjust(w) for c, w in zip(cabecalhos, larguras)))
    print("  " + "-+-".join("-" * w for w in larguras))
    for linha in linhas:
        print("  " + " | ".join(v.rjust(w) for v, w in zip(linha, larguras)))


def exibir_balanco_energetico(balanco):
    """
    Exibe o resultado de calculos.calcular_balanco_energetico() como uma
    tabela de três colunas: grandeza | valor | unidade.
    """
    imprimir_cabecalho("Balanço energético e comparação dinâmica x trabalho-energia", "-")
    for chave, descricao, unidade, casas in LINHAS_BALANCO:
        print(f"  {descricao:<42} {formatar_numero(balanco[chave], casas):>14} {unidade}")


def exibir_resultado_parada(resultado, distancia_obstaculo, sem_colisao):
    """
    Mostra o resultado analítico do cenário-base (parâmetros do enunciado).

    Parâmetros
    ----------
    resultado : dict de calculos.calcular_parada()
    distancia_obstaculo : float [m]
    sem_colisao : bool vindo de calculos.verificar_colisao()
    """
    imprimir_cabecalho("CENÁRIO-BASE - CÁLCULO ANALÍTICO DA PARADA", "-")
    itens = [
        ("Distância de reação (dr)", resultado["distancia_reacao"], "m"),
        ("Distância de frenagem (db)", resultado["distancia_frenagem"], "m"),
        ("Distância total de parada (dtotal)", resultado["distancia_total"], "m"),
        ("Tempo total até parar", resultado["tempo_total"], "s"),
        ("Distância até o obstáculo", distancia_obstaculo, "m"),
    ]
    for descricao, valor, unidade in itens:
        print(f"  {descricao:<38} {formatar_numero(valor, 4):>10} {unidade}")
    print(f"  {'Condição dtotal <= dobstáculo atendida?':<38} "
          f"{formatar_numero(sem_colisao):>10}")


def exibir_desafio(resultado):
    """
    Mostra o resultado do desafio de engenharia para o cenário-base.

    Parâmetros: resultado = dict de calculos.calcular_desafio().
    """
    imprimir_cabecalho("DESAFIO DE ENGENHARIA - VELOCIDADE MÁXIMA SEGURA", "-")
    print("  Equação resolvida: dobst = v·tr + (m·v²)/(2·Fb)  (raiz positiva)")
    itens = [
        ("Massa total", resultado["massa"], "kg", 2),
        ("Tempo de resposta", resultado["tempo_resposta"], "s", 2),
        ("Força de frenagem", resultado["forca_frenagem"], "N", 2),
        ("Distância até o obstáculo", resultado["distancia_obstaculo"], "m", 2),
        ("Velocidade máxima segura (v_max)", resultado["velocidade_maxima"], "m/s", 4),
        ("Conferência: dtotal(v_max)", resultado["distancia_total_vmax"], "m", 4),
        ("Resíduo da equação dtotal - dobst", resultado["residuo_equacao"], "m", "e"),
        ("Fator de segurança aplicado", resultado["fator_seguranca"], "", 2),
        ("Velocidade recomendada (v_rec)", resultado["velocidade_recomendada"], "m/s", 4),
        ("dtotal com v_rec", resultado["distancia_total_vrec"], "m", 4),
        ("Distância restante até o obstáculo", resultado["folga_distancia_vrec"], "m", 4),
    ]
    for descricao, valor, unidade, casas in itens:
        print(f"  {descricao:<38} {formatar_numero(valor, casas):>12} {unidade}")


def informar_arquivo_salvo(caminho):
    """Avisa no terminal que um arquivo foi gravado (mostra o caminho relativo)."""
    try:
        caminho_exibido = Path(caminho).resolve().relative_to(Path.cwd())
    except ValueError:
        caminho_exibido = caminho
    print(f"  [arquivo salvo] {caminho_exibido}")


# =============================================================================
# ENTRADA DE DADOS
# =============================================================================

def perguntar_sim_nao(pergunta, padrao=True):
    """
    Faz uma pergunta de sim/não no terminal.

    - Enter vazio devolve o valor 'padrao'.
    - Se não houver terminal interativo (EOFError, ex.: execução automática),
      também devolve 'padrao', para o programa não travar.

    Retorna: bool.
    """
    sufixo = "[S/n]" if padrao else "[s/N]"
    try:
        resposta = input(f"{pergunta} {sufixo}: ").strip().lower()
    except EOFError:
        print()
        return padrao
    if resposta == "":
        return padrao
    return resposta in ("s", "sim", "y", "yes")


def ler_numero(mensagem, valor_padrao):
    """
    Lê um número digitado pelo usuário. Aceita vírgula ou ponto decimal.

    - Enter vazio (ou ausência de terminal) mantém 'valor_padrao'.
    - Texto inválido gera nova pergunta.

    Retorna: float.
    """
    while True:
        try:
            texto = input(f"  {mensagem} [{formatar_numero(valor_padrao, 2)}]: ").strip()
        except EOFError:
            print()
            return valor_padrao
        if texto == "":
            return valor_padrao
        try:
            return float(texto.replace(",", "."))
        except ValueError:
            print("    Valor inválido. Digite um número (ex.: 3,5).")


def solicitar_parametros(parametros_padrao):
    """
    Pergunta ao usuário se deseja manter os parâmetros do enunciado ou
    digitar outros valores.

    Retorna: dict apenas com os parâmetros EDITÁVEIS (valores brutos).
    main.py repassa esse dict para calculos.montar_parametros(), que recalcula
    a massa total e o peso. Assim nenhum cálculo é feito neste módulo.
    """
    imprimir_cabecalho("ENTRADA DE PARÂMETROS")
    valores = {chave: parametros_padrao[chave] for chave in PARAMETROS_EDITAVEIS}

    if perguntar_sim_nao("Usar os parâmetros do enunciado?", padrao=True):
        return valores

    print("  Digite os novos valores (Enter mantém o valor entre colchetes):")
    for chave in PARAMETROS_EDITAVEIS:
        descricao, unidade = ROTULOS_PARAMETROS[chave]
        valores[chave] = ler_numero(f"{descricao} ({unidade})", valores[chave])
    return valores


# =============================================================================
# EXPORTAÇÃO (CSV) E PASTAS
# =============================================================================

def preparar_pastas(pasta_base):
    """
    Cria (se ainda não existirem) as pastas resultados/tabelas e
    resultados/graficos.

    Retorna: dict {"tabelas": Path, "graficos": Path}.
    """
    pastas = {"tabelas": Path(pasta_base) / "tabelas",
              "graficos": Path(pasta_base) / "graficos"}
    for pasta in pastas.values():
        pasta.mkdir(parents=True, exist_ok=True)
    return pastas


def exportar_csv(registros, colunas, caminho):
    """
    Grava uma lista de dicionários em um arquivo CSV.

    A 1ª linha recebe os rótulos das colunas; as demais, os valores formatados
    com formatar_numero() (mesmo formato exibido no terminal).
    A codificação 'utf-8-sig' faz o Excel reconhecer acentos e símbolos (², ·).

    Parâmetros: registros (lista de dict), colunas (lista de tuplas),
    caminho (str ou Path do arquivo de saída).
    """
    with open(caminho, "w", newline="", encoding="utf-8-sig") as arquivo:
        escritor = csv.writer(arquivo, delimiter=SEPARADOR_CSV)
        escritor.writerow([rotulo for _, rotulo, _ in colunas])
        for reg in registros:
            escritor.writerow([formatar_numero(reg[chave], casas) for chave, _, casas in colunas])
    informar_arquivo_salvo(caminho)


def exportar_balanco_energetico(balanco, caminho):
    """
    Grava o balanço energético em CSV com as colunas Grandeza; Valor; Unidade.
    Reaproveita exportar_csv() convertendo cada linha de LINHAS_BALANCO em um
    pequeno dicionário.
    """
    registros = [{"grandeza": descricao, "valor": formatar_numero(balanco[chave], casas),
                  "unidade": unidade}
                 for chave, descricao, unidade, casas in LINHAS_BALANCO]
    colunas = [("grandeza", "Grandeza", 0), ("valor", "Valor", 0), ("unidade", "Unidade", 0)]
    exportar_csv(registros, colunas, caminho)


def converter_simulacao_em_registros(simulacao):
    """
    Converte o resultado de calculos.simular_euler_cromer() (um dict de LISTAS)
    em uma lista de dicionários (uma linha por passo de tempo), que é o
    formato aceito por exportar_csv().

    Operação apenas de reorganização: tempo[i], posicao[i], velocidade[i] e
    aceleracao[i] passam a formar a linha i.
    """
    return [{"tempo": t, "posicao": x, "velocidade": v, "aceleracao": a}
            for t, x, v, a in zip(simulacao["tempo"], simulacao["posicao"],
                                  simulacao["velocidade"], simulacao["aceleracao"])]
