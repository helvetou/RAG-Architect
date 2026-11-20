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
          target_p95_ttft_seconds: 1.5,
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
    <label>Client name <input bind:value={clientName} type="text" /></label>
    <label>Technicians per shift <input bind:value={technicians} type="number" min="1" /></label>
    <label>Total shifts <input bind:value={totalShifts} type="number" min="1" /></label>
    <label>Manuals volume (GB) <input bind:value={manualsGb} type="text" inputmode="decimal" /></label>
    <label>Historical work orders <input bind:value={workOrders} type="number" min="0" /></label>
    <label>Avg tokens per page <input bind:value={avgTokens} type="number" min="1" /></label>
    <label>Peak shift overlap ratio <input bind:value={peakRatio} type="text" inputmode="decimal" /></label>
    <label>Avg queries per tech shift <input bind:value={avgQueries} type="number" min="1" /></label>
    <label>Electricity rate (USD/kWh) <input bind:value={electricityRate} type="text" inputmode="decimal" /></label>
    <label><input type="checkbox" bind:checked={safetyCritical} /> Safety critical (HA)</label>
    <button type="button" onclick={() => void submit()} disabled={loading} aria-busy={loading}>
      {loading ? 'Sizing…' : 'Size architecture'}
    </button>
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
