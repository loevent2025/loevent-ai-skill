# Web3 · Large Exhibitions / Expo · Venue Evaluation Criteria Knowledge Base

## Scale Quick Reference

| Scale Level | Headcount | Typical Scenarios |
|-------------|-----------|-------------------|
| Mid-Size Exhibition | 300–800 | Regional Web3 expos, Vertical ecosystem showcases (DeFi/GameFi) |
| Large-Scale Exhibition | 800–2,000 | National Web3 technology expos, L1/L2 ecosystem conferences |
| Flagship Industry Event | 2,000+ | International Web3 summits, Conference-adjacent flagship exhibitions (e.g., ETH conference satellite events) |

---

## Functional Zone Reference

The zoning logic for Web3 exhibitions is similar to AI Commercial events, but the on-chain demo area has significantly higher network isolation requirements—RPC node access being blocked by firewalls is the most common source of technical failure at Web3 exhibitions. The demo area must have an independent network circuit and backup hotspots.

| Functional Zone | Area Share | Core Requirements |
|-----------------|------------|-------------------|
| Main Exhibition Floor | 40–50% | Mix of standard and custom booths, Aisle width between booths ≥2 m |
| Main Stage / Presentation Area | 15–20% | Professional AV system, LED large screen, Independently controllable lighting |
| On-Chain Demo Experience Zone | 15–20% | Independent network circuit, Multi-device parallel operation, Wallet connection experience flow |
| Ecosystem Networking Area | 10–15% | Semi-private, Open conversation encouraged, Decentralized atmosphere (not a formal meeting room feel) |
| Rest / Dining Area | 10% | Separate zone, Strong community gathering-point character, Not shared with exhibition floor |

---

# Evaluation Criteria

---

## Criterion 1: Network & Technical Infrastructure (Primary Hard Requirement)

**Definition:**
The network risks at a large-scale Web3 exhibition are fundamentally different from AI Commercial events: the core threat is not insufficient bandwidth, but overseas blockchain node access being blocked by firewalls. Once RPC nodes become inaccessible, on-chain interaction demos, wallet signatures, and real-time transaction confirmations all fail—and this type of failure typically cannot be resolved quickly. The larger the Web3 exhibition, the broader the impact of this risk.

**Evaluation Areas:**

Network Bandwidth & Concurrency
- Total bandwidth ≥1 Gbps (2 Gbps recommended for 2,000+ attendees)
- Support for 500+ devices simultaneously accessing on-chain nodes
- Wired backbone network covering the entire booth area (Wi-Fi alone is insufficient)
- Wired access in the booth area: one dedicated wired port per booth
- Full-venue Wi-Fi coverage with no dead zones, independent APs per zone

Access Permissions (Web3 Core Requirement)
- No port restrictions or firewall blocking
- Unrestricted access to mainstream public chain RPC nodes: Ethereum, Solana, BNB Chain, Polygon, Arbitrum, Optimism, Avalanche, etc.
- Unrestricted access to node service providers: Infura, Alchemy, QuickNode, Ankr
- Unrestricted access to decentralized storage: IPFS, Arweave
- Unrestricted access to blockchain explorers: Etherscan, Solscan, BscScan, etc.
- Each booth permitted to bring its own router or 4G/5G hotspot (strongly recommended as a standard backup, not an optional add-on)

Zoned Network Isolation
- Independent network circuit for the main stage / presentation area (prevent booth traffic from affecting main stage on-chain demos)
- Independent network circuit for the on-chain demo experience zone (ensure core experience stability)
- Key booths (flagship ecosystem booths) configured with dedicated network and backup hotspots

Backup Plan
- Venue equipped with high-powered 4G/5G signal amplification equipment
- Key booths configured with dedicated backup hotspots
- Clearly committed network failure response times

Power (Hard Requirement on Par with Network)
- Standard booths: dedicated power per booth, ≥4 outlets, single-phase 10A
- Custom booths: independent circuit, support for high-power equipment
- On-chain demo experience zone: independent power circuit, support for multi-device parallel operation
- Main stage: independent power supply, support for professional AV equipment at full capacity

## Criterion 2: Exhibition Space Structure & Load Capacity (Hard Requirement)

**Definition:**
The spatial requirements for large-scale Web3 exhibitions are broadly consistent with AI Commercial events, with two notable differences: first, Web3 community culture resists spaces that feel "overly formal," so the venue structure must strike a balance between professionalism and openness; second, the on-chain demo area must support multi-person crowd viewing and interaction, requiring wider aisles and more generous spatial design.

**Evaluation Areas:**

Main Exhibition Floor
- Clear height ≥6 m (to support custom booth construction including lighting trusses)
- Floor load capacity ≥500 kg/m² (for large booth structures)
- Aisle width in the booth area ≥2 m (bi-directional flow during peak traffic)
- Level flooring suitable for carpet or flooring installation
- Forklift and freight elevator access during setup

Main Stage / Presentation Area
- Physically independent space, soundproofed or semi-isolated from the exhibition floor
- Stage clear depth ≥8 m, clear width ≥12 m
- Audience area capacity matched to attendee count (based on comfortable capacity, not maximum)
- Rigging points or truss structures to support lighting and screen installation

On-Chain Demo Experience Zone
- Dedicated area with generous viewing space (≥6 m² viewing area per experience station)
- Clear queuing flow (Web3 demos typically attract large crowds)
- Independent power and independent network circuit
- Controllable lighting (screen content must be clearly visible)

Ecosystem Networking Area
- Semi-private with some sound isolation but maintaining an open feel (the Web3 community dislikes enclosed formal meeting rooms)
- Standing conversations encouraged (not forced seating)
- Atmosphere closer to a "community gathering point" than a "business meeting room"

Crowd Flow & Circulation
- Main entrance capacity matched to attendee volume
- Clear functional zone wayfinding (or permission for the host to install custom wayfinding)

---

## Criterion 3: Main Stage AV System Capability (Hard Requirement)

**Definition:**
The main stage presentations at Web3 exhibitions are technically dense: real-time on-chain data displays, protocol architecture diagrams, and code demos demand the same screen resolution and stability as AI Commercial events, but stylistically favor dark-stage lighting and a hacker-aesthetic visual design.

**Evaluation Areas:**

Screens & Displays
- LED screen pixel pitch ≤P2.5, resolution supporting 4K
- Dual-screen output support (presenter preview + audience main screen)
- Screen dimensions matched to maximum viewing distance in the audience area
- Multi-source video signal switching support (seamless switching between presentation slides, blockchain explorers, code, and video)

Audio System
- Professional line array speakers with full-venue coverage and no dead spots
- At least 4 wireless microphones (host, presenter, backup)
- No significant echo or feedback risk

Lighting System
- Dark-stage mode support (Web3 events favor low ambient lighting to highlight screen content)
- Independently controllable stage lighting with switchable presentation and showcase modes
- No significant ambient light reflection interfering with the main screen

Livestream & Recording
- Venue structure supports multi-camera positions (with stable mounting points)
- External livestream equipment permitted
- Network supports HD livestream broadcasting (dedicated bandwidth)

⚠️ The Web3 community relies heavily on real-time online distribution. Livestream stability is as critical to community influence as the on-site experience itself—dedicated livestream network bandwidth is mandatory.

---

## Criterion 4: On-Chain Demo & Protocol Showcase Capability (Hard Requirement)

**Definition:**
The on-chain demo is the single most differentiated segment of a Web3 exhibition—live wallet signatures, real-time on-chain interactions, and protocol integration demos cannot be replicated with videos or slides. The technical credibility of these demos directly determines booth appeal and a project's community reputation.

**Evaluation Areas:**

Demo Zone Base Configuration
- Dedicated on-chain demo experience zone, physically separated from the standard booth area
- Each experience station with independent power and independent network circuit
- High-definition display equipment (≥55 inches, resolution ≥1080p, suitable for group viewing)
- Ample viewing space (Web3 demos typically draw 10–20 simultaneous viewers)
- Clear queuing flow (to prevent crowd congestion in aisles)

Web3 Demo-Specific Requirements
- Unrestricted network access to all mainstream public chain RPC nodes (see Criterion 1)
- Stable network latency (on-chain transaction broadcasting and confirmation demos are latency-sensitive)
- Support for MetaMask and hardware wallet (Ledger/Trezor) local signing demos
- Support for running local testnet nodes (local chain tools such as Hardhat/Anvil require stable port access)
- Screen sharing supports multi-window side-by-side display (smart contract code, blockchain explorer, and frontend interface shown simultaneously)
- On-site screen recording and livestream publishing permitted

Backup Support
- Venue permits each booth to maintain independent backup hotspots
- On-site technical support staff available for rapid equipment troubleshooting during the exhibition

---

## Criterion 5: Web3 Industry Identity Alignment (High-Weight Criterion)

**Definition:**
The visitor profile at large-scale Web3 exhibitions is unique: core developers, protocol contributors, DAO members, crypto-native users, and investment institutions. This audience has a strong cultural radar and instinctively rejects venues that feel "overly commercialized," "traditionally corporate," or "marketing-heavy"—while gravitating toward spaces that feel "authentic," "hacker-spirited," and "community-owned."

**Web3 Exhibition Identity Positioning:**
> Professional enough for institutional investors and partners to feel confident
> Authentic enough for the core developer community to feel a sense of belonging
> Open enough for decentralized collaboration culture to emerge naturally

**✅ Suitable Venue Types:**
- Large industrial-converted exhibition halls (high ceilings, open layout, aligning with Web3's decentralized visual language)
- Tech park dedicated exhibition venues (strong technical atmosphere, minimal commercial feel)
- University or research institution large venues (high affinity with open-source culture)
- Architecturally distinctive modern urban venues (strong shareability without a traditional business feel)

**❌ Venue Types to Avoid:**
- Traditional five-star hotel ballroom clusters (the business and luxury-consumption feel clashes sharply with Web3 culture)
- Excessively lavish commercial real estate venues (the Web3 community instinctively rejects conspicuous luxury—"where did that money come from" skepticism directly undermines host credibility)
- Heavily sponsor-branded commercial venues (the community is extremely sensitive to feeling "captured by sponsors")
- Overly corporate zones within traditional convention centers (convention centers are acceptable, but styling must clearly differentiate from traditional trade shows)

⚠️ A venue identity misstep at a Web3 exhibition carries higher consequences than at AI Commercial events—negative perceptions from core community members amplify rapidly through X/Discord, damaging a project's community trust.

---

## Criterion 6: Capacity & Crowd Comfort Management (Hard Requirement)

**Definition:**
Crowd density management at large-scale Web3 exhibitions must balance "community energy" with "not compromising the on-chain demo experience." Overcrowding in the on-chain demo zone directly degrades demo performance and visitor experience quality.

**Area Reference Standards:**

| Exhibition Mode | Area Per Person |
|-----------------|-----------------|
| Exhibition viewing (mobile) | 1.5–2 m² |
| Main stage presentation (fixed seating) | 1–1.2 m² |
| On-chain demo experience zone (interactive) | 4–6 m² |

**Evaluation Areas:**
- Use comfortable capacity as the benchmark, not the venue's maximum occupancy
- Whether HVAC capacity can handle large crowds plus high-density equipment heat output simultaneously
- Independent climate control per functional zone
- Restroom count (recommended: 2 per 100 people)
- Entrance throughput capacity (no extended queuing during peak periods)

---

## Criterion 7: Setup & Teardown Conditions (Hard Requirement)

**Definition:**
Large-scale exhibitions typically require 2–3 days for setup and 1–2 days for teardown. Custom booths at Web3 exhibitions usually feature bold visual identities (dark color schemes, illuminated installations, immersive designs), with setup requirements broadly consistent with AI Commercial events.

**Evaluation Areas:**

Setup Conditions
- Early access permitted 3–5 days before the event for setup
- Freight access and freight elevators available (supporting large booth structures and equipment transport)
- Floor capable of supporting forklift operations
- Independent water and power available during the setup period
- Venue provides setup guidelines (clear height limits, rigging regulations, power application procedures)
- Dark-stage effects permitted (blackout treatment, LED ambient lighting, projection installations)

Teardown Conditions
- Teardown window of no less than 1 day
- Venue waste removal capacity matched to event scale

Technical Support
- On-site venue technical staff responsiveness
- Committed response times for network and power failures

---

## Criterion 8: Transportation & Accessibility (High-Weight Criterion)

**Definition:**
A significant proportion of visitors at Web3 exhibitions are international attendees (especially at ecosystem conference satellite exhibitions), making transportation accessibility particularly important for international audiences. At the same time, the core Web3 community has a higher tolerance for traveling further to attend a worthwhile event compared to general audiences.

**Evaluation Areas:**
- Distance from the city center or major transportation hubs (airports / high-speed rail stations)
- Direct metro access or convenient shuttle connections
- Parking capacity (for exhibitors, VIP guests, and ride-hailing needs of international attendees)
- Loading dock area accessible to large freight vehicles
- Nearby hotel availability (international attendee accommodation needs)
- Clear venue entrance signage with strong multi-entrance throughput capacity
- Safe nighttime departure (Web3 events typically include extended social activities, resulting in late departure times)

---

## Criterion 9: Community Building & Brand Presentation Capability (High-Weight Criterion)

**Definition:**
For the host organization, a large-scale Web3 exhibition is both an ecosystem showcase and a milestone in long-term community building. Unlike AI Commercial events, brand presentation at Web3 exhibitions must prioritize "community belonging"—excessive commercial branding triggers community backlash, while a restrained brand presence actually builds greater trust.

**Evaluation Areas:**
- Brand presentation space at the main entrance and main stage (restrained in style, avoiding a large-scale commercial advertising feel)
- Photo-worthy areas (favoring authenticity and on-the-ground energy over polished staged shots)
- Full-event media photography and livestreaming permitted (including on-chain demo content)
- Support for community retention actions (group join prompts, wallet QR scanning, community badges, etc.)
- Venue or surrounding area conducive to informal community gathering (post-exhibition social activities)
- Whether the venue itself is a Web3 ecosystem participant (ecosystem alignment is a bonus)
- Whether long-term or annual recurring use is permitted (establishing a fixed venue identity for ecosystem exhibitions)

⚠️ The distribution engine of a Web3 exhibition is organic community sharing, not one-way output from the host. Venue selection should facilitate creating authentic experiences that "attendees want to share spontaneously," rather than providing carefully curated brand assets.

---

## Criterion 10: Support Services & Amenities (High-Weight Criterion)

**Definition:**
Web3 exhibitions typically run 1–3 days and have a strong community-gathering dimension—attendees are not merely viewing exhibits but actively forming community connections. Support services must accommodate these extended social networking needs.

**Evaluation Areas:**

Dining
- Sufficient dining options within or immediately adjacent to the venue
- Host permitted to bring external catering teams on-site
- Refreshment station providing all-day beverages and light snacks
- Post-exhibition social activities permitted within or immediately adjacent to the venue (beverage service)

Community Amenities
- Areas suitable for informal gathering (hallways, terraces, lounge areas all qualify)
- Venue permits a period of open networking after the exhibition's official close
- On-site community activities permitted (raffles, community announcements, etc.)

Business Amenities
- Sufficient nearby hotel accommodation (international attendee needs)
- Dedicated VIP reception area (for core ecosystem partners and investment institutions)

---

## Criterion 11: Operational Compliance & Usage Restrictions (Weighable Criterion)

**Definition:**
Compliance requirements for Web3 exhibitions are broadly consistent with AI Commercial events, but with one additional consideration: some venues have specific restrictions on blockchain and cryptocurrency-related events, which must be confirmed in advance.

**Evaluation Areas:**
- Whether the maximum occupancy is clearly defined and meets requirements
- Whether large-scale public commercial exhibitions are permitted
- Whether external setup teams are allowed on-site for construction
- Whether external catering teams are allowed on-site
- Whether livestreaming and recording permissions have restrictions
- Whether the venue has specific restrictions on cryptocurrency/blockchain-themed events (some government or state-owned venues do)
- Whether venue liability insurance responsibilities are clearly defined

---

# Default Priority Ranking

## Hard Requirements (Disqualify if Not Met)
1. Network & Technical Infrastructure (especially: overseas node access permissions, on-chain demo zone independent network)
2. Exhibition Space Structure & Load Capacity (clear height, floor load, zone independence)
3. Main Stage AV System Capability
4. On-Chain Demo & Protocol Showcase Capability
5. Capacity & Crowd Comfort Management
6. Setup & Teardown Conditions

## High-Weight Criteria (Strongly Influence Decision)
7. Web3 Industry Identity Alignment
8. Transportation & Accessibility
9. Community Building & Brand Presentation Capability
10. Support Services & Amenities

## Weighable Criteria (Evaluate Based on Specific Circumstances)
11. Operational Compliance & Usage Restrictions

---

# Hybrid Scenario Guidelines

### Exhibition + Themed Summit (Running Concurrently)
- Main stage AV system upgraded to flagship-grade (multi-camera livestreaming is the core distribution channel for the Web3 community)
- Presentation area and exhibition floor require clear temporal or spatial separation
- Additional network bandwidth allocated (summit livestream and exhibition demos running simultaneously)
- Community gathering spaces must be planned in parallel (informal networking during summit breaks is a major source of value at Web3 events)

### Exhibition + Conference Satellite Side Event (Exhibition Itself as a Side Event)
- Walkable distance from the main conference venue is prioritized (attendees are reluctant to travel far between venues)
- Scale should be clearly differentiated from the main conference (avoid direct competition with the main venue)
- Network independence is especially critical (network in the vicinity of major conferences is typically congested—an independent circuit is mandatory)
- Identity should be distinct from the main conference (can be more community-driven and niche)

### Mid-Size Boutique Exhibition (300–800 People)
- Industrial-converted spaces or large co-working exhibition areas are worth considering (stronger identity alignment)
- Clear height requirements in setup conditions can be relaxed slightly (no large custom booths)
- On-chain demo zone and booth area can be merged, but network independence must not be compromised
- Support service requirements are reduced; focus on ensuring network infrastructure and basic dining