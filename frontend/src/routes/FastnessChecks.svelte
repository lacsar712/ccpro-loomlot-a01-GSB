<script>
  import { onMount } from 'svelte';
  import { api, toLocalInput, fromLocalInput } from '../lib/api.js';

  let lots = [];
  let rows = [];
  let error = '';
  let form = {
    dyeLotId: '',
    checkedAt: toLocalInput(new Date().toISOString()),
    washFastness: 4,
    rubFastness: 3.5,
    tempC: 40,
    notes: '',
  };
  let editing = null;

  async function load() {
    error = '';
    try {
      [lots, rows] = await Promise.all([api('/dye-lots'), api('/fastness-checks')]);
      // 默认选中第一个未在静置的染程；静置中的染程不得抽检
      const firstAvailable = lots.find((l) => !l.resting);
      if (!form.dyeLotId) {
        form.dyeLotId = String((firstAvailable || lots[0] || { id: '' }).id);
      }
    } catch (e) {
      error = e.message;
    }
  }

  onMount(load);

  $: selectedLot = lots.find((x) => String(x.id) === form.dyeLotId) || null;
  // 仅拦截新建；编辑既有抽检不受静置状态影响
  $: blocked = !!selectedLot?.resting && !editing;

  function lotLabel(id) {
    const lot = lots.find((x) => x.id === id);
    return lot ? `${lot.recipeName} (#${lot.id})` : id;
  }

  async function save() {
    error = '';
    if (blocked) {
      error = '该染程固色静置未满窗（仍在进行中），禁止登记色牢度抽检；请先在「固色静置」结束静置。';
      return;
    }
    try {
      const body = {
        dyeLotId: Number(form.dyeLotId),
        checkedAt: fromLocalInput(form.checkedAt),
        washFastness: Number(form.washFastness),
        rubFastness: Number(form.rubFastness),
        tempC: Number(form.tempC),
        notes: form.notes.trim() || null,
      };
      if (editing) {
        await api(`/fastness-checks/${editing}`, { method: 'PUT', body: JSON.stringify(body) });
      } else {
        await api('/fastness-checks', { method: 'POST', body: JSON.stringify(body) });
      }
      editing = null;
      form = {
        ...form,
        checkedAt: toLocalInput(new Date().toISOString()),
        notes: '',
      };
      await load();
    } catch (e) {
      error = e.message;
    }
  }

  function startEdit(row) {
    editing = row.id;
    form = {
      dyeLotId: String(row.dyeLotId),
      checkedAt: toLocalInput(row.checkedAt),
      washFastness: row.washFastness,
      rubFastness: row.rubFastness,
      tempC: row.tempC,
      notes: row.notes || '',
    };
  }

  async function remove(id) {
    if (!confirm('确认删除该抽检？')) return;
    error = '';
    try {
      await api(`/fastness-checks/${id}`, { method: 'DELETE' });
      await load();
    } catch (e) {
      error = e.message;
    }
  }
</script>

<h1 class="page-title">色牢度抽检</h1>
<p class="page-sub">耐洗 1–5 级；摩擦牢度须大于 0；记录检测温度。固色静置未满窗的染程禁止抽检。</p>

{#if blocked}
  <p class="block-banner">
    染程「{selectedLot.recipeName}」固色静置进行中，未满窗，禁止登记抽检；结束静置后自动恢复。
  </p>
{/if}

<div class="panel" style="margin-bottom:1rem;">
  <div class="form-grid">
    <label
      >染程
      <select bind:value={form.dyeLotId}>
        {#each lots as lot}
          <option value={String(lot.id)} disabled={lot.resting}>
            {lot.recipeName} · {lot.fabricKg}kg{lot.resting ? ' · 静置中（禁检）' : ''}
          </option>
        {/each}
      </select>
    </label>
    <label>检测时间 <input type="datetime-local" bind:value={form.checkedAt} /></label>
    <label>耐洗 (1–5) <input type="number" min="1" max="5" bind:value={form.washFastness} /></label>
    <label>摩擦 (&gt;0) <input type="number" step="0.1" min="0.1" bind:value={form.rubFastness} /></label>
    <label>温度 ℃ <input type="number" step="0.1" bind:value={form.tempC} /></label>
    <label>备注 <input bind:value={form.notes} /></label>
  </div>
  <div class="toolbar">
    <button class="btn" type="button" disabled={blocked} on:click={save}>
      {editing ? '保存修改' : '登记抽检'}
    </button>
    {#if editing}
      <button class="btn ghost" type="button" on:click={() => (editing = null)}>取消</button>
    {/if}
  </div>
  {#if error}<p class="err">{error}</p>{/if}
</div>

<div class="panel">
  <table>
    <thead>
      <tr>
        <th>ID</th>
        <th>染程</th>
        <th>检测时间</th>
        <th>耐洗</th>
        <th>摩擦</th>
        <th>温度</th>
        <th>备注</th>
        <th></th>
      </tr>
    </thead>
    <tbody>
      {#each rows as row}
        <tr>
          <td>{row.id}</td>
          <td>{lotLabel(row.dyeLotId)}</td>
          <td>{new Date(row.checkedAt).toLocaleString()}</td>
          <td>{row.washFastness}</td>
          <td>{row.rubFastness}</td>
          <td>{row.tempC}℃</td>
          <td>{row.notes || '—'}</td>
          <td class="row-actions">
            <button class="btn ghost small" type="button" on:click={() => startEdit(row)}>编辑</button>
            <button class="btn danger small" type="button" on:click={() => remove(row.id)}>删除</button>
          </td>
        </tr>
      {/each}
    </tbody>
  </table>
</div>

<style>
  .block-banner {
    margin: 0 0 1rem;
    padding: 0.6rem 0.9rem;
    border: 1px solid var(--danger);
    border-radius: 3px;
    background: rgba(224, 81, 81, 0.12);
    color: var(--danger);
    font-size: 0.88rem;
  }

  .btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
    filter: none;
  }
</style>
