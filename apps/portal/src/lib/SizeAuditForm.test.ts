// CMMI Level 3 Verification Suite — Size Audit Form (TEST-UI-001)
// Traceability: M5 portal UI, deployment-mode toggles, TCO/VRAM rendering.
import { describe, expect, it, vi } from 'vitest';
import { fireEvent, render, screen } from '@testing-library/svelte';

import SizeAuditForm from './SizeAuditForm.svelte';

describe('TEST-UI-001 — Size Audit Form', () => {
  it('renders the three deployment modes and toggles between them', async () => {
    render(SizeAuditForm);
    const mode = screen.getByLabelText('Deployment mode') as HTMLSelectElement;
    expect(mode).toBeInTheDocument();
    const options = Array.from(mode.options).map((o) => o.value);
    expect(options).toEqual(expect.arrayContaining(['AIR_GAPPED_EDGE', 'HYBRID_CONNECTED', 'FULL_CLOUD']));

    await fireEvent.change(mode, { target: { value: 'HYBRID_CONNECTED' } });
    expect(mode.value).toBe('HYBRID_CONNECTED');
  });

  it('shows validation errors for invalid input on submit', async () => {
    render(SizeAuditForm);
    const submit = screen.getByRole('button', { name: /size architecture/i });
    await fireEvent.click(submit);
    expect(screen.getByText(/technicians per shift is required/i)).toBeInTheDocument();
  });

  it('renders TCO CAPEX vs OPEX and VRAM breakdown after a valid submit', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        audit_id: 'aud-gmao-2026-001',
        verdict: {
          deployment_mode: 'AIR_GAPPED_EDGE',
          model_stack: {
            weights_vram_gb: 1.85,
            kv_cache_allocated_gb: 4.66,
            vector_db_vram_gb: 1.15,
            total_vram_required_gb: 10.96,
            max_concurrent_streams: 14,
          },
          rag_parameters: { estimated_total_child_chunks: 901313 },
          tco_3year_comparison: {
            hardware_capex_usd: 16420.0,
            energy_and_maint_3yr_usd: 10038.24,
            capex_edge_total_usd: 26458.24,
            opex_cloud_total_usd: 54531.94,
            net_savings_usd: 28073.7,
            recommended_decision: 'CAPEX_ON_PREM_EDGE',
          },
        },
      }),
    }));

    render(SizeAuditForm);
    await fireEvent.input(screen.getByLabelText('Technicians per shift'), { target: { value: '35' } });
    const submit = screen.getByRole('button', { name: /size architecture/i });
    await fireEvent.click(submit);

    expect(await screen.findByText(/CAPEX \$26,458.24/i)).toBeInTheDocument();
    expect(await screen.findByText(/OPEX \$54,531.94/i)).toBeInTheDocument();
    expect(await screen.findByText(/10.96 GB/i)).toBeInTheDocument();
    vi.unstubAllGlobals();
  });

  it('shows the server error and no results when the BFF returns a non-2xx', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: false,
      status: 502,
      json: async () => ({ error: 'Sizing engine unavailable' }),
    }));
    render(SizeAuditForm);
    await fireEvent.input(screen.getByLabelText('Technicians per shift'), { target: { value: '35' } });
    await fireEvent.click(screen.getByRole('button', { name: /size architecture/i }));
    expect(await screen.findByRole('alert')).toHaveTextContent(/Sizing engine unavailable/i);
    expect(screen.queryByText(/CAPEX \$/i)).not.toBeInTheDocument();
    vi.unstubAllGlobals();
  });

  it('shows a network error when fetch rejects', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new Error('network down')));
    render(SizeAuditForm);
    await fireEvent.input(screen.getByLabelText('Technicians per shift'), { target: { value: '35' } });
    await fireEvent.click(screen.getByRole('button', { name: /size architecture/i }));
    expect(await screen.findByRole('alert')).toHaveTextContent(/Network error/i);
    vi.unstubAllGlobals();
  });

  it('parses comma-decimal inputs and sends a unique audit_id', async () => {
    let capturedBody: string | undefined;
    vi.stubGlobal('fetch', vi.fn().mockImplementation(async (_url: string, init?: { body?: string }) => {
      capturedBody = init?.body;
      return {
        ok: true,
        json: async () => ({
          audit_id: 'x',
          verdict: {
            deployment_mode: 'AIR_GAPPED_EDGE',
            model_stack: {
              weights_vram_gb: 1.85,
              kv_cache_allocated_gb: 4.66,
              vector_db_vram_gb: 1.15,
              total_vram_required_gb: 10.96,
              max_concurrent_streams: 14,
            },
            rag_parameters: { estimated_total_child_chunks: 901313 },
            tco_3year_comparison: {
              hardware_capex_usd: 16420,
              energy_and_maint_3yr_usd: 10038.24,
              capex_edge_total_usd: 26458.24,
              opex_cloud_total_usd: 54531.94,
              net_savings_usd: 28073.7,
              recommended_decision: 'CAPEX_ON_PREM_EDGE',
            },
          },
        }),
      };
    }));

    render(SizeAuditForm);
    await fireEvent.input(screen.getByLabelText('Technicians per shift'), { target: { value: '35' } });
    await fireEvent.input(screen.getByLabelText('Peak shift overlap ratio'), { target: { value: '0,40' } });
    await fireEvent.click(screen.getByRole('button', { name: /size architecture/i }));

    await screen.findByText(/CAPEX \$26,458.24/i);
    const sent = JSON.parse(capturedBody ?? '{}');
    expect(sent.concurrency.peak_shift_overlap_ratio).toBe(0.4);
    expect(sent.audit_id).toMatch(/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i);
    vi.unstubAllGlobals();
  });
});
