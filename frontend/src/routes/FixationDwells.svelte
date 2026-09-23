<script>
  import { onMount } from 'svelte';
  import { api, toLocalInput, fromLocalInput } from '../lib/api.js';

  let lots = [];
  let dwells = [];
  let weights = [];
  let error = '';
  let weightError = '';

  let dwellForm = {
    dyeLotId: '',
    startedAt: toLocalInput(new Date().toISOString()),
    plannedEndAt: toLocalInput(new Date(Date.now() + 4 * 3600 * 1000).toISOString()),
    dutyOfficer: '染程操作员',
  };
  let weightForm = {
    dyeLotId: '',
    weighedAt: toLocalInput(new Date().toISOString()),
    weightKg: 20,
    recorderName: '过磅员',
  };
  // 每条进行中静置的结束时刻输入
  let endInputs = {};

  async function load() {
    error = '';
    try {
      [lots, dwells, weights] = await Promise.all([
        api('/dye-lots'),
        api('/fixation-dwells'),
        api('/fabric-weights'),
      ]);
      if (!dwellForm.dyeLotId && lots.length) dwellForm.dyeLotId = String(lots[0].id);
      if (!weightForm.dyeLotId && lots.length) weightForm.dyeLotId = String(lots[0].id);
      dwells.forEach((d) => {
        if (d.active && !(d.id in endInputs)) {
          endInputs[d.id] = toLocalInput(new Date().toISOString());
        }
      });
    } catch (e) {
      error = e.message;
    }
  }

  onMount(load);

  function lotLabel(id) {
    const lot = lots.find((x) => x.id === id);
    return lot ? `${lot.recipeName} (#${lot.id})` : id;
  }

  function weightCount(lotId) {
    return weights.filter((w) => w.dyeLotId === lotId).length;
  }

  async function createDwell() {
    error = '';
    try {
      await api('/fixation-dwells', {
        method: 'POST',
        body: JSON.stringify({
          dyeLotId: Number(dwellForm.dyeLotId),
          startedAt: fromLocalInput(dwellForm.startedAt),
          plannedEndAt: fromLocalInput(dwellForm.plannedEndAt),
          dutyOfficer: dwellForm.dutyOfficer.trim(),
        }),
      });
      dwellForm.startedAt = toLocalInput(new Date().toISOString());
      dwellForm.plannedEndAt = toLocalInput(
        new Date(Date.now() + 4 * 3600 * 1000).toISOString()
      );
      await load();
    } catch (e) {
      error = e.message;
    }
  }

  async function endDwell(d) {
    error = '';
    try {
      await api(`/fixation-dwells/${d.id}/end`, {
        method: 'POST',
        body: JSON.stringify({ actualEndAt: fromLocalInput(endInputs[d.id]) }),
      });
      await load();
    } catch (e) {
      error = e.message;
    }
  }

  async function createWeight() {
    weightError = '';
    try {
      await api('/fabric-weights', {
        method: 'POST',
        body: JSON.stringify({
          dyeLotId: Number(weightForm.dyeLotId),
          weighedAt: fromLocalInput(weightForm.weighedAt),
          weightKg: Number(weightForm.weightKg),
          recorderName: weightForm.recorderName.trim(),
        }),
      });
      weightForm.weighedAt = toLocalInput(new Date().toISOString());
      await load();
    } catch (e) {
      weightError = e.message;
    }
  }

  async function removeWeight(id) {
    if (!confirm('确认删除该布重记录？')) return;
    weightError = '';
    try {
      await api(`/fabric-weights/${id}`, { method: 'DELETE' });
      await load();
    } catch (e) {
      weightError = e.message;
    }
  }
</script>

<h1 class="page-title">固色静置</h1>
<p class="page-sub">
  染程挂起静置；未满窗（存在进行中静置）禁止登记色牢度抽检。同一染程同时只允许一条进行中静置，排液缸染程禁止新开。
  结束静置须先有同染程布重千克记录可对账。
</p>

<div class="panel" style="margin-bottom:1rem;">
  <div class="form-grid">
    <label
      >染程
      <select bind:value={dwellForm.dyeLotId}>
        {#each lots as lot}
          <option value={String(lot.id)}>
            {lot.recipeName} · {lot.fabricKg}kg{lot.resting ? ' · 静置中' : ''}
          </option>
        {/each}
      </select>
    </label>
    <label>开始时刻 <input type="datetime-local" bind:value={dwellForm.startedAt} /></label>
    <label
      >计划结束时刻
      <input type="datetime-local" bind:value={dwellForm.plannedEndAt} />
    </label>
    <label>值班人 <input bind:value={dwellForm.dutyOfficer} /></label>
  </div>
  <div class="toolbar">
    <button class="btn" type="button" on:click={createDwell}>挂静置</button>
  </div>
  {#if error}<p class="err">{error}</p>{/if}
</div>

<div class="panel" style="margin-bottom:1rem;">
  <table>
    <thead>
      <tr>
        <th>ID</th>
        <th>染程</th>
        <th>开始时刻</th>
        <th>计划结束</th>
        <th>实际结束</th>
        <th>值班人</th>
        <th>状态 / 操作</th>
      </tr>
    </thead>
    <tbody>
      {#each dwells as d}
        <tr class:resting={d.active}>
          <td>{d.id}</td>
          <td>{lotLabel(d.dyeLotId)}</td>
          <td>{new Date(d.startedAt).toLocaleString()}</td>
          <td>{new Date(d.plannedEndAt).toLocaleString()}</td>
          <td>{d.actualEndAt ? new Date(d.actualEndAt).toLocaleString() : '—'}</td>
          <td>{d.dutyOfficer}</td>
          <td>
            {#if d.active}
              <span class="badge">静置中 · 布重 {weightCount(d.dyeLotId)} 条</span>
              <div class="end-row">
                <input type="datetime-local" bind:value={endInputs[d.id]} />
                <button class="btn small" type="button" on:click={() => endDwell(d)}>结束静置</button>
              </div>
            {:else}
              <span class="done">已结束</span>
            {/if}
          </td>
        </tr>
      {/each}
    </tbody>
  </table>
</div>

<div class="panel">
  <h2 class="section-title">布重千克记录（结束静置对账用）</h2>
  <div class="form-grid">
    <label
      >染程
      <select bind:value={weightForm.dyeLotId}>
        {#each lots as lot}
          <option value={String(lot.id)}>{lot.recipeName} · {lot.fabricKg}kg</option>
        {/each}
      </select>
    </label>
    <label>过磅时刻 <input type="datetime-local" bind:value={weightForm.weighedAt} /></label>
    <label>布重 kg <input type="number" step="0.1" bind:value={weightForm.weightKg} /></label>
    <label>记录人 <input bind:value={weightForm.recorderName} /></label>
  </div>
  <div class="toolbar">
    <button class="btn" type="button" on:click={createWeight}>登记布重</button>
  </div>
  {#if weightError}<p class="err">{weightError}</p>{/if}

  <table style="margin-top:0.75rem;">
    <thead>
      <tr>
        <th>ID</th>
        <th>染程</th>
        <th>过磅时刻</th>
        <th>布重 kg</th>
        <th>记录人</th>
        <th></th>
      </tr>
    </thead>
    <tbody>
      {#each weights as w}
        <tr>
          <td>{w.id}</td>
          <td>{lotLabel(w.dyeLotId)}</td>
          <td>{new Date(w.weighedAt).toLocaleString()}</td>
          <td>{w.weightKg}</td>
          <td>{w.recorderName}</td>
          <td class="row-actions">
            <button class="btn danger small" type="button" on:click={() => removeWeight(w.id)}>删除</button>
          </td>
        </tr>
      {/each}
    </tbody>
  </table>
</div>

<style>
  .resting {
    background: rgba(107, 92, 231, 0.08);
  }

  .badge {
    display: inline-block;
    padding: 0.1rem 0.5rem;
    border-radius: 3px;
    background: rgba(107, 92, 231, 0.25);
    border: 1px solid rgba(107, 92, 231, 0.5);
    font-size: 0.78rem;
    white-space: nowrap;
  }

  .done {
    color: var(--ok, #4caf82);
    font-size: 0.85rem;
  }

  .end-row {
    display: flex;
    gap: 0.4rem;
    align-items: center;
    margin-top: 0.35rem;
  }

  .end-row input {
    width: auto;
  }

  .section-title {
    font-size: 1rem;
    margin: 0 0 0.75rem;
  }
</style>
