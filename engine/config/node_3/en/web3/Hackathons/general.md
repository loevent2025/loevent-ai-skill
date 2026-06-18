# Web3 · Hackathon · Venue Selection Criteria Knowledge Base

## Scale Quick Reference

| Scale Level     | Capacity      | Duration    | Typical Scenarios                                              |
| --------------- | ------------- | ----------- | -------------------------------------------------------------- |
| Mini Hackathon  | 20–50 pax     | 1 day       | Protocol internal sprint, ecosystem-themed invitation-only competition |
| Standard Hackathon | 50–150 pax | 24–48 hours | Public chain ecosystem hackathon, regional Web3 developer competition |
| Large Hackathon | 150–300 pax   | 48–72 hours | National Web3 developer competition, conference-affiliated hackathon |

---

## Functional Zone Reference

| Functional Zone     | Area Share | Core Configuration Requirements                                |
| ------------------- | ---------- | --------------------------------------------------------------- |
| Development Workspace | 50–60%   | Open workstations, team zones divisible, ≥ 2 m² per person     |
| Pitch / Showcase Area | 15–20%  | Speaker area or stage, large screen, judges' seating            |
| On-Chain Demo Zone  | 10%        | Independent network circuit, multi-device parallel use, space for observers |
| Rest Area           | 10–15%    | Lie-flat space available, dimmable lighting                     |
| Dining Area         | 10%        | Separate zone, no interference with the development workspace   |
| Mentor Station      | 5–10%     | Semi-isolated corners or small meeting rooms                    |

---

# Selection Criteria

---

## Criterion 1: Network & Technical Infrastructure (Top Hard Requirement)

**Definition:**
The primary threat at a Web3 Hackathon is not insufficient bandwidth — it's blocked node access. Overseas RPC nodes, decentralized storage services, and blockchain explorers are often intercepted by firewalls on enterprise or tech-park networks, making on-chain demonstrations completely impossible. This is the number-one verification priority when selecting a Web3 Hackathon venue.

**Assessment Areas:**

Network Bandwidth & Concurrency
- Total bandwidth ≥ 500 Mbps (1 Gbps recommended for 150+ attendees)
- Support for 100+ devices simultaneously making high-frequency on-chain node requests
- Wired backbone network covering the development area (Wi-Fi alone is insufficient)
- Wired access point density: at least 1 wired port per 10 people
- Full-venue Wi-Fi coverage with no dead zones

Access Permissions (Core Web3 Requirement)
- No port restrictions, no firewall blocking
- Unrestricted access to major public chain RPC nodes: Ethereum, Solana, BNB Chain, Polygon, Arbitrum, Optimism, etc.
- Unrestricted access to node service providers: Infura, Alchemy, QuickNode, Ankr
- Unrestricted access to decentralized storage: IPFS, Arweave
- Unrestricted access to blockchain explorers: Etherscan, Solscan, etc.
- Unrestricted access to development dependencies: GitHub, npm, crates.io (for Rust/Solana development)
- Permission to bring external routers or standalone hotspots (strongly recommended as a standard backup)

Backup Plan
- Multiple 4G/5G hotspots provisioned as emergency backup
- Clearly defined incident response process and response time for network failures

Power (Hard Requirement on Par with Network)
- Independent outlet per workstation — no daisy-chained power strips
- At least 4–6 outlets per table (participants typically carry 2–3 devices)
- Total circuit load supports high-density simultaneous device operation
- Independent power circuits for the speaker area and demo zone

---

## Criterion 2: Endurance & Extended-Use Support (Hard Requirement)

**Definition:**
Web3 developers are distributed across time zones with irregular development rhythms. The late-night and early-morning hours of a Hackathon are often the most productive development phases. The venue must operate without interruption throughout the entire event duration.

**Assessment Areas:**

Usage Hours
- Explicit support for continuous 24-hour or 48-hour use (written into the contract)
- Unrestricted nighttime entry and exit (access control and security coordination)
- HVAC and ventilation systems running throughout the night (must not auto-shutdown for energy saving)
- Cleaning services available on a scheduled basis during the event without disrupting the development area

Setup & Teardown
- Permission to enter 8–12 hours before the event for setup
- Clearly defined teardown window — no immediate eviction after the event ends
- Overtime billing terms confirmed in advance

---

## Criterion 3: Development Workspace Quality (Hard Requirement)

**Definition:**
The development workspace is where participants spend the most time. Web3 developers — especially smart contract developers and protocol engineers — need a work environment that is adequate, stable, and undisturbed. It doesn't need to be luxurious, but it must support sustained high-efficiency work over long hours.

**Assessment Areas:**

Space & Furniture
- Usable area per person ≥ 2 m² (including walkways)
- Desk depth ≥ 60 cm (enough for a laptop + external devices)
- Chairs suitable for extended use (not folding chairs; must have backrests)
- Team zones divisible by furniture or signage (3–5 people per team)

Lighting & Environment
- Adjustable lighting (reduced brightness for late-night hours)
- No strong light sources causing screen glare
- Controllable noise levels (development area and pitch area require spatial separation)
- Independent HVAC controls with zone-based temperature adjustment

---

## Criterion 4: On-Chain Demo & Protocol Presentation Support (Hard Requirement)

**Definition:**
Web3 Hackathon demo scenarios are fundamentally different from other industries: participants need to present live smart contract deployments, on-chain interactions, wallet signing, and protocol integrations on-site. These demonstrations are critically dependent on network stability and unrestricted access — there is no way to "switch to a different demo format" as a workaround.

**Assessment Areas:**

Dedicated Demo Zone Configuration
- Dedicated demo corner available, supporting 2–5 booths simultaneously
- Independent power supply per booth (no shared outlets)
- Demo zone network runs on an independent circuit (prevents development area traffic congestion from affecting presentations)
- Adequate or adjustable lighting (on-chain operation interfaces must be clearly visible)
- Space for multiple observers (Web3 demos typically attract a significant crowd)

Web3 Presentation–Specific Requirements
- Network provides unrestricted access to all major public chain RPC nodes (see Criterion 1)
- Stable network latency (on-chain transaction broadcasting and confirmation are time-sensitive — excessive latency disrupts demo fluidity)
- Support for running local testnet nodes (tools like Hardhat/Anvil require stable port access)
- Support for MetaMask and hardware wallet (Ledger/Trezor) local signing demonstrations
- Screen casting supports multi-window side-by-side display (smart contract code, blockchain explorer, and frontend interface must be shown simultaneously)
- Permission for on-site screen recording and livestreaming

---

## Criterion 5: Pitch & Showcase Area Support (Hard Requirement)

**Definition:**
The pitch session is the climax of a Hackathon. The unique aspect of Web3 pitches is the high technical density of presentation content — smart contract code, on-chain data, protocol architecture diagrams — which demands exceptionally high screen clarity and stability.

**Assessment Areas:**

Stage & Visual
- Dedicated speaker area or stage (distinct from the development workspace)
- Unobstructed screen visibility from all seats
- Large screen resolution ≥ 1080p (smart contract code, transaction hashes, and protocol architecture diagrams must be clearly readable)
- Dual-screen output support (speaker preview + audience screen)
- Customizable backdrop or brand display area

Sound & Microphones
- Full-venue audio coverage with no dead spots
- At least 2 wireless microphones (speaker + roving Q&A)
- Stable microphone system with no interference

Judges & Timing
- Clearly designated judges' seating area
- Timer display support (Web3 pitches typically enforce strict time controls)

---

## Criterion 6: Living Amenities & Extended-Duration Support (High-Weight Criterion)

**Definition:**
During a 24–72-hour Hackathon, food, rest, and sanitation are the baseline conditions that affect participant performance and completion rates. Web3 developers have a relatively high tolerance for basic amenities, but essential provisions must be in place.

**Assessment Areas:**

Dining
- Dedicated dining area (not shared with the development workspace)
- Venue permits external catering teams to operate on-site
- Refrigerator or warming equipment available for storing beverages and late-night snacks
- Continuously available coffee/beverage station (24 hours)

Rest
- Dedicated rest area, physically separated from the development workspace
- Lie-flat rest permitted (air mattresses, sofas are acceptable — confirm in advance with the venue)
- Independently dimmable lighting

Restrooms
- Count: recommended 1 per 50 attendees
- Available 24 hours with no nighttime closures

---

## Criterion 7: Web3 Industry Tone Alignment (High-Weight Criterion)

**Definition:**
Web3 developers evaluate a venue's tone by one standard: does this place feel right for hackers, for the open-source ethos, for "our own community event"? Overly commercialized, overly polished, or overly corporate venues create a sense of alienation among participants — and may even reduce willingness to attend.

**Web3 Hackathon Tone Positioning:**
> Hacker-friendly, but not messy
> Community-driven, but not amateurish
> Spacious, but no luxury finishes needed

**✅ Suitable Venue Types:**
- Tech parks / innovation centers (strong sense of openness, solid infrastructure)
- Converted warehouses or industrial-style lofts (high ceilings, open floor plans — aligned with hack culture)
- Co-working spaces (open-plan preferred, no heavy corporate décor)
- Blockchain / Web3 company offices (strong ecosystem identity)
- University engineering buildings or open-source labs (high alignment with open-source culture)
- Semi-underground or basement spaces (acceptable in the Web3 context if facilities are adequate)

**❌ Venue Types to Avoid:**
- Traditional hotel banquet halls (overly corporate feel, strong clash with Web3 developer culture)
- Luxury venues (the Web3 community instinctively rejects conspicuous spending — it invites questions about "where this money came from")
- Heavily branded commercial sponsor venues (the community perceives "being marketed to" rather than "our own event")
- Pure exhibition centers (too vast and impersonal, weak technical atmosphere)

---

## Criterion 8: Spatial Capacity & Zoning Flexibility (Hard Requirement)

**Definition:**
A Hackathon requires multiple functional zones operating simultaneously without interference. A Web3 Hackathon additionally requires a dedicated on-chain demo zone with network independence from the development area, while remaining accessible for observers.

**Space Reference:**

| Event Phase       | Space per Person |
| ----------------- | ---------------- |
| Development Phase | 2 m²            |
| Pitch Phase       | 1–1.2 m²        |

**Assessment Areas:**
- Whether total area and individual zone areas satisfy simultaneous operation requirements
- Development area and pitch area can be physically separated (minimize mutual interference)
- Rest area fully isolated from the development area (ensure rest quality)
- Demo zone can be independently zoned with a dedicated network circuit
- Furniture layout is flexibly adjustable (development phase → pitch phase turnaround time ≤ 2 hours)
- HVAC and ventilation with zone-based controls

---

## Criterion 9: Transportation & Accessibility (Flexible Criterion)

**Definition:**
Web3 developers have a higher tolerance for "traveling extra distance for a good event" compared to general audiences, but poor accessibility will reduce attendance among non-core participants. Nighttime departure safety must also be considered.

**Assessment Areas:**
- Within a 15-minute walk from a metro station (can be relaxed — a venue with strong tone alignment can compensate)
- Ride-hailing friendly (clear pickup and drop-off points; participants carrying equipment need easy loading/unloading access)
- Safe late-night and early-morning departures (surrounding environment, lighting)
- Clear venue entrance signage (non-standard venues require wayfinding signage planned in advance)

---

## Criterion 10: Community Building & Brand Presentation (Flexible Criterion)

**Definition:**
For organizers, a Web3 Hackathon is both a technical competition and an ecosystem community-building opportunity. However, the Web3 community resists "over-branding" — brand presentation must prioritize community buy-in over one-directional organizer messaging.

**Assessment Areas:**
- Pitch area allows branded backdrop placement (restrained style — avoid the look of large-scale commercial advertising)
- Photo-friendly areas available (emphasizing authenticity and on-the-ground energy rather than staged shots)
- Full-event photography and livestreaming permitted (including on-chain demo content)
- Supports community retention touchpoints (group sign-up guidance, wallet address QR code scanning, etc.)
- Whether the venue operator is itself a Web3 ecosystem participant (ecosystem synergy is a bonus)
- Whether long-term recurring use is available (establishes a "regular community hub" identity)

---

## Criterion 11: Operational Compliance & Usage Restrictions (Flexible Criterion)

**Definition:**
Web3 Hackathons have a high proportion of non-standard venue usage. Overnight operations, external catering on-site, and large-scale device connectivity are all standard practice — each restriction must be confirmed with the venue in advance.

**Assessment Areas:**
- Maximum occupancy clearly defined and meets requirements
- Permission to host public competition events (some office buildings or tech parks have restrictions)
- Permission for external catering teams to operate on-site
- Noise management restrictions (during late-night hours)
- Usage compliance for non-standard venues (whether the lease agreement permits this type of competition event)
- Venue liability insurance clearly assigned

---

# Default Priority Ranking

## Hard Requirements (Failure to meet = automatic disqualification)
1. Network & Technical Infrastructure (especially: overseas node access permissions, RPC connectivity)
2. Endurance & Extended-Use Support (24-hour continuous operation)
3. Development Workspace Quality
4. On-Chain Demo & Protocol Presentation Support
5. Pitch & Showcase Area Support
6. Spatial Capacity & Zoning Flexibility

## High-Weight Criteria (Strongly influence the decision)
7. Living Amenities & Extended-Duration Support
8. Web3 Industry Tone Alignment

## Flexible Criteria (Assessed based on specific circumstances)
9. Transportation & Accessibility
10. Community Building & Brand Presentation
11. Operational Compliance & Usage Restrictions

---

# Hybrid Scenario Guidelines

### Hackathon + Opening Launch Event
- Pitch area must be upgraded to a professional-grade stage
- Community Building & Brand Presentation upgraded to a hard requirement
- AV equipment upgraded (professional sound system, minimum 2 large screens)
- Brand presentation style maintains community feel — avoid over-commercialization
- Venue must switch rapidly to development mode after the opening ceremony (turnaround time ≤ 1 hour)

### Hackathon + Demo Day (Post-Competition Pitch)
- Pitch area and judges' reception area must be planned simultaneously
- External audience admission permitted (capacity and entrance traffic flow require reassessment)
- Network must support livestream output (the Web3 community is highly dependent on online simultaneous distribution)
- On-chain demo zone retained and upgraded (Demo Day phase presentations are more complete)

### Hackathon + Conference Side Event
- Venue within walking distance of the main conference is preferred (attendees are unwilling to travel far between venues)
- Scheduling constraints are tight (attendees during conference periods have packed agendas)
- Network independence is especially critical (networks near large conferences are typically congested — an independent circuit must be established)
- Brand presentation should be more restrained (avoid over-emphasizing sponsors at a community event)

### Mini Hackathon (1 Day)
- Scheduling flexibility requirements are reduced (overnight support not needed)
- Rest area configuration requirements are reduced
- Catering only needs to cover lunch + refreshments
- Core focus areas: network (RPC access permissions), power, workspace floor area