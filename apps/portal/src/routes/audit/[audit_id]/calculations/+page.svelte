<script lang="ts">
  interface ReportData {
    audit: {
      id: string;
      clientName: string;
      deploymentConstraint: string;
      createdAt: number;
      actorId: string;
      inputSha256: string;
      outputSha256: string;
      specVersion: string;
      modelVersion: string;
    };
    calculations: Array<{
      step_id: string;
      label: string;
      formula: string;
      inputs: Record<string, string | number>;
      expression: string;
      result: string | number;
      unit: string;
      spec_section: string;
    }>;
  }

  let { data }: { data: ReportData } = $props();

  const formatDate = (unixSeconds: number) =>
    new Date(unixSeconds * 1000).toISOString().replace('T', ' ').slice(0, 19) + ' UTC';

  const inputEntries = (inputs: Record<string, string | number>) => Object.entries(inputs);
</script>

<svelte:head>
  <title>Justification des calculs — {data.audit.id}</title>
</svelte:head>

<article class="report">
  <header class="report-header">
    <h1>Justification des calculs</h1>
    <p class="subtitle">Dimensionnement RAG-Architect — traçabilité complète de bout en bout</p>

    <dl class="meta">
      <div><dt>Audit ID</dt><dd>{data.audit.id}</dd></div>
      <div><dt>Client</dt><dd>{data.audit.clientName}</dd></div>
      <div><dt>Mode</dt><dd>{data.audit.deploymentConstraint}</dd></div>
      <div><dt>Date</dt><dd>{formatDate(data.audit.createdAt)}</dd></div>
      <div><dt>Acteur</dt><dd>{data.audit.actorId}</dd></div>
      <div><dt>Spec</dt><dd>{data.audit.specVersion}</dd></div>
      <div><dt>Modèle</dt><dd>{data.audit.modelVersion}</dd></div>
      <div><dt>Hash entrée</dt><dd class="mono">{data.audit.inputSha256}</dd></div>
      <div><dt>Hash sortie</dt><dd class="mono">{data.audit.outputSha256}</dd></div>
    </dl>
  </header>

  <ol class="steps">
    {#each data.calculations as step, i}
      <li class="step">
        <div class="step-head">
          <span class="step-no">{i + 1}</span>
          <h2>{step.label}</h2>
          <span class="badge">§{step.spec_section}</span>
        </div>

        <div class="formula" aria-label="formule">formule&nbsp;: <code>{step.formula}</code></div>

        <div class="expression" aria-label="substitution chiffrée">
          <code>{step.expression}</code>
          <span class="result">= {step.result} {step.unit}</span>
        </div>

        {#if inputEntries(step.inputs).length > 0}
          <dl class="inputs">
            {#each inputEntries(step.inputs) as [key, value]}
              <div><dt>{key}</dt><dd>{value}</dd></div>
            {/each}
          </dl>
        {/if}
      </li>
    {/each}
  </ol>

  <footer class="report-footer">
    <p>Rapport généré à partir de la trace de calcul déterministe persistée dans D1 (append-only, 21 CFR Part 11).</p>
    <div class="signature">
      <div class="sign-block"><span>QA / Validation</span></div>
      <div class="sign-block"><span>Date</span></div>
    </div>
  </footer>
</article>

<style>
  .report {
    max-width: 56rem;
    margin: 0 auto;
    padding: 2rem 1.25rem;
    font-family: ui-sans-serif, system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif;
    color: #111827;
  }

  .report-header {
    border-bottom: 2px solid #e5e7eb;
    padding-bottom: 1.25rem;
    margin-bottom: 1.5rem;
  }

  h1 {
    font-size: 1.75rem;
    margin: 0 0 0.25rem;
  }

  .subtitle {
    color: #6b7280;
    margin: 0 0 1rem;
  }

  .meta {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(15rem, 1fr));
    gap: 0.5rem 1.5rem;
    margin: 0;
  }

  .meta div,
  .inputs div {
    display: flex;
    gap: 0.5rem;
  }

  .meta dt,
  .inputs dt {
    font-weight: 600;
    color: #4b5563;
    min-width: 6.5rem;
  }

  .meta dd,
  .inputs dd {
    margin: 0;
    word-break: break-all;
  }

  .mono,
  code {
    font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  }

  .steps {
    list-style: none;
    padding: 0;
    margin: 0;
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
  }

  .step {
    border: 1px solid #e5e7eb;
    border-radius: 0.5rem;
    background: #fff;
    padding: 0.875rem 1rem;
  }

  .step-head {
    display: flex;
    align-items: center;
    gap: 0.625rem;
    margin-bottom: 0.5rem;
  }

  .step-no {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 1.5rem;
    height: 1.5rem;
    border-radius: 9999px;
    background: #1d4ed8;
    color: #fff;
    font-weight: 700;
    font-size: 0.75rem;
    flex: none;
  }

  .step-head h2 {
    font-size: 1rem;
    margin: 0;
  }

  .badge {
    margin-left: auto;
    font-size: 0.7rem;
    font-weight: 600;
    color: #1d4ed8;
    background: #eff6ff;
    border: 1px solid #bfdbfe;
    border-radius: 0.25rem;
    padding: 0.1rem 0.4rem;
  }

  .formula {
    color: #6b7280;
    font-size: 0.85rem;
    margin-bottom: 0.35rem;
  }

  .expression {
    background: #f9fafb;
    border: 1px solid #e5e7eb;
    border-radius: 0.375rem;
    padding: 0.5rem 0.75rem;
    display: flex;
    flex-wrap: wrap;
    align-items: baseline;
    gap: 0.5rem;
    font-size: 0.95rem;
  }

  .expression code {
    white-space: pre-wrap;
    word-break: break-word;
  }

  .result {
    margin-left: auto;
    font-weight: 700;
    color: #065f46;
    white-space: nowrap;
  }

  .inputs {
    display: flex;
    flex-wrap: wrap;
    gap: 0.35rem 1.25rem;
    margin: 0.5rem 0 0;
    font-size: 0.8rem;
    color: #4b5563;
  }

  .inputs dt {
    min-width: auto;
    font-weight: 600;
  }

  .report-footer {
    margin-top: 2rem;
    border-top: 1px solid #e5e7eb;
    padding-top: 1rem;
    color: #6b7280;
    font-size: 0.85rem;
  }

  .signature {
    display: flex;
    gap: 2rem;
    margin-top: 1.5rem;
  }

  .sign-block {
    border-top: 1px solid #9ca3af;
    padding-top: 0.4rem;
    width: 12rem;
    color: #374151;
    font-weight: 500;
  }

  @media print {
    .step {
      break-inside: avoid;
    }
  }
</style>
