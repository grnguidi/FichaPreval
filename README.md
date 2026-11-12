# Ficha Prevalecentes 3.1

Ficha de personagem automatizada para o RPG Prevalecentes (PREVA 3.1), com modo de sessão em rede local para os jogadores levantarem a mão sem interromper a cena.

## Uso

**Com o executável:** abra `FichaPrevalecentes.exe`. Não requer Python.

**Pelo código-fonte:** instale o Python 3 e as dependências, depois execute o programa principal.

```
py -m pip install reportlab segno
py prevalecentes.py
```

## Gerar o executável

Execute `GERAR_EXE.bat`. O script instala PyInstaller, reportlab e segno, compila o programa e substitui `FichaPrevalecentes.exe` nesta pasta. Requer Python no PATH do Windows.

## Funcionalidades

- Cálculo automático de Curva, Bônus de Combate, Vida, Mana, Vigor, CA, Carga, Movimento, Iniciativa, ações extras, Redução de Dano, Resistências, Descoberta, perícias, ataques, defesas e DTs.
- Controle de pontos de atributo por nível, com painel de avisos para pendências.
- Menus de armas, encantamentos, talentos, armaduras, escudos, talismãs e sets, indicando o que está disponível e o motivo de cada restrição.
- Assistente de criação de personagem, seguindo o capítulo "Criando seu Personagem".
- Rolagens de ataque e conjuração, com consumo de Vigor e Mana e diário de rolagens.
- Comparação entre duas fichas.
- Exportação da ficha em PDF.
- Modo noturno.

As fórmulas utilizadas estão em Ajuda > Regras usadas nos cálculos.

## Sessão: levantar a mão

Permite que os jogadores sinalizem ao mestre que querem falar. Funciona na mesma rede local (Wi-Fi ou cabo). Existe uma única sessão por rede.

**Mestre:** abra Sessão e selecione "Entrar como mestre". A tela mostra a fila de mãos levantadas, na ordem. "Dar a palavra" (ou duplo clique no nome) avisa o jogador e baixa a mão dele.

**Jogador no computador:** abra Sessão e selecione "Entrar como jogador". O programa localiza o mestre automaticamente. Se não localizar, informe o IP exibido na tela do mestre.

**Jogador no celular:** aponte a câmera para o QR code da tela do mestre, ou abra o endereço exibido nela (`http://IP:5760`), informe o nome e toque em "Levantar a mão". Não requer instalação.

Observações:

- O programa não distingue mestre de jogador: apenas quem usa o botão de mestre recebe os avisos. Combinem que somente o mestre o utilize.
- Não há senha. Qualquer pessoa na mesma rede que conheça o endereço pode entrar.
- Na primeira execução como mestre, o Firewall do Windows solicita permissão. Permita o acesso em redes privadas.
- Redes que isolam dispositivos entre si (Wi-Fi de visitantes, hotéis, escolas) impedem a conexão.
- Portas utilizadas: 5757 (TCP), 5758 (UDP) e 5760 (HTTP).
- A sessão troca apenas o sinal de mão levantada. Nenhum dado da ficha é transmitido.

## Dados do livro

Armas, encantamentos e talentos estão embutidos no programa (`dados_prevalecentes.py`). Para corrigir algum dado, edite uma cópia de `dados_livro (para editar).json`, renomeie para `dados_prevalecentes.json` e coloque ao lado do executável. Esse arquivo passa a ser usado no lugar dos dados embutidos.

## Fichas salvas

As fichas são salvas manualmente em arquivos `.json` (Ctrl+S) e abertas com Ctrl+O. O programa não reabre a última ficha automaticamente.

## Arquivos

| Arquivo | Descrição |
|---|---|
| `prevalecentes.py` | Programa principal e interface |
| `regras.py` | Cálculos das regras, sem interface |
| `assistente.py` | Assistente de criação de personagem |
| `pdf_ficha.py` | Exportação para PDF |
| `sessao.py` | Sessão em rede e página do celular |
| `dados_prevalecentes.py` | Dados do livro embutidos |
| `dados_livro (para editar).json` | Cópia editável dos dados do livro |
| `GERAR_EXE.bat` | Gera o executável |
