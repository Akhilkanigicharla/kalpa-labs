# Kalpa LLM router: FreeLLMAPI (MIT, github.com/tashfeenahmed/freellmapi) pinned, plus our config builder.
FROM ghcr.io/tashfeenahmed/freellmapi:v0.16.9
COPY make-config.js allowed.json /kalpa/
ENTRYPOINT ["/bin/sh", "-c", "FREEAPI_CONFIG_JSON=\"$(node /kalpa/make-config.js)\" || exit 1; export FREEAPI_CONFIG_JSON; exec /usr/local/bin/docker-entrypoint.sh node server/dist/index.js"]
