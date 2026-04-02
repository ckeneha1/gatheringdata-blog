# Spec: gatheringdata.blog Rebuild

**Status:** Draft — awaiting alignment
**Created:** April 2026
**Repo to create:** `ckeneha1/gatheringdata-blog`

---

## Problem Statement

`gatheringdata.blog` has sat dormant since August 2023. It's on WordPress.com in a default, unconfigured state — wrong title, no real content, no design. More importantly, WordPress.com is a black box: content isn't version-controlled, the theme can't be owned as code, and there's no meaningful pathway to using the site as a full-stack learning playground.

The goal is to rebuild the site on a stack that serves three purposes simultaneously:
1. **Portfolio** — a place that represents Connor's work and thinking to the world
2. **Blog** — a publishing platform for sharing learnings from projects and professional musings
3. **Playground** — a codebase Connor owns and can extend as a vehicle for learning full-stack development

---

## Decision It Unlocks

Once this exists, every project in the portfolio (MtG analytics, Tobin's Q, macro indicators, etc.) has a natural home for writeups. The site itself becomes a compounding asset: each project published makes the next one more worth publishing.

---

## Architecture

### Framework: Astro
Astro is a static site generator well-suited to content-heavy sites. Key properties relevant here:
- Posts are Markdown/MDX files — version controlled, diffable, reviewable in PRs, no database dependency
- Ships zero JavaScript by default (fast, simple)
- **Content Collections** — a built-in TypeScript schema system for validating frontmatter on posts. This is the first natural touch point for Connor's interest in contract testing applied to content
- Component model (similar to React) enables gradual introduction of interactivity as a learning project
- Strong documentation, active community

### Hosting: Netlify
Netlify over GitHub Pages for two reasons:
1. **Deploy previews** — every PR automatically gets a live preview URL. This is how professional teams review frontend changes; we'll use it from day one
2. **Serverless functions** — as Connor builds interactive features (data visualizations, API integrations), Netlify Functions provide a backend layer without managing a server

Free tier limits: 100GB bandwidth/month, 125k function invocations/month. More than sufficient for a personal site.

### Source control: GitHub
Repo: `ckeneha1/gatheringdata-blog`
Workflow: push to `main` → Netlify auto-deploys. Feature branches + PRs for all changes, including new posts.

### Domain: DreamHost → Netlify DNS
No domain transfer needed. Process:
1. Add custom domain in Netlify dashboard
2. Netlify provides DNS values (A record or CNAME)
3. Update records in DreamHost panel
4. Netlify auto-provisions SSL via Let's Encrypt
5. WordPress.com subscription can be cancelled or left to expire

---

## Site Structure

```
/                   → Home (intro, featured work, recent posts)
/blog               → All posts, chronological
/blog/[slug]        → Individual post
/projects           → Portfolio of projects with status and links
/about              → Who Connor is, what this site is
```

Optional later:
```
/now                → A "now page" — what I'm working on currently (common in personal sites)
/uses               → Tools, stack, setup
```

### Content Model (Astro Content Collections)

**Post frontmatter schema:**
```typescript
{
  title: string
  date: Date
  description: string
  tags: string[]         // e.g. ["data-science", "experimentation", "mtg"]
  status: "draft" | "published"
  project?: string       // links post to a portfolio project
}
```

**Project frontmatter schema:**
```typescript
{
  title: string
  description: string
  status: "planned" | "in-progress" | "complete"
  tags: string[]
  repo?: string          // GitHub URL
  site?: string          // live URL if applicable
  started: Date
}
```

The schema validation is enforced at build time by TypeScript — Astro will throw a build error if a post is missing required fields. This is contract testing for content.

---

## Phased Build Plan

### Phase 1: Foundation (get something live)
- [ ] Initialize Astro project using the official blog starter template
- [ ] Set up GitHub repo `ckeneha1/gatheringdata-blog`
- [ ] Connect repo to Netlify (auto-deploy on push to main)
- [ ] Add custom domain in Netlify, update DNS in DreamHost
- [ ] Verify SSL and live site at gatheringdata.blog
- [ ] Establish branch + PR workflow

**Learning goals this phase:** Astro project structure, Netlify deploy pipeline, DNS fundamentals, CI/CD basics

### Phase 2: Structure & Design
- [ ] Implement site structure (Home, Blog, Projects, About)
- [ ] Define and enforce content collection schemas
- [ ] Customize theme/design (typography, color palette, layout)
- [ ] Set up `tags` filtering on blog index

**Learning goals this phase:** Astro components and layouts, TypeScript basics, CSS fundamentals, content modeling

### Phase 3: First Content
- [ ] Write About page
- [ ] Add Projects page with initial portfolio entries (even if sparse — planned projects count)
- [ ] Publish first post (natural candidate: "Why I rebuilt this site" — documents the technical decisions, establishes the voice)

**Learning goals this phase:** MDX (Markdown + components), writing for a technical audience, using git for content workflow

### Phase 4: Playground Features (ongoing, project-driven)
As individual projects get built, each becomes:
- A Projects entry
- One or more blog posts
- Potentially an embedded interactive feature (a chart, a live query, a small tool)

Serverless functions (Netlify Functions) introduced here when first needed — e.g., a live data fetch for the macro indicators dashboard.

---

## Responsible Ownership Checklist

These are one-time setup tasks, not ongoing maintenance:

- [ ] **DreamHost:** Enable domain auto-renewal, confirm expiry date, enable 2FA on account
- [ ] **Netlify:** Enable 2FA on account
- [ ] **GitHub:** Confirm 2FA is enabled on ckeneha1
- [ ] **WordPress.com:** Cancel subscription after DNS is confirmed working (don't cancel before — gives a rollback window)
- [ ] **SSL:** Verify auto-renewal is enabled in Netlify (it is by default via Let's Encrypt — just confirm)
- [ ] **Content backups:** Not needed — the GitHub repo IS the backup. Everything lives in files.

The key insight on responsible ownership with this stack: because content is in git, there is no "backup problem." The repo is the source of truth. WordPress's backup problem (database exports, plugin dependencies) doesn't exist here.

---

## Testing Plan

Static sites test differently than applications:

| What | How | When |
|---|---|---|
| Content schema | Astro TypeScript validation | At build time — broken schema = failed deploy |
| Broken links | `astro-link-checker` or similar | CI step on PRs |
| Build validity | Netlify build | Every push — failed build blocks deploy |
| Accessibility | Lighthouse CI | PRs (optional, add in Phase 2) |
| Visual correctness | Netlify deploy previews | Every PR gets a live preview URL |

The content schema validation is the most important: it means a post with a missing `title` or malformed `date` will fail the build before it ever goes live.

---

## Scale Considerations

A static site is essentially infinitely scalable for traffic — Netlify's CDN handles it. What breaks first:

- **Netlify Functions:** Free tier allows 125k invocations/month. Relevant when we add live data features (Phase 4). Not a concern now.
- **Build times:** Astro builds are fast. At hundreds of posts it's still seconds. Not a concern.
- **Content management:** At 50+ posts, managing Markdown files directly gets unwieldy. At that point, a headless CMS (like Contentlayer or Sanity) could sit in front of the same Astro frontend. Not a concern now — file-based is the right call for Phase 1-3.

---

## Design Direction

**Aesthetic reference:** Lenny's Newsletter (lennysnewsletter.com) — editorial, content-first, generous whitespace, clean serif typography. Simple, not sparse.

**Font:** Spectral (Google Fonts) — the same serif family Lenny's uses. Conveys authority without being stuffy. Body text in regular weight, headings in semibold.

**Color palette:**
- Background: `#ffffff`
- Body text: `#363737`
- Secondary text: `#868787`
- Accent (replaces Lenny's orange): `#b2d4e5` — used for links, highlights, interactive elements, subtle backgrounds
- Borders/dividers: `#dddddd`

**Layout:** Single-column, content width ~680px, centered. Generous vertical spacing between sections. Navigation minimal — logo left, links right.

**Post list:** Title, date, short description. No cover images initially (add in Phase 2 if desired). Clean, scannable.

---

## First Post

**"About Me"** — an outward-facing version of `working_with_me.md`. Not a resume, not a bio — a genuine explanation of who Connor is, how he thinks, what he's building, and why this site exists. Sets the tone for the whole publication.

Subsequent posts will be project-driven: each project in the portfolio generates one or more writeups as it gets built.

---

## WordPress.com Migration Notes

Connor is on the **free plan** — no subscription to cancel, no cost to walk away from. Steps:
1. Add `gatheringdata.blog` as custom domain in Netlify
2. Update DNS in DreamHost to point to Netlify's servers
3. Verify SSL auto-provisions (Netlify + Let's Encrypt, automatic)
4. WordPress.com free site will continue to exist at a `*.wordpress.com` subdomain indefinitely — no action needed

---

## Open Questions

None — all resolved. Ready to build Phase 1.
