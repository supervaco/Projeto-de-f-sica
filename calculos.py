"""
calculos.py
===========
Módulo de MODELAGEM COMPUTACIONAL E CÁLCULOS do projeto
"Sistema Autônomo de Frenagem e Prevenção de Colisões".

Papel deste módulo no projeto
-----------------------------
Este é o ÚNICO módulo que contém fórmulas físicas. Os demais módulos apenas:
    - dados.py    -> exibem, leem e exportam valores (entrada/saída);
    - graficos.py -> desenham valores que já foram calculados aqui;
    - main.py     -> coordenam a ordem de execução e repassam os resultados.

Organização interna (de baixo para cima)
----------------------------------------
    1. Parâmetros padrão do enunciado (constantes no topo do arquivo).
    2. Funções ELEMENTARES: cada uma implementa uma única fórmula.
    3. Função GENÉRICA calcular_parada(...): combina as funções elementares
       para obter dr, db e dtotal de QUALQUER conjunto de parâmetros.
    4. Função GENÉRICA executar_varredura(...): repete uma função de cálculo
       trocando apenas um parâmetro. Os Experimentos A, B e C e o estudo de
       v_max por massa são feitos por ela.
    5. Balanço energético (Experimento D).
    6. Solução analítica ponto a ponto e simulação numérica por Euler-Cromer
       (Experimento D).
    7. Velocidade máxima segura (Desafio de engenharia).

Unidades (Sistema Internacional) usadas em TODO o módulo
--------------------------------------------------------
    massa [kg] | velocidade [m/s] | tempo [s] | força [N] | distância [m]
    aceleração [m/s²] | energia e trabalho [J]

Convenção de sinais
-------------------
O eixo x aponta no sentido do movimento do robô e a origem (x = 0) é a
posição do robô no instante em que o obstáculo é identificado (t = 0).
Assim, a velocidade inicial é positiva e a força de frenagem entra nas
equações com sinal negativo (-Fb), pois o enunciado define que ela atua no
sentido contrário ao movimento.

Formato dos resultados
----------------------
As funções que produzem vários valores devolvem DICIONÁRIOS (chave -> valor).
Esse formato foi escolhido porque dados.py e graficos.py conseguem localizar
cada grandeza pelo nome da chave (ex.: registro["distancia_total"]), sem
depender da ordem dos valores.
"""

import inspect
import math

# =============================================================================
# 1. PARÂMETROS PADRÃO DO ENUNCIADO
# =============================================================================
# Valores da tabela "Parâmetros do problema". Ficam aqui, em um único lugar,
# para que nenhuma função precise ter números "fixos" escritos dentro dela.

MASSA_ROBO_VAZIO = 25.0      # kg   - massa do robô sem carga
MASSA_CARGA = 15.0           # kg   - massa da carga transportada
VELOCIDADE_INICIAL = 3.5     # m/s  - velocidade no instante da detecção
DISTANCIA_OBSTACULO = 5.0    # m    - distância entre robô e obstáculo em t = 0
TEMPO_RESPOSTA = 0.40        # s    - intervalo até o início da frenagem
FORCA_FRENAGEM = 100.0       # N    - módulo da força de frenagem (constante)
GRAVIDADE = 9.8              # m/s² - aceleração da gravidade

# Conjuntos de valores investigados em cada experimento (definidos no enunciado).
VELOCIDADES_EXPERIMENTO_A = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0]    # m/s
MASSAS_EXPERIMENTO_B = [20.0, 30.0, 40.0, 50.0, 60.0]         # kg
TEMPOS_EXPERIMENTO_C = [0.1, 0.2, 0.4, 0.6, 0.8]              # s

# Passos de tempo da simulação numérica (Experimento D).
PASSO_TEMPO_PADRAO = 0.01                                     # s
PASSOS_TEMPO_CONVERGENCIA = [0.01, 0.005, 0.001]              # s

# Desafio de engenharia: massas para o estudo de v_max e fator de segurança.
MASSAS_DESAFIO = MASSAS_EXPERIMENTO_B                         # kg
FATOR_SEGURANCA = 0.8        # v_recomendada = 0,8 × v_max (margem de 20 %)


# =============================================================================
# FUNÇÕES AUXILIARES DE VALIDAÇÃO
# =============================================================================

def _validar(nome, valor, permite_zero=False):
    """
    Verifica se um parâmetro numérico é aceitável antes de usá-lo em uma fórmula.

    Parâmetros
    ----------
    nome : str
        Nome do parâmetro (usado apenas na mensagem de erro).
    valor : float
        Valor a ser verificado.
    permite_zero : bool
        Se True, aceita valor == 0 (ex.: tempo de resposta nulo).
        Se False, exige valor > 0 (ex.: massa e força, que aparecem em divisões).

    Lança ValueError se o valor for inválido. Não retorna nada.
    """
    if permite_zero and valor < 0:
        raise ValueError(f"'{nome}' não pode ser negativo (recebido: {valor}).")
    if not permite_zero and valor <= 0:
        raise ValueError(f"'{nome}' deve ser maior que zero (recebido: {valor}).")


# =============================================================================
# 2. FUNÇÕES ELEMENTARES (uma fórmula por função)
# =============================================================================

def calcular_massa_total(massa_robo=MASSA_ROBO_VAZIO, massa_carga=MASSA_CARGA):
    """
    Calcula a massa total do conjunto robô + carga.

    Fórmula: m = m_robô + m_carga

    Parâmetros: massa_robo [kg], massa_carga [kg].
    Retorna: massa total [kg] (float).
    """
    _validar("massa_robo", massa_robo)
    _validar("massa_carga", massa_carga, permite_zero=True)
    return massa_robo + massa_carga


def calcular_forca_peso(massa, gravidade=GRAVIDADE):
    """
    Calcula o módulo da força peso.

    Fórmula: P = m × g

    Parâmetros: massa [kg], gravidade [m/s²].
    Retorna: peso [N] (float).

    Observação computacional: no modelo horizontal do enunciado, este valor é
    apenas informativo (aparece na tela de parâmetros); ele não entra no
    cálculo das distâncias.
    """
    _validar("massa", massa)
    return massa * gravidade


def calcular_distancia_reacao(velocidade, tempo_resposta):
    """
    Etapa 1 - distância percorrida durante o tempo de resposta.

    Nesta etapa o modelo usa a = 0 (velocidade constante), portanto:
        dr = v0 × tr

    Parâmetros: velocidade = v0 [m/s], tempo_resposta = tr [s].
    Retorna: dr [m] (float).
    """
    _validar("velocidade", velocidade, permite_zero=True)
    _validar("tempo_resposta", tempo_resposta, permite_zero=True)
    return velocidade * tempo_resposta


def calcular_aceleracao_frenagem(massa, forca_frenagem):
    """
    Etapa 2 - aceleração durante a frenagem, pela segunda lei de Newton.

        m × a = -Fb   =>   a = -Fb / m

    O sinal negativo vem da convenção de sinais (força contrária ao movimento).

    Parâmetros: massa [kg], forca_frenagem = Fb [N] (módulo, positivo).
    Retorna: a [m/s²] (float, negativo).
    """
    _validar("massa", massa)
    _validar("forca_frenagem", forca_frenagem)
    return -forca_frenagem / massa


def calcular_tempo_frenagem(velocidade, aceleracao):
    """
    Duração da etapa de frenagem (de v0 até v = 0) com aceleração constante.

    Da equação horária da velocidade: 0 = v0 + a × tb   =>   tb = -v0 / a

    Parâmetros: velocidade = v0 [m/s], aceleracao = a [m/s²] (negativa).
    Retorna: tb [s] (float).
    """
    return -velocidade / aceleracao


def calcular_distancia_frenagem(massa, velocidade, forca_frenagem):
    """
    Etapa 2 - distância de frenagem pelo TEOREMA TRABALHO-ENERGIA CINÉTICA.

        Wb = ΔK  =>  -Fb × db = 0 - ½ m v0²  =>  db = (m × v0²) / (2 × Fb)

    Esta é a fórmula de referência usada por calcular_parada().

    Parâmetros: massa [kg], velocidade = v0 [m/s], forca_frenagem = Fb [N].
    Retorna: db [m] (float).
    """
    _validar("massa", massa)
    _validar("velocidade", velocidade, permite_zero=True)
    _validar("forca_frenagem", forca_frenagem)
    return (massa * velocidade ** 2) / (2.0 * forca_frenagem)


def calcular_distancia_frenagem_dinamica(massa, velocidade, forca_frenagem):
    """
    Etapa 2 - distância de frenagem pelo MÉTODO DA DINÂMICA (cinemática + Newton).

    Esta função existe porque o Experimento D pede a comparação entre os dois
    métodos; ela NÃO é usada nos experimentos A, B e C.

    Passos executados:
        1. a  = -Fb / m                      (segunda lei de Newton)
        2. tb = -v0 / a                      (instante em que v = 0)
        3. db = v0 × tb + ½ × a × tb²        (equação horária da posição)

    Parâmetros: massa [kg], velocidade = v0 [m/s], forca_frenagem = Fb [N].
    Retorna: db [m] (float).
    """
    aceleracao = calcular_aceleracao_frenagem(massa, forca_frenagem)
    tempo_frenagem = calcular_tempo_frenagem(velocidade, aceleracao)
    return velocidade * tempo_frenagem + 0.5 * aceleracao * tempo_frenagem ** 2


def calcular_energia_cinetica(massa, velocidade):
    """
    Energia cinética de translação.

        K = ½ × m × v²

    Parâmetros: massa [kg], velocidade [m/s].
    Retorna: K [J] (float).
    """
    _validar("massa", massa)
    return 0.5 * massa * velocidade ** 2


def calcular_trabalho_forca_constante(forca, deslocamento):
    """
    Trabalho de uma força constante paralela ao deslocamento (movimento 1D).

        W = F × d

    O sinal de 'forca' deve seguir a convenção de sinais do módulo:
    para a força de frenagem, passa-se -Fb.

    Parâmetros: forca [N] (com sinal), deslocamento [m].
    Retorna: W [J] (float).
    """
    return forca * deslocamento


# =============================================================================
# 3. FUNÇÃO GENÉRICA DE PARADA (núcleo reutilizado por todos os experimentos)
# =============================================================================

def calcular_parada(massa, velocidade, tempo_resposta, forca_frenagem):
    """
    Calcula, de forma analítica, todas as grandezas da parada do robô para
    UM conjunto de parâmetros. É a função reutilizada pelos Experimentos A,
    B, C e D, pelo desafio de engenharia e pela validação da simulação.

    Processamento interno:
        1. dr      <- calcular_distancia_reacao(v0, tr)          (Etapa 1)
        2. db      <- calcular_distancia_frenagem(m, v0, Fb)     (Etapa 2)
        3. dtotal  <- dr + db
        4. a, tb   <- aceleração e duração da frenagem
        5. ttotal  <- tr + tb

    Parâmetros
    ----------
    massa : float           massa total m [kg]
    velocidade : float      velocidade inicial v0 [m/s]
    tempo_resposta : float  tempo de resposta tr [s]
    forca_frenagem : float  módulo da força de frenagem Fb [N]

    Retorna
    -------
    dict com as chaves:
        "massa", "velocidade", "tempo_resposta", "forca_frenagem"  (entradas)
        "distancia_reacao"   dr [m]
        "distancia_frenagem" db [m]
        "distancia_total"    dtotal [m]
        "aceleracao_frenagem" a [m/s²]
        "tempo_frenagem"     tb [s]
        "tempo_total"        tr + tb [s]
    As entradas são copiadas para o resultado para que cada linha das
    tabelas fique completa (cada registro "sabe" de quais parâmetros veio).
    """
    distancia_reacao = calcular_distancia_reacao(velocidade, tempo_resposta)
    distancia_frenagem = calcular_distancia_frenagem(massa, velocidade, forca_frenagem)
    aceleracao = calcular_aceleracao_frenagem(massa, forca_frenagem)
    tempo_frenagem = calcular_tempo_frenagem(velocidade, aceleracao)

    return {
        "massa": massa,
        "velocidade": velocidade,
        "tempo_resposta": tempo_resposta,
        "forca_frenagem": forca_frenagem,
        "distancia_reacao": distancia_reacao,
        "distancia_frenagem": distancia_frenagem,
        "distancia_total": distancia_reacao + distancia_frenagem,
        "aceleracao_frenagem": aceleracao,
        "tempo_frenagem": tempo_frenagem,
        "tempo_total": tempo_resposta + tempo_frenagem,
    }


def montar_parametros(massa_robo=MASSA_ROBO_VAZIO, massa_carga=MASSA_CARGA,
                      velocidade=VELOCIDADE_INICIAL, tempo_resposta=TEMPO_RESPOSTA,
                      forca_frenagem=FORCA_FRENAGEM,
                      distancia_obstaculo=DISTANCIA_OBSTACULO,
                      gravidade=GRAVIDADE):
    """
    Monta o dicionário de PARÂMETROS-BASE usado por todo o programa.

    Todos os argumentos têm como padrão os valores do enunciado. Se o usuário
    digitar outros valores (via dados.solicitar_parametros), main.py chama
    esta função com eles, e a massa total é recalculada aqui, mantendo o
    cálculo dentro deste módulo.

    Retorna
    -------
    dict com: "massa_robo", "massa_carga", "massa" (total), "velocidade",
    "tempo_resposta", "forca_frenagem", "distancia_obstaculo", "gravidade",
    "forca_peso".

    Por que um dicionário? Ele funciona como um "pacote" de parâmetros que
    executar_varredura() copia e modifica (uma chave por vez).
    """
    massa_total = calcular_massa_total(massa_robo, massa_carga)
    return {
        "massa_robo": massa_robo,
        "massa_carga": massa_carga,
        "massa": massa_total,
        "velocidade": velocidade,
        "tempo_resposta": tempo_resposta,
        "forca_frenagem": forca_frenagem,
        "distancia_obstaculo": distancia_obstaculo,
        "gravidade": gravidade,
        "forca_peso": calcular_forca_peso(massa_total, gravidade),
    }


def obter_parametros_padrao():
    """Atalho: devolve montar_parametros() com todos os valores do enunciado."""
    return montar_parametros()


# =============================================================================
# 4. FUNÇÃO GENÉRICA DE VARREDURA DE PARÂMETROS
# =============================================================================

def _selecionar_argumentos(funcao, parametros):
    """
    Filtra o dicionário 'parametros', mantendo apenas as chaves que 'funcao'
    aceita como argumento.

    Por que isso é necessário? O dicionário de parâmetros-base tem chaves
    extras (ex.: "distancia_obstaculo", "gravidade") que calcular_parada()
    não recebe. O módulo 'inspect' lê a assinatura da função (os nomes dos
    seus parâmetros) e permite descartar as chaves que sobram. Assim, o MESMO
    dicionário serve para funções diferentes.

    Retorna: novo dict apenas com os argumentos aceitos pela função.
    """
    nomes_aceitos = inspect.signature(funcao).parameters
    return {nome: valor for nome, valor in parametros.items() if nome in nomes_aceitos}


def executar_varredura(funcao, nome_parametro, valores, parametros_base=None):
    """
    Executa 'funcao' várias vezes, variando UM único parâmetro e mantendo
    todos os outros iguais aos de 'parametros_base'.

    É assim que os experimentos reutilizam as funções genéricas:
        Experimento A -> executar_varredura(calcular_parada, "velocidade", [...])
        Experimento B -> executar_varredura(calcular_parada, "massa", [...])
        Experimento C -> executar_varredura(calcular_parada, "tempo_resposta", [...])
        Desafio       -> executar_varredura(calcular_desafio, "massa", [...])

    Parâmetros
    ----------
    funcao : callable
        Função de cálculo a ser repetida (ex.: calcular_parada). Deve devolver
        um dicionário de resultados.
    nome_parametro : str
        Nome do argumento que será variado (precisa existir na função).
    valores : lista de float
        Valores que esse argumento vai assumir, em ordem.
    parametros_base : dict ou None
        Valores dos demais parâmetros. Se None, usa os valores do enunciado.

    Retorna
    -------
    lista de dicionários: um resultado de 'funcao' para cada valor, na mesma
    ordem de 'valores'. Essa lista é o formato de "tabela" usado em dados.py
    (cada dicionário = uma linha) e em graficos.py (cada chave = uma coluna).
    """
    if parametros_base is None:
        parametros_base = obter_parametros_padrao()

    if nome_parametro not in inspect.signature(funcao).parameters:
        raise ValueError(f"A função {funcao.__name__} não possui o parâmetro "
                         f"'{nome_parametro}'.")

    registros = []
    for valor in valores:
        # Copia o dicionário para não alterar os parâmetros-base originais.
        parametros = dict(parametros_base)
        parametros[nome_parametro] = valor
        argumentos = _selecionar_argumentos(funcao, parametros)
        registros.append(funcao(**argumentos))
    return registros


# =============================================================================
# 5. BALANÇO ENERGÉTICO (Experimento D)
# =============================================================================

def calcular_balanco_energetico(massa, velocidade, tempo_resposta, forca_frenagem):
    """
    Reúne as grandezas pedidas no Experimento D para comparar o método da
    dinâmica com o teorema trabalho-energia cinética.

    Processamento:
        1. calcular_parada(...)              -> dr, db (trabalho-energia), dtotal
        2. db pelo método da dinâmica         -> calcular_distancia_frenagem_dinamica
        3. Ki = ½ m v0²,  Kf = ½ m (0)²       -> calcular_energia_cinetica
        4. Wb = (-Fb) × db                    -> calcular_trabalho_forca_constante
        5. W na etapa de resposta (força de frenagem nula nessa etapa)
        6. Diferenças numéricas entre os dois lados de cada verificação

    Parâmetros: massa [kg], velocidade = v0 [m/s], tempo_resposta = tr [s],
    forca_frenagem = Fb [N].

    Retorna: dict com as grandezas listadas abaixo (energias em J, distâncias em m).
    """
    parada = calcular_parada(massa, velocidade, tempo_resposta, forca_frenagem)
    db_energia = parada["distancia_frenagem"]
    db_dinamica = calcular_distancia_frenagem_dinamica(massa, velocidade, forca_frenagem)

    energia_inicial = calcular_energia_cinetica(massa, velocidade)   # Ki
    energia_final = calcular_energia_cinetica(massa, 0.0)            # Kf (robô parado)
    variacao_energia = energia_final - energia_inicial                # ΔK = Kf - Ki

    # Força de frenagem com sinal (-Fb), conforme a convenção do módulo.
    trabalho_frenagem = calcular_trabalho_forca_constante(-forca_frenagem, db_energia)
    # Na etapa de resposta o modelo não aplica força de frenagem (F = 0).
    trabalho_reacao = calcular_trabalho_forca_constante(0.0, parada["distancia_reacao"])

    return {
        "massa": massa,
        "velocidade": velocidade,
        "forca_frenagem": forca_frenagem,
        "aceleracao_frenagem": parada["aceleracao_frenagem"],
        "tempo_frenagem": parada["tempo_frenagem"],
        "distancia_reacao": parada["distancia_reacao"],
        "distancia_frenagem_dinamica": db_dinamica,
        "distancia_frenagem_energia": db_energia,
        "diferenca_distancia_frenagem": db_dinamica - db_energia,
        "distancia_total": parada["distancia_total"],
        "energia_cinetica_inicial": energia_inicial,
        "energia_cinetica_final": energia_final,
        "variacao_energia_cinetica": variacao_energia,
        "trabalho_reacao": trabalho_reacao,
        "trabalho_frenagem": trabalho_frenagem,
        "diferenca_trabalho_energia": trabalho_frenagem - variacao_energia,
    }


# =============================================================================
# 6. SOLUÇÃO ANALÍTICA PONTO A PONTO E SIMULAÇÃO NUMÉRICA (Experimento D)
# =============================================================================

def calcular_estado_analitico(tempo, massa, velocidade, tempo_resposta, forca_frenagem):
    """
    Posição e velocidade EXATAS (analíticas) do robô em um instante 'tempo'.

    Serve de referência para desenhar a curva analítica junto com a curva
    numérica nos gráficos x(t) e v(t).

    O instante recebido é classificado em uma das três fases:
        (1) 0 <= t <= tr          : x = v0·t                     ; v = v0
        (2) tr < t <= tr + tb     : x = dr + v0·τ + ½·a·τ² ; v = v0 + a·τ
                                    (τ = t - tr é o tempo desde o início da frenagem)
        (3) t > tr + tb           : x = dtotal                   ; v = 0

    Retorna: tupla (posicao [m], velocidade [m/s]).
    """
    parada = calcular_parada(massa, velocidade, tempo_resposta, forca_frenagem)
    a = parada["aceleracao_frenagem"]

    if tempo <= tempo_resposta:
        return velocidade * tempo, velocidade
    if tempo <= parada["tempo_total"]:
        tau = tempo - tempo_resposta
        posicao = parada["distancia_reacao"] + velocidade * tau + 0.5 * a * tau ** 2
        return posicao, velocidade + a * tau
    return parada["distancia_total"], 0.0


def calcular_trajetoria_analitica(tempos, massa, velocidade, tempo_resposta, forca_frenagem):
    """
    Aplica calcular_estado_analitico() a uma lista de instantes.

    Parâmetros: tempos = lista de instantes [s]; demais como em calcular_parada.
    Retorna: dict {"tempo": [...], "posicao": [...], "velocidade": [...]}
    (mesmo formato de listas que simular_euler_cromer devolve).
    """
    posicoes, velocidades = [], []
    for t in tempos:
        x, v = calcular_estado_analitico(t, massa, velocidade, tempo_resposta, forca_frenagem)
        posicoes.append(x)
        velocidades.append(v)
    return {"tempo": list(tempos), "posicao": posicoes, "velocidade": velocidades}


def simular_euler_cromer(massa, velocidade, tempo_resposta, forca_frenagem,
                         passo_tempo=PASSO_TEMPO_PADRAO, max_passos=10_000_000):
    """
    Simulação numérica do movimento pelo MÉTODO DE EULER-CROMER.

    Ideia do método
    ---------------
    O tempo é dividido em passos de tamanho dt. Partindo do estado conhecido
    (t_n, x_n, v_n), calcula-se o estado seguinte com:

        a_n     = aceleração no instante t_n (depende da etapa)
        v_{n+1} = v_n + a_n × dt               (1º atualiza a velocidade)
        x_{n+1} = x_n + v_{n+1} × dt           (2º atualiza a posição com a
                                                velocidade JÁ ATUALIZADA)
        t_{n+1} = t_n + dt

    A diferença em relação ao Euler "simples" está na 2ª linha: o Euler simples
    usaria v_n; o Euler-Cromer usa v_{n+1}.

    Como as duas etapas foram implementadas
    ---------------------------------------
    Em cada passo, o instante t_n decide a aceleração:
        - se t_n < tr  -> etapa de resposta  -> a_n = 0
        - caso contrário -> etapa de frenagem -> a_n = -Fb / m
    O instante é calculado como t_n = n × dt (e não somando dt repetidamente),
    para não acumular erros de arredondamento de ponto flutuante. Uma pequena
    tolerância é usada na comparação t_n < tr pelo mesmo motivo.

    Critério de parada
    ------------------
    O laço termina quando a velocidade chega a zero. Se, em um passo, a
    atualização produzir v_{n+1} <= 0, a velocidade é fixada em 0 (o modelo
    da força de frenagem só vale enquanto o robô se move no sentido +x).
    Nesse último passo, x_{n+1} = x_n + 0 × dt.

    Como números reais são guardados com arredondamento no computador
    (ponto flutuante), uma velocidade que deveria ser exatamente 0 pode
    aparecer como 1e-15 m/s. Por isso, valores menores que uma tolerância
    minúscula (tolerancia_velocidade) também são tratados como zero; sem
    isso, o programa executaria um passo extra sem significado.

    Parâmetros
    ----------
    massa [kg], velocidade = v0 [m/s], tempo_resposta = tr [s],
    forca_frenagem = Fb [N], passo_tempo = dt [s],
    max_passos : limite de segurança para evitar laço infinito.

    Retorna
    -------
    dict com:
        "passo_tempo"            dt usado [s]
        "tempo", "posicao", "velocidade", "aceleracao"
                                 listas com os valores em cada passo
                                 (índice 0 = estado inicial)
        "distancia_total"        posição final [m]
        "distancia_reacao"       posição no início da frenagem [m]
        "tempo_parada"           instante em que v chegou a 0 [s]
        "numero_passos"          quantidade de passos executados
    """
    _validar("passo_tempo", passo_tempo)
    aceleracao_frenagem = calcular_aceleracao_frenagem(massa, forca_frenagem)
    # Tolerâncias para comparações com números de ponto flutuante:
    tolerancia = passo_tempo * 1e-6                                    # [s]
    tolerancia_velocidade = 1e-9 * abs(aceleracao_frenagem) * passo_tempo  # [m/s]

    # Estado inicial (n = 0)
    n = 0
    x = 0.0
    v = float(velocidade)

    # Listas que registram a evolução do movimento (uma posição por passo).
    tempos, posicoes, velocidades, aceleracoes = [0.0], [x], [v], []
    distancia_reacao = x if tempo_resposta <= 0 else None

    while v > 0.0:
        t_n = n * passo_tempo

        # Escolha da aceleração conforme a etapa do movimento.
        if t_n < tempo_resposta - tolerancia:
            a = 0.0                          # Etapa 1: tempo de resposta
        else:
            if distancia_reacao is None:     # 1º passo da frenagem:
                distancia_reacao = x         # registra a posição atingida
            a = aceleracao_frenagem          # Etapa 2: frenagem

        # Euler-Cromer: primeiro v, depois x usando o v novo.
        v_novo = v + a * passo_tempo
        if v_novo <= tolerancia_velocidade:
            v_novo = 0.0
        x_novo = x + v_novo * passo_tempo

        # Avança o estado e registra os valores.
        n += 1
        x, v = x_novo, v_novo
        tempos.append(n * passo_tempo)
        posicoes.append(x)
        velocidades.append(v)
        aceleracoes.append(a)

        if n >= max_passos:
            raise RuntimeError("A simulação atingiu o número máximo de passos.")

    # Repete a última aceleração para que a lista tenha o mesmo tamanho das demais.
    aceleracoes.append(aceleracoes[-1] if aceleracoes else 0.0)

    return {
        "passo_tempo": passo_tempo,
        "tempo": tempos,
        "posicao": posicoes,
        "velocidade": velocidades,
        "aceleracao": aceleracoes,
        "distancia_total": x,
        "distancia_reacao": distancia_reacao if distancia_reacao is not None else x,
        "tempo_parada": tempos[-1],
        "numero_passos": n,
    }


def comparar_simulacao_analitica(massa, velocidade, tempo_resposta, forca_frenagem,
                                 passos_tempo=PASSOS_TEMPO_CONVERGENCIA):
    """
    Executa a simulação de Euler-Cromer para vários dt e compara cada uma com
    a solução analítica de calcular_parada() (estudo de convergência).

    Para cada dt da lista:
        1. simula o movimento com simular_euler_cromer(...);
        2. calcula a referência analítica com calcular_parada(...);
        3. calcula as diferenças:
             erro absoluto = |valor numérico - valor analítico|
             erro relativo = erro absoluto / valor analítico × 100 [%]

    Retorna
    -------
    tupla (registros, simulacoes):
        registros  : lista de dicts (uma linha por dt) para tabela/CSV/gráfico;
        simulacoes : lista com os dicionários completos de cada simulação
                     (usados para desenhar as curvas x(t) sobrepostas).
    """
    analitico = calcular_parada(massa, velocidade, tempo_resposta, forca_frenagem)
    registros, simulacoes = [], []

    for dt in passos_tempo:
        sim = simular_euler_cromer(massa, velocidade, tempo_resposta, forca_frenagem, dt)
        simulacoes.append(sim)

        erro_distancia = abs(sim["distancia_total"] - analitico["distancia_total"])
        registros.append({
            "passo_tempo": dt,
            "numero_passos": sim["numero_passos"],
            "distancia_reacao_numerica": sim["distancia_reacao"],
            "distancia_reacao_analitica": analitico["distancia_reacao"],
            "distancia_total_numerica": sim["distancia_total"],
            "distancia_total_analitica": analitico["distancia_total"],
            "erro_absoluto_distancia": erro_distancia,
            "erro_relativo_distancia": 100.0 * erro_distancia / analitico["distancia_total"],
            "tempo_parada_numerico": sim["tempo_parada"],
            "tempo_parada_analitico": analitico["tempo_total"],
            "erro_absoluto_tempo": abs(sim["tempo_parada"] - analitico["tempo_total"]),
        })
    return registros, simulacoes


# =============================================================================
# 7. DESAFIO DE ENGENHARIA - VELOCIDADE MÁXIMA SEGURA
# =============================================================================

def resolver_raiz_positiva_quadratica(a, b, c):
    """
    Resolve a·x² + b·x + c = 0 pela fórmula de Bhaskara e devolve a raiz positiva.

        Δ = b² - 4ac
        x = (-b ± √Δ) / (2a)

    Se houver duas raízes positivas, devolve a maior; se não houver raiz real
    positiva, lança ValueError.

    Parâmetros: coeficientes a, b, c (float), com a ≠ 0.
    Retorna: raiz positiva (float).
    """
    if a == 0:
        raise ValueError("O coeficiente 'a' não pode ser zero em uma equação do 2º grau.")
    delta = b ** 2 - 4.0 * a * c
    if delta < 0:
        raise ValueError("A equação não possui raízes reais (Δ < 0).")

    raiz_delta = math.sqrt(delta)
    raizes = [(-b + raiz_delta) / (2.0 * a), (-b - raiz_delta) / (2.0 * a)]
    positivas = [r for r in raizes if r > 0]
    if not positivas:
        raise ValueError("A equação não possui raiz positiva.")
    return max(positivas)


def calcular_velocidade_maxima_segura(massa, tempo_resposta, forca_frenagem,
                                      distancia_obstaculo):
    """
    Calcula a velocidade inicial para a qual dtotal = dobstáculo.

    A equação do enunciado
        dobstáculo = v·tr + (m·v²)/(2·Fb)
    é reorganizada na forma a·v² + b·v + c = 0, com:
        a = m / (2·Fb)     [s²/m]
        b = tr             [s]
        c = -dobstáculo    [m]
    e resolvida por resolver_raiz_positiva_quadratica(). Nenhuma velocidade
    é inserida diretamente no código: o valor sai dos parâmetros recebidos.

    Retorna: v_max [m/s] (float).
    """
    _validar("massa", massa)
    _validar("forca_frenagem", forca_frenagem)
    _validar("distancia_obstaculo", distancia_obstaculo)
    a = massa / (2.0 * forca_frenagem)
    b = tempo_resposta
    c = -distancia_obstaculo
    return resolver_raiz_positiva_quadratica(a, b, c)


def calcular_velocidade_recomendada(velocidade_maxima, fator_seguranca=FATOR_SEGURANCA):
    """
    Velocidade operacional com margem de segurança.

        v_recomendada = fator × v_max     (enunciado: fator = 0,8)

    Retorna: v_recomendada [m/s] (float).
    """
    return fator_seguranca * velocidade_maxima


def calcular_desafio(massa, tempo_resposta, forca_frenagem, distancia_obstaculo,
                     fator_seguranca=FATOR_SEGURANCA):
    """
    Resolve o desafio de engenharia para UM conjunto de parâmetros.

    Processamento:
        1. v_max  <- calcular_velocidade_maxima_segura(...)
        2. v_rec  <- calcular_velocidade_recomendada(v_max, fator)
        3. Conferência: calcular_parada(...) é chamada com v_max e com v_rec
           para obter dtotal em cada caso. O "resíduo" dtotal(v_max) - dobst
           mostra se a raiz encontrada satisfaz a equação (deve ser ~0).

    Como recebe 'massa' como argumento, esta função também é usada por
    executar_varredura(calcular_desafio, "massa", ...) para estudar v_max
    para diferentes massas.

    Retorna: dict com massa, tempo_resposta, forca_frenagem, distancia_obstaculo,
    fator_seguranca, velocidade_maxima, velocidade_recomendada,
    distancia_total_vmax, distancia_total_vrec, residuo_equacao,
    folga_distancia_vrec (= dobst - dtotal(v_rec)).
    """
    v_max = calcular_velocidade_maxima_segura(massa, tempo_resposta, forca_frenagem,
                                              distancia_obstaculo)
    v_rec = calcular_velocidade_recomendada(v_max, fator_seguranca)

    parada_vmax = calcular_parada(massa, v_max, tempo_resposta, forca_frenagem)
    parada_vrec = calcular_parada(massa, v_rec, tempo_resposta, forca_frenagem)

    return {
        "massa": massa,
        "tempo_resposta": tempo_resposta,
        "forca_frenagem": forca_frenagem,
        "distancia_obstaculo": distancia_obstaculo,
        "fator_seguranca": fator_seguranca,
        "velocidade_maxima": v_max,
        "velocidade_recomendada": v_rec,
        "distancia_total_vmax": parada_vmax["distancia_total"],
        "distancia_total_vrec": parada_vrec["distancia_total"],
        "residuo_equacao": parada_vmax["distancia_total"] - distancia_obstaculo,
        "folga_distancia_vrec": distancia_obstaculo - parada_vrec["distancia_total"],
    }


def verificar_colisao(distancia_total, distancia_obstaculo):
    """
    Aplica a condição de segurança do enunciado: dtotal <= dobstáculo.

    Retorna True se a condição é satisfeita (sem colisão) e False caso contrário.
    """
    return distancia_total <= distancia_obstaculo
