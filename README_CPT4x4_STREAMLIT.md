# CPT 4x4 online com Streamlit

Esta é a versão online do programa CPT 4x4. Permite criar um link público onde as pessoas conseguem ver a classificação.

## Ficheiros

- `cpt4x4_streamlit.py` — aplicação principal
- `requirements.txt` — dependências necessárias
- `data/resultados_cpt4x4.json` — criado automaticamente quando a aplicação arranca

## Como testar no computador

1. Instalar as dependências:

```bash
pip install -r requirements.txt
```

2. Executar:

```bash
streamlit run cpt4x4_streamlit.py
```

3. Abrir o link local que aparecer no terminal.

## Admin

Na barra lateral existe uma secção chamada **Admin**.

Por defeito, a palavra-passe local é:

```text
admin
```

Para publicar online, deves configurar uma palavra-passe segura em `Secrets` no Streamlit Cloud:

```toml
ADMIN_PASSWORD = "a-tua-password-segura"
```

## Publicar no Streamlit Community Cloud

1. Criar conta em https://share.streamlit.io
2. Criar um repositório no GitHub
3. Enviar estes ficheiros para o repositório:
   - `cpt4x4_streamlit.py`
   - `requirements.txt`
4. No Streamlit Cloud, carregar em **New app**
5. Escolher o repositório
6. Em **Main file path**, colocar:

```text
cpt4x4_streamlit.py
```

7. Em **Advanced settings > Secrets**, colocar:

```toml
ADMIN_PASSWORD = "a-tua-password-segura"
```

8. Carregar em **Deploy**

Depois recebes um link público para partilhar.

## Regra dos 2 piores

Cada etapa conta como um resultado individual.

Exemplo:

```text
Valongo etapa 1 = 25 pontos
Valongo etapa 2 = 17 pontos
Cinfães etapa 1 = 20 pontos
Cinfães etapa 2 = 14 pontos
```

A equipa fica com:

```text
25, 17, 20, 14
```

Ao usar **Tirar 2 piores etapas**, remove:

```text
14, 17
```

Fica a contar:

```text
25 + 20 = 45
```

## Nota importante sobre dados

Esta versão guarda os dados num ficheiro JSON local. No Streamlit Cloud, funciona para começar, mas para uma solução mais robusta a longo prazo o ideal é ligar a aplicação a Google Sheets, Supabase ou outra base de dados online.
