# 🧾 Leitor de Notas Fiscais com IA

Sistema que recebe notas fiscais em **PDF ou foto** (de escaneadas e amassadas a digitais), usa IA de visão para extrair **empresa, valor total e data** e salva tudo, já validado e padronizado, em um banco SQL.

![Tela do app](docs/tela_app.png)

## Como funciona

```
PDF ──► páginas em imagem (PyMuPDF) ──┐
                                      ├──► IA de visão (Gemini) ──► validação ──► SQLite ──► interface / Excel
Foto (JPG, PNG, WebP) ────────────────┘
```

## Funcionalidades

- Upload de vários arquivos de uma vez (PDF, PNG, JPG, JPEG e WebP)
- Leitura de notas de qualidade ruim (amassadas, tortas, escaneadas) com IA de visão
- Validação antes de gravar: empresa preenchida, valor maior que zero e data real, que não esteja no futuro
- Padronização de formatos (ex.: `1.234,56` vira `1234.56`, datas em `AAAA-MM-DD`)
- Proteção contra duplicatas em duas camadas: hash do arquivo (nem chama a IA) e conferência de empresa + valor + data
- Novas tentativas e modelo reserva quando a API falha (erros 503 e 429)
- Edição e exclusão de notas direto na interface, com validação
- Exportação para Excel formatado: valores em R$, datas, filtros, linha de total e aba de resumo por empresa

## Tecnologias

Python · PyMuPDF · Google Gemini API · SQLite · Streamlit · pandas · openpyxl

## Como rodar

1. Clone o repositório e entre na pasta:
   ```bash
   git clone https://github.com/SEU-USUARIO/leitor-notas-fiscais-ia.git
   cd leitor-notas-fiscais-ia
   ```
2. Instale as dependências:
   ```bash
   python -m pip install -r requirements.txt
   ```
3. Crie uma chave no [Google AI Studio](https://aistudio.google.com) e defina a variável de ambiente `GEMINI_API_KEY`:
   - Windows (PowerShell): `setx GEMINI_API_KEY "sua_chave"` (depois feche e abra o terminal)
   - Mac/Linux: `export GEMINI_API_KEY="sua_chave"`
4. Rode o app:
   ```bash
   python -m streamlit run app.py
   ```

O banco `notas.db` é criado automaticamente na primeira execução.

## Estrutura do projeto

| Arquivo              | Função                                                                    |
| -------------------- | ------------------------------------------------------------------------- |
| `app.py`             | Interface web: upload, tabela, edição, exclusão e download do Excel       |
| `pdf_para_imagem.py` | Converte as páginas do PDF em imagens                                     |
| `leitor_ia.py`       | Envia a imagem ao Gemini e recebe os dados em JSON                        |
| `validacao.py`       | Confere e padroniza os dados antes de salvar                              |
| `banco.py`           | Operações no SQLite: inserir, listar, editar, excluir e checar duplicatas |
| `exportar_excel.py`  | Gera a planilha formatada                                                 |

## Decisões de projeto

- **Validar antes de gravar:** a IA pode errar, então nada entra no banco sem passar pelas regras de validação. Se faltar algo, a nota é rejeitada com o motivo.
- **`null` em vez de chute:** o prompt instrui a IA a devolver `null` quando não consegue ler um campo, porque um campo vazio é melhor que um valor inventado.
- **Tolerância a falhas:** erros de servidor (503) geram novas tentativas com espera crescente. Cota esgotada ou modelo indisponível (429 e 404) passam direto para o modelo reserva.
- **Economia de requisições:** o hash do arquivo evita reler uma nota já processada, o que importa porque o plano gratuito da API tem limite diário.
- **SQL com parâmetros (`?`):** todas as consultas usam parâmetros, nunca texto concatenado, para evitar SQL injection.
- **Edição "tudo ou nada":** na tela de edição, se qualquer linha for inválida, nenhuma alteração é gravada.

## Privacidade

Notas fiscais contêm dados reais (nomes, CNPJ, valores). O banco `notas.db`, os PDFs, as imagens e as planilhas geradas ficam apenas na sua máquina e estão no `.gitignore`. As imagens das notas são enviadas à API do Gemini para leitura, então consulte a política de uso de dados do plano que você utiliza antes de processar notas de terceiros.

<!--
## Resultados dos testes (preencha e remova os comentários)

| Campo | Acertos |
|---|---|
| Empresa | X de Y notas |
| Valor total | X de Y notas |
| Data | X de Y notas |

Testado com Y notas de qualidades variadas: boas, escaneadas, tortas e amassadas.
-->

## Limitações conhecidas

- Duas compras diferentes na mesma loja, no mesmo dia e com o mesmo valor são tratadas como duplicata
- O plano gratuito da API tem limite diário de requisições
- A IA pode errar em notas muito ilegíveis, e por isso existem a validação e a edição manual
- Empresas escritas de formas diferentes (ex.: maiúsculas e minúsculas) aparecem separadas no resumo por empresa

## Próximos passos

- Filtro por período e por empresa, também aplicado ao Excel exportado
- Gráfico de gastos por empresa e por mês
- Mais campos (CNPJ, itens da nota)
