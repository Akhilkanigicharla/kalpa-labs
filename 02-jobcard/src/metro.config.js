const path = require('node:path');
const { getDefaultConfig } = require('expo/metro-config');
const { withUniwindConfig } = require('uniwind/metro');

const config = getDefaultConfig(__dirname);

// JobCard shares its parser + invoice core with the WhatsApp bot (02-jobcard/lib, imported as @core/…).
config.watchFolders = [...(config.watchFolders || []), path.resolve(__dirname, '..', 'lib')];
// Babel helpers added to ../lib files resolve from this app's node_modules
config.resolver.nodeModulesPaths = [path.resolve(__dirname, 'node_modules')];
// expo-sqlite on web (used for the 390 px screenshots) ships a .wasm build of SQLite
config.resolver.assetExts = [...new Set([...config.resolver.assetExts, 'wasm'])];
config.resolver.sourceExts = [...new Set([...config.resolver.sourceExts, 'mjs'])];

// invoicePDF() (server-only, pdf-lib) is never called in the app: keep pdf-lib out of the bundle
const serverOnly = new Set(['pdf-lib', '@pdf-lib/fontkit']);
const upstream = config.resolver.resolveRequest;
config.resolver.resolveRequest = (ctx, name, platform) =>
  serverOnly.has(name)
    ? { type: 'empty' }
    : upstream
      ? upstream(ctx, name, platform)
      : ctx.resolveRequest(ctx, name, platform);

module.exports = withUniwindConfig(config, {
  cssEntryFile: './src/global.css',
});
