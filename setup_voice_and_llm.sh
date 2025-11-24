#!/bin/bash

# Setup script for Phase 19 & 20 features
# Voice Interface and Local LLM

set -e

echo "🚀 Setting up Voice Interface and Local LLM features..."
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running in virtual environment
if [ -z "$VIRTUAL_ENV" ]; then
    echo -e "${YELLOW}⚠️  Warning: Not in a virtual environment${NC}"
    echo "It's recommended to activate your virtual environment first:"
    echo "  source venv/bin/activate"
    echo ""
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Install Python dependencies
echo -e "${BLUE}📦 Installing Python dependencies...${NC}"
pip install -r requirements.txt

# Check if Ollama is installed
echo ""
echo -e "${BLUE}🤖 Checking for Ollama...${NC}"
if command -v ollama &> /dev/null; then
    echo -e "${GREEN}✓ Ollama is installed${NC}"
    
    # Check if Ollama is running
    if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Ollama server is running${NC}"
    else
        echo -e "${YELLOW}⚠️  Ollama is installed but not running${NC}"
        echo "Start it with: ollama serve"
    fi
else
    echo -e "${YELLOW}⚠️  Ollama is not installed${NC}"
    echo "Install from: https://ollama.ai"
    echo "Or run: curl https://ollama.ai/install.sh | sh"
fi

# Offer to pull Ollama models
echo ""
read -p "Do you want to pull Ollama models? (y/n) " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${BLUE}📥 Pulling Llama 3 model (this may take a while)...${NC}"
    ollama pull llama3
    
    echo ""
    read -p "Pull Phi-3 model as well? (smaller, faster) (y/n) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${BLUE}📥 Pulling Phi-3 model...${NC}"
        ollama pull phi3
    fi
fi

# Check for spaCy model (optional for NER)
echo ""
read -p "Install spaCy model for advanced PII detection? (y/n) " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${BLUE}📥 Downloading spaCy model...${NC}"
    python -m spacy download en_core_web_sm
fi

# Setup .env file
echo ""
echo -e "${BLUE}⚙️  Setting up environment variables...${NC}"
if [ ! -f .env ]; then
    echo "Creating .env from .env.example..."
    cp .env.example .env
    echo -e "${GREEN}✓ Created .env file${NC}"
    echo -e "${YELLOW}⚠️  Please edit .env and add your API keys:${NC}"
    echo "  - OPENAI_API_KEY"
    echo "  - ELEVENLABS_API_KEY (optional)"
else
    echo -e "${GREEN}✓ .env file already exists${NC}"
fi

# Check Docker
echo ""
echo -e "${BLUE}🐳 Checking for Docker...${NC}"
if command -v docker &> /dev/null; then
    echo -e "${GREEN}✓ Docker is installed${NC}"
    
    read -p "Start Docker services (Ollama, Redis, etc.)? (y/n) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${BLUE}🚀 Starting Docker services...${NC}"
        docker-compose up -d ollama redis
        echo -e "${GREEN}✓ Services started${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  Docker is not installed${NC}"
    echo "Install from: https://www.docker.com/products/docker-desktop"
fi

# Summary
echo ""
echo -e "${GREEN}✅ Setup complete!${NC}"
echo ""
echo "Next steps:"
echo "1. Edit .env and add your API keys"
echo "2. Start the API server:"
echo "   uvicorn src.api.main:app --reload"
echo "3. Test voice endpoint:"
echo "   curl http://localhost:8000/health"
echo ""
echo "Documentation:"
echo "- Voice & Local LLM Guide: VOICE_AND_LOCAL_LLM_GUIDE.md"
echo "- Walkthrough: .gemini/antigravity/brain/.../walkthrough.md"
echo ""
echo -e "${BLUE}Happy coding! 🎉${NC}"
