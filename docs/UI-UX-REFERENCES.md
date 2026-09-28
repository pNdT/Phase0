# Referências e decisões de UI/UX

Consulta em 26 de setembro de 2026. Esta pesquisa foi feita para melhorar a interface do Phase 0; os conectores automáticos do produto continuam nas etapas previstas do roadmap.

## Fontes consultadas

- [Mobbin — página pública de referências](https://mobbin.com/): organização de referências em telas, elementos de interface e fluxos; categorias como sidebar, tabs, progress indicators e chatting. A consulta não incluiu uma avaliação completa de telas de produtos do catálogo.
- [Uiverse — inputs](https://uiverse.io/inputs): catálogo de campos como referência para o componente de entrada. Não foi importado código de um componente específico.
- [21st.dev — AI Components for React: Choose the Right Layer](https://docs.21st.dev/blog/ai-components-for-react): separação entre campo de entrada, conversa e runtime, com orientação para considerar estados de carregamento e uso por teclado.

As escolhas abaixo são propostas de design para este projeto, informadas por essas referências e pelo feedback do usuário. Não são regras atribuídas aos hubs.

## Direção visual

Após as revisões, o usuário pediu mais profundidade, sem cores pastel, e aceitou mais de uma cor desde que o conjunto seja sutil. A direção atual usa azul na estrutura, verde nas áreas de projetos e estados, e cobre em detalhes e ações. Superfícies sólidas, texto com contraste, bordas discretas e cantos moderados, sem gradientes, estrelas decorativas ou slogans. Não aplicar cores diferentes a cada cartão.

A tipografia usa Segoe UI no Windows, com fontes de sistema como alternativas. São as fontes efetivamente usadas pelo aplicativo; não há download de fontes nem CDN. A hierarquia vem de tamanho, peso e espaçamento.

## Organização e interação

- Conversa como área principal, com campo de mensagem persistente dentro do painel.
- Notas de requisitos em lista, sem cartões de cores alternadas. Podem ser recolhidas em qualquer tamanho de tela; começam recolhidas em janelas menores.
- Biblioteca de fontes com lista pesquisável e estado de integração explícito.
- Criação de projetos e escolha de modelo no fluxo da página, sem modais.
- Controles de expansão fecham ao serem acionados novamente. Selecionar um projeto ou modelo fecha o seletor.
- Navegação por teclado, foco visível, rótulos acessíveis e respeito à preferência por movimento reduzido.

## Validação desta revisão

Sintaxe do JavaScript verificada. No navegador, foram verificados a abertura e fechamento das notas, a alternância entre conversa e fontes, a busca na biblioteca e o recolhimento dos controles. A largura do conteúdo correspondeu à largura disponível na janela observada, sem overflow horizontal. Projetos existentes foram preservados.

Próxima validação de UX: observar usuários reais tentando começar um projeto, encontrar uma informação e corrigir um requisito. Referências visuais e verificações técnicas não substituem essa observação.
