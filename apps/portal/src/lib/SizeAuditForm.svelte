<script lang="ts">
  import { sizeRequestSchema, type SizeRequest } from '$lib/schemas';
  import { randomUuid } from '$lib/audit';

  const MODES = ['AIR_GAPPED_EDGE', 'HYBRID_CONNECTED', 'FULL_CLOUD'] as const;

  type RecommendedHardware = {
    hardware_id: string;
    name: string;
    quantity: number;
    vram_per_unit_gb: number;
    system_ram_gb: number;
    role: string;
  };

  type SizingResult = {
    audit_id: string;
    verdict: {
      deployment_mode: string;
      recommended_hardware: RecommendedHardware[];
      model_stack: {
        weights_vram_gb: number;
        kv_cache_allocated_gb: number;
        vector_db_vram_gb: number;
        total_vram_required_gb: number;
        max_concurrent_streams: number;
      };
      rag_parameters: { estimated_total_child_chunks: number };
      sizing_rationale: {
        total_vram_required_gb: number;
        selected_hardware_id: string;
        selected_hardware_name: string;
        quantity: number;
        vram_per_unit_gb: number;
        vram_utilization_pct: number;
        ha_redundancy: boolean;
      };
      tco_3year_comparison: {
        hardware_capex_usd: number;
        energy_and_maint_3yr_usd: number;
        capex_edge_total_usd: number;
        opex_cloud_total_usd: number;
        net_savings_usd: number;
        recommended_decision: string;
      };
    };
  };

  let deploymentMode = $state('AIR_GAPPED_EDGE');
  let clientName = $state('Helvetic Precision Manufacturing');
  let technicians = $state('');
  let totalShifts = $state('3');
  let manualsGb = $state('85');
  let workOrders = $state('450000');
  let avgTokens = $state('420');
  let peakRatio = $state('0.40');
  let avgQueries = $state('15');
  let targetTtft = $state('1.5');
  let electricityRate = $state('0.18');
  let safetyCritical = $state(true);
  let result = $state<SizingResult | null>(null);
  let error = $state('');
  let fieldErrors = $state<Record<string, string>>({});
  let loading = $state(false);

  const currency = (value: number) =>
    '$' + value.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });

  const parseDecimal = (value: string | number): number => Number(String(value).replace(',', '.'));

  function validate(): Record<string, string> {
    const errors: Record<string, string> = {};
    const techniciansValue = String(technicians ?? '').trim();
    if (!techniciansValue) {
      errors.technicians = 'Technicians per shift is required';
    } else if (!Number.isFinite(parseDecimal(techniciansValue)) || parseDecimal(techniciansValue) < 1) {
      errors.technicians = 'Enter a whole number ≥ 1';
    }

    const numeric: Array<[string, string, (v: number) => boolean, string]> = [
      ['totalShifts', totalShifts, (v) => v >= 1 && Number.isInteger(v), 'Enter a whole number ≥ 1'],
      ['manualsGb', manualsGb, (v) => v >= 0, 'Enter a number ≥ 0'],
      ['workOrders', workOrders, (v) => v >= 0 && Number.isInteger(v), 'Enter a whole number ≥ 0'],
      ['avgTokens', avgTokens, (v) => v >= 1, 'Enter a number ≥ 1'],
      ['avgQueries', avgQueries, (v) => v >= 1 && Number.isInteger(v), 'Enter a whole number ≥ 1'],
      ['targetTtft', targetTtft, (v) => v > 0, 'Enter a number > 0'],
      ['electricityRate', electricityRate, (v) => v >= 0, 'Enter a number ≥ 0'],
    ];
    for (const [key, raw, ok, message] of numeric) {
      const value = parseDecimal(raw);
      if (!Number.isFinite(value) || !ok(value)) errors[key] = message;
    }

    const ratio = parseDecimal(peakRatio);
    if (!Number.isFinite(ratio) || ratio < 0 || ratio > 1) {
      errors.peakRatio = 'Enter a ratio between 0 and 1';
    }
    return errors;
  }

  function vramParts(r: SizingResult) {
    const m = r.verdict.model_stack;
    const other = Math.max(
      0,
      m.total_vram_required_gb - m.weights_vram_gb - m.kv_cache_allocated_gb - m.vector_db_vram_gb
    );
    const total = m.total_vram_required_gb || 1;
    const mk = (label: string, value: number) => ({
      label,
      value,
      pct: Math.max(0, (value / total) * 100),
    });
    return [
      mk('Weights', m.weights_vram_gb),
      mk('KV cache', m.kv_cache_allocated_gb),
      mk('VectorDB', m.vector_db_vram_gb),
      mk('Reranker + headroom', other),
    ];
  }

  async function submit() {
    error = '';
    result = null;
    fieldErrors = validate();
    if (Object.keys(fieldErrors).length > 0) {
      error = 'Please fix the highlighted fields.';
      return;
    }

    let payload: SizeRequest;
    try {
      payload = sizeRequestSchema.parse({
        audit_id: randomUuid(),
        client_name: clientName.trim() || 'Helvetic Precision Manufacturing',
        deployment_constraint: deploymentMode,
        technicians_per_shift: parseDecimal(technicians),
        total_shifts: parseDecimal(totalShifts),
        documents: {
          equipment_manuals_pdf_gb: parseDecimal(manualsGb),
          historical_work_orders_count: parseDecimal(workOrders),
          average_tokens_per_page: parseDecimal(avgTokens),
        },
        concurrency: {
          peak_shift_overlap_ratio: parseDecimal(peakRatio),
          avg_queries_per_tech_shift: parseDecimal(avgQueries),
          target_p95_ttft_seconds: parseDecimal(targetTtft),
        },
        financials: { electricity_rate_kwh_usd: parseDecimal(electricityRate) },
        safety_critical: safetyCritical,
      });
    } catch {
      error = 'Please check your inputs: all numeric fields must be valid numbers.';
      return;
    }

    loading = true;
    try {
      const response = await fetch('/api/audit', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      if (!response.ok) {
        const body = (await response.json().catch(() => null)) as { error?: string } | null;
        error = body?.error ?? 'The sizing request failed. Please try again.';
        return;
      }
      result = (await response.json()) as SizingResult;
    } catch {
      error = 'Network error — could not reach the sizing engine.';
    } finally {
      loading = false;
    }
  }
</script>

<section class="audit" aria-label="Size audit">
  <h2 class="section-title">1 · Paramètres</h2>

  <form novalidate>
    <fieldset class="group">
      <legend>Cible &amp; Exploitation</legend>
      <div class="grid">
        <div class="field span-2">
          <label for="deployment-mode">Deployment mode</label>
          <select id="deployment-mode" bind:value={deploymentMode}>
            {#each MODES as mode}
              <option value={mode}>{mode}</option>
            {/each}
          </select>
          <span class="hint">Contrainte d'exécution de l'architecture dimensionnée</span>
        </div>

        <div class="field span-2">
          <label for="client-name">Client name</label>
          <input id="client-name" bind:value={clientName} type="text" autocomplete="organization" />
          <span class="hint">Optionnel — défaut : Helvetic Precision Manufacturing</span>
        </div>

        <div class="field">
          <label for="technicians">Technicians per shift</label>
          <input
            id="technicians"
            bind:value={technicians}
            type="number"
            min="1"
            inputmode="numeric"
            aria-invalid={fieldErrors.technicians ? 'true' : undefined}
            aria-describedby={fieldErrors.technicians ? 'technicians-error' : undefined}
          />
          <span class="hint">Effectif par équipe</span>
          {#if fieldErrors.technicians}
            <p class="field-error" id="technicians-error">{fieldErrors.technicians}</p>
          {/if}
        </div>

        <div class="field">
          <label for="total-shifts">Total shifts</label>
          <input
            id="total-shifts"
            bind:value={totalShifts}
            type="number"
            min="1"
            inputmode="numeric"
            aria-invalid={fieldErrors.totalShifts ? 'true' : undefined}
            aria-describedby={fieldErrors.totalShifts ? 'total-shifts-error' : undefined}
          />
          <span class="hint">Équipes par jour</span>
          {#if fieldErrors.totalShifts}
            <p class="field-error" id="total-shifts-error">{fieldErrors.totalShifts}</p>
          {/if}
        </div>
      </div>
    </fieldset>

    <fieldset class="group">
      <legend>Corpus documentaire</legend>
      <div class="grid">
        <div class="field">
          <label for="manuals-gb">Manuals volume (GB)</label>
          <input
            id="manuals-gb"
            bind:value={manualsGb}
            type="text"
            inputmode="decimal"
            aria-invalid={fieldErrors.manualsGb ? 'true' : undefined}
            aria-describedby={fieldErrors.manualsGb ? 'manuals-gb-error' : undefined}
          />
          <span class="hint">Go de manuels équipement (PDF)</span>
          {#if fieldErrors.manualsGb}
            <p class="field-error" id="manuals-gb-error">{fieldErrors.manualsGb}</p>
          {/if}
        </div>

        <div class="field">
          <label for="work-orders">Historical work orders</label>
          <input
            id="work-orders"
            bind:value={workOrders}
            type="number"
            min="0"
            inputmode="numeric"
            aria-invalid={fieldErrors.workOrders ? 'true' : undefined}
            aria-describedby={fieldErrors.workOrders ? 'work-orders-error' : undefined}
          />
          <span class="hint">Nombre total d'ordres de travail</span>
          {#if fieldErrors.workOrders}
            <p class="field-error" id="work-orders-error">{fieldErrors.workOrders}</p>
          {/if}
        </div>

        <div class="field">
          <label for="avg-tokens">Avg tokens per page</label>
          <input
            id="avg-tokens"
            bind:value={avgTokens}
            type="number"
            min="1"
            inputmode="numeric"
            aria-invalid={fieldErrors.avgTokens ? 'true' : undefined}
            aria-describedby={fieldErrors.avgTokens ? 'avg-tokens-error' : undefined}
          />
          <span class="hint">Tokens par page</span>
          {#if fieldErrors.avgTokens}
            <p class="field-error" id="avg-tokens-error">{fieldErrors.avgTokens}</p>
          {/if}
        </div>
      </div>
    </fieldset>

    <fieldset class="group">
      <legend>Concurrence &amp; Latence</legend>
      <div class="grid">
        <div class="field">
          <label for="peak-ratio">Peak shift overlap ratio</label>
          <input
            id="peak-ratio"
            bind:value={peakRatio}
            type="text"
            inputmode="decimal"
            aria-invalid={fieldErrors.peakRatio ? 'true' : undefined}
            aria-describedby={fieldErrors.peakRatio ? 'peak-ratio-error' : undefined}
          />
          <span class="hint">0–1 (ex. 0.40)</span>
          {#if fieldErrors.peakRatio}
            <p class="field-error" id="peak-ratio-error">{fieldErrors.peakRatio}</p>
          {/if}
        </div>

        <div class="field">
          <label for="avg-queries">Avg queries per tech shift</label>
          <input
            id="avg-queries"
            bind:value={avgQueries}
            type="number"
            min="1"
            inputmode="numeric"
            aria-invalid={fieldErrors.avgQueries ? 'true' : undefined}
            aria-describedby={fieldErrors.avgQueries ? 'avg-queries-error' : undefined}
          />
          <span class="hint">Requêtes par équipe</span>
          {#if fieldErrors.avgQueries}
            <p class="field-error" id="avg-queries-error">{fieldErrors.avgQueries}</p>
          {/if}
        </div>

        <div class="field">
          <label for="target-ttft">Target P95 TTFT</label>
          <input
            id="target-ttft"
            bind:value={targetTtft}
            type="text"
            inputmode="decimal"
            aria-invalid={fieldErrors.targetTtft ? 'true' : undefined}
            aria-describedby={fieldErrors.targetTtft ? 'target-ttft-error' : undefined}
          />
          <span class="hint">Secondes (ex. 1.5)</span>
          {#if fieldErrors.targetTtft}
            <p class="field-error" id="target-ttft-error">{fieldErrors.targetTtft}</p>
          {/if}
        </div>
      </div>
    </fieldset>

    <fieldset class="group">
      <legend>Énergie &amp; TCO</legend>
      <div class="grid">
        <div class="field">
          <label for="electricity">Electricity rate (USD/kWh)</label>
          <input
            id="electricity"
            bind:value={electricityRate}
            type="text"
            inputmode="decimal"
            aria-invalid={fieldErrors.electricityRate ? 'true' : undefined}
            aria-describedby={fieldErrors.electricityRate ? 'electricity-error' : undefined}
          />
          <span class="hint">USD par kWh</span>
          {#if fieldErrors.electricityRate}
            <p class="field-error" id="electricity-error">{fieldErrors.electricityRate}</p>
          {/if}
        </div>
      </div>
    </fieldset>

    <fieldset class="group">
      <legend>Sécurité / Haute Disponibilité</legend>
      <div class="check-row">
        <input id="safety-critical" type="checkbox" bind:checked={safetyCritical} />
        <label for="safety-critical">Safety critical (HA)</label>
        <span class="hint">Active la redondance actif-actif et la gate zéro-hallucination</span>
      </div>
    </fieldset>

    <div class="actions">
      <button type="button" onclick={() => void submit()} disabled={loading} aria-busy={loading}>
        {#if loading}<span class="spinner" aria-hidden="true"></span>Sizing…{:else}Size architecture{/if}
      </button>
    </div>
  </form>

  {#if error}
    <p class="error" role="alert">{error}</p>
  {/if}
</section>

{#if result}
  <section class="results" aria-label="Sizing results">
    <h2 class="section-title">2 · Résultats</h2>

    <div class="kpis">
      <div class="kpi">
        <p class="kpi-value">CAPEX {currency(result.verdict.tco_3year_comparison.capex_edge_total_usd)}</p>
        <span class="kpi-label">Edge on-prem · 3 ans</span>
      </div>
      <div class="kpi">
        <p class="kpi-value">OPEX {currency(result.verdict.tco_3year_comparison.opex_cloud_total_usd)}</p>
        <span class="kpi-label">Cloud managé · 3 ans</span>
      </div>
      <div class="kpi">
        <p class="kpi-value">Économies {currency(result.verdict.tco_3year_comparison.net_savings_usd)}</p>
        <span class="kpi-label">Net · 3 ans</span>
      </div>
      <div class="kpi decision">
        <p class="kpi-value">{result.verdict.tco_3year_comparison.recommended_decision}</p>
        <span class="kpi-label">Recommended decision</span>
      </div>
    </div>

    {#if result.verdict.recommended_hardware?.[0]}
      <div class="hardware-card">
        <h3>Matériel recommandé</h3>
        <p class="hw-name">
          {result.verdict.recommended_hardware[0].name}
          <span class="hw-qty">× {result.verdict.recommended_hardware[0].quantity}</span>
        </p>
        <p class="hw-meta">
          {result.verdict.recommended_hardware[0].vram_per_unit_gb} GB VRAM / unité ·
          {result.verdict.sizing_rationale?.vram_utilization_pct ?? '—'} % utilisés ·
          {result.verdict.recommended_hardware[0].role}
        </p>
      </div>
    {/if}

    <div class="vram">
      <h3>Ventilation VRAM</h3>
      {#each vramParts(result) as part}
        <div class="bar-row">
          <span class="bar-label">{part.label}</span>
          <div class="bar-track"><div class="bar-fill" style="width: {part.pct}%"></div></div>
          <span class="bar-value">{part.value.toFixed(2)} GB</span>
        </div>
      {/each}
      <p class="vram-total">
        Total {result.verdict.model_stack.total_vram_required_gb.toFixed(2)} GB ·
        {result.verdict.model_stack.max_concurrent_streams} streams · {result.verdict.rag_parameters.estimated_total_child_chunks} chunks
      </p>
    </div>

    <p class="calc-link-wrap">
      <a class="calc-link" href={`/audit/${result.audit_id}/calculations`}>Voir le détail des calculs →</a>
    </p>
  </section>
{/if}

<style>
  .audit,
  .results {
    max-width: 52rem;
    margin: 0 auto;
  }

  .section-title {
    font-size: 1.15rem;
    margin: 0 0 0.75rem;
    color: #0b1220;
  }

  .group {
    border: 1px solid var(--line);
    border-radius: 0.75rem;
    background: #fff;
    padding: 1rem 1.25rem 1.25rem;
    margin: 0 0 1rem;
    box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
  }

  legend {
    font-weight: 600;
    padding: 0 0.5rem;
    color: #1f2937;
  }

  .grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 1rem 1.25rem;
    align-items: start;
  }

  .field {
    display: flex;
    flex-direction: column;
    gap: 0.375rem;
    min-width: 0;
  }

  .field.span-2 {
    grid-column: 1 / -1;
  }

  .field > label,
  .check-row label {
    font-weight: 500;
    font-size: 0.875rem;
    color: #111827;
  }

  .hint {
    font-size: 0.75rem;
    color: var(--muted);
  }

  input,
  select {
    width: 100%;
    min-width: 0;
    min-height: 44px;
    padding: 0.5rem 0.75rem;
    font-size: 1rem;
    color: #111827;
    background: #fff;
    border: 1px solid #9ca3af;
    border-radius: 0.5rem;
  }

  input:focus-visible,
  select:focus-visible {
    outline: 2px solid var(--brand);
    outline-offset: 1px;
    border-color: var(--brand);
  }

  input[aria-invalid='true'] {
    border-color: #dc2626;
  }

  .field-error {
    margin: 0;
    color: #b91c1c;
    font-size: 0.78rem;
    font-weight: 500;
  }

  .check-row {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    flex-wrap: wrap;
    min-height: 44px;
  }

  .check-row input {
    width: 1.5rem;
    height: 1.5rem;
    min-height: 1.5rem;
    accent-color: var(--brand);
  }

  .actions {
    margin-top: 0.5rem;
  }

  button {
    min-height: 44px;
    padding: 0.75rem 1.5rem;
    font-size: 1rem;
    font-weight: 600;
    color: #fff;
    background: var(--brand);
    border: none;
    border-radius: 0.5rem;
    cursor: pointer;
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
  }

  button:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }

  button:focus-visible {
    outline: 2px solid var(--brand-dark);
    outline-offset: 2px;
  }

  .spinner {
    width: 1rem;
    height: 1rem;
    border: 2px solid rgba(255, 255, 255, 0.4);
    border-top-color: #fff;
    border-radius: 50%;
    animation: spin 0.7s linear infinite;
  }

  @keyframes spin {
    to {
      transform: rotate(360deg);
    }
  }

  .error {
    color: #b91c1c;
    background: #fef2f2;
    border: 1px solid #fecaca;
    padding: 0.75rem 1rem;
    border-radius: 0.5rem;
    margin: 0.75rem 0 1rem;
  }

  .kpis {
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 0.75rem;
    margin-bottom: 1rem;
  }

  .kpi {
    background: #fff;
    border: 1px solid var(--line);
    border-radius: 0.75rem;
    padding: 0.875rem 1rem;
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
  }

  .kpi.decision {
    border-color: #bbf7d0;
    background: #f0fdf4;
  }

  .kpi-value {
    margin: 0;
    font-size: 1.05rem;
    font-weight: 700;
    font-variant-numeric: tabular-nums;
  }

  .kpi.decision .kpi-value {
    color: #065f46;
    font-size: 0.9rem;
    word-break: break-word;
  }

  .kpi-label {
    font-size: 0.72rem;
    color: var(--muted);
  }

  .hardware-card,
  .vram {
    background: #fff;
    border: 1px solid var(--line);
    border-radius: 0.75rem;
    padding: 1rem 1.25rem;
    margin-bottom: 1rem;
  }

  .hardware-card h3,
  .vram h3 {
    margin: 0 0 0.5rem;
    font-size: 0.95rem;
    color: #1f2937;
  }

  .hw-name {
    margin: 0;
    font-weight: 600;
  }

  .hw-qty {
    color: var(--brand);
    margin-left: 0.25rem;
  }

  .hw-meta {
    margin: 0.25rem 0 0;
    color: var(--muted);
    font-size: 0.85rem;
  }

  .bar-row {
    display: grid;
    grid-template-columns: 9rem 1fr 6.5rem;
    align-items: center;
    gap: 0.75rem;
    margin: 0.4rem 0;
    font-size: 0.85rem;
  }

  .bar-label {
    color: #374151;
  }

  .bar-track {
    height: 0.75rem;
    background: #eef2ff;
    border-radius: 9999px;
    overflow: hidden;
  }

  .bar-fill {
    height: 100%;
    background: linear-gradient(90deg, var(--brand), #3b82f6);
    border-radius: 9999px;
  }

  .bar-value {
    text-align: right;
    font-variant-numeric: tabular-nums;
    color: #111827;
    font-weight: 600;
  }

  .vram-total {
    margin: 0.75rem 0 0;
    font-weight: 600;
    color: #111827;
  }

  .calc-link-wrap {
    margin: 0 0 2rem;
  }

  .calc-link {
    font-weight: 600;
    color: var(--brand);
    text-decoration: none;
  }

  .calc-link:hover {
    text-decoration: underline;
  }

  @media (max-width: 48rem) {
    .grid {
      grid-template-columns: 1fr;
    }
    .kpis {
      grid-template-columns: repeat(2, minmax(0, 1fr));
    }
    .bar-row {
      grid-template-columns: 1fr;
      gap: 0.25rem;
    }
    .bar-value {
      text-align: left;
    }
  }
</style>
