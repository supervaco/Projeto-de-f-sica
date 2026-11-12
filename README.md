# Sistema Autônomo de Frenagem e Prevenção de Colisões

Projeto da disciplina de Física Aplicada e Eletromagnetismo (Engenharia de Robôs).
O programa simula a parada de um robô móvel em duas etapas (tempo de resposta e frenagem),
executa os Experimentos A–D e resolve o desafio da velocidade máxima segura.

## Estrutura

```
projeto_frenagem/
├── main.py          # ponto de entrada: coordena tudo
├── calculos.py      # modelo físico, simulação Euler-Cromer, v_max (único módulo com fórmulas)
├── dados.py         # entrada de parâmetros, tabelas no terminal, exportação CSV
├── graficos.py      # gráficos com Matplotlib (recebem resultados prontos)
├── requirements.txt
└── resultados/      # criada automaticamente
    ├── tabelas/     # arquivos .csv
    └── graficos/    # arquivos .png
```

## Instalação

Requer Python 3.8 ou superior.

```bash
pip install -r requirements.txt
```

(ou simplesmente `pip install matplotlib`). Todas as outras bibliotecas usadas
(`csv`, `math`, `inspect`, `pathlib`) já vêm com o Python.

## Execução

Dentro da pasta `projeto_frenagem`:

```bash
python main.py
```

1. O programa pergunta se deve usar os parâmetros do enunciado. Pressione **Enter** para aceitar
   ou digite `n` para informar outros valores (Enter em cada campo mantém o valor padrão;
   aceita vírgula ou ponto decimal).
2. Os resultados de todos os experimentos aparecem no terminal e são salvos em `resultados/`.
3. Ao final, o programa pergunta se deve abrir os gráficos na tela (padrão: não; os PNGs já estão salvos).

## Funções genéricas (reutilização)

| Função em `calculos.py` | Usada por |
|---|---|
| `calcular_parada(massa, velocidade, tempo_resposta, forca_frenagem)` | Exp. A, B, C, D, desafio e validação da simulação |
| `executar_varredura(funcao, nome_parametro, valores, parametros_base)` | Exp. A, B, C e v_max × massa |
| `simular_euler_cromer(..., passo_tempo)` | Exp. D (dt = 0,01; 0,005; 0,001 s) |
| `calcular_desafio(...)` | Desafio (cenário-base e varredura por massa) |

## Arquivos gerados

**Tabelas (CSV, separador `;` e vírgula decimal, abrem direto no Excel/LibreOffice em português):**
`experimento_A_velocidade.csv`, `experimento_B_massa.csv`, `experimento_C_tempo_resposta.csv`,
`experimento_D_balanco_energetico.csv`, `experimento_D_convergencia_dt.csv`,
`experimento_D_trajetoria_dt_0_01.csv` (e `_0_005`, `_0_001`), `desafio_cenario_base.csv`,
`desafio_vmax_por_massa.csv`.

**Gráficos (PNG):** distância × parâmetro (A, B, C); posição × tempo e velocidade × tempo
(numérico × analítico); comparação entre os três dt; erro × dt (log-log); v_max e v_rec × massa.

Para usar outro formato de CSV (ex.: `,` como separador e ponto decimal), altere
`SEPARADOR_CSV` e `SEPARADOR_DECIMAL` no início de `dados.py`.
