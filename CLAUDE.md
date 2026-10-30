# gaspirator

This file provides context about the project for AI assistants.

## Project Overview

- **Ecosystem**: Typescript

## Tech Stack

- **Runtime**: bun
- **Package Manager**: pnpm

### Frontend

- Framework: native-bare, tanstack-start
- CSS: tailwind
- UI Library: daisyui
- State: zustand

### Database

- Database: postgres

### Additional Features

- Testing: vitest

## Project Structure

```
my-app/
├── apps/
│   ├── web/         # Frontend application
│   ├── native/      # Mobile application (React Native)
├── packages/
│   └── db/          # Database schema
```

## Common Commands

- `pnpm install` - Install dependencies
- `pnpm dev` - Start development server
- `pnpm build` - Build for production
- `pnpm test` - Run tests
- `pnpm db:push` - Push database schema
- `pnpm db:studio` - Open database UI

## Better Fullstack project context

`bts.jsonc` is the authority for the current Stack Graph. Its `stackParts` array owns role selection and `ownerPartId` bindings. Top-level option fields are a compatibility projection and must not become a second mutation path.

### Stack Parts, ownership, and evidence

- `backend.api:dotnet:minimal-api`. It belongs to `backend:dotnet:aspnet-mvc`. Evidence is `listed` with `unverified` freshness. Verification maintainer: @Marve10s.
- `backend.auth:dotnet:aspnet-identity`. It belongs to `backend:dotnet:aspnet-mvc`. Evidence is `listed` with `unverified` freshness. Verification maintainer: @Marve10s.
- `backend.caching:dotnet:redis`. It belongs to `backend:dotnet:aspnet-mvc`. Evidence is `listed` with `unverified` freshness. Verification maintainer: @Marve10s.
- `backend.deploy:dotnet:docker`. It belongs to `backend:dotnet:aspnet-mvc`. Evidence is `listed` with `unverified` freshness. Verification maintainer: @Marve10s.
- `backend.jobQueue:dotnet:hosted-services`. It belongs to `backend:dotnet:aspnet-mvc`. Evidence is `listed` with `unverified` freshness. Verification maintainer: @Marve10s.
- `backend.libraries:dotnet:automapper`. It belongs to `backend:dotnet:aspnet-mvc`. Evidence is `listed` with `unverified` freshness. Verification maintainer: @Marve10s.
- `backend.observability:dotnet:serilog`. It belongs to `backend:dotnet:aspnet-mvc`. Evidence is `listed` with `unverified` freshness. Verification maintainer: @Marve10s.
- `backend.orm:dotnet:dapper`. It belongs to `backend:dotnet:aspnet-mvc`. Evidence is `listed` with `unverified` freshness. Verification maintainer: @Marve10s.
- `backend.realtime:dotnet:signalr`. It belongs to `backend:dotnet:aspnet-mvc`. Evidence is `listed` with `unverified` freshness. Verification maintainer: @Marve10s.
- `backend.testing:dotnet:xunit`. It belongs to `backend:dotnet:aspnet-mvc`. Evidence is `listed` with `unverified` freshness. Verification maintainer: @Marve10s.
- `backend.validation:dotnet:data-annotations`. It belongs to `backend:dotnet:aspnet-mvc`. Evidence is `listed` with `unverified` freshness. Verification maintainer: @Marve10s.
- `backend:dotnet:aspnet-mvc`. Its generated target is `apps/server`. Evidence is `listed` with `unverified` freshness. Verification maintainer: @Marve10s.
- `codeQuality:universal:eslint`. Evidence is not mapped for this installed option.
- `codeQuality:universal:prettier`. Evidence is not mapped for this installed option.
- `continuousIntegration:universal:github-actions`. Evidence is `listed` with `unverified` freshness. Verification maintainer: @Marve10s.
- `database:universal:postgres`. Its generated target is `packages/db`. Evidence is `listed` with `unverified` freshness. Verification maintainer: @Marve10s.
- `frontend.animation:typescript:gsap`. It belongs to `frontend:typescript:tanstack-start`. Evidence is `listed` with `unverified` freshness. Verification maintainer: @Marve10s.
- `frontend.css:typescript:tailwind`. It belongs to `frontend:typescript:tanstack-start`. Evidence is `listed` with `unverified` freshness. Verification maintainer: @Marve10s.
- `frontend.deploy:typescript:docker`. It belongs to `frontend:typescript:tanstack-start`. Evidence is `listed` with `unverified` freshness. Verification maintainer: @Marve10s.
- `frontend.forms:typescript:tanstack-form`. It belongs to `frontend:typescript:tanstack-start`. Evidence is `listed` with `unverified` freshness. Verification maintainer: @Marve10s.
- `frontend.httpClient:typescript:axios`. It belongs to `frontend:typescript:tanstack-start`. Evidence is `listed` with `unverified` freshness. Verification maintainer: @Marve10s.
- `frontend.stateManagement:typescript:zustand`. It belongs to `frontend:typescript:tanstack-start`. Evidence is `listed` with `unverified` freshness. Verification maintainer: @Marve10s.
- `frontend.ui:typescript:daisyui`. It belongs to `frontend:typescript:tanstack-start`. Evidence is `listed` with `unverified` freshness. Verification maintainer: @Marve10s.
- `frontend:typescript:tanstack-start`. Its generated target is `apps/web`. Evidence is `listed` with `unverified` freshness. Verification maintainer: @Marve10s.
- `gitHooks:universal:husky`. Evidence is `listed` with `unverified` freshness. Verification maintainer: @Marve10s.
- `mobile.deepLinking:react-native:expo-linking`. It belongs to `mobile:react-native:native-bare`. Evidence is `listed` with `unverified` freshness. Verification maintainer: @Marve10s.
- `mobile.navigation:react-native:expo-router`. It belongs to `mobile:react-native:native-bare`. Evidence is `listed` with `unverified` freshness. Verification maintainer: @Marve10s.
- `mobile:react-native:native-bare`. Its generated target is `apps/native`. Evidence is `listed` with `unverified` freshness. Verification maintainer: @Marve10s.

### Installed-version authority

Use `bts.jsonc` for the generator and schema version. Use local package manifests and lockfiles for installed dependency versions. Do not assume that documentation for a newer Better Fullstack release matches this project.

### Compatibility and lifecycle safety

Run `create-better-fullstack context --json` for bounded roles, capabilities, evidence, compatibility issues, and safe next actions. Run `create-better-fullstack doctor --json` before repairing graph drift. Existing-project writes must start with a plan and use the exact review token. Use `create-better-fullstack recipes check --json` before editing recipe-owned paths or managed regions, and use recipe history plus project recovery commands to undo a reviewed operation.

User code outside an explicit Better Fullstack managed region is not generator-owned. Missing or changed managed-region hashes stop recipe planning for manual review.

<!-- <better-fullstack:recipes sha256=e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855> -->

<!-- </better-fullstack:recipes> -->

## Maintenance

Keep CLAUDE.md updated when:

- Adding/removing dependencies
- Changing project structure
- Adding new features or services
- Modifying build/dev workflows

AI assistants should suggest updates to this file when they notice relevant changes.
