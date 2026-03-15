# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Purpose

Python-based home price affordability analysis project. Connects to the [FRED API](https://fred.stlouisfed.org/docs/api/fred/) to pull economic data and produces dashboards and analyses.

## Architecture

This is an early-stage Python project. As it grows, expect:
- **Data layer**: FRED API client for fetching economic indicators (home prices, income, mortgage rates, etc.)
- **Analysis layer**: Python scripts/notebooks processing and calculating affordability metrics
- **Visualization layer**: Dashboards displaying trends and comparisons

## FRED API

The Federal Reserve Economic Data (FRED) API requires an API key. Store it as an environment variable (`FRED_API_KEY`) — never hardcode it. Key series likely used:
- `MSPUS` — Median Sales Price of Houses Sold
- `MEHOINUSA672N` — Median Household Income
- `MORTGAGE30US` — 30-Year Fixed Rate Mortgage Average
- `CPIAUCSL` — Consumer Price Index (for real price adjustments)
