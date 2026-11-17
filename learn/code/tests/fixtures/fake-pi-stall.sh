#!/bin/sh
# Records one tool call in the trace, then blocks like a foreground server.
printf '{"type":"tool_call","timestamp":"%s","toolName":"bash","input":{"command":"uvicorn main:app"}}\n' \
  "$(date -u +%Y-%m-%dT%H:%M:%S.000Z)" >> "$MELLUM_TRACE_FILE"
sleep 60
