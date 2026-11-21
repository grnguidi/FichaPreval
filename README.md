# Conestoga connection

<img src="celular/src/icone-192.png" alt="Ícone: carroça Conestoga" width="96" align="right">

Ficha de personagem automatizada para o RPG **Prevalecentes (PREVA 3.3)**, para PC (Windows e Mac) e celular (app instalável, funciona offline), com **sessão de mesa**: o mestre vê Vida, Mana e Vigor dos jogadores em tempo real e envia dano, condições, efeitos e itens.

## Índice

- [Começando](#começando)
- [Funcionalidades](#funcionalidades)
- [Sessão de mesa](#sessão-de-mesa)
- [App de celular](#app-de-celular)
- [Desenvolvimento](#desenvolvimento)
- [Dados do livro e fichas salvas](#dados-do-livro-e-fichas-salvas)
- [Estrutura do projeto](#estrutura-do-projeto)

## Começando

| Quero usar… | Como |
|---|---|
| **No PC (Windows)** | Baixe `ConestogaConnection.exe` na página de [Releases](../../releases/latest) e abra. Não requer Python. |
| **No celular** | Abra <https://grnguidi.github.io/FichaPreval/> no Chrome e toque em ⋮ → "Instalar app". |
| **No Mac** | Instale o Python de [python.org](https://www.python.org/downloads/macos/) e dê dois cliques em `INICIAR.command` (instala as dependências na 1ª vez). |
| **Pelo código-fonte** | Instale o Python 3 e rode os comandos abaixo. |

```
py -m pip install -r requirements.txt
py prevalecentes.py
```

**Mac:** use o Python de python.org (ou `brew install python-tk`). O Python que vem com as Ferramentas de Linha de Comando da Apple tem um Tk antigo que fecha ao abrir janelas em alguns macOS (erro `macOS 12 (1207) or later required`). Pelo terminal: `python3 -m pip install -r requirements.txt && python3 prevalecentes.py`. No Mac os atalhos usam ⌘ (⌘S, ⌘O…) e o painel do mestre abre no Chrome/Edge se instalados; para o link público da sessão, `brew install cloudflared`. Para gerar um `ConestogaConnection.app`, rode `GERAR_APP.command`.

Para **gerar o executável** no Windows, execute `GERAR_EXE.bat` (requer Python no PATH). Ele instala as dependências (`requirements.txt` e `requirements-build.txt`), compila o programa e substitui `ConestogaConnection.exe` na pasta.

## Funcionalidades

As fórmulas usadas estão em **Ajuda > Regras usadas nos cálculos**.

### Ficha e cálculos

- Cálculo automático de Curva, Bônus de Combate, Vida, Mana, Vigor, CA, Carga, Movimento, Iniciativa, ações extras, Redução de Dano, Resistências, Descoberta, perícias, ataques, defesas e DTs.
- Pontos de atributo por nível, com painel de avisos para pendências.
- Assistente de criação de personagem, seguindo o capítulo "Criando seu Personagem" (o personagem novo entra no nível do grupo, com Caminho da Meta de Vida). No celular, o mesmo passo a passo.
- **Metas de Vida:** os 10 Caminhos do livro (com o Alquimista), com as 3 etapas em ordem e o mentor. Cada Meta concluída abre um slot de talento (M1–M5); a primeira dá +5 pontos de atributo.
- Clicar no nome de uma **perícia** mostra o que ela faz, o atributo, se exige treino e onde o livro a usa. Clicar no nome de um **atributo** mostra o que o valor atual dá na ficha. No celular, toque no nome (perícia: no Modo Edição).
- **Modo Edição e Modo Jogo.** Criar, subir de nível e escolher talentos, armas, encantamentos e equipamento só no Modo Edição (ficha nova abre nele). No Modo Jogo, usado na mesa, essas escolhas ficam travadas, e continuam liberados Vida/Mana/Vigor, rolagens, condições, Portão da Morte, inventário e anotações. Fichas abertas do disco começam no Modo Jogo.
- **Dados:** o botão 🎲 no topo do celular (e **🎲 Dados** no painel do mestre) rola qualquer expressão (`2d6+3`, `d20`, `4d8 - 1`), com d20 em vantagem ou desvantagem e a opção de crítico (dobra os dados). O histórico fica no diário da ficha. No painel do mestre, o **dano dos golpes dos inimigos é em dados** (por exemplo, um Animal de NMP 10 com `13d10` por golpe, no lugar de um número fixo) e o botão Atacar rola o acerto e o dano; o crítico dobra os dados.
- **Automático no celular (livro 3.3):** o Portão da Morte tem o botão "Rolar o d20 do turno" (marca sucesso ou falha, e com 5 sucessos volta com 1 de Vida e uma cicatriz); o **Estourar** da Adaga rola os dados pelos acúmulos de Sangria e zera o contador; o Machado Grande soma sozinho a **Fúria** (dano fixo pelos acúmulos e +1 nível de dano a cada 25% da vida perdida); o Ataque da Adaga oferece "＋1 Sangria".
- **Novidades do livro 3.3:** Adaga reformulada (Sangria e Estourar no lugar do Modo Frenesi), Espada com Guardas no lugar das Posturas (Riposte, Avanço, Abertura, Apoio e Linha de Frente), Katana com Aparar e Foco, Machado Grande com Fúria no lugar do Berserk, Espada Grande com Carregar e Golpe Carregado, Bastão com Posicionar, Colisão e Zona de Controle, Lâmina-Dínamo com o Modo Serra, Arco com Preparar Flecha, margens de crítico novas, talentos de estilo de arma reescritos, sets de condição aplicando 1d6, terreno difícil e o **Portão da Morte** novo: a morte vem com 3 falhas, mais 1 a cada 40 de Vitalidade, e a Medicina de um aliado sobe 10 de DT por cicatriz do Incapaz (a ficha, o painel do grupo e o app já usam isso).
- **Novidades do livro 3.2:** perícia **Alquimia** (poções; Kit de Alquimia, Colar do Herbolário e outros talismãs, talentos Destilador de Campo e Mestre Alquimista), 5 sets novos (50 no total), CA máxima 30, Agarrar e Derrubar como Fortitude do alvo contra a sua DT, Lira com Inteligência ou Fé à escolha (o programa usa o maior), Incapaz que nenhuma cura acorda e os tipos de dano Sangramento, Podridão e Congelamento. Poções de Mana e Vigor não têm mais limite por combate e as de nível 3 e 4 só saem por Alquimia (o preço aparece como "Feita por Alquimia" e não se compra).
- Comparação entre duas fichas.
- Dois temas góticos: **Catedral** (dia: pedra clara, roxo profundo, lilás e verde-claro, dourado e chumbo) e **Vigília** (noite: pedra quase preta e vitrais acesos). Rosácea no cabeçalho (gira a cada rolagem), faixa de vitral, nome e capitulares em letra gótica, quadrifólios nos títulos, cartões em arco ogival, barras de Vida/Mana/Vigor em vitral segmentado e a barra de abas em arcada. No celular, a Ficha › Resumo abre com a fachada: a foto (ou uma rosácea) entre lancetas e o nível em algarismos romanos.
- **Minha paleta** (menu do celular ou Exibir › Minha paleta no PC): cada pessoa escolhe 5 cores (pedra, moldura, destaque e dois vidros), clara ou escura, e o tema inteiro sai delas, com ajuste automático de contraste. Há modelos prontos (Catedral, Vigília, Rubi, Esmeralda, Âmbar, Abismo, Brasa) e um código `PAL-…` para passar a paleta a outra pessoa — o mesmo código serve no celular e no PC. A paleta fica no aparelho, não na ficha; o PDF e a folha impressa continuam na Catedral.
- A letra gótica vem embutida (KaTeX Fraktur, em `fontes/`); com internet, o celular usa Cinzel e UnifrakturMaguntia do Google Fonts.
- **Abas do celular:** cinco fixas na barra de baixo, cada uma com sub-abas presas no alto — **Ficha** (Resumo, Atributos, Espécie e alma), **Combate** (Turno, Armas, Magias, Defesas), **Saberes** (Perícias, Talentos, Grimório), **Bolsa** (Itens, Equipamento, Dinheiro) e **Diário** (Notas, Rolagens, Metas e vínculos); **Grupo** aparece na sessão. Cada seção abre e fecha (o app lembra), os textos de ajuda ficam atrás de um "?", o Modo Jogo/Edição virou um botão pequeno ao lado das sub-abas, e um ponto vermelho avisa quando é a sua vez (Combate), quando a carga passou do limite (Bolsa) e quando sobram pontos (Ficha). Dá para deslizar o dedo para os lados na página para ir à sub-aba seguinte (ou anterior); depois da última, passa para a próxima aba.
- **Layout de mesa** (celular, opcional; liga no menu ☰ com um botão de ligar e desligar): sub-aba **Combate › Turno** (que também existe com o modo desligado) com as ações do turno para tocar, favoritos (armas, encantamentos e perícias), usos e "Terminei meu turno" (vira um sinal para o mestre); a aba abre sozinha na sua vez. Vida, Mana, Vigor e condições ficam sempre no alto, e um **dado flutuante** abre iniciativa, a última rolagem, as perícias mais usadas e o dado livre (segure para o diário).
- Aba **Anotações** (PC e celular): pistas, nomes e combinados do jogador, guardados dentro da ficha.
- Exportação da ficha em PDF no visual Catedral (página em moldura de janela, rosáceas, lancetas e o nome em letra gótica), com as características de espécie (ajustes de atributo e par descritivo).

### Equipamento e build

- Menus de armas, encantamentos, talentos, armaduras, escudos, talismãs e sets, indicando o que está disponível e o motivo de cada restrição.
- **Propriedades de armas:** as 16 propriedades do livro, com o limite da arma (tabela do nível + Domínio). Os efeitos entram sozinhos (Afiada, Cruel e Poderosa no dano; Pesada sobe o dado e dobra a Força exigida; Certeira e Destruidora no crítico; Equilibrada no ataque; Elemental/Sagrada/Profana rolam o 1d6 extra; Reforçada aumenta o desgaste para 4; Voraz cura no crítico; Discreta dá +5 em Furtividade).
- **Talentos com escolha** (Maestria, Maestria dupla, Domínio, Matrícula, Matrícula avançada, Condição Endurecida, Mestre das Perícias): você escolhe a arma, a escola, a condição ou a perícia, e o efeito vale só para ela.
- **Encantamentos** com dados de condição já escalados pelo Arcano (cópias a cada 20, dados inferiores a cada 15), com Mente Arcana (+10 de Arcano) e Senhor das Condições (+1 cópia).
- **Sets** que aplicam pontos de condição (Sangria, Peçonha, Miasma, Geada, Delírio, Torpor, Gume) mostram os pontos em cada acerto ou crítico, com valor fixo (os números dos sets não escalam com o Arcano, como diz o livro).
- **Sets e talismãs automáticos:** ao pôr 2 (ou 4) peças do mesmo set, o set vale sozinho; ao tirar a peça ou o talismã, o efeito some. Entram nas contas: perícias, Reflexo/Fortitude/Vontade, CA, movimento, Mana e Vigor máximos, espaços de encantamento, contra-encantamentos, Redução de Dano por tipo (Pele de Ferro, Escama de Dragão, Casco...), acerto e dano nas rolagens de ataque e conjuração (incluindo dados extras, como Marca da Chama), custo de mana (Pergaminho do Oculto), cura por turno (Amuleto da Regeneração) e o descanso curto do Eremita. Efeitos que dependem de uma situação (Rancor com menos de 50% da vida, Insígnia do Berserker...) aparecem na aba Bolsa com um botão "Ligar agora". No PC entram só os que valem sempre; os interruptores e os que dependem do peso carregado ficam no app de celular.
- **Alma:** montador de habilidades pela Tabela de valores do livro (categorias, ajustes, execução), com valor e DT calculados; "Usar e rolar" gasta um uso e rola o dano.
- **Inventário** com a lista de Itens Diversos do livro (peso preenchido), quantidade e botão de usar consumíveis. A Mochila soma +5 de Carga; peças de set pesam 1.
- **Dinheiro** em Contos, prata, ouro e Contilha, com conversão e compra de itens do livro.

### Combate

- **Rolagens** de ataque, conjuração e perícias (1d20 a mais a cada 20 pontos do atributo, fica o maior), com consumo de Vigor e Mana. O diário guarda as 100 mais recentes na ficha.
- **Turno:** Comum, Bônus, Movimento e Reação mais as ações extras da Destreza. Ataques, encantamentos, itens e habilidades da Alma marcam a ação sozinhos e avisam quando não sobrava. Na sessão, o turno renova quando o mestre passa a vez e o combate quando ele rola a iniciativa ou o encerra.
- **Ações do livro** (Agarrar, Derrubar, Esconder, Provocar, Golpe de Oportunidade…) com a rolagem certa.
- **Ações das armas** como botões: "Usar" marca a ação do turno e "Rolar" ataca com os ajustes lidos do texto (níveis de dano, vantagem/desvantagem, crítico garantido, multiplicador, teste do alvo com a DT). Ações de vários disparos (Chuva de Flechas, Rajada Tripla, Combustão…) rolam cada disparo e descontam a munição. Há contadores da mecânica de cada arma (Momentum, Cartuchos, Flechas, Melodias…).
- **Defesas e Contradomínio:** rolar Fortitude, Reflexo, Vontade e Astúcia; Contradomínio com limite por combate (+2 com Contra-encantador); Coordenação do Uso duplo contra DT 8 + maior nível de arma.
- **Afiação das armas:** 3 turnos de uso (cada turno em que a arma ataca gasta 1, não importa quantos ataques; o turno é contado pelo Novo turno ou pela vez na sessão). O crítico reafia; a arma desgastada fica um turno parada e volta sozinha. Reforçada e Afiação Duradoura dão +1 turno cada.
- **Acerto das armas pela perícia de ataque:** Luta para as armas corpo a corpo, Pontaria para Arco e Besta Pesada, Feitiçaria ou Desejo para a Lira (pelo atributo). O cartão da arma mostra a perícia, e o bônus é o mesmo do teste da perícia (bônus de combate, nível ÷ 3, talentos, sets e talismãs, Mestre das Perícias) somado ao acerto da arma, à Maestria e às propriedades.
- **Teto de combate (3.3):** os bônus de efeitos (talentos, sets, talismãs, Mestre das Perícias, Maestria) somam no máximo +5 num ataque ou numa resistência; o excesso vira vantagem. Máximos: ataque +25, resistência +20.
- **Dados físicos** (☰ no celular, Exibir no PC): o app deixa de rolar e diz quantos e quais dados pegar em cada perícia, ataque, defesa e encantamento, com o bônus já somado (atributo, nível ÷ 3, acerto da arma, talentos, sets, talismãs, teto de combate), a vantagem (2d20, fica o maior), os dados extras (atributo, propriedades, Arcano, sets), o dano do crítico e quando o Sortudo / Sortudo maior permite rerrolar. Mana, Vigor, munição e afiação continuam sendo descontados; quando sai crítico, um toque reafia a arma.
- **Nível de dano e propriedades:** primeiro o nível de dano sobe na tabela (ações como Tiro Carregado, talentos, sets, talismãs e Fúria), depois entram os dados do atributo e as propriedades. Ex.: Arco nv 3 + Tiro Carregado = nível 5 (2d8); com Pesada, 2d10. O painel da ação mostra o dano antes de rolar.
- **Usos limitados:** talentos e talismãs "1x por combate/descanso" e os usos da Alma, recarregados no turno, no fim do combate e nos descansos.
- Descanso curto e longo (Vida, Mana, Vigor e barras de condição) e Poção Espiritual.

## Sessão de mesa

Liga o mestre aos jogadores. Existe uma única sessão por rede.

### Mestre

Abra **Sessão → "Entrar como mestre"**. O painel tem:

- **Cartão por jogador:** personagem, barras de Vida, Mana e Vigor, nível, CA, movimento, iniciativa, Portão da Morte, condições e se está no celular ou sem sinal. Atualiza sozinho.
- **Dano / Cura:** valor, tipo de dano do livro e descrição. A ficha do jogador desconta a RD e as resistências dele (Magia Pura e Relâmpago ignoram RD; "Direto" ignora tudo). Dá para marcar vários jogadores.
- **Efeito:** um dos efeitos do livro (Abalado, Caído, Exposto, Fragilizado, Paralisado…) com duração em turnos (0 = até o mestre remover). Fragilizado tira a RD e as resistências do dano recebido.
- **Condição:** pontos de Veneno, Podridão, Sangramento, Congelamento, Sono, Loucura ou Morte com a DT do inimigo. A ficha rola Fortitude ou Vontade, recebe metade num sucesso e, se a barra de 100 encher, aplica o efeito do livro.
- **Bolsa:** o mestre vê inventário, carga e dinheiro de cada jogador, dá e tira itens (do livro ou personalizados). O jogador é avisado.
- **Turnos:** "🎲 Iniciativa" rola a de todos e monta a ordem; "Passar turno ▶" avisa o jogador da vez e, depois do último, começa a rodada seguinte. As durações contam no fim do turno do afetado, e Veneno e Podridão tiram Vida no começo do turno. "Fim do combate" limpa a ordem e os efeitos de combate.
- **Mãos levantadas:** fila com "Dar a palavra", mais o registro do que o mestre enviou e dos jogadores rolaram.

### Jogador

- **No computador:** abra a ficha, depois **Sessão → "Entrar como jogador"**. O programa localiza o mestre; se não achar, informe o IP exibido na tela do mestre.
- **No celular:** aponte a câmera para o QR code da tela do mestre ou abra o endereço mostrado (`http://IP:5760`). Informe seu nome, abra ou crie a ficha e jogue. Não requer instalação nem internet. (A página antiga, só com o botão de mão, continua em `http://IP:5760/mao`.)

### Fichas da mesa (pasta `fichas/`)

Ao abrir a mesa, o programa cria a pasta `fichas/` ao lado dele, com um `.json` por jogador (`bruno.json`, `carol.json`, `kaua.json`, `enrico.json`, `guidi.json`), no mesmo formato que o app e o programa de PC abrem.

- **Entrar:** no celular, o jogador escolhe a ficha dele na lista que o mestre montou e cria (ou digita) o código dela. O celular baixa a ficha do notebook e a sessão segue como antes.
- **Salvar sozinho:** cada mudança na ficha (Vida, rolagens, itens, dano do mestre) volta ao notebook e grava no `.json` em poucos segundos.
- **Mestre muda o arquivo:** se você abrir o `.json` do jogador no programa de PC e salvar, o celular percebe a versão nova e baixa sozinho.
- **Atualizar minha ficha:** menu ☰ do celular, depois de escolher a ficha. Pega a ficha do app instalado (a editada em casa), pede confirmação e troca o `.json` do jogador no notebook.
- **Cópias de segurança:** ao abrir a mesa, `fichas/backup/sessao_DATA/` guarda todas as fichas; cada "Atualizar minha ficha" guarda a anterior em `fichas/backup/`.
- **Quem mudou por último vale.** A pasta `fichas/` está no `.gitignore`.
- **O mestre cuida da lista:** botão "📜 Fichas" na mesa do mestre. Ele cria fichas novas, importa um `.json`, abre qualquer ficha (é o próprio arquivo: ao salvar, o jogador recebe na hora), libera e exclui. Os cinco nomes de sempre continuam nascendo sozinhos; excluir um deles só esvazia a ficha. O jogador não cria mais fichas digitando um nome.
- **Dono da ficha:** quem escolhe uma ficha livre cria um código (3 a 12 caracteres). Ela fica presa a esse jogador: só entra de novo quem souber o código, até o mestre liberar. O mestre vê o código na janela de fichas. Enquanto um jogador conectado usa a ficha, ninguém mais entra nela.
- **Ficha vazia:** o jogador liga uma ficha que já tem (do aparelho, de um arquivo `.json`, do app instalado ou a que está aberta no PC) ou cria do zero.
- **No PC também:** o jogador do programa de PC escolhe a ficha ao entrar (conexão direta ou por link); a ficha da mesa troca a ficha aberta e cada mudança volta para o `.json` do mestre.
- **Foto do personagem:** fica dentro da ficha (384 px). No celular, botão "📷 Foto do personagem" no modo edição; no PC, clique no quadro "＋ foto" do cabeçalho (botão direito tira). Aparece na ficha, no PDF e na folha impressa, na lista de fichas ao entrar, no painel do Grupo e na tela do mestre. No PC, mostrar e converter fotos usa o Pillow (`requirements.txt`); sem ele só PNG ou GIF pequenos.

### Painel do mestre: inimigos, anotações e combate

Menu **Mestre → Inimigos, anotações e combate** (ou o botão **👹 Inimigos e anotações** na mesa do mestre) abre uma página no navegador **deste computador** (`http://127.0.0.1:5761`). Nenhum jogador consegue abrir: ela escuta só o endereço local. Funciona sem a sessão aberta, para você preparar o conteúdo antes.

- **Inimigos:** ao criar, escolha a **classe** (Lacaio, Comum, Forte, Animal, Prevalecente ou Deus) e o **nível** (NMP). Vida, CA, Ataque, DT, Postura, vida de condição e dano por turno saem da tabela do capítulo "Criando inimigos" (Animal, Prevalecente e Deus ajustam pelo número de jogadores). O resto é seu: golpes (com tipo de dano, acerto, dano e condição que aplicam), habilidades, Pontos Chave, resistências, imunidades, vulnerabilidades, afinidades de condição, Set e Drops, loot e anotações. Tudo vale só como ponto de partida e pode ser trocado.
- **Anotações:** várias anotações com título, etiqueta (NPC, Lugar, Enredo...), busca e fixar no topo; salvam sozinhas enquanto você escreve.
- **Iniciar combate:** o botão "⚔ Iniciar combate" pergunta quais inimigos e quantos de cada, quem da mesa entra e quem deu o primeiro golpe, rola a iniciativa e monta a **tabela de iniciativa** (ordem decrescente, quem age agora em destaque, o que cada um rolou, Vida de cada um e "Agora/Próximo"). Segue o livro: todos rolam 1d20 (mais 1d20 a cada 20 de Destreza), ficam com o maior e somam o Bônus de Combate de Destreza; quem empata rola de novo; o primeiro atacante rola com vantagem e age antes de a tabela começar a rodar. Os jogadores usam a ficha; os inimigos usam os "dados" e o "bônus" de iniciativa do cadastro (padrão 1d20 +0, já que o livro não dá Destreza a eles). Inimigo derrotado é pulado, e quem entra com o combate rolando já rola a própria iniciativa. O talento Animado (+1d20) já conta na ficha.
- **Combate:** escolha os inimigos (e quantos) e veja os jogadores e os inimigos lado a lado. Nos jogadores: dano, cura, condição e efeito, em um só ou nos marcados. Nos inimigos: dano (a resistência, a vulnerabilidade e a imunidade por tipo já entram), Postura (quebra com golpe corpo a corpo e deixa Exposto), barras de condição (ativam o efeito do livro e recarregam +50%), Pontos Chave revelados e golpes com rolagem de ataque contra a CA do jogador escolhido e botão para aplicar o dano. A iniciativa junta jogadores e inimigos, e "Passar turno" aplica o veneno, a podridão e as durações dos inimigos.
- **Onde fica:** pasta `mestre/` ao lado do programa (`inimigos.json`, `anotacoes.json`, `combate.json`). Está no `.gitignore`.

### Levar a ficha do app para a mesa (e de volta)

O jogador mantém a ficha no app instalado (GitHub Pages). Como um site `https` não pode enviar dados a `http://IP`, a ficha viaja no endereço (trecho `#f=` da URL, comprimido, lido só pelo navegador), sem servidor no meio.

- **App → mesa:** na página do mestre, toque em **📲 Trazer minha ficha do app** e, no app, em **Enviar** na ficha escolhida. Ela substitui a de mesmo nome. Também dá para usar **🛡 Entrar na mesa do mestre** no app, digitando o endereço.
- **Mesa → app:** no menu da página do mestre, **📲 Levar esta ficha de volta ao app** (o botão também aparece no aviso de fim de combate). A ficha de mesmo nome no app é substituída pela atual.
- Durante a sessão, a ficha da mesa recebe dano, cura, condições e itens; o app instalado só é atualizado por esse botão.
- O app instalado e a página da mesa guardam fichas em lugares separados. No iPhone, o app da Tela de Início e o Safari também têm armazenamento separado, então o app mostra o botão **⬇ Backup de todas as fichas** (um `.json`; "Abrir arquivo .json" restaura). Recomenda-se usar o app direto pelo Safari e fazer backup de vez em quando.

### Jogar de longe (internet)

Botão **🌐 Convidar** na mesa do mestre.

- **Mesa pela internet:** "Abrir a mesa para a internet" cria um link (túnel da Cloudflare, sem conta e sem mexer no roteador). No celular, é só abrir o link; no PC, o jogador cola o link em "link ou IP do mestre". Na primeira vez o programa pede para baixar o `cloudflared` (~65 MB) para `~/.prevalecentes`; se preferir, deixe `cloudflared.exe` ao lado do programa. O link muda a cada sessão.
- **Senha da mesa:** opcional na rede local, criada sozinha ao abrir para a internet (o link já a leva). Após 20 tentativas erradas em um minuto, a entrada trava por um minuto.
- **Chave por aparelho:** cada celular ou PC por link recebe uma chave ao entrar; sem ela ninguém lê nem age em nome de outro jogador.
- **Atualização na hora:** dano e vez chegam em menos de um segundo.
- **Reconexão automática:** o PC volta sozinho, com o mesmo nome, quando a conexão cai.
- **Mesa guardada:** rodada, ordem de turno, efeitos, fichas e eventos pendentes ficam em `~/.prevalecentes/sessao.json`. Se o PC do mestre fechar, ao entrar de novo (em até 12 horas) o programa oferece retomar.

### Grupo: interação entre os jogadores

Botão **👥 Grupo** no PC e aba **Grupo** no celular, durante a sessão.

- **Painel do grupo:** nome, barra de Vida, condições e de quem é a vez. Cada jogador escolhe o que mostra (tudo, só a barra ou nada).
- **Ajuda pelas regras:** Medicina no Portão da Morte (DT 15), Incentivar (Reação), curas e efeitos com alvo, refeição com Gastronomia (DT 10/20/30/40).
- **Trocas:** dar item ou dinheiro, espólio liberado pelo mestre (quem quer marca; empate no d20) e caixa do grupo com registro.
- **Rolagens:** feed com as rolagens de todos, reações rápidas e teste em grupo pedido pelo mestre.
- **Combinar o turno:** sinais, intenção para o próximo turno e sussurro entre dois jogadores (o mestre vê só o aviso, o texto inteiro, ou desliga).
- **Fora do combate:** vínculos entre dois personagens e diário do grupo.
- Tudo que muda a ficha de outro jogador vira um pedido, válido quando o destinatário (ou o mestre) aceita. O aceite automático vale só para ajudas; trocas sempre perguntam.
- O mestre liga e desliga cada recurso. Caixa, diário e vínculos ficam em `~/.prevalecentes/grupo.json`.

### Rede, segurança e comportamento

- **Firewall:** na primeira execução como mestre, o Windows pede permissão. Permita o acesso em redes privadas.
- **Portas:** 5757 (TCP), 5758 (UDP) e 5760 (HTTP).
- **Redes com isolamento** de dispositivos (Wi-Fi de visitantes, hotéis, escolas) impedem a conexão.
- **Sem senha na rede local:** qualquer pessoa na mesma rede que conheça o endereço pode entrar. Use a senha da mesa se precisar.
- **Papéis:** o programa não distingue mestre de jogador; apenas quem usa o botão de mestre recebe os avisos. Combinem que só o mestre o utilize.
- **O que o mestre recebe:** só o resumo da ficha (nome, espécie, nível, Vida, Mana, Vigor, CA, movimento, iniciativa, defesas, RD, resistências, Portão da Morte, barras de condição, inventário, carga e dinheiro), a cada ~1,5 s. Ele não edita a ficha do jogador: envia dano, cura, condições e itens.
- **Entrega confiável:** os eventos do mestre são repetidos até o celular confirmar, então não se perdem se a tela bloquear ou o Wi-Fi cair.
- **Tela bloqueada:** o mestre vê "(sem sinal)" ao lado do nome após 20 s e a mão continua na fila. Após 10 min sem contato, o jogador sai da mesa e perde também a vez na iniciativa, os efeitos e o resumo.
- **Conexão perdida:** o jogador no PC vê o aviso e um botão para reconectar. Se o mestre não for encontrado, o programa sugere o último IP usado.

## App de celular

Ficha de mesa para o celular: Vida, Mana e Vigor, atributos, características, perícias, armas com ações, rolagens, grimório, talentos e bolsa. Tem as mesmas funções de mesa do PC (turno, usos, Alma, Metas de Vida, dinheiro, diário, Modo Jogo/Edição) e "🖨 Imprimir / salvar PDF" no menu. Abre os mesmos arquivos `.json` do PC e funciona sem internet depois de instalado.

- **Instalar no Android:** <https://grnguidi.github.io/FichaPreval/> no Chrome → ⋮ → "Instalar app" (ou "Adicionar à tela inicial").
- **PC → celular:** "Abrir arquivo .json" carrega uma ficha salva pelo PC. As fichas ficam guardadas no aparelho.
- **Celular → PC:** menu ☰ → Exportar ficha (.json). A ficha vai e volta sem perder nada.

## Desenvolvimento

**App de celular:** o código está em `celular/src/js/`, em arquivos numerados por área (armazenamento, cálculo, telas, ações, mesa, rolagens, menu, sessão, eventos). O `celular/build.py` junta todos no mesmo escopo, na ordem do nome. Depois de mudar algo, rode:

```
py celular/build.py
```

Isso gera a pasta `docs/` (publicada pelo GitHub Pages) e o `pagina_celular.py` (a mesma ficha, servida pelo PC do mestre). Os dados do livro e a tabela de efeitos de talento vêm de `dados_prevalecentes.py` e `regras.py`, então PC e celular continuam iguais.

**Testes:**

```
sh celular/testes/rodar.sh        # regras do celular iguais às do PC (requer Node.js)
python testes/test_sessao.py      # entrega e confirmação de eventos, limpeza de quem sai
python testes/test_grupo.py       # interação entre jogadores
python testes/test_conexao.py     # conexão
python testes/test_fichas.py       # pasta fichas/: escolha, gravação, conflito e atualização
python testes/test_mestre.py       # painel do mestre: inimigos, anotações e combate
```

Os mesmos testes rodam no GitHub Actions a cada push (`.github/workflows/ci.yml`), que também confere se `docs/` e `pagina_celular.py` estão atualizados com o `celular/build.py`. Veja `celular/testes/LEIAME.md` para o que cada comparador cobre.

**Contribuindo:** rode os testes acima antes de abrir um PR; se mexer em `celular/src/` ou `regras.py`, rode `py celular/build.py` e inclua o resultado no commit. O `cloudflared` usado pela mesa pela internet tem versão e SHA-256 fixos em `tunel.py`: ao atualizar a versão, troque os dois juntos.

## Dados do livro e fichas salvas

- **Dados do livro:** armas, encantamentos e talentos estão embutidos (`dados_prevalecentes.py`). Para corrigir algum, edite uma cópia de `dados_livro (para editar).json`, renomeie para `dados_prevalecentes.json` e coloque ao lado do executável; ele passa a ser usado no lugar dos dados embutidos.
- **Fichas:** salvas manualmente em `.json` (Ctrl+S) e abertas com Ctrl+O. O programa não reabre a última ficha automaticamente.

## Estrutura do projeto

| Arquivo | Descrição |
|---|---|
| `prevalecentes.py` | Programa principal e interface |
| `regras.py` | Cálculos das regras, sem interface |
| `regras_texto.py` | Texto da janela "Regras usadas nos cálculos" |
| `assistente.py` | Assistente de criação de personagem |
| `pdf_ficha.py` | Exportação para PDF |
| `sessao.py` | Sessão em rede e painel do mestre |
| `ponte_sessao.py` | Liga a ficha do PC aberta à sessão (resumo e eventos do mestre) |
| `grupo.py`, `grupo_ui.py` | Interação entre jogadores (servidor e janelas) |
| `fichas_mesa.py` | Pasta `fichas/` com um .json por jogador (lê, grava, versão e backup) |
| `fichas_ui.py` | Janelas das fichas da mesa no PC (mestre: criar, abrir, liberar; jogador: escolher e sincronizar) |
| `foto.py` | Foto do personagem (lê, reduz e mostra a imagem) |
| `bestiario.py`, `mestre_dados.py`, `mestre_web.py`, `pagina_mestre.py` | Painel do mestre: números do bestiário, dados, servidor local e página |
| `tunel.py` | Mesa pela internet (túnel com o cloudflared) |
| `pagina_celular.py` | Ficha do celular servida pelo mestre (gerado por `celular/build.py`) |
| `dados_prevalecentes.py` | Dados do livro embutidos |
| `dados_livro (para editar).json` | Cópia editável dos dados do livro |
| `GERAR_EXE.bat` | Gera o executável |
| `celular/` | Código do app de celular (`src/js/` e `build.py`) |
| `docs/` | App de celular pronto, publicado pelo GitHub Pages |
| `testes/` | Testes de sessão, grupo e conexão |
| `exemplos/` | Ficha de exemplo (`ficha_exemplo.json`) |
| `.github/workflows/ci.yml` | Testes automáticos a cada push |
| `requirements.txt` | Dependências do Python |
