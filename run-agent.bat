@echo off
cd /d C:\Users\23705\IdeaProjects\ouragent\v3
set APP_ENV=production
set DEBUG=false
set LOG_LEVEL=INFO
set PORT=8001
set DB_HOST=localhost
set DB_PORT=3308
set DB_NAME=edu_agent
set DB_USER=root
set DB_PASSWORD=change-me-root-password
set REDIS_HOST=localhost
set REDIS_PORT=6380
set REDIS_PASSWORD=
set SECRET_KEY=change-me-secret-key
set AGENT_SERVICE_KEY=internal-agent-key-2024
set LLM_PROVIDER=openai
set LLM_API_KEY=tp-c4ksz64wen9n5g0pbqjw34nfghupg0suks538m24snl8d61u
set LLM_BASE_URL=https://token-plan-cn.xiaomimimo.com/v1
set LLM_MODEL=mimo-v2.5-pro
set EMBEDDING_API_KEY=tp-c4ksz64wen9n5g0pbqjw34nfghupg0suks538m24snl8d61u
set EMBEDDING_BASE_URL=https://token-plan-cn.xiaomimimo.com/v1
set EMBEDDING_MODEL=text-embedding-3-small
python -m uvicorn src.api:app --host 0.0.0.0 --port 8001
