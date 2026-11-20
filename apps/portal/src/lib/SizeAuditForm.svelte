<script lang="ts">
  import { sizeRequestSchema, type SizeRequest } from '$lib/schemas';
  import { randomUuid } from '$lib/audit';

  const MODES = ['AIR_GAPPED_EDGE', 'HYBRID_CONNECTED', 'FULL_CLOUD'] as const;

  type SizingResult = {
    audit_id: string;
    verdict: {
      deployment_mode: string;
      model_stack: {
        weights_vram_gb: number;
        kv_cache_allocated_gb: number;
        vector_db_vram_gb: number;
        total_vram_required_gb: number;
        max_concurrent_streams: number;
      };
      rag_parameters: { estimated_total_child_chunks: number };
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
  let loading = $state(false);

  const currency = (value: number) =>
    '$' + value.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });

  const parseDecimal = (value: string | number): number => Number(String(value).replace(',', '.'));

  async function submit() {
    error = '';
    result = null;
    if (!technicians) {
      error = 'Technicians per shift is required';
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
  <h2>Step 1 — Parameters</h2>

  <form>
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
          <span class="hint">Runtime constraint for the sized architecture</span>
        </div>

        <div class="field span-2">
          <label for="client-name">Client name</label>
          <input id="client-name" bind:value={clientName} type="text" autocomplete="organization" />
          <span class="hint">Optional — defaults to Helvetic Precision Manufacturing</span>
        </div>

        <div class="field">
          <label for="technicians">Technicians per shift</label>
          <input id="technicians" bind:value={technicians} type="number" min="1" inputmode="numeric" />
          <span class="hint">Headcount</span>
        </div>

        <div class="field">
          <label for="total-shifts">Total shifts</label>
          <input id="total-shifts" bind:value={totalShifts} type="number" min="1" inputmode="numeric" />
          <span class="hint">Daily shifts</span>
        </div>
      </div>
    </fieldset>

    <fieldset class="group">
      <legend>Corpus documentaire</legend>
      <div class="grid">
        <div class="field">
          <label for="manuals-gb">Manuals volume (GB)</label>
          <input id="manuals-gb" bind:value={manualsGb} type="text" inputmode="decimal" />
          <span class="hint">GB of equipment manuals (PDF)</span>
        </div>

        <div class="field">
          <label for="work-orders">Historical work orders</label>
          <input id="work-orders" bind:value={workOrders} type="number" min="0" inputmode="numeric" />
          <span class="hint">Total records</span>
        </div>

        <div class="field">
          <label for="avg-tokens">Avg tokens per page</label>
          <input id="avg-tokens" bind:value={avgTokens} type="number" min="1" inputmode="numeric" />
          <span class="hint">Tokens per page</span>
        </div>
      </div>
    </fieldset>

    <fieldset class="group">
      <legend>Concurrence &amp; Latence</legend>
      <div class="grid">
        <div class="field">
          <label for="peak-ratio">Peak shift overlap ratio</label>
          <input id="peak-ratio" bind:value={peakRatio} type="text" inputmode="decimal" />
          <span class="hint">0–1 (e.g. 0.40)</span>
        </div>

        <div class="field">
          <label for="avg-queries">Avg queries per tech shift</label>
          <input id="avg-queries" bind:value={avgQueries} type="number" min="1" inputmode="numeric" />
          <span class="hint">Queries per shift</span>
        </div>

        <div class="field">
          <label for="target-ttft">Target P95 TTFT</label>
          <input id="target-ttft" bind:value={targetTtft} type="text" inputmode="decimal" />
          <span class="hint">Seconds (e.g. 1.5)</span>
        </div>
      </div>
    </fieldset>

    <fieldset class="group">
      <legend>Énergie &amp; TCO</legend>
      <div class="grid">
        <div class="field">
          <label for="electricity">Electricity rate (USD/kWh)</label>
          <input id="electricity" bind:value={electricityRate} type="text" inputmode="decimal" />
          <span class="hint">USD per kWh</span>
        </div>
      </div>
    </fieldset>

    <fieldset class="group">
      <legend>Sécurité / Haute Disponibilité</legend>
      <div class="grid">
        <div class="field checkbox">
          <div class="check-row">
            <input id="safety-critical" type="checkbox" bind:checked={safetyCritical} />
            <label for="safety-critical">Safety critical (HA)</label>
          </div>
          <span class="hint">Enforces the zero-hallucination gate and high-availability sizing</span>
        </div>
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
    <h2>Step 2 — Results</h2>
    <div class="tco" aria-label="TCO comparison">
      <p>CAPEX {currency(result.verdict.tco_3year_comparison.capex_edge_total_usd)}</p>
      <p>OPEX {currency(result.verdict.tco_3year_comparison.opex_cloud_total_usd)}</p>
    </div>
    <div class="vram" aria-label="VRAM breakdown">
      <p>Weights {result.verdict.model_stack.weights_vram_gb.toFixed(2)} GB</p>
      <p>KV cache {result.verdict.model_stack.kv_cache_allocated_gb.toFixed(2)} GB</p>
      <p>VectorDB {result.verdict.model_stack.vector_db_vram_gb.toFixed(2)} GB</p>
      <p>Total {result.verdict.model_stack.total_vram_required_gb.toFixed(2)} GB</p>
      <p>Max concurrent streams {result.verdict.model_stack.max_concurrent_streams}</p>
    </div>
    <p>Chunks {result.verdict.rag_parameters.estimated_total_child_chunks}</p>
    <p>Recommended decision: {result.verdict.tco_3year_comparison.recommended_decision}</p>
  </section>
{/if}

<style>
  .audit,
  .results {
    max-width: 52rem;
    margin: 0 auto;
  }

  h2 {
    font-size: 1.25rem;
    margin: 1.5rem 0 0.75rem;
  }

  .group {
    border: 1px solid #d1d5db;
    border-radius: 0.5rem;
    background: #fff;
    padding: 1rem 1.25rem 1.25rem;
    margin: 0 0 1rem;
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

  .field > label {
    font-weight: 500;
    font-size: 0.875rem;
    color: #111827;
  }

  .hint {
    font-size: 0.75rem;
    color: #6b7280;
  }

  input,
  select {
    width: 100%;
    min-width: 0;
    min-height: 44px; /* WCAG 2.5.8 target size (>=44x44px) for factory-floor touch */
    padding: 0.5rem 0.75rem;
    font-size: 1rem;
    color: #111827;
    background: #fff;
    border: 1px solid #9ca3af;
    border-radius: 0.375rem;
    box-sizing: border-box;
  }

  input:focus-visible,
  select:focus-visible {
    outline: 2px solid #2563eb;
    outline-offset: 1px;
    border-color: #2563eb;
  }

  .checkbox .check-row {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    min-height: 44px;
  }

  .checkbox input {
    width: 1.5rem;
    height: 1.5rem;
    min-height: 1.5rem;
    accent-color: #2563eb;
  }

  .checkbox label {
    font-weight: 500;
    font-size: 0.875rem;
    color: #111827;
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
    background: #2563eb;
    border: none;
    border-radius: 0.375rem;
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
    outline: 2px solid #1d4ed8;
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
    border-radius: 0.375rem;
    margin: 0.75rem 0 1rem;
  }

  .tco,
  .vram {
    font-variant-numeric: tabular-nums;
    display: grid;
    gap: 0.25rem;
    padding: 0.75rem 1rem;
    border: 1px solid #e5e7eb;
    border-radius: 0.375rem;
    background: #f9fafb;
    margin: 0.5rem 0;
  }

  .tco p,
  .vram p {
    margin: 0;
  }

  @media (max-width: 40rem) {
    .grid {
      grid-template-columns: 1fr;
    }
  }
</style>
