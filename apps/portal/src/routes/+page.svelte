<script lang="ts">
  import SizeAuditForm from '$lib/SizeAuditForm.svelte';
</script>

<section class="page">
  <div class="page-head">
    <h1>Dimensionnement d'architecture</h1>
    <p>Calculez la configuration Edge/Cloud optimale et comparez le TCO sur 3 ans.</p>
  </div>
  <SizeAuditForm />
</section>

<style>
  .page {
    max-width: 72rem;
    margin: 0 auto;
  }

  .page-head {
    margin-bottom: 1.25rem;
  }

  .page-head h1 {
    font-size: 1.5rem;
    margin: 0 0 0.25rem;
  }

  .page-head p {
    color: var(--muted);
    margin: 0;
  }
</style>
