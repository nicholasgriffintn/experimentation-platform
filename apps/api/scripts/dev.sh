#!/bin/bash

if [ -d ".venv" ]; then
    source .venv/bin/activate
elif [ -d "venv" ]; then
    source venv/bin/activate
else
    echo "No virtual environment found. Please create one first:"
    echo "python -m venv .venv"
    echo "source .venv/bin/activate"
    echo "pip install -e '.[dev]'"
    exit 1
fi

function format() {
    echo "Formatting code..."
    python -m black src tests
    python -m isort src tests
}

function lint() {
    echo "Linting code..."
    python -m ruff src tests
    python -m mypy src tests
}

function test() {
    echo "Running tests..."
    python -m pytest tests -v
}

function all() {
    format
    lint
    test
}

case "$1" in
    "format")
        format
        ;;
    "lint")
        lint
        ;;
    "test")
        test
        ;;
    "all")
        all
        ;;
    *)
        echo "🦍 Usage: $0 {format|lint|test|all}"
        exit 1
        ;;
esac

deactivate 2>/dev/null 