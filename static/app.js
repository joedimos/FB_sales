const $ = (selector) => document.querySelector(selector);
const escapeHtml = (value='') => String(value).replace(/[&<>'"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c]));
const money = value => value == null ? 'Price unavailable' : new Intl.NumberFormat('en-US',{style:'currency',currency:'USD',maximumFractionDigits:0}).format(value);

async function loadSummary(){
  const response = await fetch('/api/summary');
  if(!response.ok) throw new Error('Could not load summary');
  const data = await response.json();
  ['total','hot','appointments'].forEach(key => $(`#${key}`).textContent = data[key]);
  $('#average_score').textContent = `${data.average_score}%`;
}

function rowTemplate(lead){
  const score = lead.score;
  const scoreClass = score >= 75 ? 'high' : score < 45 ? 'low' : '';
  const scoreMarkup = score == null ? '<span class="lead-id">Not scored</span>' : `<div class="score ${scoreClass}" aria-label="${score} percent likelihood"><span>${score}%</span><span class="score-bar" aria-hidden="true"><span style="width:${Math.max(0,Math.min(100,score))}%"></span></span></div>`;
  return `<tr><td><div class="lead-name">${escapeHtml(lead.customer)}</div><div class="lead-id">${escapeHtml(lead.crm_lead_id)} · ${escapeHtml(lead.crm_source)}</div></td><td><div>${escapeHtml(lead.vehicle)}</div><div class="vehicle-price">${money(lead.price)}</div></td><td><span class="badge">${escapeHtml(lead.status.replaceAll('_',' '))}</span></td><td>${scoreMarkup}</td><td><div class="message" title="${escapeHtml(lead.message)}">${escapeHtml(lead.message || 'No message captured')}</div></td></tr>`;
}

async function loadLeads(){
  const loading = $('#loading'), empty = $('#empty'), table = $('#lead-table');
  loading.hidden = false; empty.hidden = true; table.hidden = true;
  const params = new URLSearchParams({q: $('#search').value.trim(), status: $('#status').value});
  try{
    const response = await fetch(`/api/leads?${params}`);
    if(!response.ok) throw new Error('Could not load leads');
    const leads = await response.json();
    $('#lead-rows').innerHTML = leads.map(rowTemplate).join('');
    loading.hidden = true;
    if(leads.length) table.hidden = false; else empty.hidden = false;
  }catch(error){
    loading.textContent = 'The lead list could not be loaded. Refresh the page or check the server.';
  }
}

let searchTimer;
$('#search').addEventListener('input', () => { clearTimeout(searchTimer); searchTimer = setTimeout(loadLeads, 220); });
$('#status').addEventListener('change', loadLeads);
Promise.all([loadSummary(), loadLeads()]).catch(() => { $('#loading').textContent = 'Dashboard data is unavailable.'; });
