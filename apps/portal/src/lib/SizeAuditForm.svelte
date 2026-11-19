<script lang="ts">
  import { sizeRequestSchema } from '$lib/schemas';

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
  let technicians = $state('');
  let totalShifts = $state('3');
  let manualsGb = $state('85');
  let workOrders = $state('450000');
  let avgTokens = $state('420');
  let peakRatio = $state('0.40');
  let avgQueries = $state('15');
  let electricityRate = $state('0.18');
  let safetyCritical = $state(true);
  let result = $state<SizingResult | null>(null);
  let error = $state('');
  let loading = $state(false);

  const currency = (value: number) =>
    '$' + value.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });

  async function submit() {
    error = '';
    if (!technicians) {
      error = 'Technicians per shift is required';
      return;
    }
    const payload = sizeRequestSchema.parse({
      audit_id: 'aud-gmao-2026-001',
      client_name: 'Helvetic Precision Manufacturing',
      deployment_constraint: deploymentMode,
      technicians_per_shift: Number(technicians),
      total_shifts: Number(totalShifts),
      documents: {
        equipment_manuals_pdf_gb: Number(manualsGb),
        historical_work_orders_count: Number(workOrders),
        average_tokens_per_page: Number(avgTokens),
      },
      concurrency: {
        peak_shift_overlap_ratio: Number(peakRatio),
        avg_queries_per_tech_shift: Number(avgQueries),
        target_p95_ttft_seconds: 1.5,
      },
      financials: { electricity_rate_kwh_usd: Number(electricityRate) },
      safety_critical: safetyCritical,
    });
    loading = true;
    try {
      const response = await fetch('/api/audit', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      result = (await response.json()) as SizingResult;
    } finally {
      loading = false;
    }
  }
</script>

<section aria-label="Size audit">
  <h2>Step 1 — Parameters</h2>
  <form>
    <label>
      Deployment mode
      <select bind:value={deploymentMode}>
        {#each MODES as mode}
          <option value={mode}>{mode}</option>
        {/each}
      </select>
    </label>
    <label>Technicians per shift <input bind:value={technicians} type="number" min="1" /></label>
    <label>Total shifts <input bind:value={totalShifts} type="number" min="1" /></label>
    <label>Manuals volume (GB) <input bind:value={manualsGb} type="number" min="0" step="0.1" /></label>
    <label>Historical work orders <input bind:value={workOrders} type="number" min="0" /></label>
    <label>Avg tokens per page <input bind:value={avgTokens} type="number" min="1" /></label>
    <label>Peak shift overlap ratio <input bind:value={peakRatio} type="number" min="0" max="1" step="0.01" /></label>
    <label>Avg queries per tech shift <input bind:value={avgQueries} type="number" min="1" /></label>
    <label>Electricity rate (USD/kWh) <input bind:value={electricityRate} type="number" min="0" step="0.01" /></label>
    <label><input type="checkbox" bind:checked={safetyCritical} /> Safety critical (HA)</label>
    <button type="button" onclick={() => void submit()} disabled={loading}>Size architecture</button>
  </form>
  {#if error}
    <p role="alert">{error}</p>
  {/if}
</section>

{#if result}
  <section aria-label="Sizing results">
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
  label {
    display: block;
    margin: 0.5rem 0;
  }
  input,
  select,
  button {
    min-height: 44px; /* WCAG 2.5.8 target size (>=44x44px) for factory-floor touch */
    font-size: 1rem;
  }
  button {
    padding: 0.5rem 1rem;
  }
  .tco,
  .vram {
    font-variant-numeric: tabular-nums;
  }
</style>
