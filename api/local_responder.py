import re
import json
import os

def generate_local_response(user_message: str) -> str:
    msg = user_message.lower().strip()
    
    # Load prompt.json data if available
    current_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(current_dir, "prompt.json")
    data = {}
    if os.path.exists(json_path):
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            pass

    # Guardrail 1: Code generation / technical scripts / leetcode
    if any(k in msg for k in [
        "write code", "python script", "javascript", "binary search", "algorithm", 
        "solve this", "function(", "def ", "class ", "write a program", "write a function",
        "sql query", "html code", "react code"
    ]):
        return (
            "I'm designed as a portfolio guide rather than a general coding assistant.\n\n"
            "- I specialize in answering questions about Chen's product design work, design systems, and enterprise UX.\n"
            "- Under his strict guardrails, I don't write scripts or solve general programming exercises.\n"
            "- If you'd like to discuss technical implementation or collaboration, feel free to reach out to Chen directly.\n\n"
            "→ View: https://chenthuran.in/work"
        )

    # Guardrail 2: Salary / Compensation / Rates
    if any(k in msg for k in [
        "salary", "compensation", "rate", "cost", "how much", "hourly", 
        "package", "ctc", "pricing", "budget", "fee"
    ]):
        return (
            "Chen handles all compensation and contracting conversations directly.\n\n"
            "- Rates and compensation depend on project scope, role requirements, and engagement model.\n"
            "- You can connect with him directly to discuss compensation details:\n"
            "- Email: chencse@gmail.com\n"
            "- LinkedIn: https://www.linkedin.com/in/chenthuran-ilango-aa2026b7/\n\n"
            "→ View: https://chenthuran.in/#contact"
        )

    # Suggestion 3 / Contact queries
    if any(k in msg for k in [
        "contact", "email", "reach", "hire", "phone", "linkedin", "touch", 
        "connect", "call", "message him", "get in touch"
    ]):
        return (
            "Here is how you can connect with Chen directly:\n\n"
            "- Email: chencse@gmail.com\n"
            "- LinkedIn: https://www.linkedin.com/in/chenthuran-ilango-aa2026b7/\n"
            "- Location: India / Open to global remote opportunities\n"
            "- Target Roles: Senior IC roles in Design Systems, Enterprise UX, and Developer Platforms.\n\n"
            "→ View: https://chenthuran.in/#contact"
        )

    # Location / Remote work / Availability
    if any(k in msg for k in ["location", "remote", "where is", "where does", "relocate", "relocation", "availability", "timezone"]):
        return (
            "Chen is based in India and fully available for global remote roles:\n\n"
            "- Location: India (collaborates across US, Europe, and APAC time zones).\n"
            "- Availability: Open to Senior Product Designer / Staff IC opportunities.\n"
            "- Work Model: Remote / distributed teams.\n"
            "- Contact directly to discuss alignment and timelines.\n\n"
            "→ View: https://chenthuran.in/#contact"
        )

    # Suggestion 2 / Most complex project queries
    if any(k in msg for k in [
        "complex project", "most complex", "hardest", "challenging", "biggest challenge",
        "most difficult", "complex system"
    ]):
        return (
            "Chen's most architecturally complex project is the DOSB Financing Ecosystem:\n\n"
            "- The challenge: Balancing opposite user needs — simple enough for small business borrowers, trustworthy enough for institutional allocators.\n"
            "- The approach: Abstracted smart contract complexity behind a unified identity pass (Wells Pass) while keeping governance transparent.\n"
            "- Impact: Slashed underwriting approval cycles from weeks to under 48 hours in pilot testing.\n"
            "- Another high-complexity system is Horizon Bank Developer Central, unifying fragmented toolchains for thousands of engineers.\n\n"
            "→ View: https://chenthuran.in/dosb-financing-ecosystem"
        )

    # Transforming a Design System / Table component / Tokens
    if any(k in msg for k in [
        "design system", "token", "figma library", "components", "table component", 
        "library", "detachment", "assembly time", "design kit", "prescriptive"
    ]):
        return (
            "Chen has deep expertise in architecting enterprise design systems that teams actually adopt:\n\n"
            "- Rebuilt an internal component library into a prescriptive platform, cutting assembly time from 20 minutes to under 5.\n"
            "- Reduced component detachment by 50% by building sensible defaults and simplifying complex configurations.\n"
            "- Solved hard data patterns like responsive enterprise tables and nested filters.\n"
            "- Embedded design guidance directly into the Figma canvas to eliminate wiki documentation friction.\n\n"
            "→ View: https://chenthuran.in/transforming-a-design-system"
        )

    # Horizon Bank Developer Central / Developer Tools
    if any(k in msg for k in [
        "horizon", "developer central", "developer tool", "mfe", "internal tool", 
        "portal", "bank", "onboarding lead time", "integration bugs", "developer platform"
    ]):
        return (
            "Here is an overview of Chen's work on Horizon Bank Developer Central:\n\n"
            "- Consolidated fragmented internal developer tools into a single self-service portal (Discover, Build, Learn, Manage).\n"
            "- Cut onboarding lead time by 65% and integration bugs by 35% across thousands of engineers.\n"
            "- Designed in-browser sandbox editors, API exploration tools, and automated code scaffolding.\n"
            "- Supported migration to modular Micro-Front-End (MFE) architecture.\n\n"
            "→ View: https://chenthuran.in/horizon-bank-developer-central"
        )

    # DOSB Financing Ecosystem / Fintech / Blockchain / DLT
    if any(k in msg for k in [
        "dosb", "fintech", "defi", "ledger", "dlt", "blockchain", "equity", 
        "diverse", "loan", "lending", "capital bridge", "wells pass"
    ]):
        return (
            "Here is an overview of Chen's work on the DOSB Financing Ecosystem:\n\n"
            "- Designed a decentralized capital bridge on Distributed Ledger Technology for diverse-owned small businesses.\n"
            "- Abstracted complex on-chain verification behind a familiar digital identity pass (Wells Pass).\n"
            "- Integrated real-time proxy voting modules directly into financial dashboards alongside live NAV and yield metrics.\n"
            "- Reduced loan approval times from 21 days to under 48 hours in prototype pilot testing.\n\n"
            "→ View: https://chenthuran.in/dosb-financing-ecosystem"
        )

    # Beyond BAU / Initiatives / Plugins / Experiments / Idea Godown
    if any(k in msg for k in [
        "beyond bau", "plugin", "idea godown", "initiative", "side project", 
        "experiment", "hardware", "research", "comment analyzer", "decision log", "personality workshop"
    ]):
        return (
            "Chen actively builds self-directed tooling and research initiatives beyond routine product work:\n\n"
            "- Comment Analyzer Plugin: LLM-powered Figma plugin categorizing design review comments (40% triage speedup).\n"
            "- Design Decision Log: Captures canvas rationale and syncs live to Notion and GitHub via webhooks.\n"
            "- Design System Assistant: AI copilot testing design tokens and accessibility specs.\n"
            "- Idea Godown: Research ledger exploring speculative hardware, gaming controllers, and physical interfaces.\n\n"
            "→ View: https://chenthuran.in/beyond-bau"
        )

    # Design process / Developer collaboration / Working with engineers
    if any(k in msg for k in [
        "process", "collaboration", "engineer", "developers", "methodology", 
        "how does he work", "how he works", "workflow", "critique", "handoff"
    ]):
        return (
            "Chen's design approach centers on systems thinking and deep engineering collaboration:\n\n"
            "- Partners early with engineers to understand architectural constraints and API realities before designing.\n"
            "- Replaces static specs with prescriptive design components and living canvas documentation.\n"
            "- Connects design tokens directly with frontend code to eliminate handoff ambiguity.\n"
            "- Focuses on measurable adoption and real developer velocity rather than isolated mockups.\n\n"
            "→ View: https://chenthuran.in/work"
        )

    # Awards / Career Highlights / Bio / Background / Experience
    if any(k in msg for k in [
        "award", "highlight", "experience", "years", "career", "background", 
        "who is", "about", "bio", "tell me about chen", "summary"
    ]):
        return (
            "Chen is a Senior Product Designer with over 10 years of enterprise design experience:\n\n"
            "- Specializes in design systems, developer platforms, and complex financial/enterprise software.\n"
            "- Received 5 career awards: 2x Manager Spotlight Award, 2x Star Award (Employee of the Year), and 1x iDesign Award.\n"
            "- Proven measurable impact: cut component assembly from 20 to 5 minutes, and dropped onboarding lead times by 65%.\n"
            "- Worked across Fintech, DeFi/DLT, Enterprise SaaS, Banking, Healthcare, and Government sectors.\n\n"
            "→ View: https://chenthuran.in/work"
        )

    # Suggestion 1 / Core design skills / expertise
    if any(k in msg for k in [
        "core design skills", "skill", "expertise", "competenc", "strength", 
        "what can", "core", "tools", "figma"
    ]):
        return (
            "Chen's core design expertise spans four main areas:\n\n"
            "- Design Systems & Platform Work: Tokenized architecture, composite components, and driving adoption across large teams.\n"
            "- Enterprise & Developer UX: Transforming dense, high-friction technical workflows into intuitive self-service platforms.\n"
            "- Complex Systems & Fintech: Simplifying multi-stakeholder lending workflows, compliance, and distributed ledger mechanics.\n"
            "- AI & Agentic Design: Designing AI assistants and copilots that surface clear mental models and actionable trust signals.\n\n"
            "→ View: https://chenthuran.in/work"
        )

    # Off-topic / Non-portfolio questions
    if any(k in msg for k in [
        "capital of", "weather", "recipe", "joke", "movie", "president", 
        "song", "who won", "game"
    ]):
        return (
            "I'm Chen's portfolio assistant, so I'm focused specifically on his design work:\n\n"
            "- I can answer questions about his design systems, developer platforms, and case studies.\n"
            "- I can share insights into his 10+ years of enterprise UX experience and career milestones.\n"
            "- Feel free to ask about any project or reach out to Chen directly.\n\n"
            "→ View: https://chenthuran.in/work"
        )

    # Greetings / Default portfolio introduction
    return (
        "Hello! I am Chen's personal portfolio assistant. Here are quick ways to explore his work:\n\n"
        "- Design Systems: Transforming a component library into a productivity platform with 5-minute assembly times.\n"
        "- Developer Platforms: Horizon Bank Developer Central, unifying internal workflows for thousands of engineers.\n"
        "- Fintech & DLT: Architecture as Equity, expanding capital access for diverse-owned small businesses.\n"
        "- Beyond BAU: Figma automation plugins, decision logging tools, and interactive hardware prototypes.\n\n"
        "→ View: https://chenthuran.in/work"
    )
