#!/bin/bash

function format() {
    echo "Formatting code..."
    black src tests
    isort src tests
}

function lint() {
    echo "Linting code..."
    ruff src tests
    mypy src tests
}

function test() {
    echo "Running tests..."
    pytest tests -v
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
        echo "Usage: $0 {format|lint|test|all}"
        exit 1
        ;;
esac 