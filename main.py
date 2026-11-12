"""
main.py
=======
Arquivo PRINCIPAL do projeto "Sistema Autônomo de Frenagem e Prevenção de
Colisões". Toda a execução começa aqui:

    python main.py

Como os módulos se comunicam
----------------------------
              (parâmetros)                  (resultados: dicts e listas)
    main.py  ─────────────►  calculos.py  ─────────────────────────────►  main.py
    main.py  ── resultados ─►  dados.py     (tabelas no terminal + arquivos CSV)
    main.py  ── resultados ─►  graficos.py  (figuras PNG + exibição na tela)

main.py não contém fórmulas físicas. Cada experimento abaixo apenas:
    1. escolhe QUAL função genérica de calculos.py usar e COM QUAIS parâmetros;
    2. entrega o resultado a dados.py (exibir/exportar);
    3. entrega o resultado a graficos.py (desenhar/salvar).

Saídas geradas
--------------
    resultados/tabelas/*.csv   -> tabelas de todos os experimentos
    resultados/graficos/*.png  -> gráficos de todos os experimentos
"""

from pathlib import Path

import calculos as calc
import dados
import graficos

# Pasta de resultados sempre ao lado deste arquivo, independentemente da
# pasta a partir da qual o comando "python main.py" foi executado.
PASTA_RESULTADOS = Path(__file__).resolve().parent / "resultados"


def executar_experimento_varredura(codigo, titulo, nome_parametro, valores, rotulo_x,
                                   parametros, pastas):
    """
    Roteiro comum aos Experimentos A, B e C.

    Os três experimentos usam o MESMO modelo (calcular_parada); muda apenas
    qual parâmetro é variado e quais valores ele assume. Por isso há uma
    única função para os três, que recebe essas diferenças como argumentos.

    Parâmetros
    ----------
    codigo : str          letra do experimento ("A", "B" ou "C"), usada nos nomes dos arquivos
    titulo : str          título exibido na tabela e no gráfico
    nome_parametro : str  argumento de calcular_parada que será variado
    valores : list        valores investigados (definidos em calculos.py)
    rotulo_x : str        nome do eixo x no gráfico (com unidade)
    parametros : dict     parâmetros-base (mantidos constantes)
    pastas : dict         {"tabelas": Path, "graficos": Path}

    Retorna: lista de dicionários com os resultados (uma linha por valor).
    """
    # 1) Cálculo: a função genérica é repetida para cada valor da lista.
    registros = calc.executar_varredura(calc.calcular_parada, nome_parametro,
                                        valores, parametros)

    # 2) Saída: tabela no terminal + CSV.
    nome_base = f"experimento_{codigo}_{nome_parametro}"
    dados.exibir_tabela(registros, dados.COLUNAS_PARADA, f"Experimento {codigo} - {titulo}")
    dados.exportar_csv(registros, dados.COLUNAS_PARADA, pastas["tabelas"] / f"{nome_base}.csv")

    # 3) Gráfico.
    graficos.grafico_distancia_vs_parametro(
        registros, nome_parametro, rotulo_x,
        f"Experimento {codigo} - {titulo}",
        pastas["graficos"] / f"{nome_base}.png")
    return registros


def executar_experimento_d(parametros, pastas):
    """
    Experimento D: balanço energético, simulação de Euler-Cromer e
    estudo de convergência com diferentes dt.

    Etapas:
        D.1 - balanço energético analítico (dinâmica x trabalho-energia);
        D.2 - simulações para dt = 0,01; 0,005; 0,001 s e comparação com a
              solução analítica (tabela de convergência);
        D.3 - gráficos x(t) e v(t) da simulação com dt = 0,01 s, sobrepostos
              à solução analítica, e registro passo a passo em CSV;
        D.4 - gráficos de comparação entre os dt e de erro em função de dt.
    """
    # Apenas os quatro argumentos do modelo de parada (descarta as chaves extras).
    argumentos = {chave: parametros[chave]
                  for chave in ("massa", "velocidade", "tempo_resposta", "forca_frenagem")}

    dados.imprimir_cabecalho("EXPERIMENTO D - BALANÇO ENERGÉTICO E SIMULAÇÃO NUMÉRICA")

    # --- D.1 Balanço energético ---------------------------------------------
    balanco = calc.calcular_balanco_energetico(**argumentos)
    dados.exibir_balanco_energetico(balanco)
    dados.exportar_balanco_energetico(balanco, pastas["tabelas"] / "experimento_D_balanco_energetico.csv")

    # --- D.2 Simulações e convergência --------------------------------------
    registros_conv, simulacoes = calc.comparar_simulacao_analitica(
        **argumentos, passos_tempo=calc.PASSOS_TEMPO_CONVERGENCIA)
    dados.exibir_tabela(registros_conv, dados.COLUNAS_CONVERGENCIA,
                        "Experimento D - Comparação numérico x analítico para diferentes dt")
    dados.exportar_csv(registros_conv, dados.COLUNAS_CONVERGENCIA,
                       pastas["tabelas"] / "experimento_D_convergencia_dt.csv")

    # Seleciona a simulação feita com o dt padrão (0,01 s) e a de menor dt.
    sim_padrao = next(s for s in simulacoes if s["passo_tempo"] == calc.PASSO_TEMPO_PADRAO)
    sim_fina = min(simulacoes, key=lambda s: s["passo_tempo"])

    # A curva analítica é avaliada nos instantes da simulação de menor dt,
    # apenas para que a linha desenhada tenha muitos pontos.
    analitico = calc.calcular_trajetoria_analitica(sim_fina["tempo"], **argumentos)

    # --- D.3 Trajetória com dt padrão ---------------------------------------
    for sim in simulacoes:
        nome = f"experimento_D_trajetoria_dt_{sim['passo_tempo']:g}".replace(".", "_")
        dados.exportar_csv(dados.converter_simulacao_em_registros(sim),
                           dados.COLUNAS_TRAJETORIA, pastas["tabelas"] / f"{nome}.csv")

    graficos.grafico_trajetoria(
        sim_padrao, analitico, "posicao", "Posição (m)",
        "Experimento D - Posição em função do tempo",
        pastas["graficos"] / "experimento_D_posicao_tempo.png",
        parametros["tempo_resposta"],
        linha_horizontal=(parametros["distancia_obstaculo"],
                          f"Obstáculo (x = {parametros['distancia_obstaculo']:g} m)"))
    graficos.grafico_trajetoria(
        sim_padrao, analitico, "velocidade", "Velocidade (m/s)",
        "Experimento D - Velocidade em função do tempo",
        pastas["graficos"] / "experimento_D_velocidade_tempo.png",
        parametros["tempo_resposta"])

    # --- D.4 Comparação entre passos de tempo --------------------------------
    graficos.grafico_comparacao_passos(simulacoes, analitico,
                                       pastas["graficos"] / "experimento_D_comparacao_dt.png")
    graficos.grafico_convergencia(registros_conv,
                                  pastas["graficos"] / "experimento_D_erro_vs_dt.png")


def executar_desafio(parametros, pastas):
    """
    Desafio de engenharia:
        1. v_max e v_recomendada para os parâmetros-base (calcular_desafio);
        2. a mesma função repetida para várias massas (executar_varredura).
    """
    dados.imprimir_cabecalho("DESAFIO DE ENGENHARIA")

    argumentos = {chave: parametros[chave] for chave in
                  ("massa", "tempo_resposta", "forca_frenagem", "distancia_obstaculo")}

    # 1) Cenário-base
    resultado = calc.calcular_desafio(**argumentos, fator_seguranca=calc.FATOR_SEGURANCA)
    dados.exibir_desafio(resultado)

    # 2) Variação com a massa: reutiliza a varredura genérica.
    registros = calc.executar_varredura(calc.calcular_desafio, "massa",
                                        calc.MASSAS_DESAFIO, parametros)
    dados.exibir_tabela(registros, dados.COLUNAS_DESAFIO,
                        "Desafio - Velocidade máxima segura para diferentes massas")
    dados.exportar_csv([resultado], dados.COLUNAS_DESAFIO,
                       pastas["tabelas"] / "desafio_cenario_base.csv")
    dados.exportar_csv(registros, dados.COLUNAS_DESAFIO,
                       pastas["tabelas"] / "desafio_vmax_por_massa.csv")
    graficos.grafico_velocidade_maxima_vs_massa(
        registros, pastas["graficos"] / "desafio_vmax_por_massa.png")
    return resultado


def main():
    """
    Sequência completa de execução do programa.
    """
    dados.imprimir_cabecalho("SISTEMA AUTÔNOMO DE FRENAGEM E PREVENÇÃO DE COLISÕES")

    # Preparação: pastas de saída e estilo dos gráficos.
    pastas = dados.preparar_pastas(PASTA_RESULTADOS)
    graficos.configurar_estilo()

    # Parâmetros: o usuário pode manter os do enunciado ou digitar outros.
    # dados.py só coleta os valores; a massa total é calculada em calculos.py.
    valores = dados.solicitar_parametros(calc.obter_parametros_padrao())
    parametros = calc.montar_parametros(**valores)
    dados.exibir_parametros(parametros)

    # Cenário-base (resultado analítico com os parâmetros escolhidos).
    parada = calc.calcular_parada(parametros["massa"], parametros["velocidade"],
                                  parametros["tempo_resposta"], parametros["forca_frenagem"])
    sem_colisao = calc.verificar_colisao(parada["distancia_total"],
                                         parametros["distancia_obstaculo"])
    dados.exibir_resultado_parada(parada, parametros["distancia_obstaculo"], sem_colisao)

    # Experimentos A, B e C: mesmo roteiro, mudando apenas o parâmetro variado.
    dados.imprimir_cabecalho("EXPERIMENTOS A, B e C - VARREDURA DE PARÂMETROS")
    executar_experimento_varredura("A", "Distância de parada em função da velocidade inicial",
                                   "velocidade", calc.VELOCIDADES_EXPERIMENTO_A,
                                   "Velocidade inicial v0 (m/s)", parametros, pastas)
    executar_experimento_varredura("B", "Distância de parada em função da massa total",
                                   "massa", calc.MASSAS_EXPERIMENTO_B,
                                   "Massa total m (kg)", parametros, pastas)
    executar_experimento_varredura("C", "Distância de parada em função do tempo de resposta",
                                   "tempo_resposta", calc.TEMPOS_EXPERIMENTO_C,
                                   "Tempo de resposta tr (s)", parametros, pastas)

    # Experimento D e desafio.
    executar_experimento_d(parametros, pastas)
    executar_desafio(parametros, pastas)

    # Exibição opcional dos gráficos na tela (todos já foram salvos em PNG).
    dados.imprimir_cabecalho("FIM DA EXECUÇÃO")
    print(f"  Resultados salvos em: {PASTA_RESULTADOS}")
    if dados.perguntar_sim_nao("Exibir os gráficos na tela agora?", padrao=False):
        graficos.exibir_graficos()
    graficos.fechar_graficos()


# Este bloco garante que main() só rode quando o arquivo é executado
# diretamente (python main.py), e não quando é importado por outro arquivo.
if __name__ == "__main__":
    main()
