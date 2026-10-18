const { getDefaultConfig } = require('expo/metro-config');
const { withUniwindConfig } = require('uniwind/metro');

const path = require('node:path');

const config = getDefaultConfig(__dirname);
// JobCard shares its parser + invoice core with the bot and tests (02-jobcard/lib)
config.watchFolders = [...(config.watchFolders || []), path.resolve(__dirname, '..', 'lib')];
config.resolver.nodeModulesPaths = [path.resolve(__dirname, 'node_modules')];
// invoicePDF() (server-only, pdf-lib) is never called in the app: keep pdf-lib out of the bundle
const serverOnly = new Set(['pdf-lib', '@pdf-lib/fontkit']);
const upstream = config.resolver.resolveRequest;
config.resolver.resolveRequest = (ctx, name, platform) =>
  serverOnly.has(name) ? { type: 'empty' } : (upstream ? upstream(ctx, name, platform) : ctx.resolveRequest(ctx, name, platform));
config.resolver.sourceExts = [...new Set([...config.resolver.nodeModulesPaths = [path.resolve(__dirname, 'node_modules')];
config.resolver.sourceExts, 'mjs'])];

module.exports = withUniwindConfig(config, {
  cssEntryFile: './src/global.css',
});
