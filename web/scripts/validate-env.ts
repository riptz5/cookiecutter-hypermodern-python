#!/usr/bin/env node

/**
 * Validate that all required environment variables are set
 * Run this before starting development or production
 */

const requiredVars = [
  'NEXT_PUBLIC_API_URL',
  'NEXT_PUBLIC_GCP_PROJECT_ID',
];

const optionalVars = [
  'NEXT_PUBLIC_DEBUG_MODE',
  'NEXT_PUBLIC_MOCK_DATA',
  'NEXT_PUBLIC_ENABLE_REAL_TIME_LOGS',
  'NEXT_PUBLIC_ENABLE_COST_TRACKING',
  'NEXT_PUBLIC_ENABLE_AUTO_REFRESH',
];

console.log('🔍 Validating environment variables...\n');

const missing: string[] = [];
const set: string[] = [];

for (const varName of requiredVars) {
  if (process.env[varName]) {
    set.push(`✅ ${varName} = ${process.env[varName]}`);
  } else {
    missing.push(`❌ ${varName} (REQUIRED)`);
  }
}

for (const varName of optionalVars) {
  if (process.env[varName]) {
    set.push(`⚠️  ${varName} = ${process.env[varName]}`);
  }
}

if (set.length > 0) {
  console.log('Found variables:');
  set.forEach(line => console.log(`  ${line}`));
  console.log();
}

if (missing.length > 0) {
  console.log('Missing required variables:');
  missing.forEach(line => console.log(`  ${line}`));
  console.log();
  console.log('📝 Copy .env.example to .env.local and fill in your values:');
  console.log('   cp .env.example .env.local');
  process.exit(1);
}

console.log('✅ All required environment variables are set!');
process.exit(0);
