# Tutoriel CLI & Glossaire : Diagnostic, Déploiement et Validation E2E de RAG-Architect

Ce document retrace de manière chronologique et pédagogique l'ensemble des commandes exécutées en ligne de commande pour diagnostiquer, corriger, déployer et valider l'architecture **RAG-Architect** (Portail SvelteKit sur Cloudflare Pages, Moteur de dimensionnement Python/FastAPI sur Fly.io, et Base d'audit immuable sur Cloudflare D1).

---

## Architecture du flux validé

```text
[Client / curl] 
      │  POST /api/audit (JSON)
      ▼
[Cloudflare Pages BFF] ──(1. Validation Zod)──► [Moteur Fly.io (FastAPI)]
      │                                               │  POST /api/v1/size-architecture
      │◄─────────────(2. Verdict CAPEX/OPEX)──────────┘
      │
      ├──(3. Persistance Append-Only)──► [Cloudflare D1 : audit_submissions]
      │                                        └── Trigger 21 CFR Part 11 (BEFORE DELETE)
      ▼
[HTTP/2 200 OK + JSON complet]
```

---

## Phase 1 : Tests de l'API BFF et Diagnostic de l'erreur `502`

### 1.1 Premier test de l'endpoint `/api/audit` (Validation du schéma)
L'objectif initial était de tester la route BFF (Backend-for-Frontend) directement depuis le terminal sans passer par le navigateur.

```bash
curl -i -s -X POST "https://3c62ceaa.rag-architect-portal.pages.dev/api/audit" \
  -H "Content-Type: application/json" \
  -d '{
    "audit_id": "aud-cli-test-001",
    "client_name": "Helvetic Precision Manufacturing",
    "technicians_per_shift": 4,
    "total_shifts": 3,
    "deployment_constraint": "AIR_GAPPED_EDGE",
    "documents": {
      "equipment_manuals_pdf_gb": 85,
      "historical_work_orders_count": 450000,
      "average_tokens_per_page": 420
    },
    "concurrency": {
      "peak_shift_overlap_ratio": 0.4,
      "avg_queries_per_tech_shift": 15,
      "target_p95_ttft_seconds": 1.5
    },
    "financials": {
      "electricity_rate_kwh_usd": 0.18
    }
  }'
```
* **Résultat obtenu :** `HTTP/2 400 Bad Request` avec le détail Zod : `Invalid input: expected boolean, received undefined` sur le chemin `["safety_critical"]`. Cela a confirmé que le routage Cloudflare Pages et la validation Zod fonctionnaient.

### 1.2 Isolation de l'erreur `502 Bad Gateway`
Après ajout de `"safety_critical": true`, le portail a renvoyé `HTTP/2 502` avec un corps de 37 octets : `{"error":"Sizing engine unavailable"}`. Pour savoir si le moteur Python sur Fly.io était en panne ou si le problème venait du Worker Cloudflare, nous avons testé Fly.io en direct et inspecté ses logs.

```bash
# 1. Inspecter la résolution d'URL dans le code source du portail
cat apps/portal/src/lib/config.ts

# 2. Tester directement l'API du moteur Fly.io (contournement du portail)
curl -i -s -X POST "https://rag-architect-sizing.fly.dev/api/v1/size-architecture" \
  -H "Content-Type: application/json" \
  -d '{
    "audit_id": "aud-cli-test-001",
    "client_name": "Helvetic Precision Manufacturing",
    "technicians_per_shift": 4,
    "total_shifts": 3,
    "deployment_constraint": "AIR_GAPPED_EDGE",
    "safety_critical": true,
    "documents": {
      "equipment_manuals_pdf_gb": 85,
      "historical_work_orders_count": 450000,
      "average_tokens_per_page": 420
    },
    "concurrency": {
      "peak_shift_overlap_ratio": 0.4,
      "avg_queries_per_tech_shift": 15,
      "target_p95_ttft_seconds": 1.5
    },
    "financials": {
      "electricity_rate_kwh_usd": 0.18
    }
  }'; echo ""

# 3. Consulter les journaux d'exécution de la machine Fly.io
fly logs --app rag-architect-sizing --no-tail

# 4. Vérifier la négociation TLS et HTTP/1.1 avec Fly.io
curl -v --http1.1 -s -o /dev/null -X POST "https://rag-architect-sizing.fly.dev/api/v1/size-architecture" \
  -H "Content-Type: application/json" \
  -d '{"audit_id":"aud-tls-check", ...}'
```
* **Résultat obtenu :** L'appel direct vers Fly.io a renvoyé `HTTP/2 200 OK` avec le calcul complet. Le problème venait donc exclusivement de l'appel sortant (`fetch`) exécuté depuis le Worker Cloudflare Pages.

### 1.3 Diagnostic par instrumentation temporaire du bloc `catch`
Pour capturer l'exception exacte levée par le Worker Cloudflare (masquée par un `catch` générique), nous avons injecté temporairement `engineUrl` et `detail` dans la réponse `502` de `apps/portal/src/routes/api/audit/+server.ts`, puis redéployé :

```bash
# Patch temporaire de diagnostic
python3 - << 'EOF'
path = "apps/portal/src/routes/api/audit/+server.ts"
with open(path, "r") as f:
    src = f.read()

old = """  } catch {
    return json({ error: 'Sizing engine unavailable' }, { status: 502 });
  }"""

new = """  } catch (err) {
    const detail = err instanceof Error ? err.message : String(err);
    return json({ error: 'Sizing engine unavailable', engineUrl, detail }, { status: 502 });
  }"""

assert old in src
with open(path, "w") as f:
    f.write(src.replace(old, new, 1))
EOF

# Build et déploiement de diagnostic
pnpm --filter @rag-architect/portal run build
npx wrangler pages deploy apps/portal/.svelte-kit/cloudflare \
  --project-name=rag-architect-portal \
  --branch=main
```
* **Cause racine révélée :** Le diagnostic a retourné :
  `Invalid URL: [https://rag-architect-sizing.fly.dev](https://rag-architect-sizing.fly.dev)/api/v1/size-architecture`
  La variable d'environnement `SIZING_ENGINE_URL` configurée dans Cloudflare Pages contenait un lien au format Markdown au lieu d'une URL brute.

---

## Phase 2 : Correction, Assainissement et Déploiement en Production

### 2.1 Normalisation des URLs (`config.ts`) et nettoyage du code
Nous avons implémenté une fonction `normalizeUrl()` dans `apps/portal/src/lib/config.ts` capable d'extraire automatiquement l'URL cible d'un lien Markdown `[texte](url)`, de supprimer les chevrons `< >` et les slashs finaux, et de valider le protocole `http:` ou `https:` via `new URL()`. Nous avons ensuite retiré le diagnostic temporaire de `+server.ts`.

### 2.2 Validation Git et poussée vers le dépôt distant
Une fois les tests unitaires (`vitest`), la vérification de types (`svelte-check`) et la documentation (`README.md`, `docs/progress.md`) validés :

```bash
cd /media/malek/DONNEES/pydev/RAG-Architect

# Indexation des fichiers du portail, de la documentation et de la config Fly.io
git add \
  README.md \
  docs/progress.md \
  apps/portal/src/lib/config.ts \
  apps/portal/src/lib/config.test.ts \
  apps/portal/wrangler.toml \
  services/sizing-engine/.dockerignore \
  services/sizing-engine/fly.toml

# Création d'un commit atomique documenté
git commit -m "chore(portal,sizing): harden URL normalization, D1 audit config, and Fly deployment" \
  -m "- Normalize SIZING_ENGINE_URL and TELEMETRY_WORKER_URL in config.ts to fix 502 on malformed URLs" \
  -m "- Add unit tests in config.test.ts and Cloudflare Pages config in apps/portal/wrangler.toml" \
  -m "- Add Fly.io sizing-engine deployment files and update README.md and docs/progress.md"

# Vérification de l'état local et envoi sur la branche distante
git status
git log -n 1
git push origin HEAD
```

### 2.3 Déploiement propre des deux services
```bash
# 1. Compilation et déploiement du portail sur Cloudflare Pages
cd /media/malek/DONNEES/pydev/RAG-Architect
pnpm --filter @rag-architect/portal run build
npx wrangler pages deploy apps/portal/.svelte-kit/cloudflare \
  --project-name=rag-architect-portal \
  --branch=main

# 2. Déploiement du moteur de dimensionnement sur Fly.io
cd /media/malek/DONNEES/pydev/RAG-Architect/services/sizing-engine
fly deploy --app rag-architect-sizing
```

---

## Phase 3 : Validation End-to-End (E2E) et Conformité 21 CFR Part 11

### 3.1 Requête E2E complète sur l'URL de production
```bash
cd /media/malek/DONNEES/pydev/RAG-Architect

curl -i -s -X POST "https://rag-architect-portal.pages.dev/api/audit" \
  -H "Content-Type: application/json" \
  -d '{
    "audit_id": "aud-post-deploy-001",
    "client_name": "Helvetic Precision Manufacturing",
    "technicians_per_shift": 4,
    "total_shifts": 3,
    "deployment_constraint": "AIR_GAPPED_EDGE",
    "safety_critical": true,
    "documents": {
      "equipment_manuals_pdf_gb": 85,
      "historical_work_orders_count": 450000,
      "average_tokens_per_page": 420
    },
    "concurrency": {
      "peak_shift_overlap_ratio": 0.4,
      "avg_queries_per_tech_shift": 15,
      "target_p95_ttft_seconds": 1.5
    },
    "financials": {
      "electricity_rate_kwh_usd": 0.18
    }
  }'; echo ""
```
* **Résultat :** `HTTP/2 200 OK` retournant l'architecture matérielle (`rugged-edge-l4-24g` x2), la stack LLM/Embeddings (`llama-3.2-3b-instruct-q4`, `bge-m3-industrial`), les paramètres RAG (`901 313` chunks enfants, RRF hybride) et la comparaison TCO sur 3 ans (`CAPEX $26,458.24` vs `OPEX $20,639.46`).

### 3.2 Vérification de la persistance D1 et du verrou d'immuabilité
```bash
# 1. Vérifier l'insertion dans la table audit_submissions sur la base D1 distante
npx wrangler d1 execute rag-architect-db \
  --remote \
  --config apps/telemetry-worker/wrangler.toml \
  --command="SELECT id, client_name, deployment_constraint, actor_id, created_at FROM audit_submissions ORDER BY created_at DESC LIMIT 5;"

# 2. Tester l'immuabilité 21 CFR Part 11 (toute tentative de suppression doit échouer)
npx wrangler d1 execute rag-architect-db \
  --remote \
  --config apps/telemetry-worker/wrangler.toml \
  --command="DELETE FROM audit_submissions;"
```
* **Résultat :**
  * Le `SELECT` affiche les enregistrements `aud-post-deploy-001` et `aud-cli-test-004` horodatés et signés avec `actor_id: portal-bff`.
  * Le `DELETE` est bloqué au niveau moteur SQLite par l'erreur : `audit_submissions is append-only: SQLITE_CONSTRAINT (extended: SQLITE_CONSTRAINT_TRIGGER) [code: 7500]`.

---

## Glossaire Technique des Outils, Options et Concepts

| Terme / Option | Catégorie | Définition et rôle dans le projet |
| :--- | :--- | :--- |
| **`curl -i -s -X POST`** | CLI HTTP | Client de transfert de données. `-i` inclut les en-têtes HTTP de réponse (`HTTP/2 200`), `-s` active le mode silencieux (masque la barre de progression), `-X POST` force la méthode HTTP POST. |
| **`curl -v --http1.1`** | CLI HTTP | `-v` (verbose) affiche la poignée de main TLSv1.3, les certificats SSL et la résolution DNS/IPv6. `--http1.1` force le protocole HTTP/1.1 pour tester la compatibilité avec le proxy inverse. |
| **`BFF` (Backend-for-Frontend)** | Architecture | Couche serveur légère (ici les endpoints SvelteKit `/api/*` exécutés sur Cloudflare Workers) qui valide les entrées client, appelle les microservices internes et gère la persistance D1. |
| **`Zod`** | Validation TS | Bibliothèque de validation de schémas TypeScript utilisée dans `schemas.ts` pour rejeter toute requête mal formée (`HTTP 400`) avant qu'elle n'atteigne le moteur de calcul ou la base D1. |
| **`wrangler pages deploy`** | Cloudflare CLI | Déploie le dossier compilé `.svelte-kit/cloudflare` (actifs statiques + Worker SSR/API) vers Cloudflare Pages sur la branche spécifiée (`--branch=main`). |
| **`wrangler d1 execute --remote`** | Cloudflare CLI | Exécute une requête SQL directement sur la base de données SQLite distribuée Cloudflare D1 en production (`--remote`), par opposition à la base locale de développement. |
| **`21 CFR Part 11` & `Append-Only`** | Conformité | Norme réglementaire exigeant des pistes d'audit infalsifiables. Implémentée ici via un trigger SQLite `BEFORE DELETE` (et `BEFORE UPDATE`) qui lève `ABORT` (`SQLITE_CONSTRAINT_TRIGGER`). |
| **`fly deploy` / `fly logs`** | Fly.io CLI | `fly deploy` construit l'image Docker du moteur Python FastAPI et la déploie sur une micro-VM Firecracker. `fly logs --no-tail` affiche l'historique récent des journaux sans bloquer le terminal. |
| **`Cold Start` (Démarrage à froid)** | Cloud / Serverless | Délai de démarrage d'une machine mise en veille automatique (`auto-stop` après inactivité ou limite de 5 minutes sur machine *Trial* Fly.io). |
| **`pnpm --filter <pkg>`** | Monorepo CLI | Exécute un script (`build`, `test`) uniquement sur un paquet spécifique du monorepo (`@rag-architect/portal`) sans recompiler l'ensemble du dépôt. |
| **`git push origin HEAD`** | Contrôle de version | Pousse le commit actif (`HEAD`) de la branche locale courante vers le dépôt distant `origin` sans avoir à retaper le nom complet de la branche. |