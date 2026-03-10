#!/usr/bin/env node
import fs from 'fs/promises';
import path from 'path';

const ALLOWED_KEYS = new Set([
  'entry_id',
  'date',
  'title',
  'summary',
  'content_markdown',
  'tags',
  'mood',
  'created_at',
]);

const ALLOWED_MOODS = new Set([
  'steady',
  'excited',
  'reflective',
  'milestone',
  'challenging',
]);

const entryPath = process.argv[2];

if (!entryPath) {
  console.error('Usage: node scripts/validate_entry.mjs <entry-json-path>');
  process.exit(1);
}

async function main() {
  const absolutePath = path.resolve(process.cwd(), entryPath);
  const raw = await fs.readFile(absolutePath, 'utf8');
  const entry = JSON.parse(raw);
  const errors = validateEntry(entry);

  if (errors.length > 0) {
    for (const error of errors) {
      console.error(`[bubble-entry] ${error}`);
    }
    process.exit(1);
  }

  console.log(`[bubble-entry] Validation passed: ${absolutePath}`);
}

function validateEntry(entry) {
  const errors = [];

  if (!isPlainObject(entry)) {
    return ['entry must be a JSON object'];
  }

  const extraKeys = Object.keys(entry).filter((key) => !ALLOWED_KEYS.has(key));
  if (extraKeys.length > 0) {
    errors.push(`unexpected properties: ${extraKeys.join(', ')}`);
  }

  const entryId = readRequiredString(entry, 'entry_id', errors);
  const date = readRequiredString(entry, 'date', errors);
  const title = readRequiredString(entry, 'title', errors);
  const contentMarkdown = readRequiredString(entry, 'content_markdown', errors);

  if (entryId && !/^bubble-\d{4}-\d{2}-\d{2}$/.test(entryId)) {
    errors.push('entry_id must match bubble-YYYY-MM-DD');
  }

  if (date && !/^\d{4}-\d{2}-\d{2}$/.test(date)) {
    errors.push('date must match YYYY-MM-DD');
  }

  if (entryId && date && entryId !== `bubble-${date}`) {
    errors.push(`entry_id must equal bubble-${date}`);
  }

  if (title && title.length > 200) {
    errors.push('title must be 1-200 characters');
  }

  if (typeof entry.summary !== 'undefined') {
    if (typeof entry.summary !== 'string' || entry.summary.trim().length === 0) {
      errors.push('summary must be a non-empty string when provided');
    } else if (entry.summary.length > 500) {
      errors.push('summary must be 1-500 characters');
    }
  }

  if (contentMarkdown) {
    if (containsBlockedMarkdown(contentMarkdown)) {
      errors.push('content_markdown must not contain import/export/script tags');
    }
  }

  if (typeof entry.tags !== 'undefined') {
    if (!Array.isArray(entry.tags)) {
      errors.push('tags must be an array when provided');
    } else {
      if (entry.tags.length > 10) {
        errors.push('tags must contain at most 10 items');
      }

      const seen = new Set();
      for (const tag of entry.tags) {
        if (typeof tag !== 'string' || !/^[a-z0-9-]+$/.test(tag)) {
          errors.push('each tag must match ^[a-z0-9-]+$');
          break;
        }

        if (seen.has(tag)) {
          errors.push('tags must be unique');
          break;
        }

        seen.add(tag);
      }
    }
  }

  if (typeof entry.mood !== 'undefined') {
    if (typeof entry.mood !== 'string' || !ALLOWED_MOODS.has(entry.mood)) {
      errors.push(`mood must be one of: ${Array.from(ALLOWED_MOODS).join(', ')}`);
    }
  }

  if (typeof entry.created_at !== 'undefined') {
    if (typeof entry.created_at !== 'string' || Number.isNaN(Date.parse(entry.created_at))) {
      errors.push('created_at must be a valid ISO 8601 date-time string');
    }
  }

  return errors;
}

function readRequiredString(entry, key, errors) {
  const value = entry[key];

  if (typeof value !== 'string' || value.trim().length === 0) {
    errors.push(`${key} is required and must be a non-empty string`);
    return '';
  }

  return value.trim();
}

function containsBlockedMarkdown(content) {
  return /^import\s.+$/m.test(content)
    || /^export\s.+$/m.test(content)
    || /<script[\s\S]*?<\/script>/i.test(content);
}

function isPlainObject(value) {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}

main().catch((error) => {
  console.error('[bubble-entry] Validation failed:', error);
  process.exit(1);
});
