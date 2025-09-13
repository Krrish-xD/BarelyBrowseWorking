# ChatGPT Browser

## Overview

ChatGPT Browser is a minimal Python-based desktop application that provides a dedicated browsing environment exclusively for ChatGPT.com. The application features workspace isolation, session persistence, and a built-in notepad system. It's designed to provide users with multiple isolated ChatGPT sessions while maintaining complete separation between workspaces.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture
- **UI Framework**: PyQt6-based desktop application with QtWebEngine for web rendering
- **Window Management**: Single main window with tabbed interface and workspace switching
- **Component Structure**: Modular UI components including main window, notepad widget, and workspace management dialogs
- **Theme**: Dark theme with consistent color palette (#141414, #282828, #3c3c3c)

### Backend Architecture
- **Session Management**: JSON-based session persistence with automatic saving every 4 minutes
- **Data Storage**: File-system based storage with separate directories per workspace
- **URL Filtering**: Custom interceptor restricting navigation to ChatGPT and essential OpenAI domains only
- **Workspace Isolation**: Each workspace maintains separate QtWebEngine profiles with isolated cookies, cache, and local storage

### Core Components
- **Main Application**: Entry point with headless mode support for CI/testing
- **Workspace Management**: 4 isolated workspaces with independent web sessions
- **Tab Management**: Multi-tab support within each workspace with restore functionality
- **Notepad System**: Per-workspace notepad with Markdown support and persistent storage
- **Session Persistence**: Automatic save/restore of workspace states, tabs, and notepad content

### Web Engine Configuration
- **Profile Isolation**: Each workspace uses separate QtWebEngine profiles stored in isolated directories
- **Security Settings**: Sandbox configuration with development/CI environment adaptations
- **URL Restriction**: Strict filtering allowing only ChatGPT-related domains and essential resources

### Data Storage Design
- **Session Data**: JSON files storing workspace configurations, tab states, and metadata
- **Notepad Storage**: Separate text files per workspace for notepad content
- **Profile Data**: QtWebEngine profile directories for cookies, cache, and web storage
- **Cross-Platform Paths**: Platform-aware directory management using Qt's standard paths with fallbacks

### State Management
- **Auto-Save Triggers**: 4-minute intervals, app close, workspace switch, and tab close events
- **Restoration**: Complete workspace state restoration on application startup
- **Workspace Switching**: Hot-swapping between workspaces with preserved states

## External Dependencies

### Core Framework
- **PyQt6**: Main UI framework and QtWebEngine for web rendering
- **QtWebEngineCore**: Web engine profiles, URL interception, and page management

### System Integration
- **Cross-Platform Support**: Windows (APPDATA), macOS (Library/Application Support), Linux (XDG_DATA_HOME)
- **Headless Environment**: CI/testing support with sandbox configuration
- **Standard Paths**: Qt's QStandardPaths for platform-appropriate data directories

### Web Dependencies
- **Allowed Domains**: Restricted to chatgpt.com and essential OpenAI subdomains (auth0.openai.com, cdn.openai.com, static.openai.com, api.openai.com)
- **CDN Resources**: Cloudflare CDN and Azure blob storage for ChatGPT assets
- **OAuth Integration**: OpenAI authentication services through designated endpoints