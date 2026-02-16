# Flow Visualizations Index

This index helps you find the right diagram for your needs.

## Quick Links

- **[PRODUCT_ANALYST_DIAGRAMS.md](PRODUCT_ANALYST_DIAGRAMS.md)** - Comprehensive technical diagrams (27KB, 930 lines)
- **[QUICK_FLOW_REFERENCE.md](QUICK_FLOW_REFERENCE.md)** - Quick reference and simplified flows (10KB, 250 lines)

---

## What diagram should I look at?

### I want to understand...

#### **...how the system works overall**
→ [System Architecture Diagram](PRODUCT_ANALYST_DIAGRAMS.md#1-system-architecture)  
Shows all components (Telegram, FastAPI, LLM, Swiss Ephemeris, Database) and their interactions.

#### **...what happens when a new user joins**
→ [First-Time User Journey](PRODUCT_ANALYST_DIAGRAMS.md#21-first-time-user-journey)  
Complete flow from sending birth data to receiving first reading.

#### **...what happens when users chat with the bot**
→ [Returning User Journey](PRODUCT_ANALYST_DIAGRAMS.md#22-returning-user-journey-assistant-mode)  
Shows how assistant mode works with conversation context.

#### **...how messages are processed**
→ [Message Processing Pipeline](PRODUCT_ANALYST_DIAGRAMS.md#31-message-processing-pipeline)  
Step-by-step flow from webhook to response.

#### **...how birth data is extracted**
→ [Birth Data Extraction Flow](PRODUCT_ANALYST_DIAGRAMS.md#32-birth-data-extraction-flow)  
LLM-based parsing of natural language input.

#### **...how natal charts are generated**
→ [Chart Generation Flow](PRODUCT_ANALYST_DIAGRAMS.md#33-chart-generation-flow)  
Swiss Ephemeris astronomical calculations.

#### **...what user states exist**
→ [User State Transitions](PRODUCT_ANALYST_DIAGRAMS.md#41-user-state-transitions)  
State machine showing all possible user states.

#### **...the database structure**
→ [Entity Relationship Diagram](PRODUCT_ANALYST_DIAGRAMS.md#61-entity-relationship-diagram)  
Complete database schema with all tables and relationships.

#### **...how deployment works**
→ [Deployment Architecture](PRODUCT_ANALYST_DIAGRAMS.md#7-deployment-architecture)  
Local development vs production (Render) setup.

#### **...metrics I can track**
→ [Key Metrics & Analytics](PRODUCT_ANALYST_DIAGRAMS.md#8-key-metrics--analytics-points)  
SQL queries for user engagement, performance, and feature usage.

#### **...a quick overview without details**
→ [Quick Flow Reference](QUICK_FLOW_REFERENCE.md)  
Simplified ASCII diagrams and quick facts.

---

## Diagram Types

### System Architecture
**Location:** [PRODUCT_ANALYST_DIAGRAMS.md § 1](PRODUCT_ANALYST_DIAGRAMS.md#1-system-architecture)  
**Format:** Mermaid flowchart  
**Purpose:** High-level component overview  
**Best for:** Understanding system boundaries and external dependencies

### User Journey Flows
**Location:** [PRODUCT_ANALYST_DIAGRAMS.md § 2](PRODUCT_ANALYST_DIAGRAMS.md#2-user-journey-flows)  
**Format:** Mermaid flowchart  
**Count:** 3 flows (first-time, returning, multi-profile)  
**Best for:** Understanding user experience and decision points

### Data Flow Diagrams
**Location:** [PRODUCT_ANALYST_DIAGRAMS.md § 3](PRODUCT_ANALYST_DIAGRAMS.md#3-data-flow--processing-pipeline)  
**Format:** Mermaid flowchart  
**Count:** 3 flows (message processing, birth data, chart generation)  
**Best for:** Understanding internal data transformations

### State Diagrams
**Location:** [PRODUCT_ANALYST_DIAGRAMS.md § 4](PRODUCT_ANALYST_DIAGRAMS.md#4-state-management)  
**Format:** Mermaid state diagram  
**Count:** 2 diagrams (user states, message processing)  
**Best for:** Understanding state transitions and edge cases

### Sequence Diagrams
**Location:** [PRODUCT_ANALYST_DIAGRAMS.md § 5](PRODUCT_ANALYST_DIAGRAMS.md#5-sequence-diagrams)  
**Format:** Mermaid sequence diagram  
**Count:** 4 sequences (birth data, chart generation, assistant, throttling)  
**Best for:** Understanding component interactions over time

### Database Schema
**Location:** [PRODUCT_ANALYST_DIAGRAMS.md § 6](PRODUCT_ANALYST_DIAGRAMS.md#6-database-schema)  
**Format:** Mermaid ERD  
**Best for:** Understanding data model and relationships

### Deployment Architecture
**Location:** [PRODUCT_ANALYST_DIAGRAMS.md § 7](PRODUCT_ANALYST_DIAGRAMS.md#7-deployment-architecture)  
**Format:** Mermaid flowchart  
**Count:** 3 diagrams (local, production, comparison)  
**Best for:** Understanding infrastructure and deployment options

---

## Use Cases by Role

### Product Manager
**Primary diagrams:**
- [User Journey Flows](PRODUCT_ANALYST_DIAGRAMS.md#2-user-journey-flows) - Understand user experience
- [Key Metrics](PRODUCT_ANALYST_DIAGRAMS.md#8-key-metrics--analytics-points) - Track engagement and usage
- [Quick Reference](QUICK_FLOW_REFERENCE.md) - Response times and common paths

**Questions you can answer:**
- What's the onboarding flow for new users?
- How long does each operation take?
- What metrics can I track?
- What features are being used most?

### System Architect
**Primary diagrams:**
- [System Architecture](PRODUCT_ANALYST_DIAGRAMS.md#1-system-architecture) - Component design
- [Deployment Architecture](PRODUCT_ANALYST_DIAGRAMS.md#7-deployment-architecture) - Infrastructure
- [Database Schema](PRODUCT_ANALYST_DIAGRAMS.md#6-database-schema) - Data model

**Questions you can answer:**
- What are the system boundaries?
- How do components communicate?
- What are the scalability constraints?
- How is data persisted?

### Developer (New to Codebase)
**Primary diagrams:**
- [Quick Reference](QUICK_FLOW_REFERENCE.md) - Start here for overview
- [Message Processing Pipeline](PRODUCT_ANALYST_DIAGRAMS.md#31-message-processing-pipeline) - Request flow
- [Sequence Diagrams](PRODUCT_ANALYST_DIAGRAMS.md#5-sequence-diagrams) - Component interactions

**Questions you can answer:**
- How does a message get processed?
- What happens when I call this function?
- Where should I add my feature?
- How do components interact?

### QA / Tester
**Primary diagrams:**
- [User Journey Flows](PRODUCT_ANALYST_DIAGRAMS.md#2-user-journey-flows) - Test scenarios
- [State Diagrams](PRODUCT_ANALYST_DIAGRAMS.md#4-state-management) - Edge cases
- [Quick Reference](QUICK_FLOW_REFERENCE.md#error-handling-points) - Validation points

**Questions you can answer:**
- What user flows should I test?
- What are the edge cases?
- What validation happens where?
- What error scenarios exist?

### Data Analyst
**Primary resources:**
- [Key Metrics & Analytics](PRODUCT_ANALYST_DIAGRAMS.md#8-key-metrics--analytics-points) - SQL queries
- [Database Schema](PRODUCT_ANALYST_DIAGRAMS.md#6-database-schema) - Table structure
- [Quick Reference](QUICK_FLOW_REFERENCE.md#key-metrics) - Metric definitions

**Questions you can answer:**
- How many users have completed onboarding?
- What's the average conversation depth?
- Which features are most popular?
- How many messages are throttled?

### DevOps / SRE
**Primary diagrams:**
- [Deployment Architecture](PRODUCT_ANALYST_DIAGRAMS.md#7-deployment-architecture) - Infrastructure
- [Message Processing Pipeline](PRODUCT_ANALYST_DIAGRAMS.md#31-message-processing-pipeline) - Request path
- [Quick Reference](QUICK_FLOW_REFERENCE.md#deployment-quick-reference) - Setup commands

**Questions you can answer:**
- How is the app deployed?
- What are the external dependencies?
- How do I set up monitoring?
- What's the difference between dev and prod?

---

## Diagram Format

All diagrams use **Mermaid** syntax, which:
- ✅ Renders automatically in GitHub
- ✅ Renders in most Markdown viewers
- ✅ Can be exported as PNG/SVG
- ✅ Is version-controllable (plain text)
- ✅ Is easy to update and maintain

To render locally:
- Use GitHub's Markdown preview
- Use VS Code with [Mermaid extension](https://marketplace.visualstudio.com/items?itemName=bierner.markdown-mermaid)
- Use [Mermaid Live Editor](https://mermaid.live/) for editing

---

## Quick Stats

**PRODUCT_ANALYST_DIAGRAMS.md:**
- File size: 27KB
- Total lines: 930
- Diagrams: 18 Mermaid diagrams
- Sections: 8 major sections
- Coverage: Architecture, flows, states, sequences, schema, deployment, metrics

**QUICK_FLOW_REFERENCE.md:**
- File size: 10KB
- Total lines: 250
- Format: Simplified ASCII art + tables
- Coverage: Core flows, timings, commands, quick reference

**Total documentation:** 37KB, 1180 lines of flow visualization

---

## Related Documentation

- [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) - Code organization and module responsibilities
- [STATEFUL_BOT_GUIDE.md](guides/STATEFUL_BOT_GUIDE.md) - State management implementation
- [CONVERSATION_THREAD_GUIDE.md](guides/CONVERSATION_THREAD_GUIDE.md) - Thread context details
- [DEBUG_MODE.md](guides/DEBUG_MODE.md) - Developer debug tools

---

## Contributing

To add or update diagrams:

1. Edit the Mermaid code in the markdown files
2. Test rendering in GitHub preview or Mermaid Live Editor
3. Ensure diagram supports both light and dark themes
4. Update this index if adding new diagrams
5. Keep diagrams focused and avoid overcrowding

**Mermaid tips:**
- Use subgraphs for grouping related components
- Add `style` directives for visual emphasis
- Keep text concise (use notes for details)
- Test both light/dark mode rendering
