<script lang="ts">
  import '../app.css';

  let { children } = $props();
</script>

<div class="shell">
  <header class="site-header">
    <a class="brand" href="/">
      <span class="brand-mark" aria-hidden="true">RA</span>
      <span class="brand-text">
        <strong>RAG-Architect</strong>
        <small>Audit Portal · GMAO v3.0</small>
      </span>
    </a>
    <span class="pill">GMP-qualified · BL-06 Release 1.0</span>
  </header>

  <main class="site-main">{@render children()}</main>

  <footer class="site-footer">
    <span>rag-architect.helveticore.com</span>
    <span>21 CFR Part 11 · CMMI-DEV L3</span>
  </footer>
</div>

<style>
  .shell {
    min-height: 100vh;
    display: flex;
    flex-direction: column;
  }

  .site-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 1rem;
    padding: 0.875rem 1.5rem;
    background: #0b1220;
    color: #fff;
  }

  .brand {
    display: inline-flex;
    align-items: center;
    gap: 0.625rem;
    color: inherit;
    text-decoration: none;
  }

  .brand-mark {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 2.25rem;
    height: 2.25rem;
    border-radius: 0.5rem;
    background: var(--brand);
    font-weight: 800;
    letter-spacing: 0.02em;
  }

  .brand-text {
    display: flex;
    flex-direction: column;
    line-height: 1.1;
  }

  .brand-text strong {
    font-size: 1rem;
  }

  .brand-text small {
    color: #94a3b8;
    font-size: 0.72rem;
  }

  .pill {
    font-size: 0.72rem;
    color: #bbf7d0;
    background: rgba(34, 197, 94, 0.15);
    border: 1px solid rgba(34, 197, 94, 0.35);
    padding: 0.25rem 0.6rem;
    border-radius: 9999px;
    white-space: nowrap;
  }

  .site-main {
    flex: 1;
    width: 100%;
    padding: 1.5rem 1rem 3rem;
  }

  .site-footer {
    display: flex;
    justify-content: space-between;
    gap: 1rem;
    padding: 0.875rem 1.5rem;
    border-top: 1px solid var(--line);
    color: var(--muted);
    font-size: 0.75rem;
  }

  @media (max-width: 40rem) {
    .site-header {
      flex-wrap: wrap;
    }
    .pill {
      display: none;
    }
    .site-footer {
      flex-direction: column;
    }
  }
</style>
