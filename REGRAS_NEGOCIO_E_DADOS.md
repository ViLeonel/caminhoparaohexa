# REGRAS DE NEGÓCIO E DADOS

## Posições oficiais
Goleiro; Lateral-direito; Lateral-esquerdo; Zagueiro; Volante;
Mezzala esquerdo; Mezzala direito; Meia-esquerda; Meia-direita;
Meia-armador; Ponta-esquerda; Ponta-direita; Segundo atacante; Centroavante.

## Convocação
- 11 titulares.
- Até 15 reservas.
- Máximo de 26 convocados.
- Nenhum atleta pode ocupar mais de uma vaga.
- Titulares devem respeitar compatibilidade tática.
- Reservas não podem repetir titulares.

## Avaliações
- Escala editorial de 0 a 10.
- Notas de Vini e Beto são independentes.
- Avaliações trimestrais devem registrar performance, condição e síntese da conversa.
- A nota numérica não substitui o histórico qualitativo.

## Mercado
- Valor atual e valor máximo são dados auxiliares.
- Calcular percentual do pico apenas quando o pico for maior que zero.
- Ausência de dado não deve virar zero em análises comparativas.
- Datas conflitantes devem ser preservadas e sinalizadas, nunca reinterpretadas silenciosamente.

## Persistência
- JSON é a fonte canônica temporária.
- Alterações feitas apenas na instância do Streamlit Cloud podem ser perdidas em reinícios.
- Enquanto não houver banco externo, mudanças permanentes devem ser versionadas no GitHub.

## Concorrência e versionamento
- Toda sessão deve salvar usando a versão lida da fonte.
- Se a fonte mudar após o carregamento, a escrita deve ser recusada.
- Conflitos nunca devem ser resolvidos por sobrescrita silenciosa.
- A sessão que falhar não pode atualizar seu estado local como se tivesse salvo.
- Escritas devem ocorrer sob bloqueio curto, com arquivo temporário, validação e backup.
- Hash, data UTC e origem da última alteração devem ser registrados separadamente.

## Auditoria

- Eventos operacionais ficam fora do JSON canônico dos jogadores.
- Cada evento é imutável e identifica atleta, campo, valores, origem, data e versões.
- Campos sem alteração não devem gerar novo evento.
- Falha de persistência canônica não pode produzir evento de auditoria.
- O histórico operacional não substitui o campo editorial `historico`.
