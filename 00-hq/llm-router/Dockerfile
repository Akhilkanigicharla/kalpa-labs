# Kalpa LLM router: FreeLLMAPI (MIT, github.com/tashfeenahmed/freellmapi) pinned, plus our config builder.
FROM ghcr.io/tashfeenahmed/freellmapi:v0.16.9
COPY make-config.js allowed.json /kalpa/
ENV FREEAPI_CONFIG_PATH=/tmp/kalpa-router.json
ENTRYPOINT ["/bin/sh", "-c", "node /kalpa/make-config.js && exec /usr/local/bin/docker-entrypoint.sh node server/dist/index.js"]
