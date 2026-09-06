#!/usr/bin/env node
/**
 * TakaBooks installer CLI — টাকাবুকস ইনস্টলার
 *
 * Copies a built TakaBooks bundle into the place the target LLM platform expects.
 *
 *   npx @bemoshiur/takabooks install claude      -> ~/.claude/skills/bd-bookkeeping-tax/
 *   npx @bemoshiur/takabooks install chatgpt     -> ./takabooks-chatgpt/
 *   npx @bemoshiur/takabooks install gemini      -> ./takabooks-gemini/
 *   npx @bemoshiur/takabooks install universal   -> ./takabooks-complete.md
 *   npx @bemoshiur/takabooks install agents      -> ./AGENTS.md
 *   npx @bemoshiur/takabooks list
 *
 * Contracts this file honours:
 *   - Zero dependencies. Node built-ins only. Works on macOS, Linux and Windows.
 *   - Never clobbers an existing install without --force.
 *   - Non-zero exit on any failure. No silent fallback. (spec section 2)
 *   - Ships no tax rate, threshold or deadline. Those live in
 *     src/data/rates-AY2026-27.toml with a source URL and a `verified` flag.
 *     (spec sections 4.5 and 6)
 *
 * TakaBooks — Moshiur Rahman (@bemoshiur) · Ticon Sys — https://ticonsys.com
 * MIT licensed.
 */

import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import process from 'node:process';
import { fileURLToPath } from 'node:url';

// ---------------------------------------------------------------------------
// Constants and environment
// ---------------------------------------------------------------------------

const BIN_DIR = path.dirname(fileURLToPath(import.meta.url));
const PKG_ROOT = path.resolve(BIN_DIR, '..');
const REPO_URL = 'https://github.com/bemoshiur/TakaBooks';
const COMPANY_URL = 'https://ticonsys.com';

const EXIT_OK = 0;
const EXIT_FAIL = 1;
const EXIT_USAGE = 2;

/** Errors we raise on purpose; anything else is a genuine crash. */
class CliError extends Error {
  constructor(message, { hint = null, code = EXIT_FAIL } = {}) {
    super(message);
    this.name = 'CliError';
    this.hint = hint;
    this.code = code;
  }
}

function readPackageVersion() {
  try {
    const raw = fs.readFileSync(path.join(PKG_ROOT, 'package.json'), 'utf8');
    return JSON.parse(raw).version || '0.0.0';
  } catch {
    return '0.0.0';
  }
}

const VERSION = readPackageVersion();

// ---------------------------------------------------------------------------
// Terminal helpers
// ---------------------------------------------------------------------------

const ESC = '\u001b'; // ASCII escape, written as a JS escape so the source stays plain text

const USE_COLOR =
  process.stdout.isTTY === true && !process.env.NO_COLOR && process.env.TERM !== 'dumb';

const paint = (code, s) => (USE_COLOR ? `${ESC}[${code}m${s}${ESC}[0m` : s);
const bold = (s) => paint('1', s);
const dim = (s) => paint('2', s);
const red = (s) => paint('31', s);
const green = (s) => paint('32', s);
const yellow = (s) => paint('33', s);
const cyan = (s) => paint('36', s);

/**
 * Bangla output is required by spec section 6.4, but a legacy Windows console on
 * a non-UTF-8 code page renders it as mojibake. Detect the hopeless case and
 * fall back to English only there.
 */
function supportsBangla() {
  if (process.env.TAKABOOKS_NO_BANGLA) return false;
  if (process.platform !== 'win32') return true;
  return Boolean(process.env.WT_SESSION || process.env.TERM_PROGRAM || process.env.TERM);
}

/** An English line, optionally followed by its Bangla twin. */
function bilingual(en, bn) {
  const lines = [en];
  if (bn && supportsBangla()) lines.push(bn);
  return lines;
}

// ---------------------------------------------------------------------------
// Targets
// ---------------------------------------------------------------------------

/**
 * Each target says where its bundle lives inside dist/, where it goes by
 * default, and what the user must do next. `sources` are tried in order; the
 * first that exists wins.
 */
const TARGETS = {
  claude: {
    aliases: ['claude', 'claude-skill', 'claude-code', 'claude-desktop', 'anthropic'],
    label: 'Claude Skill',
    kind: 'dir',
    sources: (ctx) => [path.join(ctx.distDir, 'claude-skill', 'bd-bookkeeping-tax')],
    defaultDest: () => path.join(os.homedir(), '.claude', 'skills', 'bd-bookkeeping-tax'),
    describeDest: '~/.claude/skills/bd-bookkeeping-tax/',
    nextSteps: (dest, ctx) => {
      const zip = path.join(ctx.distDir, 'claude-skill', 'bd-bookkeeping-tax.zip');
      const steps = [
        `Claude Code and Claude Desktop read skills from ${dest}`,
        'Restart Claude, then ask: "Set up my books with TakaBooks."',
      ];
      if (isFile(zip)) {
        steps.push(`For claude.ai in the browser, upload the zip instead: ${zip}`);
      }
      return steps;
    },
  },

  chatgpt: {
    aliases: ['chatgpt', 'gpt', 'openai', 'custom-gpt'],
    label: 'ChatGPT custom GPT bundle',
    kind: 'dir',
    sources: (ctx) => [path.join(ctx.distDir, 'chatgpt')],
    defaultDest: () => path.join(process.cwd(), 'takabooks-chatgpt'),
    describeDest: './takabooks-chatgpt/',
    nextSteps: (dest) => [
      'Create a GPT at https://chatgpt.com/gpts/editor and open the Configure tab.',
      `Paste ${path.join(dest, 'instructions.md')} into "Instructions".`,
      '  It is built to fit the 8,000-character cap; do not append to it.',
      `Upload every file in ${path.join(dest, 'knowledge')} under "Knowledge".`,
    ],
  },

  gemini: {
    aliases: ['gemini', 'gem', 'google', 'bard'],
    label: 'Gemini Gem bundle',
    kind: 'dir',
    sources: (ctx) => [path.join(ctx.distDir, 'gemini')],
    defaultDest: () => path.join(process.cwd(), 'takabooks-gemini'),
    describeDest: './takabooks-gemini/',
    nextSteps: (dest) => [
      'Create a Gem at https://gemini.google.com/gems/create.',
      `Paste ${path.join(dest, 'gem-instructions.md')} into the instructions box.`,
      `Attach every file in ${path.join(dest, 'knowledge')} as Gem knowledge.`,
    ],
  },

  universal: {
    aliases: ['universal', 'any', 'anyllm', 'complete', 'paste'],
    label: 'Universal single-file bundle',
    kind: 'file',
    sources: (ctx) => [path.join(ctx.distDir, 'universal', 'takabooks-complete.md')],
    defaultDest: () => path.join(process.cwd(), 'takabooks-complete.md'),
    describeDest: './takabooks-complete.md',
    nextSteps: (dest) => [
      `Paste the whole of ${dest} into the system prompt or first message of any LLM`,
      '  — Kimi, DeepSeek, Llama, Mistral, Copilot, Qwen, or a self-hosted model.',
    ],
  },

  agents: {
    aliases: ['agents', 'agents-md', 'agentsmd', 'cursor', 'codex', 'copilot', 'windsurf'],
    label: 'AGENTS.md (cross-agent standard)',
    kind: 'file',
    sources: (ctx) => [
      path.join(ctx.distDir, 'agents-md', 'AGENTS.md'),
      path.join(ctx.pkgRoot, 'AGENTS.md'),
    ],
    defaultDest: () => path.join(process.cwd(), 'AGENTS.md'),
    describeDest: './AGENTS.md',
    nextSteps: (dest) => [
      `AGENTS.md is now at ${dest}.`,
      'Cursor, Codex, Copilot and other agent tools read it from the project root',
      'automatically. Commit it so the whole team gets the same rules.',
    ],
  },
};

const TARGET_KEYS = Object.keys(TARGETS);

function resolveTargetKey(name) {
  const wanted = String(name).toLowerCase();
  for (const key of TARGET_KEYS) {
    if (TARGETS[key].aliases.includes(wanted)) return key;
  }
  return null;
}

// ---------------------------------------------------------------------------
// dist/ resolution
// ---------------------------------------------------------------------------

function isDirectory(p) {
  try {
    return fs.statSync(p).isDirectory();
  } catch {
    return false;
  }
}

function isFile(p) {
  try {
    return fs.statSync(p).isFile();
  } catch {
    return false;
  }
}

/**
 * Where the built bundles live. An explicit --dist wins, then TAKABOOKS_DIST,
 * then the dist/ directory shipped inside this package. The current working
 * directory is deliberately NOT searched: an unrelated ./dist in the user's own
 * project must never be mistaken for a TakaBooks build.
 */
function resolveDistDir(opts) {
  const candidates = [];
  if (opts.dist) candidates.push({ dir: path.resolve(opts.dist), why: '--dist' });
  if (process.env.TAKABOOKS_DIST) {
    candidates.push({ dir: path.resolve(process.env.TAKABOOKS_DIST), why: 'TAKABOOKS_DIST' });
  }
  candidates.push({ dir: path.join(PKG_ROOT, 'dist'), why: 'package' });

  for (const c of candidates) {
    if (isDirectory(c.dir)) return { ...c, exists: true };
  }
  return { ...candidates[0], exists: false };
}

function distHint(dist) {
  return [
    `No built bundles found at ${dist.dir}`,
    'Build them from a TakaBooks checkout:',
    '      python3 build/build.py --target all',
    'then point the installer at the result:',
    '      npx @bemoshiur/takabooks install <target> --dist ./dist',
    `Or download a bundle from ${REPO_URL}/releases/latest`,
  ].join('\n    ');
}

// ---------------------------------------------------------------------------
// Filesystem work
// ---------------------------------------------------------------------------

/**
 * Recursive copy using only long-stable APIs. fs.cpSync would do this in one
 * call but emits an ExperimentalWarning on Node 18 and 20, and this CLI has to
 * be quiet enough to trust.
 */
function copyTree(src, dest, stats) {
  const st = fs.statSync(src); // follows symlinks: a linked file is copied as a real file
  if (st.isDirectory()) {
    fs.mkdirSync(dest, { recursive: true });
    for (const name of fs.readdirSync(src).sort()) {
      copyTree(path.join(src, name), path.join(dest, name), stats);
    }
  } else if (st.isFile()) {
    fs.mkdirSync(path.dirname(dest), { recursive: true });
    fs.copyFileSync(src, dest);
    stats.files += 1;
    stats.bytes += st.size;
  }
  // Sockets, FIFOs and devices are skipped on purpose — a bundle has none.
  return stats;
}

function measure(src) {
  const stats = { files: 0, bytes: 0 };
  const walk = (p) => {
    const st = fs.statSync(p);
    if (st.isDirectory()) {
      for (const name of fs.readdirSync(p)) walk(path.join(p, name));
    } else if (st.isFile()) {
      stats.files += 1;
      stats.bytes += st.size;
    }
  };
  walk(src);
  return stats;
}

function isEmptyDir(p) {
  try {
    return fs.readdirSync(p).length === 0;
  } catch {
    return false;
  }
}

/**
 * --force deletes the destination, so make it impossible to aim somewhere
 * catastrophic: refuse the filesystem root, the home directory itself, and
 * anything shallower than two segments below the root.
 */
function assertSafeDest(dest) {
  const resolved = path.resolve(dest);
  const root = path.parse(resolved).root;

  if (resolved === root) {
    throw new CliError(`Refusing to install to the filesystem root (${resolved}).`);
  }
  const home = os.homedir();
  if (home && path.resolve(home) === resolved) {
    throw new CliError(`Refusing to install directly over your home directory (${resolved}).`);
  }
  const depth = path.relative(root, resolved).split(path.sep).filter(Boolean).length;
  if (depth < 2) {
    throw new CliError(
      `Refusing to install to ${resolved} — it is too close to the filesystem root.`,
      { hint: 'Pass --dest with a deeper path.' },
    );
  }
  return resolved;
}

function humanBytes(n) {
  if (n < 1024) return `${n} B`;
  if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)} KB`;
  return `${(n / (1024 * 1024)).toFixed(1)} MB`;
}

// ---------------------------------------------------------------------------
// Argument parsing
// ---------------------------------------------------------------------------

const BOOLEAN_FLAGS = new Set(['force', 'dry-run', 'json', 'quiet', 'help', 'version', 'no-bangla']);
const VALUE_FLAGS = new Set(['dest', 'dist']);
const SHORT = { h: 'help', v: 'version', f: 'force', n: 'dry-run', q: 'quiet' };

function parseArgs(argv) {
  const opts = {
    force: false,
    dryRun: false,
    json: false,
    quiet: false,
    help: false,
    version: false,
    dest: null,
    dist: null,
  };
  const positional = [];

  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];

    if (arg === '--') {
      positional.push(...argv.slice(i + 1));
      break;
    }

    if (arg.startsWith('--')) {
      const eq = arg.indexOf('=');
      const name = eq === -1 ? arg.slice(2) : arg.slice(2, eq);
      const inlineValue = eq === -1 ? null : arg.slice(eq + 1);

      if (VALUE_FLAGS.has(name)) {
        const value = inlineValue !== null ? inlineValue : argv[(i += 1)];
        if (value === undefined || value === '') {
          throw new CliError(`--${name} needs a value.`, { code: EXIT_USAGE });
        }
        opts[name] = value;
        continue;
      }
      if (BOOLEAN_FLAGS.has(name)) {
        if (inlineValue !== null) {
          throw new CliError(`--${name} does not take a value.`, { code: EXIT_USAGE });
        }
        if (name === 'dry-run') opts.dryRun = true;
        else if (name === 'no-bangla') process.env.TAKABOOKS_NO_BANGLA = '1';
        else opts[name] = true;
        continue;
      }
      throw new CliError(`Unknown option: ${arg}`, {
        hint: 'Run `takabooks help` to see the supported options.',
        code: EXIT_USAGE,
      });
    }

    if (arg.length > 1 && arg[0] === '-') {
      for (const ch of arg.slice(1)) {
        const long = SHORT[ch];
        if (!long) throw new CliError(`Unknown option: -${ch}`, { code: EXIT_USAGE });
        if (long === 'dry-run') opts.dryRun = true;
        else opts[long] = true;
      }
      continue;
    }

    positional.push(arg);
  }

  return { opts, positional };
}

// ---------------------------------------------------------------------------
// Output
// ---------------------------------------------------------------------------

function emitJson(payload, code) {
  process.stdout.write(`${JSON.stringify(payload, null, 2)}\n`);
  process.exitCode = code;
}

function disclaimer() {
  return bilingual(
    'TakaBooks prepares figures. It is not professional advice — verify with a licensed ITP/CA before filing.',
    'টাকাবুকস কেবল হিসাব প্রস্তুত করে। এটি পেশাদার পরামর্শ নয় — দাখিলের আগে লাইসেন্সপ্রাপ্ত ITP/CA-এর সঙ্গে যাচাই করুন।',
  );
}

function printFooter(log) {
  log('');
  log(dim('  Every rate, threshold and deadline lives in src/data/rates-AY<year>.toml with a'));
  log(dim('  source URL and a `verified` flag. Check it before you rely on a number.'));
  for (const line of disclaimer()) log(dim(`  ${line}`));
  log('');
  log(dim(`  ${REPO_URL}  ·  Ticon Sys — ${COMPANY_URL}`));
  log('');
}

function helpText() {
  const rows = TARGET_KEYS.map((key) => {
    const t = TARGETS[key];
    return `    ${key.padEnd(11)}${t.label.padEnd(34)}${dim(t.describeDest)}`;
  });

  return [
    '',
    `  ${bold('TakaBooks')} ${dim(`v${VERSION}`)} — টাকাবুকস`,
    '  Bangladeshi bookkeeping & taxation (মূসক / VAT, উৎসে কর কর্তন / TDS) for any LLM.',
    '',
    `  ${bold('Usage')}`,
    '    npx @bemoshiur/takabooks install <target> [options]',
    '    npx @bemoshiur/takabooks list [--json]',
    '',
    `  ${bold('Targets')}`,
    ...rows,
    '',
    `  ${bold('Options')}`,
    '    --dest <path>   Install somewhere other than the default destination',
    '    --dist <path>   Read bundles from this dist/ directory instead of the packaged one',
    '    --force, -f     Replace an existing install (deletes the destination first)',
    '    --dry-run, -n   Report what would happen; write nothing',
    '    --json          Machine-readable output on stdout',
    '    --quiet, -q     Only report failures',
    '    --no-bangla     English-only output, for legacy consoles',
    '    --help, -h      This text',
    '    --version, -v   Print the version',
    '',
    `  ${bold('Environment')}`,
    '    TAKABOOKS_DIST       Default --dist directory',
    '    TAKABOOKS_NO_BANGLA  Same as --no-bangla',
    '    NO_COLOR             Disable colour',
    '',
    `  ${bold('Examples')}`,
    '    npx @bemoshiur/takabooks install claude',
    '    npx @bemoshiur/takabooks install chatgpt --dest ./gpt-bundle',
    '    npx @bemoshiur/takabooks install universal --force',
    '    node bin/takabooks.mjs install claude --dist ./dist    # from a checkout',
    '',
    '  Exit codes: 0 success · 1 failure · 2 bad usage',
    '',
    `  Maintained by Moshiur Rahman (@bemoshiur) · Ticon Sys — ${COMPANY_URL}`,
    `  ${REPO_URL}`,
    '',
  ].join('\n');
}

// ---------------------------------------------------------------------------
// Commands
// ---------------------------------------------------------------------------

function commandList(opts) {
  const dist = resolveDistDir(opts);
  const ctx = { distDir: dist.dir, pkgRoot: PKG_ROOT };

  const rows = TARGET_KEYS.map((key) => {
    const target = TARGETS[key];
    const source = target
      .sources(ctx)
      .find((p) => (target.kind === 'dir' ? isDirectory(p) && !isEmptyDir(p) : isFile(p)));
    return {
      target: key,
      label: target.label,
      kind: target.kind,
      available: Boolean(source),
      source: source || null,
      destination: target.defaultDest(),
      aliases: target.aliases,
    };
  });

  if (opts.json) {
    emitJson(
      {
        ok: true,
        command: 'list',
        version: VERSION,
        distDir: dist.dir,
        distExists: dist.exists,
        distSource: dist.why,
        targets: rows,
      },
      EXIT_OK,
    );
    return;
  }

  const log = (line) => process.stdout.write(`${line}\n`);
  log('');
  log(`  ${bold('TakaBooks')} ${dim(`v${VERSION}`)} — available bundles`);
  log(`  ${dim(`bundles: ${dist.dir}${dist.exists ? '' : '   (not found)'}`)}`);
  log('');
  log(`  ${bold('TARGET'.padEnd(12) + 'STATUS'.padEnd(13) + 'INSTALLS TO')}`);
  for (const row of rows) {
    const word = row.available ? 'ready' : 'not built';
    const status = row.available ? green(word) : yellow(word);
    log(`  ${row.target.padEnd(12)}${status}${' '.repeat(13 - word.length)}${row.destination}`);
  }
  if (rows.some((r) => !r.available)) {
    log('');
    log(`  ${yellow('!')} ${distHint(dist)}`);
  }
  printFooter(log);
  process.exitCode = EXIT_OK;
}

function commandInstall(positional, opts) {
  const name = positional[0];
  if (!name) {
    throw new CliError('install needs a target.', {
      hint: `Targets: ${TARGET_KEYS.join(', ')}`,
      code: EXIT_USAGE,
    });
  }
  if (positional.length > 1) {
    throw new CliError(`install takes one target, got: ${positional.join(' ')}`, {
      hint: 'Run the command once per target.',
      code: EXIT_USAGE,
    });
  }

  const key = resolveTargetKey(name);
  if (!key) {
    throw new CliError(`Unknown target: ${name}`, {
      hint: `Targets: ${TARGET_KEYS.join(', ')}   (run \`takabooks list\`)`,
      code: EXIT_USAGE,
    });
  }

  const target = TARGETS[key];
  const dist = resolveDistDir(opts);
  const ctx = { distDir: dist.dir, pkgRoot: PKG_ROOT };

  const candidates = target.sources(ctx);
  const source = candidates.find((p) => (target.kind === 'dir' ? isDirectory(p) : isFile(p)));
  if (!source) {
    throw new CliError(`No ${target.label} found in this package.`, {
      hint: `Looked for:\n      ${candidates.join('\n      ')}\n    ${distHint(dist)}`,
    });
  }
  if (target.kind === 'dir' && isEmptyDir(source)) {
    throw new CliError(`The ${target.label} at ${source} is empty.`, {
      hint: 'Re-run `python3 build/build.py --target all` and read its output.',
    });
  }

  const dest = assertSafeDest(opts.dest ? path.resolve(opts.dest) : target.defaultDest());

  // Refuse to clobber.
  let replacing = false;
  if (fs.existsSync(dest)) {
    const destStat = fs.statSync(dest);
    const kindMatches = target.kind === 'dir' ? destStat.isDirectory() : destStat.isFile();
    const occupied = target.kind === 'dir' ? !isEmptyDir(dest) : true;

    if (occupied || !kindMatches) {
      if (!opts.force) {
        throw new CliError(`${dest} already exists.`, {
          hint:
            'Nothing was changed. Re-run with --force to replace it, or pass\n' +
            '    --dest <path> to install somewhere else.\n' +
            '    --force DELETES that path before copying — back up local edits first.',
        });
      }
      replacing = true;
    }
  }

  const size = measure(source);

  if (opts.dryRun) {
    if (opts.json) {
      emitJson(
        {
          ok: true,
          command: 'install',
          target: key,
          dryRun: true,
          source,
          destination: dest,
          replacing,
          files: size.files,
          bytes: size.bytes,
        },
        EXIT_OK,
      );
      return;
    }
    const log = (line) => process.stdout.write(`${line}\n`);
    log('');
    log(`  ${cyan('dry run')} — nothing was written.`);
    log(`  ${bold(target.label)}`);
    log(`    from  ${source}`);
    log(`    to    ${dest}`);
    log(
      `    ${size.files} file(s), ${humanBytes(size.bytes)}` +
        (replacing ? yellow('   (would REPLACE the existing install)') : ''),
    );
    log('');
    process.exitCode = EXIT_OK;
    return;
  }

  if (replacing) {
    fs.rmSync(dest, { recursive: true, force: true });
  }
  if (target.kind === 'dir') {
    fs.mkdirSync(dest, { recursive: true });
  } else {
    fs.mkdirSync(path.dirname(dest), { recursive: true });
  }

  const copied = { files: 0, bytes: 0 };
  copyTree(source, dest, copied);

  if (copied.files === 0) {
    throw new CliError(`Copied nothing from ${source}. The bundle looks broken.`, {
      hint: 'Rebuild with `python3 build/build.py --target all` and try again.',
    });
  }

  const steps = target.nextSteps(dest, ctx);

  if (opts.json) {
    emitJson(
      {
        ok: true,
        command: 'install',
        target: key,
        dryRun: false,
        source,
        destination: dest,
        replaced: replacing,
        files: copied.files,
        bytes: copied.bytes,
        nextSteps: steps,
        disclaimer: disclaimer(),
      },
      EXIT_OK,
    );
    return;
  }

  if (opts.quiet) {
    process.exitCode = EXIT_OK;
    return;
  }

  const log = (line) => process.stdout.write(`${line}\n`);
  log('');
  log(`  ${green('OK')}  ${bold(target.label)} installed${replacing ? dim(' (replaced)') : ''}`);
  log(`      ${dim(`${copied.files} file(s), ${humanBytes(copied.bytes)}`)}`);
  log(`      ${dest}`);
  log('');
  log(`  ${bold('Next')}`);
  for (const step of steps) log(`    ${step}`);
  printFooter(log);
  process.exitCode = EXIT_OK;
}

// ---------------------------------------------------------------------------
// Entry point
// ---------------------------------------------------------------------------

function fail(err, asJson) {
  const isCli = err instanceof CliError;
  const code = isCli ? err.code : EXIT_FAIL;

  if (asJson) {
    emitJson({ ok: false, error: err.message, hint: isCli ? err.hint : null }, code);
    return;
  }

  process.stderr.write(`\n  ${red('ERROR')}  ${err.message}\n`);
  if (isCli && err.hint) {
    process.stderr.write(`    ${dim(err.hint)}\n`);
  }
  if (!isCli) {
    process.stderr.write(`${dim(err.stack || String(err))}\n`);
    process.stderr.write(`    ${dim(`Please report this at ${REPO_URL}/issues`)}\n`);
  }
  process.stderr.write('\n');
  process.exitCode = code;
}

function main(argv) {
  let parsed;
  try {
    parsed = parseArgs(argv);
  } catch (err) {
    fail(err, argv.includes('--json'));
    return;
  }
  const { opts, positional } = parsed;

  try {
    if (opts.version) {
      process.stdout.write(opts.json ? `${JSON.stringify({ version: VERSION })}\n` : `${VERSION}\n`);
      process.exitCode = EXIT_OK;
      return;
    }

    const command = positional.shift();

    if (opts.help || !command || command === 'help') {
      if (opts.json) {
        emitJson({ ok: true, command: 'help', version: VERSION, targets: TARGET_KEYS }, EXIT_OK);
      } else {
        process.stdout.write(`${helpText()}\n`);
      }
      // Being invoked with no command at all is a usage problem, not a success.
      process.exitCode = opts.help || command === 'help' ? EXIT_OK : EXIT_USAGE;
      return;
    }

    switch (command) {
      case 'install':
      case 'add':
        commandInstall(positional, opts);
        return;
      case 'list':
      case 'ls':
        commandList(opts);
        return;
      case 'version':
        process.stdout.write(`${VERSION}\n`);
        process.exitCode = EXIT_OK;
        return;
      default:
        throw new CliError(`Unknown command: ${command}`, {
          hint: 'Commands: install, list, help, version',
          code: EXIT_USAGE,
        });
    }
  } catch (err) {
    fail(err, opts.json);
  }
}

main(process.argv.slice(2));
