<script>
  import { onMount } from 'svelte';
  import { api, VAT_STATUS, toLocalInput, fromLocalInput } from '../lib/api.js';

  let lots = [];
  let vatsById = {};
  let windows = [];
  let weights = [];
  let error = '';
  let info = '';

  let form = {
    dyeLotId: '',
    startAt: toLocalInput(new Date().toISOString()),
    plannedEndAt: toLocalInput(new Date(Date.now() + 2 * 3600_000).toISOString()),
    dutyOfficer: '染程操作员',
  };

  let weightForm = {
    dyeLotId: '',
    weighedAt: toLocalInput(new Date().toISOString()),
    weightKg: 20,
    recorderName: '染程操作员',
    notes: '',
  };

  async function load() {
    error = '';
    try {
      const [vats, lotRows, winRows, weightRows] = await Promise.all([
        api('/vats'),
        api('/dye-lots'),
        api('/fixation-windows'),
        api('/fabric-weights'),
      ]);
      vatsById = Object.fromEntries(vats.map((v) => [v.id, v]));
      lots = lotRows;
      windows = winRows;
      weights = weightRows;
      if (!form.dyeLotId && lots.length) form.dyeLotId = String(lots[0].id);
      if (!weightForm.dyeLotId && lots.length) weightForm.dyeLotId = String(lots[0].id);
    } catch (e) {
      error = e.message;
    }
  }

  onMount(load);

  $: lotById = Object.fromEntries(lots.map((l) => [l.id, l]));

  function lotText(id) {
    const lot = lotById[id];
    if (!lot) return `#${id}`;
    const vat = vatsById[lot.vatId];
    return `${lot.recipeName} (#${lot.id})${vat ? ` · ${vat.vatCode}` : ''}`;
  }

  function weightCount(lotId) {
    return weights.filter((w) => w.dyeLotId === lotId).length;
  }

  async function openWindow() {
    error = '';
    info = '';
    if (form.plannedEndAt <= form.startAt) {
      error = '计划结束时刻必须晚于开始时刻';
      return;
    }
    try {
      await api('/fixation-windows', {
        method: 'POST',
        body: JSON.stringify({
          dyeLotId: Number(form.dyeLotId),
          startAt: fromLocalInput(form.startAt),
          plannedEndAt: fromLocalInput(form.plannedEndAt),
          dutyOfficer: form.dutyOfficer.trim(),
        }),
      });
      info = '固色静置已开始';
      await load();
    } catch (e) {
      error = e.message;
    }
  }

  async function finishWindow(win) {
    error = '';
    info = '';
    const input = prompt('填写实际结束时刻（本地时间，格式 YYYY-MM-DD HH:mm）', toLocalInput(new Date().toISOString()));
    if (input === null) return;
    let iso;
    try {
      iso = fromLocalInput(input.replace(' ', 'T'));
      if (Number.isNaN(Date.parse(iso))) throw new Error('bad date');
    } catch {
      error = '实际结束时刻格式无效';
      return;
    }
    try {
      await api(`/fixation-windows/${win.id}/finish`, {
        method: 'POST',
        body: JSON.stringify({ actualEndAt: iso }),
      });
      info = `静置 #${win.id} 已结束，色牢度抽检已恢复`;
      await load();
    } catch (e) {
      error = e.message;
    }
  }

  async function addWeight() {
    error = '';
    info = '';
    try {
      await api('/fabric-weights', {
        method: 'POST',
        body: JSON.stringify({
          dyeLotId: Number(weightForm.dyeLotId),
          weighedAt: fromLocalInput(weightForm.weighedAt),
          weightKg: Number(weightForm.weightKg),
          recorderName: weightForm.recorderName.trim(),
          notes: weightForm.notes.trim() || null,
        }),
      });
      weightForm.notes = '';
      await load();
    } catch (e) {
      error = e.message;
    }
  }
</script>

<h1 class="page-title">固色静置</h1>
<p class="page-sub">
  染程挂上固色静置窗后方可进入静置；同一染程同时仅允许一条未结束静置，排液缸禁止开静置。
  <strong>静置进行中、未满窗时，色牢度抽检被禁止（409）；结束静置后方可登记抽检。</strong>
  结束静置前该染程须至少已有一条布重（千克）记录用于对账。
</p>

<div class="panel" style="margin-bottom:1rem;">
  <h2 class="panel-title" style="margin-top:0;">新开静置窗</h2>
  <div class="form-grid">
    <label
      >所属染程
      <select bind:value={form.dyeLotId}>
        {#each lots as lot}
          {@const vat = vatsById[lot.vatId]}
          <option value={String(lot.id)}>
            {lot.recipeName} (#{lot.id}) · {vat ? vat.vatCode : ''} ·
            {vat ? VAT_STATUS[vat.status] || vat.status : ''}{lot.fixationActive ? ' · 静置中' : ''}
          </option>
        {/each}
      </select>
    </label>
    <label>开始时刻 <input type="datetime-local" bind:value={form.startAt} /></label>
    <label>计划结束时刻 <input type="datetime-local" bind:value={form.plannedEndAt} /></label>
    <label>值班人 <input bind:value={form.dutyOfficer} /></label>
  </div>
  <div class="toolbar">
    <button class="btn" type="button" on:click={openWindow}>开始固色静置</button>
  </div>
</div>

<div class="panel" style="margin-bottom:1rem;">
  <h2 class="panel-title" style="margin-top:0;">布重（千克）对账记录</h2>
  <div class="form-grid">
    <label
      >染程
      <select bind:value={weightForm.dyeLotId}>
        {#each lots as lot}
          <option value={String(lot.id)}>{lot.recipeName} (#{lot.id})</option>
        {/each}
      </select>
    </label>
    <label>称重时刻 <input type="datetime-local" bind:value={weightForm.weighedAt} /></label>
    <label>布重 kg <input type="number" step="0.1" min="0.1" bind:value={weightForm.weightKg} /></label>
    <label>记录人 <input bind:value={weightForm.recorderName} /></label>
    <label>备注 <input bind:value={weightForm.notes} placeholder="可空" /></label>
  </div>
  <div class="toolbar">
    <button class="btn ghost" type="button" on:click={addWeight}>登记布重</button>
  </div>
</div>

{#if error}<p class="err">{error}</p>{/if}
{#if info}<p class="ok-msg">{info}</p>{/if}

<div class="panel">
  <h2 class="panel-title" style="margin-top:0;">静置窗</h2>
  <table>
    <thead>
      <tr>
        <th>ID</th>
        <th>所属染程</th>
        <th>开始时刻</th>
        <th>计划结束</th>
        <th>实际结束</th>
        <th>值班人</th>
        <th>状态</th>
        <th>布重记录</th>
        <th></th>
      </tr>
    </thead>
    <tbody>
      {#each windows as win}
        <tr>
          <td>{win.id}</td>
          <td>{lotText(win.dyeLotId)}</td>
          <td>{new Date(win.startAt).toLocaleString()}</td>
          <td>{new Date(win.plannedEndAt).toLocaleString()}</td>
          <td>{win.actualEndAt ? new Date(win.actualEndAt).toLocaleString() : '—'}</td>
          <td>{win.dutyOfficer}</td>
          <td>
            {#if win.active}
              <span class="badge fixation">静置中</span>
            {:else}
              <span class="badge muted">已结束</span>
            {/if}
          </td>
          <td>{weightCount(win.dyeLotId)} 条</td>
          <td class="row-actions">
            {#if win.active}
              <button class="btn small" type="button" on:click={() => finishWindow(win)}>结束静置</button>
            {/if}
          </td>
        </tr>
      {/each}
      {#if windows.length === 0}
        <tr><td colspan="9" style="color:var(--indigo-mist);">暂无静置窗</td></tr>
      {/if}
    </tbody>
  </table>
</div>
