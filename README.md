# Ficha Prevalecentes 3.1

Ficha de personagem automatizada para o RPG Prevalecentes (PREVA 3.1), com sessão em rede local: painel do mestre com a Vida, Mana e Vigor dos jogadores em tempo real, dano e condições enviados pela mesa, e mão levantada.

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
- Assistente de criação de personagem, seguindo o capítulo "Criando seu Personagem", com nível inicial (personagem novo entra no nível do grupo) e Caminho da Meta de Vida. No celular, o mesmo passo a passo.
- Rolagens de ataque, conjuração e perícias (1d20 a mais a cada 20 pontos do atributo, fica o maior), com consumo de Vigor e Mana e diário de rolagens.
- Propriedades de armas: lista das 16 propriedades do livro com o limite da arma (tabela do nível + Domínio). Os efeitos entram sozinhos: Afiada, Cruel e Poderosa no dano, Pesada sobe o dado e dobra a Força exigida, Certeira e Destruidora no crítico, Equilibrada no ataque, Elemental/Sagrada/Profana rolam o 1d6 extra, Reforçada aumenta o desgaste para 4, Voraz cura no crítico e Discreta dá +5 em Furtividade.
- Talentos com escolha (Maestria, Maestria dupla, Domínio, Matrícula, Matrícula avançada, Condição Endurecida, Mestre das Perícias): ao lado do talento você escolhe a arma, a escola, a condição ou a perícia, e o efeito vale só para ela (acerto +1 na arma da Maestria, propriedade extra na arma do Domínio, −Mana e −espaço nos encantamentos da escola, +20 na barra da condição, +2 e 1 vantagem na perícia).
- Encantamentos com dados de condição já escalados pelo Arcano (cópias a cada 20, dados inferiores a cada 15), com Mente Arcana (+10 de Arcano) e Senhor das Condições (+1 cópia).
- Sets que aplicam pontos de condição (Sangria, Peçonha, Miasma, Geada, Delírio, Torpor, Gume) mostram os pontos em cada acerto ou crítico, com valor fixo: como diz o livro, os números dos sets não escalam com o Arcano.
- Clicar no nome de uma perícia (no celular, tocar nela no Modo Edição) mostra o que ela faz, o atributo, se exige treino e onde o livro a usa.
- Desgaste de armas: 3 turnos afiados, o crítico reafia; a arma desgastada fica um turno parada.
- Descanso curto e longo (Vida, Mana, Vigor e barras de condição) e Poção Espiritual.
- Inventário com a lista de Itens Diversos do livro (peso já preenchido), quantidade e botão de usar consumíveis (poções de Mana e Vigor, antídotos…). A Mochila soma +5 de Carga; peças de set pesam 1.
- **Turno:** Comum, Bônus, Movimento e Reação mais as ações extras da Destreza (cada uma escolhida uma vez como Comum ou Bônus). Ataques, encantamentos, itens e habilidades da Alma marcam a ação sozinhos e avisam quando não sobrava. "Novo turno" e "Novo combate" renovam; na sessão, o turno renova quando o mestre passa a vez e o combate quando ele rola a iniciativa ou encerra o combate.
- **Ações do livro** (Agarrar, Derrubar, Esconder, Provocar, Golpe de Oportunidade…) com a rolagem certa: Atletismo, Furtividade, DT de Provocar (10 + BC de Mente + nível ÷ 3) ou ataque com a arma.
- **Ações das armas** como botões: "Usar" marca a ação do turno e "Rolar" ataca com os ajustes lidos do texto (níveis de dano, vantagem/desvantagem, crítico garantido, multiplicador, teste do alvo com a DT). Ações de vários disparos (Chuva de Flechas, Rajada Tripla, Rajada Brutal, Combustão, Rajada de Fogo) rolam cada disparo, com um teste de acerto para cada ou um só quando o livro diz, e descontam a munição do contador. Contadores da mecânica de cada arma (Momentum, Cartuchos, Flechas, Melodias…).
- **Defesas e Contradomínio:** rolar Fortitude, Reflexo, Vontade e Astúcia; Contradomínio com o limite por combate (+2 com Contra-encantador); Coordenação do Uso duplo contra DT 8 + maior nível de arma.
- **Usos limitados:** talentos e talismãs "1x por combate/descanso" e os usos da Alma, recarregados no turno, no fim do combate e nos descansos.
- **Alma:** montador de habilidades pela Tabela de valores do livro (categorias, ajustes de Facilitando e dificultando, execução), com o valor e a DT calculados; "Usar e rolar" gasta um uso e rola o dano.
- **Metas de Vida:** os 9 Caminhos do livro com as 3 etapas em ordem e o mentor. Cada Meta concluída abre um slot de talento (M1–M5); a primeira dá +5 pontos de atributo.
- **Dinheiro em Contos, prata, ouro e Contilha**, com conversão, e compra de itens do livro descontando o preço.
- O diário de rolagens fica guardado na ficha (as 100 mais recentes).
- Acerto do cajado/selo somado ao conjurar, como o acerto da arma.
- Comparação entre duas fichas.
- Exportação da ficha em PDF.
- Modo noturno.
- **Modo Edição e Modo Jogo.** Criar ou subir de nível, escolher talentos, armas, encantamentos e equipamento só no Modo Edição (ficha nova abre nele). No Modo Jogo, usado na mesa, essas escolhas ficam travadas e continuam liberados Vida/Mana/Vigor, rolagens, condições, Portão da Morte, inventário e anotações. Troque pelo botão no topo da ficha. Fichas abertas do disco começam no Modo Jogo.

As fórmulas utilizadas estão em Ajuda > Regras usadas nos cálculos.

## Sessão na rede local

Liga o mestre aos jogadores na mesma rede local (Wi-Fi ou cabo). Existe uma única sessão por rede.

**Mestre:** abra Sessão e selecione "Entrar como mestre". Abre o painel do mestre:

- Um cartão por jogador com o personagem, barras de Vida, Mana e Vigor, nível, CA, movimento, iniciativa, Portão da Morte (quando a Vida chega a 0), acúmulos de condição e se está no celular ou sem sinal. Atualiza sozinho quando o jogador muda a ficha.
- **Dano / Cura:** valor, um dos tipos de dano do livro e descrição. A ficha de cada jogador desconta a RD e as resistências dele (Magia Pura e Relâmpago ignoram RD; "Direto" ignora tudo) e o resultado volta para o registro do mestre. Marque vários jogadores para enviar a todos de uma vez.
- **Efeito:** um dos efeitos do livro (Abalado, Caído, Exposto, Fragilizado, Paralisado…) com a descrição já preenchida, duração em turnos (0 = até o mestre remover). Aparece na aba Combate do jogador. Fragilizado tira a RD e as resistências do dano recebido.
- **Condição:** pontos de Veneno, Podridão, Sangramento, Congelamento, Sono, Loucura ou Morte com a DT do inimigo. A ficha rola Fortitude ou Vontade, recebe metade num sucesso e, se a barra de 100 encher, aplica o efeito do livro (Sangramento tira 25% da Vida na hora; Veneno tira 5% por turno por 5 turnos; Sono deixa Inconsciente…).
- **Bolsa:** o mestre vê o inventário, a carga e o dinheiro de cada jogador, dá itens (da lista do livro ou personalizados) e tira itens. O jogador é avisado.
- **Turnos:** "🎲 Iniciativa" rola a iniciativa de todos pela ficha e monta a ordem de turno (dá para mudar valores ou tirar alguém). "Passar turno ▶" passa a vez, avisa o jogador da vez e, depois do último, começa a rodada seguinte. As durações contam no fim do turno do afetado, como no livro, e Veneno e Podridão tiram Vida no começo do turno. "Fim do combate" limpa a ordem e os efeitos que duram até o fim do combate.
- À direita, a ordem de turno, a fila de mãos levantadas ("Dar a palavra" avisa o jogador e baixa a mão dele) e o registro de tudo que o mestre enviou e do que os jogadores rolaram.

**Jogador no computador:** abra a ficha, depois Sessão → "Entrar como jogador". O programa localiza o mestre automaticamente; se não localizar, informe o IP exibido na tela do mestre. A ficha aberta é enviada ao painel do mestre e recebe dano e condições.

**Jogador no celular:** aponte a câmera para o QR code da tela do mestre, ou abra o endereço exibido nela (`http://IP:5760`). O PC do mestre entrega a ficha completa do celular: informe seu nome, abra ou crie a ficha e jogue. A barra acima das abas mostra a rodada, as condições do mestre e o botão ✋. Não requer instalação nem internet. (A página antiga, só com o botão de mão, continua em `http://IP:5760/mao`.)

**Levar a ficha do app para a mesa (e de volta):** o jogador mantém e atualiza a ficha no app instalado (GitHub Pages), em casa. Como um site `https` não pode enviar dados a `http://IP`, a ficha viaja no endereço (o trecho `#f=` da URL, comprimido, que só o navegador lê), sem servidor no meio:
- *Do app para a mesa:* na página do mestre (`http://IP:5760`), toque em **📲 Trazer minha ficha do app**. O app abre com a lista de fichas; toque em **Enviar** na que vai jogar. A página do mestre guarda a ficha (substitui a de mesmo nome) e entra na mesa com o nome do personagem. Também dá para abrir o app e usar **🛡 Entrar na mesa do mestre** digitando o endereço.
- *Da mesa para o app:* no menu da página do mestre, **📲 Levar esta ficha de volta ao app** (o botão também aparece no aviso de fim de combate). A ficha de mesmo nome no app é substituída pela atual (Vida, Mana, Vigor, condições, inventário, dinheiro).
- Durante a sessão, a ficha da mesa recebe dano, cura, condições e itens do mestre; o app instalado só é atualizado pelo botão acima.
- O mestre recebe o resumo da ficha a cada ~1,5 s e não edita a ficha do jogador diretamente: envia dano, cura, condições e itens.
- O app instalado e a página da mesa guardam fichas em lugares separados (origens diferentes do navegador). No iPhone isso vai além: o app da Tela de Início e o Safari também têm armazenamento separado, e o link "de volta ao app" abre no Safari. Por isso, no iPhone o app mostra um aviso na tela inicial (só quando aberto pela Tela de Início) com o botão **⬇ Backup de todas as fichas**, que salva um único `.json` (no iPhone abre "Salvar em Arquivos"); "Abrir arquivo .json" restaura esse backup. Recomenda-se usar o app direto pelo Safari e fazer o backup de vez em quando.

Observações:

- O programa não distingue mestre de jogador: apenas quem usa o botão de mestre recebe os avisos. Combinem que somente o mestre o utilize.
- Não há senha. Qualquer pessoa na mesma rede que conheça o endereço pode entrar.
- Na primeira execução como mestre, o Firewall do Windows solicita permissão. Permita o acesso em redes privadas.
- Redes que isolam dispositivos entre si (Wi-Fi de visitantes, hotéis, escolas) impedem a conexão.
- Portas utilizadas: 5757 (TCP), 5758 (UDP) e 5760 (HTTP).
- A sessão envia ao mestre só o resumo da ficha (nome, espécie, nível, Vida, Mana, Vigor, CA, movimento, iniciativa, defesas, RD, resistências, Portão da Morte, barras de condição, inventário, carga e dinheiro).
- Os eventos do mestre (dano, condições, itens) são repetidos até o celular confirmar o recebimento, então não se perdem se a tela bloquear ou o Wi-Fi cair; o celular ignora repetições. Quem sai da mesa (10 min sem contato) perde também a vez na iniciativa, os efeitos e o resumo.
- Celular com a tela bloqueada continua na mesa: o mestre vê "(sem sinal)" ao lado do nome depois de 20 segundos e a mão continua na fila. O jogador só sai da mesa depois de 10 minutos sem contato.
- Se a conexão cair, o jogador no computador vê "Conexão perdida" e um botão para conectar de novo. Quando o mestre não é encontrado na rede, o programa sugere o último IP usado.

## App de celular (ficha de mesa)

Versão para usar na mesa pelo celular: Vida, Mana e Vigor, atributos, características, perícias, armas com ações, rolagens de ataque e conjuração, grimório, talentos e bolsa (inventário com os itens do livro, quantidade, botão de usar, carga, dinheiro e peças de set com os bônus ativos). Também rola perícias, faz descanso curto/longo, Poção Espiritual e controla o desgaste das armas. Também tem Modo Jogo e Modo Edição, como no PC. Abre os mesmos arquivos `.json` do programa de PC e funciona sem internet depois de instalado.

**Instalar no Android:** abra https://grnguidi.github.io/FichaPreval/ no Chrome e toque em ⋮ → "Instalar app" (ou "Adicionar à tela inicial").

- "Abrir arquivo .json" carrega uma ficha salva pelo PC. As fichas ficam guardadas no celular.
- Para levar de volta ao PC: menu ☰ → Exportar ficha (.json).
- O celular tem as mesmas funções de mesa do PC (turno, usos, ações de arma, Alma com montador, Metas de Vida, dinheiro, diário) e "🖨 Imprimir / salvar PDF" no menu. A ficha vai e volta entre PC e celular sem perder nada.

**Para desenvolver:** o código do app está em `celular/src/js/` (arquivos numerados por área: armazenamento, cálculo, telas, ações, mesa, rolagens, menu, sessão, eventos; o `build.py` junta todos no mesmo escopo, na ordem do nome). Depois de mudar algo, rode `py celular/build.py` para gerar a pasta `docs/`, que é o que o GitHub Pages publica, e o `pagina_celular.py`, que é a mesma ficha servida pelo PC do mestre na sessão. Os dados do livro e a tabela de efeitos de talento vêm de `dados_prevalecentes.py` e `regras.py`, então PC e celular continuam iguais. `sh celular/testes/rodar.sh` confere que as regras do celular dão os mesmos resultados que as do PC (requer Node.js). `python testes/test_sessao.py` testa a entrega e a confirmação dos eventos da sessão e a limpeza de quem sai.

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
| `sessao.py` | Sessão em rede e painel do mestre |
| `ponte_sessao.py` | Liga a ficha do PC aberta à sessão (resumo e eventos do mestre) |
| `regras_texto.py` | Texto da janela "Regras usadas nos cálculos" |
| `testes/` | Testes da sessão (`python testes/test_sessao.py`) |
| `pagina_celular.py` | Ficha do celular servida pelo mestre (gerado por `celular/build.py`) |
| `dados_prevalecentes.py` | Dados do livro embutidos |
| `dados_livro (para editar).json` | Cópia editável dos dados do livro |
| `GERAR_EXE.bat` | Gera o executável |
| `celular/` | Código do app de celular (`src/js/` e `build.py`, que gera a pasta `docs/`) |
| `docs/` | App de celular pronto, publicado pelo GitHub Pages |
