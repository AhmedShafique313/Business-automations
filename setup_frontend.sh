#!/bin/bash
set -e

echo "Cleaning up existing frontend directory..."
rm -rf frontend

echo "Creating new Next.js project..."
yes "n" | npx create-next-app@13.5.6 frontend \
  --typescript \
  --tailwind \
  --eslint \
  --app \
  --src-dir \
  --use-npm \
  --no-turbo

echo "Installing additional dependencies..."
cd frontend && npm install \
  @reduxjs/toolkit \
  react-redux \
  @headlessui/react \
  @heroicons/react \
  chart.js \
  react-chartjs-2 \
  @mui/material \
  @mui/icons-material \
  @emotion/react \
  @emotion/styled \
  react-beautiful-dnd \
  axios \
  --legacy-peer-deps

echo "Setup complete!"
