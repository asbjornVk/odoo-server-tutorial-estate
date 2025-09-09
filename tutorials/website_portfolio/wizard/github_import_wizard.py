# Part of Odoo. See LICENSE file for full copyright and licensing details.
# -*- coding: utf-8 -*-
import re
import requests
from urllib.parse import urlparse
from odoo import api, fields, models, _
from odoo.exceptions import UserError

GITHUB_API = "https://api.github.com"

QUARANTINE_TAG = "Quarantine"
NO_MD_TAG = "NoMD"

def _first_paragraph_text(html: str, max_len: int = 240) -> str:
    """Return first readable paragraph from README HTML."""
    if not html:
        return ""
    m = re.search(r"<p[^>]*>(.*?)</p>", html, flags=re.I | re.S)
    body = m.group(1) if m else html
    text = re.sub(r"<[^>]+>", " ", body)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:max_len]

class WebsitePortfolioGithubWizard(models.TransientModel):
    _name = "website_portfolio.github_wizard"
    _description = "Import project from GitHub"

    owner = fields.Char(required=True, help="GitHub owner/user/org or full URL")
    repo = fields.Char(help="Repository name (optional if Owner contains full URL)")
    token = fields.Char(help="Optional personal access token")
    publish_now = fields.Boolean(string="Publish now", default=True)
    publish_from = fields.Datetime(string="Publish From")
    publish_to = fields.Datetime(string="Publish To")

    import_topics = fields.Boolean(string="Create tags from GitHub topics", default=True)
    import_primary_language = fields.Boolean(string="Tag with primary language", default=True)
    import_all_languages = fields.Boolean(string="Tag with all languages", default=False)

    include_private = fields.Boolean(string="Include private (requires token)")
    skip_existing = fields.Boolean(string="Skip existing repos", default=True)
    fetch_readme = fields.Boolean(string="Fetch README content", default=True)

    @api.onchange('publish_now')
    def _onchange_publish_now(self):
        if self.publish_now:
            self.publish_from = False
            self.publish_to = False

    # ---------------- Helpers ----------------
    @staticmethod
    def _rewrite_github_links(html: str, owner: str, repo: str, default_branch: str) -> str:
        """Make README <img src> and <a href> absolute to raw GitHub."""
        if not html:
            return html

        def to_raw(url: str) -> str:
            if not url:
                return url
            u = url.strip() 
            # already absolute
            if u.startswith(("http://", "https://", "mailto:")):
                # convert github "blob" to raw if present
                m = re.match(r"https?://github\.com/([^/]+)/([^/]+)/blob/([^/]+)/(.*)", u)
                if m:
                    o, r, br, path = m.groups()
                    return f"https://raw.githubusercontent.com/{o}/{r}/{br}/{path}"
                return u    
            # root-relative or relative path -> raw content
            u = u.lstrip("/")  # drop any leading slash
            return f"https://raw.githubusercontent.com/{owner}/{repo}/{default_branch}/{u}"

        # src=""
        html = re.sub(
            r'(<img\b[^>]*\bsrc=)("|\')(.*?)(\2)',
            lambda m: m.group(1) + m.group(2) + to_raw(m.group(3)) + m.group(4),
            html, flags=re.I | re.S
        )
        # href="" (use raw for direct file links)
        html = re.sub(
            r'(<a\b[^>]*\bhref=)("|\')(.*?)(\2)',
            lambda m: m.group(1) + m.group(2) + to_raw(m.group(3)) + m.group(4),
            html, flags=re.I | re.S
        )
        return html


    def _headers(self):
        h = {"Accept": "application/vnd.github+json", "User-Agent": "odoo-website-portfolio"}
        if self.token:
            h["Authorization"] = f"Bearer {self.token}"
        return h

    def _normalize_owner_repo(self, owner: str, repo: str):
        """Accept owner, owner/repo, https URL, ssh URL; strip .git."""
        owner = (owner or "").strip()
        repo = (repo or "").strip()

        def strip_git(s): return re.sub(r"\.git$", "", s or "", flags=re.I)

        if owner.startswith(("http://", "https://")):
            p = urlparse(owner)
            parts = [x for x in p.path.strip("/").split("/") if x]
            if len(parts) >= 1:
                owner = parts[0]
            if len(parts) >= 2 and not repo:
                repo = parts[1]
        elif owner.startswith("git@"):
            after = owner.split(":", 1)[-1]
            parts = [x for x in after.strip("/").split("/") if x]
            if len(parts) >= 1:
                owner = parts[0]
            if len(parts) >= 2 and not repo:
                repo = parts[1]
        elif "/" in owner and not repo:
            o, _sep, r = owner.partition("/")
            owner, repo = o, r

        return owner.strip(), strip_git(repo)

    # Topics & languages
    def _get_topics(self, owner, repo):
        url = f"{GITHUB_API}/repos/{owner}/{repo}/topics"
        r = requests.get(url, headers=self._headers(), timeout=20)
        if r.status_code == 200:
            data = r.json() or {}
            return data.get("names", []) or []
        return []

    def _get_languages(self, owner, repo):
        url = f"{GITHUB_API}/repos/{owner}/{repo}/languages"
        r = requests.get(url, headers=self._headers(), timeout=20)
        if r.status_code == 200:
            return list((r.json() or {}).keys())
        return []

    def _normalize_tag(self, s: str):
        if not s:
            return ""
        name = s.replace("-", " ").strip()
        low = name.lower()
        if low in ("csharp", "c sharp"):
            return "C#"
        return name

    def _get_repo(self, owner, repo):
        url = f"{GITHUB_API}/repos/{owner}/{repo}"
        r = requests.get(url, headers=self._headers(), timeout=20)
        if r.status_code == 404:
            raise UserError(_("Repository not found or private. Check owner/repo and token."))
        if r.status_code != 200:
            raise UserError(_("GitHub repo fetch failed (%s): %s") % (r.status_code, r.text))
        return r.json()

    def _get_readme_html(self, owner, repo):
        url = f"{GITHUB_API}/repos/{owner}/{repo}/readme"
        headers = self._headers(); headers["Accept"] = "application/vnd.github.html"
        r = requests.get(url, headers=headers, timeout=20)
        return r.text if r.status_code == 200 and r.text else ""

    def _collect_tag_names(self, meta, owner_login, repo_name):
        """Collect tag names from topics and languages based on options."""
        names = []

        if self.import_topics:
            topics = self._get_topics(owner_login, repo_name)
            if not topics:
                topics = meta.get("topics") or []
            names.extend(topics)

        if self.import_all_languages:
            names.extend(self._get_languages(owner_login, repo_name))
        elif self.import_primary_language:
            lang = meta.get("language")
            if lang:
                names.append(lang)

        norm = []
        seen = set()
        for n in names:
            nn = self._normalize_tag(n)
            if nn and nn not in seen:
                seen.add(nn); norm.append(nn)
        return norm

    def _upsert_from_meta(self, meta, publish_now, publish_from, publish_to,
                          fetch_readme, skip_existing):
        """Create or update a project record from a repo JSON."""
        Project = self.env["website_portfolio"].sudo()
        Tag = self.env["website_portfolio.tag"].sudo()

        owner_login = (meta.get("owner") or {}).get("login") or ""
        repo_name = meta.get("name") or ""
        full_name = meta.get("full_name") or f"{owner_login}/{repo_name}"
        repo_url = meta.get("html_url") or f"https://github.com/{full_name}"
        short = meta.get("description") or ""

        tag_ids = []
        for t in self._collect_tag_names(meta, owner_login, repo_name):
            tag = Tag.search([("name", "=", t)], limit=1) or Tag.create({"name": t})
            tag_ids.append(tag.id)

        # README and quarantine logic
        quarantine = False
        extra_tag_names = []
        long_html = ""

        if fetch_readme and owner_login and repo_name:
            br = meta.get("default_branch") or "main"
            long_html = self._get_readme_html(owner_login, repo_name)
            long_html = self._rewrite_github_links(long_html, owner_login, repo_name, br)

        if not (long_html or "").strip():
            # No README -> quarantine + tag
            quarantine = True
            extra_tag_names += [NO_MD_TAG, QUARANTINE_TAG]
        elif not short:
            # README exists but no short description -> derive from README
            short = _first_paragraph_text(long_html)

        # ensure extra tags exist
        for tname in extra_tag_names:
            tag = Tag.search([("name", "=", tname)], limit=1) or Tag.create({"name": tname})
            tag_ids.append(tag.id)

        # publishing state: quarantine forces unpublish
        website_published = False if quarantine else bool(publish_now)
        pf = False if quarantine or publish_now else publish_from
        pt = False if quarantine or publish_now else publish_to

        vals = {
            "name": repo_name or full_name,
            "repo_url": repo_url,
            "description_short": short,
            "description_long": long_html,
            "website_published": website_published,
            "publish_from": pf,
            "publish_to": pt,
            "tag_ids": [(6, 0, tag_ids)] if tag_ids else False,
            "github_full_name": full_name,
        }

        existing = Project.search([("github_full_name", "=", full_name)], limit=1)
        if existing:
            if skip_existing:
                return False, existing
            existing.write(vals)
            return "updated", existing
        else:
            rec = Project.create(vals)
            return "created", rec

    # -------- Actions --------

    def action_import(self):
        self.ensure_one()
        owner, repo = self._normalize_owner_repo(self.owner, self.repo)
        if not owner or not repo:
            raise UserError(_("Please provide a valid owner and repository."))

        meta = self._get_repo(owner, repo)
        status, rec = self._upsert_from_meta(
            meta, self.publish_now, self.publish_from, self.publish_to,
            self.fetch_readme, self.skip_existing,
        )
        return {
            "type": "ir.actions.act_window",
            "res_model": "website_portfolio",
            "res_id": (rec.id if rec else self.env["website_portfolio"].search(
                [("github_full_name", "=", f"{owner}/{repo}")], limit=1).id),
            "view_mode": "form",
            "target": "current",
        }

    def action_import_all(self):
        self.ensure_one()
        owner, _repo = self._normalize_owner_repo(self.owner, self.repo)
        if not owner:
            raise UserError(_("Please provide Owner (username/org)."))

        created = updated = skipped = 0
        for meta in self._iter_owner_repos(owner, self.include_private):
            result, _rec = self._upsert_from_meta(
                meta,
                self.publish_now, self.publish_from, self.publish_to,
                self.fetch_readme, self.skip_existing,
            )
            if result == "created":
                created += 1
            elif result == "updated":
                updated += 1
            else:
                skipped += 1

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("GitHub Import"),
                "message": _("Created: %s  Updated: %s  Skipped: %s") % (created, updated, skipped),
                "sticky": False,
            },
        }

    def _iter_owner_repos(self, owner, include_private=False):
        """Yield repo JSON for user/org with pagination."""
        u = requests.get(f"{GITHUB_API}/users/{owner}", headers=self._headers(), timeout=20)
        if u.status_code == 404:
            raise UserError(_("GitHub owner not found: %s") % owner)
        if u.status_code != 200:
            raise UserError(_("Owner lookup failed (%s): %s") % (u.status_code, u.text))
        is_org = (u.json().get("type") == "Organization")

        base = f"{GITHUB_API}/orgs/{owner}/repos" if is_org else f"{GITHUB_API}/users/{owner}/repos"
        params = {
            "per_page": 100,
            "type": "all" if include_private else "public",
            "sort": "full_name",
            "direction": "asc",
        }
        page = 1
        while True:
            params["page"] = page
            r = requests.get(base, headers=self._headers(), params=params, timeout=30)
            if r.status_code in (401, 403) and include_private:
                raise UserError(_("Including private repositories requires a token with 'repo' scope."))
            if r.status_code != 200:
                raise UserError(_("Repo listing failed (%s): %s") % (r.status_code, r.text))
            items = r.json() or []
            if not items:
                break
            for meta in items:
                yield meta
            if len(items) < 100:
                break
            page += 1
