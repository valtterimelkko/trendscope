---
name: domain-name-brainstormer
description: Generates creative domain name ideas and verifies availability via Porkbun API (or WHOIS fallback) before suggesting them. Only recommends domains that are actually available.
---

# Domain Name Brainstormer

This skill helps you find available domain names for your project. It generates candidates, **checks availability using Porkbun API** (with WHOIS fallback), and only suggests domains you can actually register.

## Prerequisites

### Option 1: Porkbun API (Recommended - Most Accurate)

1. Create a Porkbun account at [porkbun.com](https://porkbun.com)
2. Generate API credentials:
   - Go to https://porkbun.com/account/api
   - Create an API key (or use an existing one)
   - Copy your API Key and Secret Key
3. Store credentials in `.env` file in project root:
   ```bash
   # Create .env file in project root with your credentials:
   PORKBUN_API_KEY=your-actual-api-key
   PORKBUN_API_SECRET=your-actual-secret-key
   ```

   **Important**: `.env` is in `.gitignore` and will NOT be committed to git. This is secure.

**Alternative (GLM-5 Desktop only)**: If using GLM-5 Desktop, you can set environment variables in your shell profile:
```bash
# Add to ~/.bashrc or ~/.zshrc
export PORKBUN_API_KEY="your-api-key"
export PORKBUN_API_SECRET="your-api-secret"
```

**Note for GLM-5 Web/Mobile**: GLM-5 Web and Mobile don't load shell profiles automatically, so the `.env` file approach is required.

### Option 2: WHOIS (Fallback - Less Reliable)

Install the `whois` command-line tool:
```bash
sudo apt install whois
```

**Important**: WHOIS verification is less reliable than Porkbun API. Some domains marked as "available" by WHOIS may actually be taken. For best results, use Porkbun API.

**Note**: This skill requires Linux and system shell access.

## When to Use This Skill

- Starting a new project, company, or product
- Creating a personal brand or portfolio
- Rebranding or launching a side project
- Finding available alternatives when your first choice is taken

## How It Works

1. **Understand your project** — Gather context about what you're building
2. **Generate 15-20 candidates** — Create names using proven strategies
3. **Check availability** — Run the helper script on all candidates
4. **Present only available domains** — No false promises
5. **Explain the rationale** — Why each available name works

## The Availability Check Script

Location: `.shared/scripts/check-domain.sh`

### Usage

```bash
# Check a single domain
.shared/scripts/check-domain.sh example.com

# Check multiple domains
.shared/scripts/check-domain.sh example.com mysite.io coolapp.dev

# Check one name across multiple TLDs
.shared/scripts/check-domain.sh myproject .com .io .dev .ai .co

# Pipe a list of domains
echo -e "domain1.com\ndomain2.io" | .shared/scripts/check-domain.sh
```

### Output with Porkbun API

```
Using Porkbun API for domain verification (most accurate)

Checking 3 domain(s)...

✓ myproject.dev - AVAILABLE (Porkbun verified)
✗ myproject.com - Taken (Porkbun verified)
✓ myproject.io - AVAILABLE (Porkbun verified)

Done. Checked 3 domain(s).
```

### Output with WHOIS Fallback

```
Using WHOIS for domain verification (less reliable, consider configuring Porkbun API)

Checking 3 domain(s)...

✓ myproject.dev - AVAILABLE (WHOIS - less reliable)
✗ myproject.com - Taken (GoDaddy)
✓ myproject.io - AVAILABLE (WHOIS - less reliable)

Done. Checked 3 domain(s).
```

### Requirements

- **Porkbun API (recommended)**:
  - `PORKBUN_API_KEY` environment variable
  - `PORKBUN_API_SECRET` environment variable
  - `curl` command-line tool (usually pre-installed)

- **WHOIS (fallback)**:
  - Linux with `whois` installed (`sudo apt install whois`)
  - Slower and less reliable than Porkbun API

## Example Workflow

**User**: "I'm building a tool for developers to share code snippets. Suggest domain names."

**Claude's Process**:

1. Generate candidates using naming strategies:
   - `snippetbox`, `codeclip`, `devpaste`, `snipshare`
   - `pastedev`, `codebin`, `sniphub`, `clipcode`
   - `sharesnip`, `devsnip`, `codestash`, `snippy`

2. Run availability check:
   ```bash
   .shared/scripts/check-domain.sh snippetbox codeclip devpaste snipshare pastedev codebin sniphub clipcode .com .io .dev
   ```

3. Present only verified available domains with rationale.

**Example Output**:

```
## Available Domains (Verified)

1. **sniphub.dev** ✓
   - Short (7 chars), uses familiar "hub" pattern
   - .dev extension perfect for developer tools
   - Passes radio test: easy to spell over phone

2. **codestash.io** ✓
   - Implies saving/storing code
   - Memorable metaphor (stash = hidden collection)
   - .io signals tech product

3. **clipcode.com** ✓
   - Action word "clip" implies quick capture
   - .com for universal recognition
   - No double-letter confusion

## Not Available
- snippetbox.com - Taken
- codeclip.io - Taken

Want me to generate more candidates and check those?
```

## Name Generation Strategies

Use these proven techniques to generate candidates:

### Portmanteaus
Combine two relevant words:
- Pinterest = Pin + Interest
- Groupon = Group + Coupon
- Instacart = Instant + Cart

### Intentional Misspellings
Remove vowels or alter spelling:
- Lyft, Tumblr, Flickr, Fiverr
- Creates unique, trademarkable names

### Prefix/Suffix Patterns
Use common patterns:
- `Get_____`: GetResponse, GetPocket
- `_____ly`: Grammarly, Bitly, Calendly
- `_____ify`: Spotify, Shopify, Testify
- `_____hub`: GitHub, DocHub, DesignHub
- `_____base`: Codebase, Coinbase, Firebase

### Action Verbs
Names that imply doing:
- Zoom, Slack, Notion, Figma, Canva

### Abstract/Metaphor
Unrelated words that evoke feeling:
- Apple, Amazon, Asana (yoga pose = focus)
- Slack (opposite of busy = calm communication)

### Invented Words
Create new, phonetically pleasing words:
- Hulu, Kodak, Xerox, Vimeo
- 2-3 syllables, easy consonant-vowel patterns

## What Makes a Good Domain

### The Radio Test
Can someone hear the name and type it correctly?

✓ **Passes**: `codebox.io` — unambiguous spelling
✗ **Fails**: `writecode.io` — "write" or "right"?

### Quick Checklist

| Criterion | Target |
|-----------|--------|
| Length | Under 12 characters ideal |
| Syllables | 2-3 syllables |
| Spelling | Obvious from pronunciation |
| Typing | No awkward key combinations |
| Uniqueness | Distinct from competitors |

## Pitfalls to Avoid

### Unintended Word Combinations
Read the name as one string — what else could it spell?
- `expertsexchange.com` → reads as something else
- `penisland.com` → Pen Island, but...
- `speedofart.com` → Speed of Art, but...

**Fix**: Check the domain as a single lowercase string.

### Double Letters at Boundaries
When words meet, doubled letters cause confusion:
- `pressstart.com` — Is it "press start" or "pres start"?
- `accessstorage.com` — Three S's in a row

**Fix**: Avoid or hyphenate (but hyphens have their own issues).

### Homophones
Words that sound like other words:
- `their/there/they're`, `write/right`, `new/knew`
- Confusing when spoken aloud

### Plural Confusion
Users will try both:
- If you register `app.com`, someone will try `apps.com`
- Consider registering both if affordable

### Hard to Spell
If you need to spell it out, it's too complex:
- `acquisitions.io` — "Is that with a 'c' or an 's'?"
- `entrepreneur.co` — Common misspelling

## TLD Guide

| TLD | Best For | Notes |
|-----|----------|-------|
| **.com** | Universal credibility | Still the gold standard |
| **.io** | Tech/developer tools | Popular with startups |
| **.dev** | Developer products | Requires HTTPS |
| **.ai** | AI/ML products | Increasingly common |
| **.app** | Mobile/web apps | Requires HTTPS |
| **.co** | .com alternative | Risk: users type .com instead |

### TLD Caveats

- **.io** is technically British Indian Ocean Territory — some avoid for ethical reasons
- **Country TLDs** (.de, .fi, .uk) may have residency requirements
- **.co** causes typo confusion with .com — may lose traffic
- **New TLDs** (.xyz, .online) can seem less credible to non-tech users

## Pricing Context

- **Standard .com**: ~$10-15/year
- **Premium TLDs** (.io, .ai, .dev): ~$30-60/year
- **Country TLDs**: Varies by country

Note: This skill checks availability only. Pricing varies by registrar. Check your preferred registrar for exact costs.

## After Finding a Domain

Once you've selected an available domain:

1. **Register immediately** — Good domains get taken fast
2. **Consider variations** — Register .com + .io to protect brand
3. **Check social handles** — Manually verify @username availability on Twitter, Instagram, GitHub
4. **Trademark search** — Manually search USPTO or your country's trademark database
5. **Say it aloud** — Test with friends, does it pass the radio test?

## Limitations

This skill:
- ✓ Checks domain availability via Porkbun API (accurate) or WHOIS (less reliable)
- ✓ Generates creative name candidates
- ✓ Provides naming rationale
- ✓ Provides pricing/renewal cost info from Porkbun

This skill does NOT:
- ✗ Check social media handle availability (do manually)
- ✗ Search trademarks (do manually)
- ✗ Register domains (use your preferred registrar)

## Troubleshooting

### Porkbun API not configured
The script will fall back to WHOIS if Porkbun API keys are not set. To enable Porkbun API:

**Using .env file (Recommended - works everywhere):**
```bash
# 1. Create .env file in project root with your Porkbun credentials:
PORKBUN_API_KEY=your-actual-key
PORKBUN_API_SECRET=your-actual-secret

# 2. The script will automatically load from .env
./.shared/scripts/check-domain.sh mysite.com
```

**Using environment variables (GLM-5 Desktop only):**
```bash
export PORKBUN_API_KEY="your-api-key"
export PORKBUN_API_SECRET="your-api-secret"
```

### "API error" message
- Verify your Porkbun API credentials are correct in `.env` or environment
- Check your Porkbun account still has API access enabled (go to https://porkbun.com/account/api)
- Verify network connectivity
- Make sure `.env` file exists and has the correct format (no extra quotes)

### "Rate limited" errors with WHOIS fallback
The whois servers limit requests. Wait 30-60 seconds and try again, or check fewer domains at once.

### "Could not query whois" with WHOIS fallback
Some TLDs have restricted whois. Try a different TLD or check manually at the registrar's website.

### curl not found
The Porkbun API requires `curl`. It's usually pre-installed, but if not:
```bash
sudo apt install curl
```

### .env file not being loaded
- Verify the `.env` file exists in the project root
- Check the file format: `KEY=VALUE` (no extra spaces or quotes around values)
- Make sure you're running the script from the project root or a subdirectory where it can find `.env`
- The script looks for `.env` relative to the current working directory
