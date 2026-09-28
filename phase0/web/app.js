const $ = id => document.getElementById(id);
const token = document.querySelector('meta[name="phase0-token"]').content;
const labels = {product:'Product & audience',platform:'Platform',features:'First-version features',budget:'Budget',geography:'Business & user geography',monetization:'Monetization',technical_comfort:'Technical comfort',scale:'Expected usage',privacy:'Privacy & deployment',integrations:'Integrations & AI'};
let project = null, busy = false, selectedModel = '', models = [], projects = [], hubs = null, toolCatalog = {}, currentView = 'chat';
let notesManuallySet = false;
const compactLayout = window.matchMedia('(max-width: 1000px)');
function showNotes(open) {
  disclosure('profile-toggle','profile-panel',open);
  $('discovery-section').classList.toggle('notes-hidden',!open);
}
async function api(path, body) {
  const response = await fetch(path, {method: body === undefined ? 'GET' : 'POST', headers: {'X-Phase0-Token':token,'Content-Type':'application/json'}, ...(body === undefined ? {} : {body:JSON.stringify(body)})});
  const result = await response.json();
  if (!response.ok) throw new Error(result.error || 'Request failed.');
  return result;
}
function error(message) { $('error').textContent=message; $('error').hidden=!message; }
function element(tag, cls, content) { const node=document.createElement(tag); if(cls)node.className=cls; if(content!==undefined)node.textContent=content; return node; }
function disclosure(button, panel, open) { $(panel).hidden=!open; $(button).setAttribute('aria-expanded',String(open)); }
function setBusy(value) {
  busy=value;
  ['send','message','new-project','model','refresh','create-button','project-title','research-online'].forEach(id=>$(id).disabled=value);
  document.querySelectorAll('.project-choice,.model-choice').forEach(button=>button.disabled=value);
  $('waiting').textContent=value?'Ollama: understanding, researching and comparing… this may take a few minutes.':'Ctrl + Enter to send';
  $('send').textContent=value?'Processing…':'Send message ↑';
}
function render() {
  $('project-name').textContent=project?.name || 'Untitled project';
  $('messages').replaceChildren();
  const messages=project?.messages || [];
  if(!messages.length) {
    const welcome=element('div','welcome');
    welcome.append(element('span','welcome-kicker','SOFTWARE & VIBECODING'),element('h2','','What are you building?'),element('p','','Describe your product, features and constraints. Ollama will choose public searches, compare compatible tools and prepare a dossier with a stack, sources and build prompts. Unknown requirements stay explicit.'));
    const tips=element('div','idea-tips');['Purpose','Audience','Budget & constraints'].forEach(tip=>tips.append(element('span','',tip)));welcome.append(tips);$('messages').append(welcome);
  }
  messages.forEach(m=>{const node=element('article','message '+m.role);node.append(element('div','message-role',m.role==='user'?'YOU':'PHASE 0'),element('p','',m.content));$('messages').append(node);});
  $('messages').scrollTop=messages.length?$('messages').scrollHeight:0;
  $('profile').replaceChildren();let count=0;
  Object.entries(labels).forEach(([key,label])=>{const fact=project?.profile[key];const node=element('div','fact');node.append(element('div','fact-label',label),element('p',fact?.value?'':'unknown',fact?.value || 'Not defined'));if(fact?.value){count++;const details=element('details','');details.append(element('summary','','View source message'),element('p','evidence',fact.evidence));node.append(details);} $('profile').append(node);});
  $('progress-bar').style.width=(count*10)+'%';$('progress-text').textContent=`${count} of 10 areas covered`;$('notes-count').textContent=`${count}/10`;$('export').disabled=!project;
  $('send').textContent='Send message ↑';
  renderProjects();
  renderDossier();
}
function renderProjects() {
  $('projects').replaceChildren();
  if(!projects.length)$('projects').append(element('p','empty-projects','No saved projects yet.'));
  projects.forEach(p=>{const button=element('button','project-choice',p.name);button.type='button';button.title=p.name;button.disabled=busy;button.setAttribute('aria-pressed',String(p.id===project?.id));button.onclick=async()=>{if(busy)return;try{project=await api('/api/projects/'+p.id);render();error('');showView(false);disclosure('project-picker','projects',false);}catch(e){error(e.message);}};$('projects').append(button);});
}
async function refreshProjects(){projects=await api('/api/projects');renderProjects();}
function renderModels() {
  $('model-name').textContent=selectedModel || 'No local model found';
  $('model-options').replaceChildren();
  if(!models.length)$('model-options').append(element('p','muted','Start Ollama and install a chat model, then refresh.'));
  models.forEach(name=>{const button=element('button','model-choice',name);button.type='button';button.disabled=busy;button.setAttribute('aria-pressed',String(name===selectedModel));button.onclick=()=>{selectedModel=name;renderModels();disclosure('model','model-options',false);$('model').focus();};$('model-options').append(button);});
}
async function connection() {
  const status=await api('/api/status');models=status.models;
  if(!models.includes(selectedModel))selectedModel=models[0] || '';
  $('status').textContent=status.ollama==='ready'?(models.length?'● Ollama connected':'○ Install a local chat model'):'○ Ollama is offline';
  renderModels();
  if(status.ollama!=='ready')error('Start Ollama, then refresh the connection.');else if(!models.length)error('Install a local chat model with Ollama, then refresh.');else error('');
}
function showView(view) {
  if(typeof view==='boolean')view=view?'sources':'chat';
  currentView=view;
  const sources=view==='sources';
  $('discovery-section').hidden=view!=='chat';$('hubs-section').hidden=!sources;$('dossier-section').hidden=view!=='dossier';
  $('profile-toggle').hidden=view!=='chat';
  ['sources-tab','show-hubs'].forEach(id=>$(id).setAttribute('aria-expanded',String(sources)));
  [['sources-tab','sources'],['discovery-tab','chat'],['dossier-tab','dossier']].forEach(([id,name])=>{$(id).setAttribute('aria-pressed',String(view===name));$(id).classList.toggle('active',view===name);});
}
function renderHubs() {
  const search=$('hub-search').value.trim().toLowerCase();
  const matches=(hubs || []).filter(h=>(h.name+' '+h.category).toLowerCase().includes(search));
  $('hubs-list').replaceChildren();
  matches.forEach(h=>{const card=element('article','hub');card.append(element('span','hub-category',h.category),element('h3','',h.name),element('span','hub-status',h.status.startsWith('active')?'Active public connector':'Planned'));if(h.status.includes(';'))card.append(element('p','muted',h.status.split(';').slice(1).join(';').trim()));$('hubs-list').append(card);});
  $('hub-results').textContent=`${matches.length} of ${(hubs || []).length} sources`;
  if(!matches.length)$('hubs-list').append(element('p','muted','No matches yet. Try a different name or category.'));
}
async function toggleSources() {
  const opening=$('hubs-section').hidden;
  showView(opening);
  if(!opening)return;
  if(!hubs){$('hub-results').textContent='Loading your source collection…';try{hubs=await api('/api/hubs');$('source-count').textContent=hubs.length;}catch(e){error(e.message);$('hub-results').textContent='Unable to load sources. Close and reopen to retry.';return;}}
  renderHubs();
}
$('new-project').onclick=()=>{const open=$('create-project').hidden;disclosure('new-project','create-project',open);if(open)$('project-title').focus();};
$('cancel-project').onclick=()=>{disclosure('new-project','create-project',false);$('new-project').focus();};
$('create-project').onsubmit=async event=>{event.preventDefault();if(busy)return;const name=$('project-title').value.trim();if(!name){$('project-title').focus();return;}setBusy(true);try{project=await api('/api/projects',{name});await refreshProjects();render();$('project-title').value='';disclosure('new-project','create-project',false);showView(false);error('');}catch(e){error(e.message);}finally{setBusy(false);$('message').focus();}};
$('project-picker').onclick=()=>disclosure('project-picker','projects',$('projects').hidden);
$('profile-toggle').onclick=()=>{notesManuallySet=true;showNotes($('profile-panel').hidden);};
compactLayout.addEventListener('change',event=>{if(!notesManuallySet)showNotes(!event.matches);});
$('model').onclick=()=>disclosure('model','model-options',$('model-options').hidden);
$('refresh').onclick=()=>connection().catch(e=>error(e.message));
$('chat-form').onsubmit=async event=>{event.preventDefault();if(busy)return;const message=$('message').value.trim();if(!message)return;if(!selectedModel){error('Connect Ollama and choose a local model first.');return;}disclosure('model','model-options',false);setBusy(true);error('');try{if(!project){project=await api('/api/projects',{name:message.slice(0,60)});await refreshProjects();}const previous=project.dossier?.created_at;project=await api(`/api/projects/${project.id}/chat`,{message,model:selectedModel,research_online:$('research-online').checked});$('message').value='';render();if(project.dossier && project.dossier.created_at!==previous){showView('dossier');$('dossier-title').setAttribute('tabindex','-1');$('dossier-title').focus();}if(project.rejected_updates?.length)error('Could not validate updates for: '+project.rejected_updates.map(key=>labels[key]||key).join(', ')+'. Previous notes were kept; review the source quotes.');}catch(e){error(e.message);}finally{setBusy(false);if(currentView==='chat')$('message').focus();}};
$('send').onclick=event=>{event.preventDefault();$('chat-form').requestSubmit();};
$('message').onkeydown=event=>{if(event.key==='Enter'&&(event.ctrlKey||event.metaKey)){event.preventDefault();$('chat-form').requestSubmit();}};
$('export').onclick=()=>{if(!project)return;const content={schema_version:1,stage:'discovery',exported_at:new Date().toISOString(),project};const url=URL.createObjectURL(new Blob([JSON.stringify(content,null,2)],{type:'application/json'}));const link=element('a');link.href=url;link.download='phase0-discovery.json';link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);};
$('show-hubs').onclick=toggleSources;$('sources-tab').onclick=toggleSources;$('discovery-tab').onclick=()=>showView(false);$('close-hubs').onclick=()=>{showView(false);$('discovery-tab').focus();};$('hub-search').oninput=renderHubs;
$('dossier-tab').onclick=()=>showView(currentView==='dossier'?'chat':'dossier');
$('refine-dossier').onclick=()=>{showView('chat');$('message').focus();};
$('export-dossier').onclick=()=>{if(!project?.dossier)return;downloadJSON({schema_version:1,project_name:project.name,dossier:project.dossier},'phase0-dossier.json');};
document.addEventListener('keydown',event=>{if(event.key==='Escape'){disclosure('model','model-options',false);disclosure('new-project','create-project',false);if(!$('hubs-section').hidden){showView(false);$('sources-tab').focus();}}});
function downloadJSON(content,name){const url=URL.createObjectURL(new Blob([JSON.stringify(content,null,2)],{type:'application/json'}));const link=element('a');link.href=url;link.download=name;link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}
function sourceLink(label,url){const link=element('a','source-link',label);if(typeof url==='string'&&url.startsWith('https://')){link.href=url;link.target='_blank';link.rel='noopener noreferrer';}return link;}
function listItems(items){const list=element('ul','dossier-list');items.forEach(item=>list.append(element('li','',item)));return list;}
function dossierSection(title){const section=element('section','dossier-section');section.append(element('h3','',title));$('dossier-content').append(section);return section;}
function renderDossier(){
  const d=project?.dossier;const root=$('dossier-content');root.replaceChildren();$('export-dossier').disabled=!d;
  if(!d){$('dossier-subtitle').textContent='Describe your product in the chat to start.';root.append(element('p','dossier-empty','Your plan will appear here automatically, including the research trail and ready-to-copy prompts.'));return;}
  const pt=d.language==='pt',tr=(a,b)=>pt?a:b;
  $('dossier-subtitle').textContent=project.name+' · '+tr(d.status==='blocked'?'Combinação bloqueada':'Proposta inicial — pendências explícitas',d.status==='blocked'?'No compatible stack':'Initial proposal — unresolved requirements shown');
  const overview=dossierSection(tr('O produto que entendi','Product understanding'));
  overview.append(element('p','product-summary',d.summary),element('p','',d.brief));
  const brief=element('details','dossier-details');brief.append(element('summary','',tr('Descrição completa e requisitos confirmados','Full description and confirmed requirements')),element('p','brief-text',d.brief));
  const facts=Object.entries(d.requirements).filter(([,v])=>v.value).map(([k,v])=>labels[k]+': '+v.value);brief.append(listItems(facts));overview.append(brief);
  if(d.assumptions.length)overview.append(element('h4','',tr('Hipóteses usadas','Working assumptions')),listItems(d.assumptions));
  const live=d.live_research||{},tasks=live.tasks||[],recommendations=live.recommendations||[];
  const research=dossierSection(tr('Pesquisa conduzida pelo Ollama','Research directed by Ollama'));
  research.append(element('p','muted',tr('Modelo: ','Model: ')+(live.model||selectedModel)+' · '+(live.mode||'offline')+' · '+(live.status||'not-run')));
  if(!tasks.length)research.append(element('p','',tr('Nenhuma consulta pública foi executada nesta rodada. A proposta usa a base local.','No public queries were executed this turn. The proposal uses the local catalog.')));
  const traces=element('div','research-traces');tasks.forEach(t=>{const row=element('article','research-trace');row.append(element('strong','',t.source+' · '+t.query),element('span','trace-status',t.status==='ok'?tr('Resultados: ','Results: ')+t.result_count:t.status),element('p','muted',t.tool_id||t.topic));if(t.error)row.append(element('p','muted',t.error));traces.append(row);});research.append(traces);
  if(recommendations.length){const found=element('div','dossier-grid');recommendations.forEach(r=>{const card=element('article','tool-card');card.append(sourceLink(r.name,r.url),element('p','',r.reason),element('blockquote','',r.evidence),element('p','muted',tr('Licença: ','License: ')+r.license));found.append(card);});research.append(found);}else if(tasks.length)research.append(element('p','muted',tr('Nenhum recurso retornado passou pela seleção com evidência nesta rodada. Isso não significa que não existam opções.','No returned resource passed evidence-backed selection this turn. This does not mean options do not exist.')));
  if(live.selection_status)research.append(element('p','muted',live.selection_status));
  const raw=element('details','dossier-details');raw.append(element('summary','',tr('Ver todos os resultados recebidos','View all fetched results')));(live.results||[]).forEach(r=>raw.append(sourceLink(r.name,r.url),element('p','muted',r.description)));research.append(raw);
  research.append(element('p','muted',tr('Consultas limitadas a categorias públicas. A descrição e o histórico são processados no Ollama local. Popularidade e estrelas não comprovam adequação.','Queries use bounded public categories. Product descriptions and history are processed in local Ollama. Popularity and stars do not establish suitability.')));
  const stack=dossierSection(tr('Stack recomendada para começar','Recommended starting stack'));
  stack.append(element('p','',d.decision.reason),element('p','muted',tr('Decisão: ','Decision: ')+d.decision.driver));
  function toolCards(section,tools){const grid=element('div','dossier-grid');tools.forEach(t=>{const card=element('article','tool-card');card.append(element('span','hub-category',t.role),element('h4','',t.name),element('p','',t[pt?'evidence':'evidence_en']),element('p','tool-limit',t[pt?'limitations':'limitations_en']),element('p','muted',t[pt?'cost':'cost_en']),sourceLink(tr('Documentação','Documentation'),t.source));if(t.pricing_source)card.append(sourceLink(tr('Preços para verificar','Pricing to verify'),t.pricing_source));grid.append(card);});section.append(grid);}
  toolCards(stack,d.tools);
  if(d.alternatives.length){const alternatives=element('details','dossier-details');alternatives.append(element('summary','',tr('Alternativas compatíveis consideradas','Compatible alternatives considered')));d.alternatives.forEach(a=>alternatives.append(element('p','',a.tool_ids.map(id=>toolCatalog[id]?.name||id).join(' + ')),element('p','muted',tr('Requisitos atendidos: ','Matched requirements: ')+a.matched_requirements.join(', '))));stack.append(alternatives);}
  const rejected=element('details','dossier-details');rejected.append(element('summary','',tr('Combinações descartadas e motivos','Rejected combinations and reasons')));rejected.append(listItems(d.rejected_stacks.map(a=>a.id+': '+a.reasons.join(', '))));stack.append(rejected);
  const costs=dossierSection(tr('Custos e decisões pendentes','Costs and unresolved decisions'));costs.append(element('p','',tr('Total mensal ainda não verificado. Não há promessa de custo zero.','Monthly total is unverified. No zero-cost promise.')),listItems(d.pending));
  if(d.integrations.length)toolCards(dossierSection(tr('Integrações do produto','Product integrations')),d.integrations);
  if(d.payments.length)toolCards(dossierSection(tr('Opções de pagamento — condicionais','Conditional payment options')),d.payments);
  dossierSection(tr('Segurança e autenticação','Security and authentication')).append(listItems(d.security));
  const workflow=dossierSection(tr('Ferramentas de apoio e modelo','Supporting tools and model'));workflow.append(element('p','',d.model_workflow));toolCards(workflow,d.resources);
  const prompts=dossierSection(tr('Prompts para começar a construir','Prompts to start building'));
  d.prompts.forEach((p,i)=>{const card=element('article','prompt-card');const heading=element('div','prompt-heading');const copy=element('button','secondary',tr('Copiar prompt ','Copy prompt ')+(i+1));copy.type='button';heading.append(element('h4','',p.title),copy);const area=element('textarea','prompt-text');area.value=p.text;area.readOnly=true;area.rows=6;area.setAttribute('aria-label',p.title);const status=element('span','muted');status.setAttribute('role','status');copy.onclick=async()=>{try{await navigator.clipboard.writeText(p.text);status.textContent=tr('Copiado.','Copied.');}catch{area.focus();area.select();status.textContent=tr('Texto selecionado. Use Ctrl+C.','Text selected. Press Ctrl+C.');}};card.append(heading,area,status);prompts.append(card);});
  const provenance=dossierSection(tr('Base local usada','Local catalog used'));provenance.append(element('p','muted',tr('Catálogo inicial: ','Initial catalog: ')+d.research.tools_considered+tr(' ferramentas; ',' tools; ')+d.research.stacks_compared+tr(' combinações avaliadas. Revisão: ',' combinations evaluated. Reviewed: ')+d.research.reviewed_at+tr('. Registros do catálogo são referências; somente as consultas acima representam pesquisa desta rodada.','. Catalog entries are references; only the queries above represent research in this turn.')));
}
async function init(){showNotes(!compactLayout.matches);render();try{await connection();await refreshProjects();const catalog=await api('/api/catalog');toolCatalog=Object.fromEntries(catalog.tools.map(t=>[t.id,t]));if(projects.length){project=await api('/api/projects/'+projects[0].id);render();}}catch(e){error(e.message);}}
init();
