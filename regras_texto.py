# -*- coding: utf-8 -*-
"""Texto da janela "Regras usadas nos cálculos" (menu Ajuda)."""
REGRAS_TXT = """Fórmulas (PREVA 3.4)

Atributos: distribuição inicial 16/14/12/11/10/9/8/7; +10 pontos por nível e +5 extras em níveis múltiplos de 3 (nível máx. 30).
Sem alma ("Jogando sem uma Alma"): +2 pontos de atributo a mais por nível, e a aba Alma não é usada.
Acima de 99 conta como 99 nas tabelas.
Curva: +1 a cada 5 pontos até 20; +2 a cada 5 de 25 a 35; +3 de 40 a 55; +4 de 60 a 75; +5 de 80 a 95; +2 no 99 (99 = 60).
Bônus de Combate: +1 a cada 20 pontos (99 = +5). Vantagem (2d20) com 60+.

Vida = 10 + 5 por nível acima do 1º + (Curva da VIT) dados de 1d12 (ou 7 fixo por dado).
Mana = 2 × Mente + 2 × Curva da Mente.
Vigor = 20 + Força + Curva da Força. Recupera Curva da Força ÷ 4 por turno. Armas de Vigor: 5 por ataque, 8 a partir do nv 4, 10 a partir do nv 8.
Descoberta = 10 + 10 a cada 15 de Arcano.
CA = 10 + armadura + escudo + 1 a cada 20 TEN (máx. +4); mínima 10, máxima 30 (o que passar é perdido).
Teto de combate: bônus fixos de talentos, talismãs, sets, refeições, encantamentos e habilidades de arma somam no máximo +5 a ataque, CA ou resistência
(Bônus de Combate, nível/3, acerto da arma, condições e posturas ficam fora). Máximos finais: ataque +25, resistência +20, DT 25, CA 30.
Carga = 10 + 2 × TEN + FOR ÷ 2 + Curva da TEN. Lentidão a partir de metade; Exaustão com 10 ou menos livres.
Movimento = 9 m; +3 m aos 30 de DES e a cada 15 acima.
Ações extras: 1 a cada um destes valores de DES: 15, 30, 45, 55, 65, 75, 85, 95.
Cada ação extra é Comum ou Bônus, escolhida uma vez e fixa.
Conjurar: 1d20 + BC + nível ÷ 3 + acerto do cajado/selo (o mesmo da arma do nível).
Provocar: Vontade do alvo contra 10 + BC de Força + nível ÷ 3 + 3.
Agarrar e Derrubar: Fortitude do alvo contra 10 + BC de Força + nível ÷ 3 (quem é agarrado repete o teste no início do turno, com ação de movimento).
Contradomínio: 1d20 + BC (INT ou Fé) + nível ÷ 3; 1 por combate a cada 10 de INT ou Fé.
Coordenação (Uso duplo): DES (ou ARC ao conjurar) contra DT 8 + maior nível de arma.
Alma: valor da Tabela no nível da alma + ajustes − 1 por categoria a mais (0 a 11).
Meta de Vida: +1 talento por Meta concluída; a primeira dá +5 pontos de atributo.
Dinheiro: 10 Contos = 1 de prata; 100 de prata = 1 de ouro; 1000 de ouro = 1 Contilha.
Iniciativa: 1d20 + 1d20 a cada 20 DES (fica com o maior) + BC de DES.
Redução de Dano: 1d4 a cada 20 TEN (máx. 4d4). Resistências por TEN: 20 Fogo … 90 Sagrado.

Perícias fora de combate: nível/2, + Curva do atributo se treinada; +1d20 a cada 20 pontos no atributo.
Atributos das perícias (3.2): Agricultura (Horta e Pasto), Alquimia e Navegação usam Inteligência; Tática usa Inteligência ou Mente (o maior).
Alquimia exige treino; Gastronomia (INT/DES) e Navegação não exigem.
Treinadas: 1 de ataque + 5 fora de combate, +1 a cada 10 em INT ou MEN (o programa usa o maior dos dois).
Ataque: 1d20 + BC + nível/3 + acerto da arma (nv1 +0 … nv10 +5). Defesa: 1d20 + BC + nível/3.
DT (encantamentos, alma, armas) = 10 + BC + nível/3.

Armas: nível máximo = metade do nível do personagem, arredondado para cima. +1 dado de dano a cada 30 no atributo de ataque.
Uso duplo: em cada atributo, maior requisito + metade do outro. Coordenação: DT 8 + maior nível.

Encantamentos: Espaços = 1 + 1 a cada 6 pontos de INT + FÉ somados. Versão de nível N exige o atributo da tabela
(10/15/25/30/40/45/55/65/75/85) e personagem de nível 2 × N (nível 1 com cajado/selo inicial). Conjurar exige cajado (Magia)
ou selo (Feitiço) de nível igual ou maior. Teste de aprendizado: DT 15 + 3 por nível acima do 1º.
+1 dado de dano a cada 30 de INT (Magias) / FÉ (Feitiços). Contra-encantamentos: 1 a cada 10 em INT ou FÉ (o maior).

Alma: nível = nível do personagem ÷ 3. Usos por descanso longo = 2 + nível da alma ÷ 3. Nova ativa nos níveis 10, 20 e 30.

Descanso curto: recupera metade de Vida, Mana e Vigor e tira 25 pontos de cada condição (máx. 2 entre descansos longos).
Descanso longo: recupera tudo e zera as condições (remove também efeitos Fracos e Médios; Forte e Extremo continuam). Poção Espiritual: (½ nível + ½ Curva da VIT) d10 de Vida, mínimo 2 dados.
Incapaz (Vida 0): nenhuma cura, nem a Poção Espiritual, acorda um Incapaz; só os testes para escapar da morte.
Portão da Morte (3.3): 5 sucessos salvam; a morte vem com 3 falhas + 1 a cada 40 de Vitalidade. Cada cicatriz já começa com uma falha (até uma a menos que o limite). Medicina de um aliado: DT 15 + 10 por cicatriz do Incapaz.
Terreno difícil (3.3): cada 1,5 m nele custa 3 m do movimento (soma com outros custos, como a Zona de Controle do Bastão). Empurrões, puxões e Posicionar não são afetados.
Poções (Alquimia): não restauram Vida (só vida temporária); Mana e Vigor sem limite por combate (o freio é a ação, a Carga e o preço); Elixires: 1 por descanso longo.
Itens diversos: sem limite de quantidade; quem limita é a Carga.
Afiação: 3 turnos de uso por arma (cada turno em que ela ataca conta 1, não importa quantos ataques); o crítico reafia; ao acabar, a arma fica 1 turno sem uso. Reforçada e Afiação Duradoura dão +1 cada.
Arcano nas condições: a cada 20 de ARC, uma cópia dos dados de condição do encantamento; a cada 15, +1 dado um tamanho
abaixo (d12→d10→d8→d6→d4). Morte só recebe os dados inferiores. Valores fixos não copiam.
Condições: barra de 100 por condição. Pontos de inimigo: teste de Fortitude (Veneno, Podridão, Sangramento, Congelamento)
ou Vontade (Sono, Loucura, Morte) contra a DT; sucesso recebe metade. Ao encher, o efeito ativa e a barra volta a zero.
Dano recebido: rola a RD (1d4 a cada 20 TEN) e depois a resistência corta pela metade. Magia Pura e Relâmpago ignoram RD.
Carga: Capacete, Manopla, Calça e Bota de set pesam 1 cada; a Mochila aumenta a Carga em 5.
Talentos com escolha: Maestria/Maestria dupla +1 de ataque só na arma escolhida; Domínio +1 propriedade na arma escolhida
(+1 com Arma de família); Matrícula −1 Mana e −1 espaço na escola escolhida (mínimo 1), Matrícula avançada −2 de Mana
ou uma segunda escola, Matrícula Suprema vale para todas (até −3); Condição Endurecida +20 na barra escolhida;
Mestre das Perícias +2 e 1 vantagem na perícia escolhida.
Propriedades de armas: limite = tabela da arma no nível + Domínio. Afiada +1 dado; Cruel +3; Poderosa +2 (exige Cruel);
Pesada dado um nível acima (d12: +1 dado) e o dobro de Força; Certeira margem −1; Destruidora crítico ×3; Equilibrada +1 ataque;
Elemental/Sagrada/Profana +1d6; Reforçada desgaste 4; Voraz cura 1d10 no crítico; Discreta +5 Furtividade.
Talismãs: 1 espaço + 1 a cada 6 níveis (máx. 5).
Versões de encantamento: as superiores costumam custar mais Mana, mas versões de utilidade podem custar menos; vale o custo escrito.
Lira: atributo de ataque, requisito e perícia são Inteligência ou Fé, à escolha (o programa usa o maior dos dois).

Novidades do livro 3.4 (só referência, o programa não calcula):
Ambiente e Perigos: grau Leve / Moderado / Grave = DT 10 / 15 / 20 + NMP ÷ 3 e dano de 5% / 15% / 30% da vida máxima
(passou no teste: metade). Frio: falha põe 25 na barra de Congelamento. Calor: 1ª falha deixa Lento, 2ª seguida causa o dano.
Em chamas: 5% da vida máxima de Fogo no início do turno; apagar = ação comum (Reflexo DT Leve). Penumbra: −2 à distância
e em Percepção visual além de 9 m; escuridão total = Cegueira. Armadilhas: achar (Percepção) e desarmar (Tecnologia, ação
completa) contra a DT do grau; falhar por 5 ou mais dispara.
Perda de Membros: um único golpe com dano final ≥ metade da vida máxima remove 1 membro (role 1d8: olhos, mãos, braços,
pernas). Danos mentais, Veneno, Sangramento, Podridão e Congelamento não removem. Visão Parcial −2 à distância e em
Percepção visual; Mão Única sem uso duplo nem escudo com arma, duas mãos −4 de acerto e −1 dado; Perneta deslocamento
pela metade e −2 em Reflexo e Atletismo. A perda é permanente.
Montarias: montar/desmontar = ação de movimento (3 m). Montado, usa o deslocamento da montaria; comandar um ataque dela
custa sua ação de movimento. Investida de 6 m em linha reta: +1 dado no 1º ataque corpo a corpo; à distância em movimento −2.
Cultos e Igrejas: com Fé 20 ou mais, o personagem funda um Culto (Grau 1 a 5) e converte comunidades por Conflito Social.
Cada Tema dá Bênção, Prece (1 por descanso longo) e Milagre (1 por Andar); os bônus contam para o teto de +5.
Novo talismã: Olho Caído Putrefato.

Talentos aplicados automaticamente: Vida Dura, Fôlego de Guerreiro, Mochileiro, Mula de Carga, Cabeça Cheia, Mente Expandida,
Pé Ligeiro, Pele Grossa, Mão Extra, Mente Infinita, Treinado, Colecionador de Talismãs, Relicário, Veterano de Armadura,
Mãos Gêmeas, Empunhadura Folgada e os +2 de defesa (Fortitude de Ferro, Reflexos de Gato, Mente Blindada, Vontade Inabalável).

Os dados de armas, encantamentos e talentos vêm do livro. Para corrigir algo, coloque um arquivo dados_prevalecentes.json
ao lado do programa (mesmo formato) e ele será usado no lugar dos dados embutidos.
"""
