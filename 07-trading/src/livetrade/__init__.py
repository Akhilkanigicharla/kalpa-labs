"""b7 live-ready layer (A153): Broker interface, Live Guard, runner. Paper by default.

Nothing here places a real order: the real adapters are stubs that refuse to start
unless LIVE_TRADING=YES and Akhil's file-based "go" flag both exist, and even then
raise NotImplementedError until they are built and tested. Own money only, not advice.
"""
